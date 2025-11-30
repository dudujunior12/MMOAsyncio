class ColliderShape:
    def get_aabb(self, x, y):
        """Retorna (min_x, min_y, max_x, max_y). Todas as colisões de swept testam AABB."""
        raise NotImplementedError

class BoxCollider(ColliderShape):
    def __init__(self, width, height):
        self.hw = width / 2
        self.hh = height / 2

    def get_aabb(self, x, y):
        return (
            x - self.hw,
            y - self.hh,
            x + self.hw,
            y + self.hh,
        )

    def __repr__(self):
        return f"Box({self.hw*2:.2f}, {self.hh*2:.2f})"

class CircleCollider(ColliderShape):
    def __init__(self, radius):
        self.radius = radius

    def get_aabb(self, x, y):
        r = self.radius
        return (x - r, y - r, x + r, y + r)

    def __repr__(self):
        return f"Circle(r={self.radius:.2f})"

class SpriteCollider(BoxCollider):
    def __init__(self, sprite_w, sprite_h, scale=1.0):
        super().__init__(
            (sprite_w / 100) * scale,
            (sprite_h / 100) * scale,
        )
