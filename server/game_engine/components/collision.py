class CollisionComponent:
    def __init__(self, shape, offset=(0,0), is_trigger=False):
        self.shape = shape
        self.offset_x, self.offset_y = offset
        self.is_trigger = is_trigger
        
    def __repr__(self):
        return f"Collision({self.shape})"