from shared.logger import get_logger
from shared.protocol import (
    PACKET_MOVE,
    PACKET_CHAT_MESSAGE,
    PACKET_ITEM_USE,
    PACKET_POSITION_UPDATE,
)
from shared.constants import GAME_TICK_RATE, TICK_INTERVAL

logger = get_logger(__name__)
import asyncio
from server.game_engine.world import World
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.db.player import get_player_data, update_player_position

class GameEngine:
    def __init__(self, db_pool, network_manager):
        self.db_pool = db_pool
        self.network_manager = network_manager
        self.running = False
        self.world = World()
        self.player_entity_map = {}
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
            await self._sync_world_state()
            await asyncio.sleep(TICK_INTERVAL)
        logger.info("Game Loop stopped.")
    
    
    async def player_connected(self, writer, username):
        
        player_data = await get_player_data(self.db_pool, username)
        initial_x = player_data['pos_x'] if player_data else 10.0
        initial_y = player_data['pos_y'] if player_data else 10.0
        
        entity_id = self.world.create_entity()
        self.world.add_component(entity_id, PositionComponent(initial_x, initial_y))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        self.player_entity_map[username] = entity_id
        logger.info(f"Entity {entity_id} created for player {username}.")
        
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
                pos_comp.x = new_x
                pos_comp.y = new_y
                
                logger.debug(f"Updated position for Entity {entity_id} to ({new_x}, {new_y})")
                
                update_packet = {
                    "type": PACKET_POSITION_UPDATE,
                    "entity_id": entity_id,
                    "x": new_x,
                    "y": new_y,
                    "asset_type": user
                }
                
                await self.network_manager.broadcast_game_update(update_packet, exclude_writer=writer)
        
        elif pkt_type == PACKET_ITEM_USE:
            pass
        else:
            logger.warning(f"Unknown packet type received: {pkt_type}")
            
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