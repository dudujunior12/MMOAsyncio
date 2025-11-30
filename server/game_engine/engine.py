from server.game_engine.components.player_class import ClassComponent
from server.game_engine.components.collision import CollisionComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from server.systems.ai_system import AISystem
from server.systems.combat_system import CombatSystem, calculate_distance
from server.systems.evolution import EvolutionSystem
from server.systems.movement_system import MovementSystem
from server.systems.world_initializer import WorldInitializer
from server.utils.class_loader import get_class_metadata
from server.utils.map_loader import load_map_metadata
from shared.logger import get_logger
from server.game_engine.serialization import packet_builder # <--- IMPORTANTE: O SERIALIZADOR
from shared.protocol import (
    PACKET_DAMAGE,
    PACKET_ENTITY_NEW,
    PACKET_ENTITY_REMOVE,
    PACKET_ENTITY_UPDATE,
    PACKET_EVOLVE,
    PACKET_MAP_DATA,
    PACKET_MOVE,
    PACKET_CHAT_MESSAGE,
    PACKET_ITEM_USE,
    PACKET_SYSTEM_MESSAGE,
)
from shared.constants import A_O_I_RANGE, GAME_TICK_RATE, PLAYER_ATTRS, STAT_ALIAS_MAP, TICK_INTERVAL

logger = get_logger(__name__)
import asyncio
from server.game_engine.world import World
from server.game_engine.map import GameMap
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.game_engine.components.viewport import ViewportComponent
from server.db.player import get_player_data, update_player_data
from server.game_engine.collision.shapes import BoxCollider
from server.systems.collision import CollisionSystem

