import pygame
from .base_ui import BaseUI

class RegisterUI(BaseUI):
    def __init__(self, screen):
        super().__init__(screen)
        self.username = ""
        self.password = ""
        self.confirm_password = ""
        self.active_field = None
        
        self.input_bg = (35, 35, 45)
        self.input_active = (0, 180, 255)
        self.input_inactive = (100, 110, 130)
        self.placeholder_color = (170, 170, 170)
        self.button_color = (180, 0, 255) # Cor roxa para diferenciar o registro
        self.button_hover = (140, 0, 200)
        self.link_color = (100, 180, 255)

   
        self.form_h = 400 # Aumentado para 3 campos
        self.form_y = (screen.get_height() - self.form_h)//2

        self.input_w = 320
        self.input_h = 45
        self.input_gap = 25
        self.link_gap = 15

        # Retângulos dos campos
        self.username_rect = pygame.Rect(
            self.form_x + 50, self.form_y + 20,
            self.input_w, self.input_h
        )
        self.password_rect = pygame.Rect(
            self.username_rect.x,
            self.username_rect.bottom + self.input_gap,
            self.input_w, self.input_h
        )
        self.confirm_password_rect = pygame.Rect(
            self.username_rect.x,
            self.password_rect.bottom + self.input_gap,
            self.input_w, self.input_h
        )

        # Botão de Registro
        self.register_button_rect = pygame.Rect(
            self.form_x + 50,
            self.confirm_password_rect.bottom + 40,
            self.input_w, 55
        )
        
        # Link para Login
        self.login_link_rect = pygame.Rect(
            self.form_x + 50,
            self.register_button_rect.bottom + self.link_gap,
            self.input_w, 30
        )
        link_temp_surf = self.small_font.render("Already have an account? Login", True, self.link_color)
        self.login_link_rect.w = link_temp_surf.get_width()
        self.login_link_rect.x = self.screen.get_width()//2 - link_temp_surf.get_width()//2
        

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.username_rect.collidepoint(event.pos):
                self.active_field = "username"
            elif self.password_rect.collidepoint(event.pos):
                self.active_field = "password"
            elif self.confirm_password_rect.collidepoint(event.pos):
                self.active_field = "confirm_password"
            else:
                self.active_field = None

            if self.register_button_rect.collidepoint(event.pos):
                return "submit"
            
            if self.login_link_rect.collidepoint(event.pos):
                return "switch_to_login"

        elif event.type == pygame.KEYDOWN and self.active_field:
            if event.key == pygame.K_TAB:
                # Lógica de TAB para alternar campos
                if self.active_field == "username":
                    self.active_field = "password"
                elif self.active_field == "password":
                    self.active_field = "confirm_password"
                else:
                    self.active_field = "username"

            elif event.key == pygame.K_RETURN:
                return "submit"

            elif event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                elif self.active_field == "password":
                    self.password = self.password[:-1]
                else:
                    self.confirm_password = self.confirm_password[:-1]

            else:
                char = event.unicode
                if len(char) == 1 and 32 <= ord(char) <= 126:
                    if self.active_field == "username":
                        self.username += char
                    elif self.active_field == "password":
                        self.password += char
                    else:
                        self.confirm_password += char

        return None

    def draw(self):
            self._draw_background()
            
            self._draw_title("MMO Register", self.form_y) 
            
            self._draw_input(self.username_rect, self.username, "Username", "username")
            self._draw_input(self.password_rect, "*" * len(self.password), "Password", "password")
            self._draw_input(self.confirm_password_rect, "*" * len(self.confirm_password), "Confirm Password", "confirm_password")
            self._draw_button()
            self._draw_link()
            
            # 🎯 CORREÇÃO: Passar a posição Y inferior para _draw_message
            self._draw_message(self.login_link_rect.bottom)
        
    def _draw_input(self, rect, text, placeholder, field_name):
        # Adaptação do _draw_input do LoginUI
        pygame.draw.rect(self.screen, self.input_bg, rect, border_radius=6)

        border_color = self.input_active if self.active_field == field_name else self.input_inactive
        pygame.draw.rect(self.screen, border_color, rect, width=3, border_radius=6)

        if text or self.active_field == field_name:
            label_surface = self.small_font.render(placeholder, True, self.placeholder_color)
            self.screen.blit(label_surface, (rect.x, rect.y - 22))
        else:
            placeholder_surface = self.font.render(placeholder, True, self.placeholder_color)
            self.screen.blit(placeholder_surface, (rect.x + 10, rect.y + 8))

        if text:
            txt_surface = self.font.render(text, True, self.text_color)
            self.screen.blit(txt_surface, (rect.x + 10, rect.y + 8))
            
    # Adicionar _draw_background, _draw_title, _draw_message, _draw_button e _draw_link aqui.
    # Para ser eficiente, sugere-se mover os métodos de drawing (fundo, título, mensagem) para BaseUI
    # e ajustar _draw_button para aceitar o texto do botão.
    
    def _draw_button(self):
        mouse = pygame.mouse.get_pos()
        color = self.button_hover if self.register_button_rect.collidepoint(mouse) else self.button_color
        pygame.draw.rect(self.screen, color, self.register_button_rect, border_radius=8)

        text_surf = self.font.render("Register", True, (255, 255, 255))
        self.screen.blit(
            text_surf,
            (
                self.register_button_rect.centerx - text_surf.get_width()//2,
                self.register_button_rect.centery - text_surf.get_height()//2
            )
        )
        
    def _draw_link(self):
        mouse = pygame.mouse.get_pos()
        color = self.link_color
        if self.login_link_rect.collidepoint(mouse):
            color = self.button_hover 

        text_surf = self.small_font.render("Already have an account? Login", True, color)
        self.screen.blit(
            text_surf,
            (
                self.login_link_rect.centerx - text_surf.get_width()//2,
                self.login_link_rect.centery - text_surf.get_height()//2
            )
        )
    
    # OBS: Você deve adicionar aqui ou mover para BaseUI os métodos _draw_background, _draw_title, _draw_message.
    # Se não fizer isso, ocorrerá um erro de atributo.