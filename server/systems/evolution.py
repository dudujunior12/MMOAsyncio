# server/systems/evolution.py

from server.game_engine.world import World
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.player_class import ClassComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.network import NetworkComponent
from server.utils.class_loader import get_class_metadata
from shared.logger import get_logger
from shared.protocol import PACKET_ENTITY_UPDATE

from server.game_engine.serialization import packet_builder 

logger = get_logger(__name__)

class EvolutionSystem:
    """
    Sistema responsável por gerenciar a progressão de classes dos jogadores.
    """
    def __init__(self, world: World, engine):
        self.world = world
        self.engine = engine

    async def change_class(self, entity_id: int, target_class_name: str) -> bool:
        class_comp = self.world.get_component(entity_id, ClassComponent)
        stats_comp = self.world.get_component(entity_id, StatsComponent)
        health_comp = self.world.get_component(entity_id, HealthComponent)

        if not all([class_comp, stats_comp, health_comp]):
            await self.engine.send_system_message(entity_id, "Error: Missing class or stats components.")
            return False

        current_class = class_comp.class_name

        current_metadata = get_class_metadata(current_class)
        target_metadata = get_class_metadata(target_class_name)

        if not current_metadata or not target_metadata:
            await self.engine.send_system_message(entity_id, f"Error: Class '{current_class}' or '{target_class_name}' not found.")
            return False

        evolution_data = current_metadata.get('evolution')
        if not evolution_data or target_class_name not in evolution_data.get('to_classes', []):
            await self.engine.send_system_message(entity_id, f"Evolution from '{current_class}' to '{target_class_name}' is not allowed.")
            return False

        required_level = evolution_data.get('level', float('inf'))
        if stats_comp.level < required_level:
            await self.engine.send_system_message(entity_id, f"Minimum Level Requirement not met: You need Level {required_level} to evolve to {target_class_name}.")
            return False

        target_base_health = target_metadata.get("base_health", stats_comp.base_health)
        target_class_bonus = target_metadata.get("class_bonus", {})

        class_comp.class_name = target_class_name
        stats_comp.class_bonus = target_class_bonus
        stats_comp.base_health = target_base_health

        old_max = health_comp.max_health
        new_max = stats_comp.get_max_health_for_level()
        health_comp.max_health = new_max
        health_comp.current_health = new_max

        await self.engine.send_system_message(entity_id, f"*** CONGRATULATIONS! You have evolved into '{target_class_name}'! ***")
        await self.engine.send_system_message(entity_id, f"Your maximum health changed from {old_max} to {new_max}. Your base attributes were not modified — only class bonuses were applied.")

        await self._send_entity_update(entity_id)

        logger.info(f"Entity {entity_id} evolved from {current_class} to {target_class_name} at Level {stats_comp.level}.")
        return True

    async def _send_entity_update(self, entity_id: int):
        update_packet = packet_builder.serialize_entity(self.world, entity_id)
        
        update_packet["type"] = PACKET_ENTITY_UPDATE
        
        await self.engine.send_aoi_update(entity_id, update_packet)