class GameEngine:
    def __init__(self, db_pool, network_manager):
        self.db_pool = db_pool
        self.network_manager = network_manager
        self.running = False
        self.world = World()
        self.player_entity_map = {}
        initial_map_data = load_map_metadata("Starting_Area")
        if not initial_map_data:
            raise Exception("Critical: Could not load initial map metadata.")
        self.current_map_name = "Starting_Area"
        self.map = GameMap(self.current_map_name, initial_map_data)
        
        self.collision_system = CollisionSystem(self.map)
        self.world_initializer = WorldInitializer(self.world, self.map, self.db_pool)
        self.combat_system = CombatSystem(
            self.world, 
            self.network_manager, 
            self.send_aoi_update,
            self.send_system_message
        )
        self.movement_system = MovementSystem(
            self.world,
            self.network_manager,
            self.collision_system,
            self.send_aoi_update
        )
        self.ai_system = AISystem(
            self.world,
            self.movement_system,
            self.send_aoi_update
        )
        self.evolution_system = EvolutionSystem(self.world, self)
        logger.info("Game Engine initialized.")
        
    async def start(self):
        self.running = True
        await self.world_initializer.initialize_world()
        logger.info("Game Engine started. Starting game loop at {} ticks per second.".format(GAME_TICK_RATE))
        asyncio.create_task(self._run_game_loop())
        
    async def _run_game_loop(self):
        while self.running:
            #self._update_movement()
            #self._update_combat()
            #self._update_npc_behaviors()
            #await self.ai_system.run()
            await asyncio.sleep(TICK_INTERVAL)
        logger.info("Game Loop stopped.")
    
    
    async def player_connected(self, writer, username):
        player_data = await get_player_data(self.db_pool, username)

        DEFAULT_CLASS = 'Novice'
        final_data = {}

        if player_data is None:
            logger.info(f"New player '{username}'. Loading {DEFAULT_CLASS} class metadata.")

            metadata = get_class_metadata(DEFAULT_CLASS) or {}

            class_bonus = metadata.get("class_bonus", {})
            base_health = metadata.get("base_health", 100)

            final_data = {
                'class_name': DEFAULT_CLASS,
                'level': 1,
                'experience': 0,
                'stat_points': 0,
                'pos_x': 10.0,
                'pos_y': 10.0,
                'current_health': None,
                'strength': 1,
                'agility': 1,
                'vitality': 1,
                'intelligence': 1,
                'dexterity': 1,
                'luck': 1,
                'base_health': base_health,
                'class_bonus': class_bonus
            }

        else:
            final_data = dict(player_data)

            class_name = final_data.get('class_name', DEFAULT_CLASS)
            current_metadata = get_class_metadata(class_name) or {}

            class_bonus = current_metadata.get("class_bonus", {})
            base_health = current_metadata.get("base_health", 100)

            final_data['base_health'] = base_health
            final_data['class_bonus'] = class_bonus

            for stat in ['strength', 'agility', 'vitality', 'intelligence', 'dexterity', 'luck']:
                if final_data.get(stat) is None:
                    final_data[stat] = 1

            final_data.setdefault('stat_points', 0)
            final_data['class_name'] = class_name

        map_packet = {
            "type": PACKET_MAP_DATA,
            "map_name": self.map.MAP_NAME,
            "width": self.map.MAP_WIDTH,
            "height": self.map.MAP_HEIGHT,
            "tiles": self.map._tile_data,
            "metadata": self.map.tile_metadata
        }
        await self.network_manager.send_packet(writer, map_packet)
        logger.info(f"Sent map '{self.map.MAP_NAME}' to player {username}.")

        entity_id = self.world.create_entity()

        self.world.add_component(entity_id, ClassComponent(final_data['class_name']))

        stats_comp = StatsComponent(
            level=final_data['level'],
            experience=final_data['experience'],
            stat_points=final_data['stat_points'],

            base_health=final_data['base_health'],

            strength=final_data['strength'],
            agility=final_data['agility'],
            vitality=final_data['vitality'],
            intelligence=final_data['intelligence'],
            dexterity=final_data['dexterity'],
            luck=final_data['luck'],

            class_bonus=final_data['class_bonus']
        )
        self.world.add_component(entity_id, stats_comp)

        self.world.add_component(entity_id, TypeComponent('player'))
        self.world.add_component(entity_id, PositionComponent(final_data['pos_x'], final_data['pos_y']))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        self.world.add_component(entity_id, CollisionComponent(BoxCollider(1, 1)))
        self.world.add_component(entity_id, ViewportComponent(radius=A_O_I_RANGE))


        max_hp = stats_comp.get_max_health_for_level()
        saved_hp = final_data.get('current_health')

        if saved_hp is None or saved_hp <= 0:
            initial_hp = max_hp
        elif saved_hp > max_hp:
            initial_hp = max_hp
        else:
            initial_hp = saved_hp

        self.world.add_component(entity_id, HealthComponent(max_health=max_hp, initial_health=initial_hp))


        self.player_entity_map[username] = entity_id
        logger.info(f"Entity {entity_id} created for player {username}.")

        entity_data = packet_builder.serialize_entity(self.world, entity_id)

        # Pacote para o próprio jogador (is_local_player: True)
        local_player_packet = {
            "type": PACKET_ENTITY_NEW,
            "is_local_player": True,
            **entity_data
        }
        await self.network_manager.send_packet(writer, local_player_packet)

        await self._receive_initial_aoi(entity_id, writer)

        neighbor_packet = {
            "type": PACKET_ENTITY_NEW,
            "is_local_player": False,
            **entity_data
        }
        await self.send_aoi_update(entity_id, neighbor_packet, exclude_writer=writer)
        
    async def player_disconnected(self, username):
        entity_id = self.player_entity_map.pop(username, None)
        if entity_id:
            network_comp = self.world.get_component(entity_id, NetworkComponent)
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            health_comp = self.world.get_component(entity_id, HealthComponent)
            stats_comp = self.world.get_component(entity_id, StatsComponent)
            class_comp = self.world.get_component(entity_id, ClassComponent)
            
            if pos_comp and health_comp and stats_comp and class_comp:
                await update_player_data(
                    self.db_pool, 
                    username, 
                    pos_comp.x, 
                    pos_comp.y,
                    health_comp.current_health,
                    stats_comp.stat_points,
                    class_comp.class_name,
                    stats_comp.level,
                    stats_comp.experience,
                    stats_comp.strength,
                    stats_comp.agility,
                    stats_comp.vitality,
                    stats_comp.intelligence,
                    stats_comp.dexterity,
                    stats_comp.luck,
                )
                logger.info(f"Saved player {username}'s state: Pos ({pos_comp.x:.1f}, {pos_comp.y:.1f}), HP {health_comp.current_health}, Lvl {stats_comp.level}")
            
            asset_type = network_comp.username if network_comp else f"Entity {entity_id}"

            self.world.remove_entity(entity_id)
            logger.info(f"Entity {entity_id} removed for player {username}.")
            
            return entity_id, asset_type
        return None, None
    
    def get_player_entity_id(self, username: str) -> int | None:
        return self.player_entity_map.get(username)
    
    async def process_network_packet(self, writer, packet):
        pkt_type = packet.get('type')
        user = self.network_manager.get_user_by_writer(writer)
        if not user:
            logger.warning("Received packet from unauthenticated user.")
            return

        entity_id = self.get_player_entity_id(user)
        
        if pkt_type == PACKET_CHAT_MESSAGE:
            message = packet.get('content', '').strip()
            
            if message.startswith('/'):
                parts = message.split()
                command = parts[0].lower()

                if command == '/stats':
                    await self.handle_command_stats(entity_id)
                elif command == '/evolve':
                    await self.handle_command_evolve(entity_id, parts)
                elif command == '/add':
                    await self.handle_command_add_stat(entity_id, parts)
                else:
                    await self.send_system_message(entity_id, f"Comando desconhecido: {command}")
            
            else:
                logger.info(f"Entity {entity_id} (User {user}) sent chat message: {message}")
                await self.network_manager.broadcast_chat_message(
                    sender=user,
                    message=message,
                    exclude_writer=None
                )
                
        elif pkt_type == PACKET_DAMAGE:
            target_id = packet.get('target_entity_id')
            if target_id is None:
                logger.warning(f"Malformed DAMAGE packet from {user}.")
            else:    
                await self.combat_system.handle_damage_request(entity_id, target_id)
            
        elif pkt_type == PACKET_MOVE:
            #logger.debug(f"Entity {entity_id} (User {user}) sent move packet.")
            x = packet.get('x')
            y = packet.get('y')
            
            if x is None or y is None:
                 dx = packet.get('dx')
                 dy = packet.get('dy')
                 if dx is not None and dy is not None:
                     await self.movement_system.handle_move_request(entity_id, writer, dx, dy)
                 else:
                     logger.warning("Malformed move packet: missing coordinates.")
                     return
            else:
                 await self.movement_system.handle_move_request(entity_id, writer, x, y)
            
        elif pkt_type == PACKET_EVOLVE:
            target_class_name = packet.get('class_name')
            if target_class_name:
                await self.evolution_system.change_class(entity_id, target_class_name)
                
                entity_data = packet_builder.serialize_entity(self.world, entity_id)
                update_packet = {
                    "type": PACKET_ENTITY_UPDATE,
                    **entity_data
                }
                await self.send_aoi_update(entity_id, update_packet)
            else:
                logger.warning(f"Malformed EVOLVE packet from {user}: missing class_name.")
                await self.send_system_message(entity_id, "Error: Target class name missing for evolution.")
        
        elif pkt_type == PACKET_ITEM_USE:
            pass
        else:
            logger.warning(f"Unknown packet type received: {pkt_type}")
            

    async def handle_command_add_stat(self, entity_id: int, parts: list):
        if len(parts) < 2:
            await self.send_system_message(entity_id, f"Use: /add <{ '|'.join(STAT_ALIAS_MAP.keys()) }>")
            return

        stat_alias = parts[1].lower()
        stats_comp = self.world.get_component(entity_id, StatsComponent)
        if not stats_comp:
            return

        if stats_comp.stat_points <= 0:
            await self.send_system_message(entity_id, "You do not have enough stat points.")
            return

        if stat_alias not in STAT_ALIAS_MAP:
            await self.send_system_message(entity_id, f"Invalid attribute. Use: {', '.join(STAT_ALIAS_MAP.keys())}")
            return

        attr_name = STAT_ALIAS_MAP[stat_alias]

        current_val = getattr(stats_comp, attr_name)
        setattr(stats_comp, attr_name, current_val + 1)
        stats_comp.stat_points -= 1

        if attr_name == "vitality":
            health_comp = self.world.get_component(entity_id, HealthComponent)
            if health_comp:
                health_comp.max_health = stats_comp.get_max_health_for_level()

        await self.send_system_message(
            entity_id, f"{attr_name.capitalize()} increased to {current_val + 1}. Remaining points: {stats_comp.stat_points}"
        )

        entity_data = packet_builder.serialize_entity(self.world, entity_id)
        update_packet = {
            "type": PACKET_ENTITY_UPDATE,
            **entity_data
        }
        await self.send_aoi_update(entity_id, update_packet)
                
    async def handle_command_evolve(self, entity_id: int, parts: list):
        if not self.is_player(entity_id):
            await self.send_system_message(entity_id, "Erro: Apenas jogadores podem evoluir.")
            return

        if len(parts) < 2:
            await self.send_system_message(entity_id, "Uso: /evolve <ClasseAlvo>")
            class_comp = self.world.get_component(entity_id, ClassComponent)
            if class_comp:
                metadata = get_class_metadata(class_comp.class_name)
                evolution = metadata.get('evolution')
                if evolution:
                    targets = ", ".join(evolution.get('to_classes', []))
                    await self.send_system_message(entity_id, f"Evoluções disponíveis (Nível {evolution.get('level')}): {targets}")
            return

        target_class_name = parts[1]
        
        # Chama o sistema de evolução para processar a mudança
        success = await self.evolution_system.change_class(entity_id, target_class_name)
        
        if success:
            # Depois da evolução, envia pacote atualizado usando serialize_entity
            entity_data = packet_builder.serialize_entity(self.world, entity_id)
            update_packet = {
                "type": PACKET_ENTITY_UPDATE,
                **entity_data
            }
            await self.send_aoi_update(entity_id, update_packet)
            
    async def send_aoi_update(self, source_entity_id: int, packet: dict, exclude_writer=None):
            """
            Atualiza todos os jogadores sobre uma mudança de estado de uma entidade.
            Garante envio apenas para os que estão na AOI e evita duplicação.
            """
            # ... código para obter source_pos ...
            source_pos = self.world.get_component(source_entity_id, PositionComponent)
            if not source_pos:
                return

            # Obter o NetworkComponent da entidade fonte para checar se é um jogador
            source_net = self.world.get_component(source_entity_id, NetworkComponent)
            source_is_player = source_net is not None
            
            for username, player_id in self.player_entity_map.items():
                # ... código para obter net, viewport, player_pos ...
                net = self.world.get_component(player_id, NetworkComponent)
                viewport = self.world.get_component(player_id, ViewportComponent)
                player_pos = self.world.get_component(player_id, PositionComponent)

                if not net or not viewport or not player_pos:
                    continue

                writer = net.writer
                if writer == exclude_writer:
                    continue

                # Cálculo de distância (supondo que a AOI é um quadrado: dx <= radius and dy <= radius)
                dx = abs(player_pos.x - source_pos.x)
                dy = abs(player_pos.y - source_pos.y)

                entity_visible = dx <= viewport.radius and dy <= viewport.radius
                already_sent = source_entity_id in viewport.last_sent_entities

                if entity_visible:
                    if not already_sent:
                        # Entidade Fonte (PN) ENTROU na AOI do Player Vizinho (PA).
                        
                        # 1. Player Vizinho (PA) agora vê a Entidade Fonte (PN).
                        viewport.last_sent_entities.add(source_entity_id)
                        enter_packet = { 
                            "type": PACKET_ENTITY_NEW,
                            "is_local_player": False,
                            **packet_builder.serialize_entity(self.world, source_entity_id)
                        }
                        await self.network_manager.send_packet(writer, enter_packet)
                        
                        # 2. **NOVO**: Se a Entidade Fonte (PN) é um jogador,
                        # e o Player Vizinho (PA) é um vizinho (que não está se movendo), 
                        # então o Player Vizinho (PA) precisa ser notificado de volta para a Entidade Fonte (PN).
                        # A Entidade Fonte (PN) está AGORA vendo o Player Vizinho (PA)
                        if source_is_player:
                            source_viewport = self.world.get_component(source_entity_id, ViewportComponent)
                            if source_viewport and player_id not in source_viewport.last_sent_entities:
                                
                                # O Player Novo (PN) AGORA vê o Player Antigo (PA).
                                source_viewport.last_sent_entities.add(player_id)
                                
                                pa_data = packet_builder.serialize_entity(self.world, player_id)
                                reverse_enter_packet = {
                                    "type": PACKET_ENTITY_NEW,
                                    "is_local_player": False,
                                    **pa_data
                                }
                                # Envia o pacote do PA para o PN
                                await self.network_manager.send_packet(source_net.writer, reverse_enter_packet)
                                
                    else:
                        # Já estava na AOI, apenas atualiza
                        await self.network_manager.send_packet(writer, packet)

                elif already_sent:
                    # Saiu da AOI
                    viewport.last_sent_entities.remove(source_entity_id)
                    leave_packet = {
                        "type": PACKET_ENTITY_REMOVE,
                        "entity_id": source_entity_id
                    }
                    await self.network_manager.send_packet(writer, leave_packet)

            
    async def send_system_message(self, target_entity_id: int, message: str):
        network_comp = self.world.get_component(target_entity_id, NetworkComponent)
        if network_comp and network_comp.writer:
            packet = {
                "type": PACKET_SYSTEM_MESSAGE, 
                "content": message
            }
            await self.network_manager.send_packet(network_comp.writer, packet)

    async def handle_command_stats(self, entity_id: int):
        
        stats_comp = self.world.get_component(entity_id, StatsComponent)
        health_comp = self.world.get_component(entity_id, HealthComponent)
        network_comp = self.world.get_component(entity_id, NetworkComponent)
        
        if not stats_comp or not health_comp or not network_comp:
            await self.send_system_message(entity_id, "Error: Health/Stats Components not found.")
            return

        try:
            attack_power = stats_comp.get_attack_power()
        except AttributeError:
            attack_power = "N/A (Missing get_attack_power)"
        
        message = (
            f"--- STATUS OF {network_comp.username.upper()} ---\n"
            f"Level: {stats_comp.level} | EXP: {stats_comp.experience}\n"
            f"Health: {health_comp.current_health}/{health_comp.max_health}\n"
            f"Attack: {attack_power}\n"
            f"STR: {stats_comp.strength} | AGI: {stats_comp.agility} | VIT: {stats_comp.vitality}\n"
            f"INT: {stats_comp.intelligence} | DEX: {stats_comp.dexterity} | LUC: {stats_comp.luck}\n"
            f"Stat Points Available: {stats_comp.stat_points}"
        )
        
        await self.send_system_message(entity_id, message)
            
    def get_type_comp(self, entity_id: int):
        type_comp = self.world.get_component(entity_id, TypeComponent)
        if type_comp:
            return type_comp

        return None

    def is_player(self, entity_id: int) -> bool:
        type_comp = self.get_type_comp(entity_id)
        return type_comp and type_comp.entity_type == 'player'

    def is_monster(self, entity_id: int) -> bool:
        type_comp = self.get_type_comp(entity_id)
        return type_comp and type_comp.entity_type == 'monster'
            
    async def _receive_initial_aoi(self, entity_id, writer):
            """
            Envia visão inicial do mundo para o jogador recém-conectado.
            """
            pos = self.world.get_component(entity_id, PositionComponent)
            viewport = self.world.get_component(entity_id, ViewportComponent)

            if not pos or not viewport:
                return

            # 1️⃣ Enviar entidades existentes para o novo jogador
            visible = []
            for other_id, (other_pos,) in self.world.get_components_of_type(PositionComponent):
                if other_id == entity_id:
                    continue
                
                if abs(other_pos.x - pos.x) <= viewport.radius and abs(other_pos.y - pos.y) <= viewport.radius:
                    entity_data = packet_builder.serialize_entity(self.world, other_id)
                    visible.append(entity_data)

            # Atualiza o last_sent_entities do NOVO jogador com quem ele VÊ.
            viewport.last_sent_entities = set(e.get("id") or e.get("entity_id") for e in visible)

            for entity_data in visible:
                entry_packet = {
                    "type": PACKET_ENTITY_NEW,
                    "is_local_player": False,
                    **entity_data
                }
                await self.network_manager.send_packet(writer, entry_packet)
            
    async def _sync_world_state(self):
        world_state_data = []
        
        for entity_id, (pos_comp,) in self.world.get_components_of_type(PositionComponent):
            network_comp = self.world.get_component(entity_id, NetworkComponent)
            asset_type = network_comp.username if network_comp else f"NPC_{entity_id}"
            
            entity_data = {
                "id": entity_id,
                "x": pos_comp.x,
                "y": pos_comp.y,
                "asset_type": asset_type
            }
            world_state_data.append(entity_data)
        
        world_state_packet = {
            "type": "WORLD_STATE",
            "entities": world_state_data
        }
        
        await self.network_manager.broadcast_game_update(world_state_packet)
            
    async def shutdown(self):
        logger.info("Game Engine shutdown complete.")