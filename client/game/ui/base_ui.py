import pygame

class BaseUI:
    def __init__(self, screen):
        self.screen = screen
        
        # --- ESTILOS VISUAIS COMUNS (CORES E FONTES) ---
        self.font_title = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 26)

        self.bg_top = (15, 18, 30)
        self.bg_bottom = (30, 35, 55)
        self.text_color = (255, 255, 255)
        self.error_color = (255, 90, 90)
        self.message = "" # Adiciona campo de mensagem para ser usado nas subclasses
        
        # Geometria da UI (Usada pelas subclasses)
        self.form_w = 420
        self.form_x = (screen.get_width() - self.form_w)//2
        
    # ------------------ MÉTODOS DE DESENHO COMPARTILHADOS ------------------

    def _draw_background(self):
        """Desenha um fundo gradiente."""
        h = self.screen.get_height()
        w = self.screen.get_width()
        for y in range(h):
            t = y / h
            r = int(self.bg_top[0]*(1-t) + self.bg_bottom[0]*t)
            g = int(self.bg_top[1]*(1-t) + self.bg_bottom[1]*t)
            b = int(self.bg_top[2]*(1-t) + self.bg_bottom[2]*t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (w, y))

    def _draw_title(self, text, form_y_start):
        """Desenha o título no topo do formulário."""
        surf = self.font_title.render(text, True, self.text_color)
        self.screen.blit(
            surf,
            (self.screen.get_width()//2 - surf.get_width()//2, form_y_start - 80)
        )
        
    def _draw_message(self, bottom_y):
        """Desenha a mensagem de erro/status."""
        if not self.message:
            return

        surf = self.small_font.render(self.message, True, self.error_color)
        self.screen.blit(
            surf,
            (self.screen.get_width()//2 - surf.get_width()//2,
             bottom_y + 15)
        )

    def handle_event(self, event):
        """Captura eventos (teclado, mouse)"""
        pass

    def update(self, dt):
        """Atualiza elementos da UI"""
        pass

    def draw(self):
        """Desenha elementos da UI"""
        pass