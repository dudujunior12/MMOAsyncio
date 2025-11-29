import pygame
from .base_ui import BaseUI

class LoginUI(BaseUI):
    def __init__(self, screen):
        super().__init__(screen)
        self.username = ""
        self.password = ""
        self.active_field = None
        self.message = ""

        self.font_title = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 26)

        self.bg_top = (15, 18, 30)
        self.bg_bottom = (30, 35, 55)
        self.input_bg = (35, 35, 45)
        self.input_active = (0, 180, 255)
        self.input_inactive = (100, 110, 130)
        self.text_color = (255, 255, 255)
        self.placeholder_color = (170, 170, 170)
        self.error_color = (255, 90, 90)
        self.button_color = (0, 180, 255)
        self.button_hover = (0, 140, 200)
        
        self.form_w = 420
        self.form_h = 300
        self.form_x = (screen.get_width() - self.form_w)//2
        self.form_y = (screen.get_height() - self.form_h)//2

        self.input_w = 320
        self.input_h = 45
        self.input_gap = 25

        self.username_rect = pygame.Rect(
            self.form_x + 50, self.form_y + 20,
            self.input_w, self.input_h
        )
        self.password_rect = pygame.Rect(
            self.username_rect.x,
            self.username_rect.bottom + self.input_gap,
            self.input_w, self.input_h
        )

        self.button_rect = pygame.Rect(
            self.form_x + 50,
            self.password_rect.bottom + 40,
            self.input_w, 55
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.username_rect.collidepoint(event.pos):
                self.active_field = "username"
            elif self.password_rect.collidepoint(event.pos):
                self.active_field = "password"
            else:
                self.active_field = None

            if self.button_rect.collidepoint(event.pos):
                return "submit"

        elif event.type == pygame.KEYDOWN and self.active_field:
            if event.key == pygame.K_TAB:
                self.active_field = (
                    "password" if self.active_field == "username" else "username"
                )

            elif event.key == pygame.K_RETURN:
                return "submit"

            elif event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]

            else:
                char = event.unicode
                if len(char) == 1 and 32 <= ord(char) <= 126:
                    if self.active_field == "username":
                        self.username += char
                    else:
                        self.password += char

        return None

    def draw(self):
        self._draw_background()
        self._draw_title("MMO Login")
        self._draw_input(self.username_rect, self.username, "Username")
        self._draw_input(self.password_rect, "*" * len(self.password), "Password")
        self._draw_button()
        self._draw_message()

    def _draw_background(self):
        h = self.screen.get_height()
        w = self.screen.get_width()
        for y in range(h):
            t = y / h
            r = int(self.bg_top[0]*(1-t) + self.bg_bottom[0]*t)
            g = int(self.bg_top[1]*(1-t) + self.bg_bottom[1]*t)
            b = int(self.bg_top[2]*(1-t) + self.bg_bottom[2]*t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (w, y))

    def _draw_title(self, text):
        surf = self.font_title.render(text, True, self.text_color)
        self.screen.blit(
            surf,
            (self.screen.get_width()//2 - surf.get_width()//2, self.form_y - 80)
        )

    def _draw_input(self, rect, text, placeholder):
        pygame.draw.rect(self.screen, self.input_bg, rect, border_radius=6)

        border_color = self.input_active if self.active_field == placeholder.lower() else self.input_inactive
        pygame.draw.rect(self.screen, border_color, rect, width=3, border_radius=6)

        if text or self.active_field == placeholder.lower():
            label_surface = self.small_font.render(placeholder, True, self.placeholder_color)
            self.screen.blit(label_surface, (rect.x, rect.y - 22))
        else:
            placeholder_surface = self.font.render(placeholder, True, self.placeholder_color)
            self.screen.blit(placeholder_surface, (rect.x + 10, rect.y + 8))

        if text:
            txt_surface = self.font.render(text, True, self.text_color)
            self.screen.blit(txt_surface, (rect.x + 10, rect.y + 8))

    def _draw_button(self):
        mouse = pygame.mouse.get_pos()
        color = self.button_hover if self.button_rect.collidepoint(mouse) else self.button_color
        pygame.draw.rect(self.screen, color, self.button_rect, border_radius=8)

        text_surf = self.font.render("Login", True, (255, 255, 255))
        self.screen.blit(
            text_surf,
            (
                self.button_rect.centerx - text_surf.get_width()//2,
                self.button_rect.centery - text_surf.get_height()//2
            )
        )

    def _draw_message(self):
        if not self.message:
            return

        surf = self.small_font.render(self.message, True, self.error_color)
        self.screen.blit(
            surf,
            (self.screen.get_width()//2 - surf.get_width()//2,
             self.button_rect.bottom + 15)
        )
