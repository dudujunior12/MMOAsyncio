from server.game_engine.components.collision import CollisionComponent
from shared.logger import get_logger
from shared.protocol import (
    PACKET_ENTITY_NEW,
    PACKET_MAP_DATA,
    PACKET_MOVE,
    PACKET_CHAT_MESSAGE,
    PACKET_ITEM_USE,
    PACKET_POSITION_UPDATE,
)
from shared.constants import GAME_TICK_RATE, TICK_INTERVAL

logger = get_logger(__name__)
import asyncio
from server.game_engine.world import World
from server.game_engine.map import GameMap
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.db.player import get_player_data, update_player_position
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
        logger.info("Game Engine initialized.")
        
    async def start(self):
        self.running = True
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
        initial_x = player_data['pos_x'] if player_data else 10.0
        initial_y = player_data['pos_y'] if player_data else 10.0
        
        radius = 0.5
        
        entity_id = self.world.create_entity()
        self.world.add_component(entity_id, PositionComponent(initial_x, initial_y))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        self.world.add_component(entity_id, CollisionComponent(radius))
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
            "asset_type": username
        }
        await self.network_manager.send_packet(writer, new_entity_packet)
        await self.send_aoi_update(entity_id, new_entity_packet, exclude_writer=writer)
        await self._receive_initial_aoi(entity_id, writer)
        
    async def player_disconnected(self, username):
        entity_id = self.player_entity_map.pop(username, None)
        if entity_id:
            network_comp = self.world.get_component(entity_id, NetworkComponent)
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            if pos_comp:
                await update_player_position(self.db_pool, username, pos_comp.x, pos_comp.y)
                logger.info(f"Saved player {username}'s last position: ({pos_comp.x:.1f}, {pos_comp.y:.1f})")
            
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
            message = packet.get('content', '')
            logger.info(f"Entity {entity_id} (User {user}) sent chat message: {message}")
            response = f"[{user}]: {message}"
            await self.network_manager.broadcast_chat_message(response, writer)
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
            
    async def _receive_initial_aoi(self, target_entity_id: int, target_writer):
        target_pos_comp = self.world.get_component(target_entity_id, PositionComponent)
        if not target_pos_comp:
            return

        for source_username, source_entity_id in self.player_entity_map.items():
            if source_entity_id == target_entity_id:
                continue
                
            source_pos_comp = self.world.get_component(source_entity_id, PositionComponent)
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