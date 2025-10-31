from server.game_engine.components.collision import CollisionComponent
from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.type import TypeComponent
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.network import NetworkComponent
from shared.logger import get_logger

logger = get_logger(__name__)

class WorldInitializer:
    def __init__(self, world, game_map):
        self.world = world
        self.game_map = game_map

    def initialize_world(self):

        logger.info("Starting world initialization and map loading...")

        self._spawn_initial_npcs()

        logger.info("World initialization complete. Game ready.")

    def _spawn_initial_npcs(self):

        initial_npcs = [
            {
                'x': 20.0, 'y': 5.0, 
                'asset_type': 'Green_Slime', 
                'level': 1, 'base_health': 30, 'strength': 5, 'vitality': 2
            },
            {
                'x': 25.0, 'y': 15.0, 
                'asset_type': 'Wolf_Pack_Leader', 
                'level': 5, 'base_health': 80, 'strength': 15, 'vitality': 5
            }
        ]

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
        
        logger.info(f"NPC Entity {npc_entity_id} ('{asset_type}') spawned at ({x}, {y}).")

        return npc_entity_id