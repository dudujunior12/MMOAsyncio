# server/systems/evolution.py

from server.game_engine.world import World
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.player_class import ClassComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.network import NetworkComponent
from server.utils.class_loader import get_class_metadata
from shared.logger import get_logger
from shared.protocol import PACKET_ENTITY_UPDATE

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

        # --- AQUI NÃO ALTERAMOS stats base do jogador ---
        # Apenas trocamos a classe e aplicamos os class_bonus e base_health

        target_base_health = target_metadata.get("base_health", stats_comp.base_health)
        target_class_bonus = target_metadata.get("class_bonus", {})

        # Atualiza apenas o que é class-related
        class_comp.class_name = target_class_name

        # Atualiza os bônus da classe no componente de stats (não persistir)
        stats_comp.class_bonus = target_class_bonus

        # Atualiza o 'base_health' usado no cálculo de HP (opcional: manter histórico do que já estava salvo)
        stats_comp.base_health = target_base_health

        # Recalcula HP máximo e ajusta atual para novo máximo (cura total na evolução)
        old_max = health_comp.max_health
        new_max = stats_comp.get_max_health_for_level()
        health_comp.max_health = new_max
        health_comp.current_health = new_max

        await self.engine.send_system_message(entity_id, f"*** CONGRATULATIONS! You have evolved into '{target_class_name}'! ***")
        await self.engine.send_system_message(entity_id, f"Your maximum health changed from {old_max} to {new_max}. Your base attributes were not modified — only class bonuses were applied.")

        # Enviar atualização para a AoI (com valores totais)
        await self._send_entity_update(entity_id, stats_comp, health_comp, class_comp)

        logger.info(f"Entity {entity_id} evolved from {current_class} to {target_class_name} at Level {stats_comp.level}.")
        return True

    async def _send_entity_update(self, entity_id, stats_comp, health_comp, class_comp):
        update_packet = {
            "type": PACKET_ENTITY_UPDATE,
            "entity_id": entity_id,
            "class_name": class_comp.class_name,
            "level": stats_comp.level,
            "current_health": health_comp.current_health,
            "max_health": health_comp.max_health,
            # enviar valores totais (base + bônus)
            "strength": stats_comp.total_strength,
            "agility": stats_comp.total_agility,
            "vitality": stats_comp.total_vitality,
            "intelligence": stats_comp.total_intelligence,
            "dexterity": stats_comp.total_dexterity,
            "luck": stats_comp.total_luck,
            "stat_points": stats_comp.stat_points
        }
        await self.engine.send_aoi_update(entity_id, update_packet)
