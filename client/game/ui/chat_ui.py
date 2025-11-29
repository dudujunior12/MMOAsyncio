import pygame
import textwrap

class ChatUI:
    def __init__(self, screen):
        self.screen = screen

        # ----- Responsivo -----
        w, h = screen.get_size()
        self.width = int(w * 0.30)       # 30% da largura da tela
        self.height = int(h * 0.35)      # 35% da altura da tela

        self.font = pygame.font.SysFont("consolas", max(14, int(h * 0.018)))

        # Dados
        self.messages = []
        self.input_text = ""
        self.active = False
        self.max_messages = 100          # scroll buffer

        # Estética
        self.bg_color = (15, 15, 22)
        self.border_color = (180, 180, 180)
        self.msg_color = (230, 230, 230)
        self.input_bg = (25, 25, 35)
        self.input_border = (200, 200, 255)

        # Espaçamentos
        self.padding = 12
        self.line_spacing = 4

    def wrap_text(self, text, max_width):
        """Quebra uma mensagem em várias linhas que caibam no retângulo."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test = current_line + (" " if current_line else "") + word
            if self.font.size(test)[0] <= max_width:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def add_message(self, sender, text):
        msg = f"{sender}: {text}"
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if self.active:
                if event.key == pygame.K_RETURN:
                    txt = self.input_text
                    self.input_text = ""
                    self.active = False
                    return txt

                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]

                else:
                    if len(self.input_text) < 300:
                        self.input_text += event.unicode

            else:
                if event.key == pygame.K_t:
                    self.active = True
                    return None

        return None

    def draw(self):

        # --- Chat rect responsivo ---
        x = 10
        y = self.screen.get_height() - self.height - 10
        chat_rect = pygame.Rect(x, y, self.width, self.height)

        # --- Fundo ---
        pygame.draw.rect(self.screen, self.bg_color, chat_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.border_color, chat_rect, 2, border_radius=8)

        # Área para mensagens
        text_area_height = self.height - 50
        text_area = pygame.Rect(x + self.padding, y + self.padding,
                                self.width - self.padding * 2,
                                text_area_height)

        # --- Render das mensagens com quebra de linha ---
        lines = []
        for msg in self.messages[-30:]:  # exibe só últimas 30 (com scroll interno)
            wrapped = self.wrap_text(msg, text_area.width)
            lines.extend(wrapped)

        # Mantém dentro da área
        max_lines = text_area.height // (self.font.get_height() + self.line_spacing)
        lines = lines[-max_lines:]

        draw_y = text_area.y
        for line in lines:
            surf = self.font.render(line, True, self.msg_color)
            self.screen.blit(surf, (text_area.x, draw_y))
            draw_y += self.font.get_height() + self.line_spacing

        # --- Input box responsiva ---
        input_rect = pygame.Rect(
            x + 6,
            y + self.height - 38,
            self.width - 12,
            30
        )

        if self.active:
            pygame.draw.rect(self.screen, self.input_bg, input_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.input_border, input_rect, 2, border_radius=6)

            txt_surf = self.font.render(self.input_text, True, (255, 255, 255))
            self.screen.blit(txt_surf, (input_rect.x + 6, input_rect.y + 6))
        else:
            # Mostra um input "desativado", mais escuro
            pygame.draw.rect(self.screen, (30, 30, 40), input_rect, border_radius=6)
            pygame.draw.rect(self.screen, (60, 60, 80), input_rect, 1, border_radius=6)

            hint = self.font.render("[T] para digitar…", True, (120, 120, 140))
            self.screen.blit(hint, (input_rect.x + 6, input_rect.y + 6))
