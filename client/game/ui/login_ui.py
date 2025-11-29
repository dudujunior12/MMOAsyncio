import pygame
from .base_ui import BaseUI

class LoginUI(BaseUI):
    def __init__(self, screen):
        super().__init__(screen)
        self.username = ""
        self.password = ""
        self.active_field = None  # Nenhum ativo inicialmente
        self.message = ""
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Cores
        self.bg_color_top = (20, 20, 30)
        self.bg_color_bottom = (40, 40, 60)
        self.input_bg = (50, 50, 50)
        self.input_border_active = (0, 200, 255)
        self.input_border_inactive = (100, 100, 120)
        self.text_color = (255, 255, 255)
        self.msg_color = (255, 100, 100)
        self.button_color = (0, 200, 255)
        self.button_hover = (0, 150, 200)
        self.button_text = (255, 255, 255)

        # Dimensões
        self.form_width = 400
        self.form_height = 250
        self.form_x = (screen.get_width() - self.form_width) // 2
        self.form_y = (screen.get_height() - self.form_height) // 2

        self.input_width = 300
        self.input_height = 40
        self.input_spacing = 20

        # Inputs (rects para detectar clique)
        self.username_rect = pygame.Rect(
            self.form_x + (self.form_width - self.input_width)//2,
            self.form_y,
            self.input_width,
            self.input_height
        )
        self.password_rect = pygame.Rect(
            self.form_x + (self.form_width - self.input_width)//2,
            self.form_y + self.input_height + self.input_spacing,
            self.input_width,
            self.input_height
        )

        # Botão
        self.button_rect = pygame.Rect(
            self.form_x + (self.form_width - self.input_width)//2,
            self.form_y + 2*self.input_height + 2*self.input_spacing + 10,
            self.input_width,
            50
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Foco nos inputs
            if self.username_rect.collidepoint(event.pos):
                self.active_field = "username"
            elif self.password_rect.collidepoint(event.pos):
                self.active_field = "password"
            else:
                self.active_field = None

            # Botão
            if self.button_rect.collidepoint(event.pos):
                return "submit"

        elif event.type == pygame.KEYDOWN and self.active_field:
            # Digitação
            if event.key == pygame.K_TAB:
                self.active_field = "password" if self.active_field == "username" else "username"
            elif event.key == pygame.K_RETURN:
                return "submit"
            elif event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]
            else:
                char = event.unicode
                if self.active_field == "username":
                    self.username += char
                else:
                    self.password += char

        return None

    def draw(self):
        # Fundo degradê
        for y in range(self.screen.get_height()):
            color_ratio = y / self.screen.get_height()
            r = int(self.bg_color_top[0]*(1-color_ratio) + self.bg_color_bottom[0]*color_ratio)
            g = int(self.bg_color_top[1]*(1-color_ratio) + self.bg_color_bottom[1]*color_ratio)
            b = int(self.bg_color_top[2]*(1-color_ratio) + self.bg_color_bottom[2]*color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.screen.get_width(), y))

        # Título
        title_surface = self.font.render("MMO Login", True, self.text_color)
        self.screen.blit(title_surface, (
            self.screen.get_width()//2 - title_surface.get_width()//2,
            self.form_y - 60
        ))

        # Inputs
        self._draw_input(self.username_rect, self.username, "Username")
        self._draw_input(self.password_rect, "*"*len(self.password), "Password")

        # Botão
        mouse_pos = pygame.mouse.get_pos()
        btn_color = self.button_hover if self.button_rect.collidepoint(mouse_pos) else self.button_color
        pygame.draw.rect(self.screen, btn_color, self.button_rect, border_radius=5)

        btn_text = self.font.render("Login", True, self.button_text)
        self.screen.blit(
            btn_text,
            (self.button_rect.centerx - btn_text.get_width()//2,
             self.button_rect.centery - btn_text.get_height()//2)
        )

        # Mensagem de erro
        msg_surface = self.small_font.render(self.message, True, self.msg_color)
        self.screen.blit(
            msg_surface,
            (self.screen.get_width()//2 - msg_surface.get_width()//2,
             self.button_rect.bottom + 15)
        )

    def _draw_input(self, rect, text, label):
        # Label acima do input
        label_surface = self.small_font.render(label, True, (200, 200, 200))
        self.screen.blit(label_surface, (rect.x, rect.y - 25))

        # Background
        pygame.draw.rect(self.screen, self.input_bg, rect, border_radius=5)

        # Borda
        color = self.input_border_active if self.active_field == label.lower() else self.input_border_inactive
        pygame.draw.rect(self.screen, color, rect, width=3, border_radius=5)

        # Texto centralizado verticalmente
        text_surface = self.font.render(text, True, self.text_color)
        text_y = rect.y + (rect.height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (rect.x + 10, text_y))
