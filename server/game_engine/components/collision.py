class CollisionComponent:
    def __init__(self, radius: float = 0.5):
        self.radius = radius
        
    def __repr__(self):
        return f"Collision(radius={self.radius})"