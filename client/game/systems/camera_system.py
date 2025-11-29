from shared.constants import SPRITE_SIZE


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def apply(self, x, y):
        return x - self.x, y - self.y

    def update(self, target):
        target_x = int(target["x_visual"] * SPRITE_SIZE - self.width // 2)
        target_y = int(target["y_visual"] * SPRITE_SIZE - self.height // 2)
        
        # Interpolação suave
        self.x += (target_x - self.x) * 0.2
        self.y += (target_y - self.y) * 0.2
