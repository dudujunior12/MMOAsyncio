from typing import Literal

AI_STATES = Literal['idle', 'wandering', 'chasing', 'attacking', 'returning']

class AIComponent:
    def __init__(self, initial_state: AI_STATES = 'wandering', target_entity_id: int | None = None, home_x: float | None = None, home_y: float | None = None):
        self.state: AI_STATES = initial_state
        
        self.target_entity_id: int | None = target_entity_id
        
        self.home_x: float | None = home_x
        self.home_y: float | None = home_y