# server/systems/leveling_system.py

from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent

class LevelingSystem:
    def __init__(self, world, engine):
        self.world = world
        self.engine = engine

    async def add_experience(self, entity_id: int, amount: int):
        stats_comp = self.world.get_component(entity_id, StatsComponent)
        if not stats_comp:
            return

        leveled_up = stats_comp.add_xp(amount)

        if leveled_up:
            health_comp = self.world.get_component(entity_id, HealthComponent)
            if health_comp:
                new_max = stats_comp.get_max_health_for_level()
                health_comp.max_health = new_max
                health_comp.current_health = new_max

            await self.engine.send_system_message(entity_id, f"LEVEL UP! You reached level {stats_comp.level}. (+{5} points per level)")
            try:
                await self.engine.send_aoi_update(entity_id, {
                    "type": "PLAYER_LEVEL_UP",
                    "entity_id": entity_id,
                    "level": stats_comp.level,
                    "stat_points": stats_comp.stat_points,
                    "max_health": health_comp.max_health if health_comp else None,
                })
            except Exception:
                pass
