import math
from server.game_engine.components.collision import CollisionComponent
from server.game_engine.map import GameMap

from server.game_engine.components.position import PositionComponent
from server.game_engine.world import World
from shared.logger import get_logger

logger = get_logger(__name__)

class CollisionSystem:
    def __init__(self, game_map: GameMap):
        self.game_map = game_map
        
    def check_map_collision(self, new_x: float, new_y: float) -> bool:
        if not self.game_map.is_walkable(new_x, new_y):
            tile_type = self.game_map.get_tile_type(new_x, new_y)
            
            if tile_type is not None:
                logger.warning(f"Movement blocked at ({new_x:.2f}, {new_y:.2f}): Tile type '{tile_type}' is not walkable.")
            else:
                logger.warning(f"Movement blocked at ({new_x:.2f}, {new_y:.2f}): Outside map boundaries.")
                
            return False
        return True
    
    def check_entity_collision(self, current_entity_id: int, target_x: float, target_y: float, world: World) -> bool:
        current_collision = world.get_component(current_entity_id, CollisionComponent)
        if not current_collision:
            return False
        
        current_radius = current_collision.radius
        
        entity_iter = world.get_entities_with_components((PositionComponent, CollisionComponent))
        
        for entity_id, components_list in entity_iter:
            if entity_id == current_entity_id:
                continue
            
            other_pos = components_list[0]
            other_collision = components_list[1]
        
            other_radius = other_collision.radius
            
            dx = target_x - other_pos.x
            dy = target_y - other_pos.y
            distance = math.sqrt(dx**2 + dy**2)
            
            min_distance = current_radius + other_radius
            
            if distance < min_distance:
                logger.warning(f"Entity {current_entity_id} blocked by Entity {entity_id} at ({target_x:.2f}, {target_y:.2f}).")
                return True
        return False
    
    def process_movement(self, entity_id: int, current_pos: PositionComponent, target_x: float, target_y: float, world: World) -> tuple[bool, float, float]:
        if not self.check_map_collision(target_x, target_y):
            return (False, current_pos.x, current_pos.y)
        
        if self.check_entity_collision(entity_id, target_x, target_y, world):
            return (False, current_pos.x, current_pos.y)
        
        return (True, target_x, target_y)
