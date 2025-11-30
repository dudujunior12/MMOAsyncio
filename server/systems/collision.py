import math
from server.game_engine.components.collision import CollisionComponent
from server.game_engine.collision.shapes import BoxCollider, CircleCollider, SpriteCollider
from server.game_engine.map import GameMap
from server.game_engine.components.position import PositionComponent
from server.game_engine.world import World
from shared.logger import get_logger

logger = get_logger(__name__)

EPS = 1e-8

class CollisionSystem:
    def __init__(self, game_map: GameMap):
        self.game_map = game_map

    # -----------------------
    # Verifica colisão com mapa
    # -----------------------
    def check_map_collision(self, new_x: float, new_y: float, col: CollisionComponent) -> bool:
        # Para box, checamos os cantos
        if isinstance(col.shape, (BoxCollider, SpriteCollider)):
            hw, hh = col.shape.hw, col.shape.hh
            # verifica todos os 4 cantos
            corners = [
                (new_x - hw, new_y - hh),
                (new_x + hw, new_y - hh),
                (new_x - hw, new_y + hh),
                (new_x + hw, new_y + hh)
            ]
            for cx, cy in corners:
                if not self.game_map.is_walkable(cx, cy):
                    return False
            return True
        elif isinstance(col.shape, CircleCollider):
            # Checa ponto central
            return self.game_map.is_walkable(new_x, new_y)
        else:
            # fallback
            return self.game_map.is_walkable(new_x, new_y)

    # -----------------------
    # Checa colisão entre entidades
    # -----------------------
    def check_entity_collision(self, current_entity_id: int, target_x: float, target_y: float, world: World) -> bool:
        current_collision = world.get_component(current_entity_id, CollisionComponent)
        if not current_collision:
            return False

        entity_iter = world.get_entities_with_components((PositionComponent, CollisionComponent))

        for entity_id, (pos, col) in entity_iter:
            if entity_id == current_entity_id:
                continue

            # determina colisão dependendo do tipo de shape
            if isinstance(current_collision.shape, CircleCollider) and isinstance(col.shape, CircleCollider):
                # círculo vs círculo
                dx = target_x - pos.x
                dy = target_y - pos.y
                distance = math.hypot(dx, dy)
                min_dist = current_collision.shape.radius + col.shape.radius
                if distance < min_dist:
                    return True
            else:
                # qualquer outro caso -> usar AABB
                # current AABB
                if isinstance(current_collision.shape, CircleCollider):
                    hw = hh = current_collision.shape.radius
                else:
                    hw = getattr(current_collision.shape, "hw", 0.5)
                    hh = getattr(current_collision.shape, "hh", 0.5)
                cur_left = target_x - hw
                cur_right = target_x + hw
                cur_top = target_y - hh
                cur_bottom = target_y + hh

                # other AABB
                if isinstance(col.shape, CircleCollider):
                    ohw = ohh = col.shape.radius
                else:
                    ohw = getattr(col.shape, "hw", 0.5)
                    ohh = getattr(col.shape, "hh", 0.5)
                other_left = pos.x - ohw
                other_right = pos.x + ohw
                other_top = pos.y - ohh
                other_bottom = pos.y + ohh

                # AABB check
                if (cur_right > other_left and cur_left < other_right and
                    cur_bottom > other_top and cur_top < other_bottom):
                    return True

        return False

    # -----------------------
    # Processa movimentação
    # -----------------------
    def process_movement(self, entity_id: int, current_pos: PositionComponent, target_x: float, target_y: float, world: World) -> tuple[bool, float, float]:
        col = world.get_component(entity_id, CollisionComponent)
        if not col:
            # sem colisão, move livremente
            return True, target_x, target_y

        if not self.check_map_collision(target_x, target_y, col):
            return False, current_pos.x, current_pos.y

        if self.check_entity_collision(entity_id, target_x, target_y, world):
            return False, current_pos.x, current_pos.y

        return True, target_x, target_y
