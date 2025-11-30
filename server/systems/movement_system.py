# server/systems/movement_system.py

from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.utils.utils import calculate_distance
from shared.logger import get_logger
from shared.protocol import PACKET_POSITION_UPDATE

logger = get_logger(__name__)

class MovementSystem:
    def __init__(self, world, network_manager, collision_system, send_aoi_update_func):
        self.world = world
        self.network_manager = network_manager
        self.collision_system = collision_system
        self.send_aoi_update = send_aoi_update_func
        self.MAX_MOVE_DISTANCE = 5.0

    async def handle_move_request(self, entity_id: int, writer, dx: float, dy: float):
        pos_comp = self.world.get_component(entity_id, PositionComponent)
        network_comp = self.world.get_component(entity_id, NetworkComponent)

        if not pos_comp or not network_comp:
            logger.warning(f"Move request for invalid entity {entity_id}.")
            return

        user = network_comp.username
        current_x = pos_comp.x
        current_y = pos_comp.y

        # Calcula nova posição alvo
        requested_new_x = current_x + dx
        requested_new_y = current_y + dy

        # Verifica distância máxima
        distance_moved = (dx ** 2 + dy ** 2) ** 0.5
        if distance_moved > self.MAX_MOVE_DISTANCE:
            logger.warning(f"User {user} attempted invalid move distance ({distance_moved:.2f})")
            await self._resync_position(entity_id, writer, current_x, current_y, user)
            return

        # Aplica colisão
        moved, final_x, final_y = self.collision_system.process_movement(
            entity_id, pos_comp, requested_new_x, requested_new_y, self.world
        )

        if not moved:
            await self._resync_position(entity_id, writer, current_x, current_y, user)
            return

        # Atualiza posição
        pos_comp.x = final_x
        pos_comp.y = final_y

        # logger.debug(f"Updated position for Entity {entity_id} to ({final_x:.1f}, {final_y:.1f})")

        update_packet = {
            "type": PACKET_POSITION_UPDATE,
            "entity_id": entity_id,
            "x": final_x,
            "y": final_y,
            "asset_type": user
        }

        # Atualiza clientes na AoI
        await self.send_aoi_update(entity_id, update_packet, exclude_writer=writer)
        await self.network_manager.send_packet(writer, update_packet)

    async def _resync_position(self, entity_id, writer, x, y, user):
        await self.network_manager.send_packet(writer, {
            "type": PACKET_POSITION_UPDATE,
            "entity_id": entity_id,
            "x": x,
            "y": y,
            "asset_type": user
        })
        
    async def handle_npc_move(self, entity_id: int, new_x: float, new_y: float):

        pos_comp = self.world.get_component(entity_id, PositionComponent)
        network_comp = self.world.get_component(entity_id, NetworkComponent)
        
        if not pos_comp or not network_comp:
            return
            
        asset_type = network_comp.username 
        
        moved, final_x, final_y = self.collision_system.process_movement(
            entity_id, pos_comp, new_x, new_y, self.world
        )
        
        if not moved:
            return

        pos_comp.x = final_x
        pos_comp.y = final_y
        
        update_packet = {
            "type": PACKET_POSITION_UPDATE,
            "entity_id": entity_id,
            "x": final_x,
            "y": final_y,
            "asset_type": asset_type
        }
        
        await self.send_aoi_update(entity_id, update_packet, exclude_writer=None)
        
        #logger.debug(f"NPC {asset_type} moved to ({final_x:.1f}, {final_y:.1f})")