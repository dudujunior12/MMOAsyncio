from server.game_engine.components.collision import CollisionComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from server.systems.world_initializer import WorldInitializer
from shared.logger import get_logger
from shared.protocol import (
    PACKET_DAMAGE,
    PACKET_ENTITY_NEW,
    PACKET_ENTITY_REMOVE,
    PACKET_HEALTH_UPDATE,
    PACKET_MAP_DATA,
    PACKET_MOVE,
    PACKET_CHAT_MESSAGE,
    PACKET_ITEM_USE,
    PACKET_POSITION_UPDATE,
    PACKET_SYSTEM_MESSAGE,
)
from shared.constants import GAME_TICK_RATE, TICK_INTERVAL

logger = get_logger(__name__)
import asyncio
from server.game_engine.world import World
from server.game_engine.map import GameMap
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.db.player import get_player_data, update_player_data
from server.systems.collision import CollisionSystem
import math

A_O_I_RANGE = 25.0 # Define o raio de alcance (25 unidades de mapa)

def calculate_distance(pos1: PositionComponent, pos2: PositionComponent) -> float:
    """Calcula a distância euclidiana entre dois componentes de posição."""
    return math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)

class GameEngine:
    def __init__(self, db_pool, network_manager):
        self.db_pool = db_pool
        self.network_manager = network_manager
        self.running = False
        self.world = World()
        self.player_entity_map = {}
        self.map = GameMap()
        self.collision_system = CollisionSystem(self.map)
        self.world_initializer = WorldInitializer(self.world, self.map)
        logger.info("Game Engine initialized.")
        
    async def start(self):
        self.running = True
        self.world_initializer.initialize_world()
        logger.info("Game Engine started. Starting game loop at {} ticks per second.".format(GAME_TICK_RATE))
        asyncio.create_task(self._run_game_loop())
        
    async def _run_game_loop(self):
        while self.running:
            #self._update_movement()
            #self._update_combat()
            #self._update_npc_behaviors()
            #await self._sync_world_state()
            await asyncio.sleep(TICK_INTERVAL)
        logger.info("Game Loop stopped.")
    
    
    async def player_connected(self, writer, username):
        player_data = await get_player_data(self.db_pool, username)
        
        initial_stats = {
            'level': 1, 'experience': 0,
            'strength': 1, 'agility': 1, 'vitality': 1, 
            'intelligence': 1, 'dexterity': 1, 'luck': 1,
            'pos_x': 10.0, 'pos_y': 10.0
        }
        
        BASE_HEALTH = 100
        stats = {**initial_stats, **(player_data if player_data else {})}
        stats_comp = StatsComponent(
            level=stats['level'], 
            experience=stats['experience'],
            base_health=BASE_HEALTH,
            strength=stats['strength'],
            agility=stats['agility'],
            vitality=stats['vitality'],
            intelligence=stats['intelligence'],
            dexterity=stats['dexterity'],
            luck=stats['luck']
        )
        
        calculated_max_health = stats_comp.get_max_health_for_level()
        
        saved_current_health = player_data.get('current_health') if player_data else None
        
        if saved_current_health is None or saved_current_health <= 0:
            # Cenário 1: Novo jogador (current_health é None/NULL).
            # Cenário 2: Jogador morto (current_health <= 0).
            # Em ambos os casos, o jogador começa com a vida cheia calculada.
            initial_health = calculated_max_health
        
        elif saved_current_health > calculated_max_health:
            # Cenário 3: Vida salva > Vida Máxima atual (ajuste após nerf ou bug).
            initial_health = calculated_max_health
            
        else:
            # Cenário 4: Jogador existente com vida válida (78, 88, 100, etc.).
            # Carregamos o valor salvo, sem curar.
            initial_health = saved_current_health
        
        initial_x = stats['pos_x']
        initial_y = stats['pos_y']
        
        radius = 0.5
        
        entity_id = self.world.create_entity()
        self.world.add_component(entity_id, TypeComponent(entity_type='player'))
        self.world.add_component(entity_id, PositionComponent(initial_x, initial_y))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        self.world.add_component(entity_id, CollisionComponent(radius))
        self.world.add_component(entity_id, stats_comp)
        self.world.add_component(entity_id, HealthComponent(max_health=calculated_max_health, initial_health=initial_health))
        self.player_entity_map[username] = entity_id
        logger.info(f"Entity {entity_id} created for player {username}.")
        
        map_data_packet = {
            "type": PACKET_MAP_DATA,
            "data": self.map.get_map_data_for_client()
        }
        await self.network_manager.send_packet(writer, map_data_packet)
        logger.debug(f"Map data sent to player {username}.")
        
        
        new_entity_packet = {
            "type": PACKET_ENTITY_NEW,
            "entity_id": entity_id,
            "x": initial_x,
            "y": initial_y,
            "asset_type": username,
            "current_health": initial_health,
            "max_health": calculated_max_health,
            "level": stats_comp.level,
            "strength": stats_comp.strength,
            "agility": stats_comp.agility,
            "vitality": stats_comp.vitality,
            "inteligence": stats_comp.intelligence,
            "dexterity": stats_comp.dexterity,
            "luck": stats_comp.luck,
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
            if pos_comp and health_comp and stats_comp:
                await update_player_data(
                    self.db_pool, 
                    username, 
                    pos_comp.x, 
                    pos_comp.y,
                    health_comp.current_health,
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
                else:
                    await self.send_system_message(entity_id, f"Comando desconhecido: {command}")
            
            else:
                logger.info(f"Entity {entity_id} (User {user}) sent chat message: {message}")
                response = f"[{user}]: {message}"
                await self.network_manager.broadcast_chat_message(response, writer)
        elif pkt_type == PACKET_DAMAGE:
            target_id = packet.get('target_entity_id')
            if target_id is None:
                logger.warning(f"Malformed DAMAGE packet from {user}.")
                
            source_pos = self.world.get_component(entity_id, PositionComponent)
            target_pos = self.world.get_component(target_id, PositionComponent)
            
            ATTACK_RANGE = 2.0
            
            if not source_pos or not target_pos:
                await self.send_system_message(entity_id, "Server error in finding player position.")
                return
            
            distance = calculate_distance(source_pos, target_pos)
            
            if distance > ATTACK_RANGE:
                await self.send_system_message(entity_id, "Target is too far to attack.")
                return
            
            damage_amount = await self._calculate_final_damage(entity_id, target_id)
            
            is_dead = await self.apply_damage(target_id, damage_amount, entity_id)

            if not is_dead:
                logger.info(f"Player {user} (Entity {entity_id}) attacked Entity {target_id} for {damage_amount} damage.")
            
        elif pkt_type == PACKET_MOVE:
            logger.info(f"Entity {entity_id} (User {user}) sent move packet.")
            new_x = packet.get('x')
            new_y = packet.get('y')
            if new_x is None or new_y is None:
                logger.warning("Malformed move packet: missing coordinates.")
                return
            
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            if pos_comp:
                
                current_x = pos_comp.x
                current_y = pos_comp.y
                distance_moved = calculate_distance(pos_comp, PositionComponent(new_x, new_y))
                
                if distance_moved > 5.0:
                    logger.warning(f"User {user} attempted invalid move distance ({distance_moved:.2f})")
                    await self.network_manager.send_packet(writer, {
                        "type": PACKET_POSITION_UPDATE,
                        "entity_id": entity_id,
                        "x": current_x, 
                        "y": current_y,
                        "asset_type": user
                    })
                    return
                
                moved, final_x, final_y = self.collision_system.process_movement(entity_id, pos_comp, new_x, new_y, self.world)
                
                if not moved:
                    await self.network_manager.send_packet(writer, {
                        "type": PACKET_POSITION_UPDATE,
                        "entity_id": entity_id,
                        "x": current_x, 
                        "y": current_y,
                        "asset_type": user
                    })
                    return

                pos_comp.x = final_x
                pos_comp.y = final_y
                
                logger.debug(f"Updated position for Entity {entity_id} to ({final_x}, {final_y})")
                
                update_packet = {
                    "type": PACKET_POSITION_UPDATE,
                    "entity_id": entity_id,
                    "x": final_x,
                    "y": final_y,
                    "asset_type": user
                }
                
                await self.send_aoi_update(entity_id, update_packet, exclude_writer=writer)
                await self.network_manager.send_packet(writer, update_packet)
        
        elif pkt_type == PACKET_ITEM_USE:
            pass
        else:
            logger.warning(f"Unknown packet type received: {pkt_type}")
            
    async def send_aoi_update(self, source_entity_id: int, packet: dict, exclude_writer=None):
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
            f"INT: {stats_comp.intelligence} | DEX: {stats_comp.dexterity} | LUC: {stats_comp.luck}"
        )
        
        await self.send_system_message(entity_id, message)
        
    async def _broadcast_health_update(self, entity_id: int, health_comp: HealthComponent):
        health_update_packet = {
            "type": PACKET_HEALTH_UPDATE,
            "entity_id": entity_id,
            "current_health": health_comp.current_health,
            "max_health": health_comp.max_health
        }
        
        target_network_comp = self.world.get_component(entity_id, NetworkComponent)
        target_writer = target_network_comp.writer if target_network_comp else None
        
        if target_writer:
             await self.network_manager.send_packet(target_writer, health_update_packet)

        await self.send_aoi_update(entity_id, health_update_packet, exclude_writer=target_writer)
            
    async def apply_damage(self, target_entity_id: int, damage_amount: int, source_entity_id: int = None):
        
        health_comp = self.world.get_component(target_entity_id, HealthComponent)
        
        if not health_comp or health_comp.is_dead:
            return False

        damage_dealt = health_comp.take_damage(damage_amount)
        
        logger.info(f"Entity {target_entity_id} took {damage_dealt} damage. HP: {health_comp.current_health}/{health_comp.max_health}")
        
        await self._broadcast_health_update(target_entity_id, health_comp)
        
        source_user = "Unknown"
        if source_entity_id:
            source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
            if source_network_comp:
                    source_user = source_network_comp.username

        target_user = self.world.get_component(target_entity_id, NetworkComponent).username if self.world.get_component(target_entity_id, NetworkComponent) else f"Entity {target_entity_id}"

        if source_entity_id:
            await self.send_system_message(source_entity_id, f"You dealt {damage_dealt} of damage to {target_user}.")

        await self.send_system_message(target_entity_id, f"You received {damage_dealt} of damage from {source_user}. Health left: {health_comp.current_health}/{health_comp.max_health}")


        if health_comp.is_dead:
            logger.info(f"Entity {target_entity_id} has died.")
            
            await self.network_manager.broadcast_system_message(f"{target_user} has been defeated!", exclude_writer=None)
            
            RESPAWN_X = 10.0 
            RESPAWN_Y = 10.0 
            
            await self._handle_entity_death(target_entity_id, target_user, RESPAWN_X, RESPAWN_Y, source_id=source_entity_id)
            
            return True
            
        return False
    
    async def _calculate_final_damage(self, source_id: int, target_id: int) -> int:
        source_stats = self.world.get_component(source_id, StatsComponent)
        target_stats = self.world.get_component(target_id, StatsComponent)

        if not source_stats or not target_stats:
            return 1 

        raw_attack = source_stats.get_attack_power() 
        
        BASE_DEFENSE = 5
        DEFENSE_BONUS_PER_VIT = 1

        total_defense = BASE_DEFENSE + (target_stats.vitality * DEFENSE_BONUS_PER_VIT)

        final_damage = raw_attack - total_defense

        return max(1, final_damage)
    
    async def _handle_entity_death(self, entity_id: int, target_name: str, initial_x: float = 10.0, initial_y: float = 10.0, source_id: int = None):
        if self.is_player(entity_id):
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            health_comp = self.world.get_component(entity_id, HealthComponent)
            
            if pos_comp and health_comp:
                pos_comp.x = initial_x
                pos_comp.y = initial_y
                
                health_comp.heal_to_full() 
                
                await self.send_system_message(entity_id, "You have been defeated! Returning to spawn.")
                
                respawn_pos_packet = {
                    "type": PACKET_POSITION_UPDATE,
                    "entity_id": entity_id,
                    "x": pos_comp.x,
                    "y": pos_comp.y,
                    "asset_type": target_name
                }
                await self.send_aoi_update(entity_id, respawn_pos_packet, exclude_writer=None) 
                
                await self._broadcast_health_update(entity_id, health_comp)
            else:
                logger.error(f"Cannot respawn Player {entity_id}: Missing Position or Health Component.")
                
        elif self.is_monster(entity_id):
            
            logger.info(f"Monster {target_name} (Entity {entity_id}) died. Removing entity.")
            
            # TODO: Adicionar lógica de EXP para o source_id (jogador que matou)
            # TODO: Adicionar lógica de Drop de Itens
            
            remove_packet = {
                "type": PACKET_ENTITY_REMOVE,
                "entity_id": entity_id,
                "asset_type": target_name
            }
            await self.send_aoi_update(entity_id, remove_packet) 

            self.world.remove_entity(entity_id)
            
            # TODO: Adicionar temporizador de respawn
            
        else:
            logger.warning(f"Entity {entity_id} died but its type ({target_name}) is unknown. Ignoring death logic.")
            
    def get_type_comp(self, entity_id: int):
        """Método de conveniência para obter o TypeComponent."""
        # Se não tiver, verifica se é um jogador pela rede (fallback)
        type_comp = self.world.get_component(entity_id, TypeComponent)
        if type_comp:
            return type_comp

        return None

    def is_player(self, entity_id: int) -> bool:
        """Identifica se a entidade é um jogador."""
        type_comp = self.get_type_comp(entity_id)
        return type_comp and type_comp.entity_type == 'player'

    def is_monster(self, entity_id: int) -> bool:
        """Identifica se a entidade é um monstro."""
        type_comp = self.get_type_comp(entity_id)
        return type_comp and type_comp.entity_type == 'monster'
            
    async def _receive_initial_aoi(self, target_entity_id: int, target_writer):
        target_pos_comp = self.world.get_component(target_entity_id, PositionComponent)
        if not target_pos_comp:
            return

        for source_username, source_entity_id in self.player_entity_map.items():
            if source_entity_id == target_entity_id:
                continue
                
            source_pos_comp = self.world.get_component(source_entity_id, PositionComponent)
            
            source_health_comp = self.world.get_component(source_entity_id, HealthComponent)
            source_stats_comp = self.world.get_component(source_entity_id, StatsComponent)
            
            distance = calculate_distance(target_pos_comp, source_pos_comp)
            if source_pos_comp and distance <= A_O_I_RANGE:
                logger.debug(f"AoI Initial Sync: Sending Entity {source_entity_id} to New Player {target_entity_id}. Dist: {distance:.2f}")
                source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
                
                new_entity_packet = {
                    "type": PACKET_ENTITY_NEW,
                    "entity_id": source_entity_id,
                    "x": source_pos_comp.x,
                    "y": source_pos_comp.y,
                    "asset_type": source_network_comp.username if source_network_comp else "NPC"
                }
                
                if source_health_comp:
                    new_entity_packet["current_health"] = source_health_comp.current_health
                    new_entity_packet["max_health"] = source_health_comp.max_health
                    
                if source_stats_comp:
                    new_entity_packet["level"] = source_stats_comp.level
                    new_entity_packet["strength"] = source_stats_comp.strength
                    new_entity_packet["agility"] = source_stats_comp.agility
                    new_entity_packet["vitality"] = source_stats_comp.vitality
                    new_entity_packet["intelligence"] = source_stats_comp.intelligence
                    new_entity_packet["dexterity"] = source_stats_comp.dexterity
                    new_entity_packet["luck"] = source_stats_comp.luck
                await self.network_manager.send_packet(target_writer, new_entity_packet)
            
    async def _sync_world_state(self):
        world_state_data = []
        
        for entity_id, (pos_comp,) in self.world.get_components_of_type(PositionComponent):
            network_comp = self.world.get_component(entity_id, NetworkComponent)
            
            asset_type = None
            
            if network_comp:
                asset_type = network_comp.username
            else:
                asset_type = f"NPC_{entity_id}"
            
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
        
        #logger.debug(f"World State synced. Broadcasting {len(world_state_data)} entities.")
            
    async def shutdown(self):
        logger.info("Game Engine shutdown complete.")