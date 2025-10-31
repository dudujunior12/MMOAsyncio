from server.game_engine.components.collision import CollisionComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from server.systems.ai_system import AISystem
from server.systems.combat_system import CombatSystem, calculate_distance
from server.systems.movement_system import MovementSystem
from server.systems.world_initializer import WorldInitializer
from server.utils.map_loader import load_map_metadata
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
from shared.constants import A_O_I_RANGE, GAME_TICK_RATE, TICK_INTERVAL

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
            #await self.ai_system.run() descomentar para voltar a funcionar movimento de npc
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
            initial_health = calculated_max_health
        
        elif saved_current_health > calculated_max_health:
            initial_health = calculated_max_health
            
        else:
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
                
            await self.combat_system.handle_damage_request(entity_id, target_id)
            
        elif pkt_type == PACKET_MOVE:
            logger.info(f"Entity {entity_id} (User {user}) sent move packet.")
            new_x = packet.get('x')
            new_y = packet.get('y')
            if new_x is None or new_y is None:
                logger.warning("Malformed move packet: missing coordinates.")
                return
            
            await self.movement_system.handle_move_request(entity_id, writer, new_x, new_y)
        
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
            
            source_type_comp = self.world.get_component(source_entity_id, TypeComponent)
            if not source_type_comp:
                continue
                
            source_pos_comp = self.world.get_component(source_entity_id, PositionComponent)
            
            source_health_comp = self.world.get_component(source_entity_id, HealthComponent)
            source_stats_comp = self.world.get_component(source_entity_id, StatsComponent)
            
            distance = calculate_distance(target_pos_comp, source_pos_comp)
            
            if source_pos_comp and distance <= A_O_I_RANGE:
                logger.debug(f"AoI Initial Sync: Sending Entity {source_entity_id} to New Player {target_entity_id}. Dist: {distance:.2f}")
                
                asset_type = None
                if source_type_comp.entity_type == 'player':
                    source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
                    asset_type = source_network_comp.username if source_network_comp else "Player_Unknown"
                else: # NPC, Monster, etc.
                    # Como você adicionou NetworkComponent aos NPCs com o nome como 'username'
                    source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
                    asset_type = source_network_comp.username if source_network_comp else source_type_comp.entity_type
                    
                if not asset_type: continue
                
                new_entity_packet = {
                    "type": PACKET_ENTITY_NEW,
                    "entity_id": source_entity_id,
                    "x": source_pos_comp.x,
                    "y": source_pos_comp.y,
                    "asset_type": asset_type
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