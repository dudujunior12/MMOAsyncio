import math
from server.game_engine.components.position import PositionComponent


def calculate_distance(pos1: PositionComponent, pos2: PositionComponent) -> float:
    return math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)