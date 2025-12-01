# server/systems/movement_system.py

from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from server.game_engine.components.stats import StatsComponent
from server.utils.utils import calculate_distance
from shared.logger import get_logger
from shared.protocol import PACKET_POSITION_UPDATE
from shared.constants import MAX_MOVE_DISTANCE

logger = get_logger(__name__)

class MovementSystem:
    def __init__(self, world, network_manager, collision_system, send_aoi_update_func):
        self.world = world
        self.network_manager = network_manager
        self.collision_system = collision_system
        self.send_aoi_update = send_aoi_update_func
        self.MAX_MOVE_DISTANCE = MAX_MOVE_DISTANCE

    async def handle_move_request(self, entity_id: int, writer, dx: float, dy: float):
        pos_comp = self.world.get_component(entity_id, PositionComponent)
        network_comp = self.world.get_component(entity_id, NetworkComponent)

        if not pos_comp or not network_comp:
            logger.warning(f"Move request for invalid entity {entity_id}.")
            return
        
        stats_comp = self.world.get_component(entity_id, StatsComponent)
        if not stats_comp:
            # Lidar com entidade sem stats, talvez usar uma velocidade padrão
            max_allowed_distance = self.MAX_MOVE_DISTANCE 
        else:
            # 1. OBTER a velocidade da entidade
            move_speed = stats_comp.get_movement_speed()
            # Você pode querer que a MAX_MOVE_DISTANCE seja a velocidade * por um fator de tempo
            # Ex: Move_speed é unidades/seg, MAX_MOVE_DISTANCE (temporária) é unidades/tick.
            
            # A forma mais simples de usar as stats é LIMITAR o MAX_MOVE_DISTANCE
            # Pelo que o cliente está enviando (dx, dy), parece que ele já está calculando 
            # o deslocamento total para o tick/pacote.
            max_allowed_distance = move_speed

        user = network_comp.username
        current_x = pos_comp.x
        current_y = pos_comp.y

        # Calcula nova posição alvo
        requested_new_x = current_x + dx
        requested_new_y = current_y + dy

        # Verifica distância máxima
        distance_moved = (dx ** 2 + dy ** 2) ** 0.5
        if distance_moved > max_allowed_distance:
            logger.warning(f"User {user} attempted invalid move distance ({distance_moved:.2f}) > allowed ({max_allowed_distance:.2f})")
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