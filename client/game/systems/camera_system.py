from shared.constants import SPRITE_SIZE

# Fator de suavização da câmera
CAMERA_SMOOTHING_SPEED = 5.0 

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0.0 # Alterado para float para interpolação precisa
        self.y = 0.0 # Alterado para float para interpolação precisa

    def apply(self, x, y):
        # A posição do sprite menos o deslocamento da câmera
        return x - self.x, y - self.y

    def update(self, target, dt):
        """
        Atualiza a posição da câmera de forma suave (interpolação baseada em tempo).
        target deve conter a posição visual interpolada ("x_visual", "y_visual").
        """
        # 1. Calcula a posição alvo (onde a câmera DEVERIA estar)
        target_x_center = target.get("x", 0) * SPRITE_SIZE
        target_y_center = target.get("y", 0) * SPRITE_SIZE
        
        target_x = target_x_center - self.width / 2
        target_y = target_y_center - self.height / 2
        
        # 2. Interpolação suave (Lerp baseada em tempo)
        # O fator de interpolação é baseado no delta time para ser consistente
        lerp_factor = min(1.0, CAMERA_SMOOTHING_SPEED * dt) 
        
        self.x += (target_x - self.x) * lerp_factor
        self.y += (target_y - self.y) * lerp_factor