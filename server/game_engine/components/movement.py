class MovementComponent:
    def __init__(self, speed: float = 5.0):
        self.base_speed = speed
        
        self.dx = 0.0
        self.dy = 0.0
        
        self.direction = None
        
    def set_direction(self, direction: str | None):
        self.direction = direction
        
    def __repr__(self):
        return f"Move(speed={self.base_speed}, dir={self.direction}, dx={self.dx:.2f}, dy={self.dy:.2f})"