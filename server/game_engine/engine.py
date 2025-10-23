from shared.logger import get_logger
from shared.protocol import (
    PACKET_MOVE,
    PACKET_CHAT_MESSAGE,
    PACKET_ITEM_USE,
    PACKET_POSITION_UPDATE,
)

logger = get_logger(__name__)
import asyncio
from server.game_engine.world import World
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent

# Constante para a taxa de atualização do mundo (ex: 30 ticks por segundo)
# Isso equivale a 1 / 30 = 0.0333 segundos por tick
GAME_TICK_RATE = 30 
TICK_INTERVAL = 1.0 / GAME_TICK_RATE

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
            #self._update_world_events()
            await asyncio.sleep(TICK_INTERVAL)
        logger.info("Game Loop stopped.")
    
    
    async def player_connected(self, writer, username):
        # Load player data
        initial_x, initial_y = 10.0, 10.0  # Load from DB in future
        # Initialize player state in the world
        entity_id = self.world.create_entity()
        # Add components
        self.world.add_component(entity_id, PositionComponent(initial_x, initial_y))
        self.world.add_component(entity_id, NetworkComponent(writer, username))
        # Map username to entity ID
        self.player_entity_map[username] = entity_id
        logger.info(f"Entity {entity_id} created for player {username}.")
    async def player_disconnected(self, username):
        # Remove player from world
        entity_id = self.player_entity_map.pop(username, None)
        if entity_id:
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            logger.info(f"Saving player {username}'s last position: {pos_comp}")
            # Save to DB
            self.world.remove_entity(entity_id)
            logger.info(f"Entity {entity_id} removed for player {username}.")
        pass
    
    def get_player_entity_id(self, username: str) -> int | None:
        return self.player_entity_map.get(username)
    
    async def process_network_packet(self, writer, packet):
        # Implement packet processing, for example a Move Packet, Chat Packet, etc.
        pkt_type = packet.get('type')
        user = self.network_manager.get_user_by_writer(writer)
        if not user:
            logger.warning("Received packet from unauthenticated user.")
            return

        entity_id = self.get_player_entity_id(user)
        if pkt_type == PACKET_CHAT_MESSAGE:
            # Process chat message
            message = packet.get('content', '')
            logger.info(f"Entity {entity_id} (User {user}) sent chat message: {message}")
            response = f"[{user}]: {message}"
            await self.network_manager.broadcast_chat_message(response, writer)
        elif pkt_type == PACKET_MOVE:
            # Process move packet
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
                    "y": new_y
                }
                
                await self.network_manager.broadcast_game_update(update_packet, exclude_writer=writer)
        
        elif pkt_type == PACKET_ITEM_USE:
            pass
        else:
            logger.warning(f"Unknown packet type received: {pkt_type}")
            
    async def shutdown(self):
        logger.info("Game Engine shutdown complete.")