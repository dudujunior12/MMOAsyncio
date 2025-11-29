import pygame

class BaseUI:
    def __init__(self, screen):
        self.screen = screen

    def handle_event(self, event):
        """Captura eventos (teclado, mouse)"""
        pass

    def update(self, dt):
        """Atualiza elementos da UI"""
        pass

    def draw(self):
        """Desenha elementos da UI"""
        pass
