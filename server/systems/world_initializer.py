from server.db.npcs import get_initial_spawns
from server.game_engine.components.ai import AIComponent
from server.game_engine.components.collision import CollisionComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from shared.logger import get_logger

logger = get_logger(__name__)

class WorldInitializer:
    def __init__(self, world, game_map, db_pool):
        self.world = world
        self.game_map = game_map
        self.db_pool = db_pool

    async def initialize_world(self):

        logger.info("Starting world initialization and map loading...")

        await self._spawn_initial_npcs()

        logger.info("World initialization complete. Game ready.")

    async def _spawn_initial_npcs(self):

        initial_npcs = await get_initial_spawns(self.db_pool)

        if not initial_npcs:
            logger.warning("No initial NPC spawn data found in the database. Spawning skipped.")
            return

        for npc_data in initial_npcs:
            self._create_npc_entity(**npc_data)

    def _create_npc_entity(self, x: float, y: float, asset_type: str, level: int, base_health: int, strength: int, vitality: int, radius: float = 0.5):
        
        npc_entity_id = self.world.create_entity()
        
        npc_stats = StatsComponent(
            level=level, 
            experience=0, 
            base_health=base_health,
            strength=strength, 
            agility=1,
            vitality=vitality,
            intelligence=1,
            dexterity=1,
            luck=1
        )
        calculated_max_health = npc_stats.get_max_health_for_level()
        
        self.world.add_component(npc_entity_id, PositionComponent(x, y))
        self.world.add_component(npc_entity_id, CollisionComponent(radius))
        self.world.add_component(npc_entity_id, npc_stats)
        self.world.add_component(npc_entity_id, HealthComponent(max_health=calculated_max_health, initial_health=calculated_max_health))
        
        self.world.add_component(npc_entity_id, TypeComponent(entity_type='monster'))
        self.world.add_component(npc_entity_id, NetworkComponent(writer=None, username=asset_type))
        self.world.add_component(npc_entity_id, AIComponent(
            initial_state='wandering', 
            home_x=x, 
            home_y=y
        ))
        
        logger.info(f"NPC Entity {npc_entity_id} ('{asset_type}') spawned at ({x}, {y}).")

        return npc_entity_id