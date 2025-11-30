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
from server.db.player import get_player_data, update_player_data
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
            logger.info(f"New player '{username}'. Loading {DEFAULT_CLASS} base stats.")
            metadata = get_class_metadata(DEFAULT_CLASS) or {}
            base_stats = metadata.get("base_stats", {})

            # Inicializa valores que serão persistidos para o player
            final_data = {
                'class_name': DEFAULT_CLASS,
                'level': 1,
                'experience': 0,
                'stat_points': 0,
                'pos_x': 10.0,
                'pos_y': 10.0,
                'current_health': None,
                # base stats (persistidos) — jogador começa com os valores da classe base como pontos iniciais
                'strength': base_stats.get('strength', 1),
                'agility': base_stats.get('agility', 1),
                'vitality': base_stats.get('vitality', 1),
                'intelligence': base_stats.get('intelligence', 1),
                'dexterity': base_stats.get('dexterity', 1),
                'luck': base_stats.get('luck', 1),
                'base_health': base_stats.get('base_health', 100)
            }

        else:
            is_fresh_player = player_data.get('level', 0) == 1 and player_data.get('experience', -1) == 0
            if is_fresh_player:
                log_message = f"New player '{username}' (freshly registered). Loading {DEFAULT_CLASS} metadata stats."
            else:
                log_message = f"Existing player '{username}' (Lvl {player_data.get('level', 1)}) loaded from DB."
            logger.info(log_message)

            # Inicializa final_data com todos os dados salvos (não sobrescrever)
            final_data = dict(player_data)  # cópia rasa

            class_name = final_data.get('class_name', DEFAULT_CLASS)
            current_metadata = get_class_metadata(class_name) or {}
            base_stats = current_metadata.get("base_stats", {})
            
            # Assegura campos mínimos existam (stats do player)
            stats_to_load = ['strength', 'agility', 'vitality', 'intelligence', 'dexterity', 'luck']
            for stat in stats_to_load:
                if final_data.get(stat) is None:
                    # fallback caso DB não tenha campo (campo novo), usa o base da classe
                    final_data[stat] = base_stats.get(stat, 1)

            # garante base_health (que vem da classe, não do player)
            final_data['base_health'] = final_data.get('base_health', base_stats.get('base_health', 100))
            final_data.setdefault('stat_points', 0)

            # Se player foi criado mas é "fresh" (caso especial), re-inicializa posições/vida e stat points
            if is_fresh_player:
                final_data.update({
                    'level': 1,
                    'experience': 0,
                    'pos_x': 10.0,
                    'pos_y': 10.0,
                    'current_health': None,
                    'stat_points': 0,
                })

            final_data['class_name'] = class_name
            
        # --- ENVIA MAPA ---
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

        # --- CRIAR ENTIDADE E COMPONENTES ---
        entity_id = self.world.create_entity()

        # 1. Classe
        class_comp = ClassComponent(class_name=final_data['class_name'])
        self.world.add_component(entity_id, class_comp)

        # 2. Stats (Usa valores finais calculados acima)
        stats_comp = StatsComponent(
            level=final_data.get('level', 1),
            experience=final_data.get('experience', 0),
            base_health=final_data.get('base_health', 100),
            strength=final_data.get('strength', 1),
            agility=final_data.get('agility', 1),
            vitality=final_data.get('vitality', 1),
            intelligence=final_data.get('intelligence', 1),
            dexterity=final_data.get('dexterity', 1),
            luck=final_data.get('luck', 1),
            stat_points=final_data.get('stat_points', 0)
        )
        self.world.add_component(entity_id, stats_comp)

        # 3. Posição e Rede
        initial_x = final_data.get('pos_x', 10.0)
        initial_y = final_data.get('pos_y', 10.0)
        radius = 0.5

        self.world.add_component(entity_id, TypeComponent(entity_type='player'))
        self.world.add_component(entity_id, PositionComponent(initial_x, initial_y))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        self.world.add_component(entity_id, CollisionComponent(radius))

        # 4. Vida (Health)
        calculated_max_health = stats_comp.get_max_health_for_level()
        saved_current_health = final_data.get('current_health')

        if saved_current_health is None or saved_current_health <= 0:
            initial_health = calculated_max_health
        elif saved_current_health > calculated_max_health:
            initial_health = calculated_max_health
        else:
            initial_health = saved_current_health

        self.world.add_component(entity_id, HealthComponent(max_health=calculated_max_health, initial_health=initial_health))
        
        # Registrar no mapa de entidades
        self.player_entity_map[username] = entity_id
        logger.info(f"Entity {entity_id} created for player {username}.")

        # --- ENVIAR PACOTE DE ENTIDADE USANDO SERIALIZADOR ---
        # Aqui usamos o packet_builder para evitar repetição manual de campos
        entity_data = packet_builder.serialize_entity(self.world, entity_id)
        
        new_entity_packet = {
            "type": PACKET_ENTITY_NEW,
            **entity_data # Espalha todos os dados (level, stats, class, health, etc)
        }
        
        await self.network_manager.send_packet(writer, new_entity_packet)
        await self.send_aoi_update(entity_id, new_entity_packet, exclude_writer=writer)
        await self._receive_initial_aoi(entity_id, writer)
        
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
                    stats_comp.luck
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
        # O método de envio permanece o mesmo, mas agora o pacote já vem serializado
        source_pos_comp = self.world.get_component(source_entity_id, PositionComponent)
        if not source_pos_comp:
            return

        target_writers = []
        
        for target_username, target_entity_id in self.player_entity_map.items():
            
            target_network_comp = self.world.get_component(target_entity_id, NetworkComponent)
            target_pos_comp = self.world.get_component(target_entity_id, PositionComponent)
            
            if not target_pos_comp or not target_network_comp:
                continue
                
            writer = target_network_comp.writer
            
            if writer == exclude_writer:
                continue

            distance = calculate_distance(source_pos_comp, target_pos_comp)
            
            if distance <= A_O_I_RANGE:
                target_writers.append(writer)

        for writer in target_writers:
            await self.network_manager.send_packet(writer, packet)
            
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
            
    async def _receive_initial_aoi(self, target_entity_id: int, target_writer):
        target_pos_comp = self.world.get_component(target_entity_id, PositionComponent)
        if not target_pos_comp:
            return

        for source_entity_id, (source_pos_comp,) in self.world.get_components_of_type(PositionComponent):
            if source_entity_id == target_entity_id:
                continue
            
            source_pos_comp = self.world.get_component(source_entity_id, PositionComponent)
            distance = calculate_distance(target_pos_comp, source_pos_comp)
            
            if source_pos_comp and distance <= A_O_I_RANGE:
                #logger.debug(f"AoI Initial Sync: Sending Entity {source_entity_id} to New Player {target_entity_id}.")
                
                entity_data = packet_builder.serialize_entity(self.world, source_entity_id)
                
                if "asset_type" not in entity_data: continue

                new_entity_packet = {
                    "type": PACKET_ENTITY_NEW,
                    **entity_data
                }
                
                await self.network_manager.send_packet(target_writer, new_entity_packet)
                
    async def broadcast_entity_removal(self, entity_id: int, asset_type: str, exclude_writer=None):
        removal_packet = {
            'type': PACKET_ENTITY_REMOVE,
            'entity_id': entity_id,
            'asset_type': asset_type,
        }

        for target_username, target_entity_id in self.player_entity_map.items():
            target_network_comp = self.world.get_component(target_entity_id, NetworkComponent)
            if not target_network_comp or not target_network_comp.writer:
                continue

            writer = target_network_comp.writer
            if writer == exclude_writer:
                continue

            try:
                await self.network_manager.send_packet(writer, removal_packet)
            except Exception as e:
                logger.error(f"Error sending entity removal packet to {target_username}: {e}")
            
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