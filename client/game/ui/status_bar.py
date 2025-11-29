import pygame
from client.game.ui.base_ui import BaseUI
from shared.logger import get_logger

logger = get_logger(__name__)

class StatusBar(BaseUI):
    def __init__(self, screen, player_entity_id, world):
        super().__init__(screen)
        self.player_entity_id = player_entity_id
        self.world = world

        # ----- Responsivo -----
        w, h = screen.get_size()
        self.width = int(w * 0.22)      # 22% da largura da tela
        self.height = int(h * 0.16)     # 16% da altura da tela

        font_size = max(14, int(h * 0.018))
        self.font = pygame.font.SysFont("consolas", font_size)

        # ----- Estética igual ao chat -----
        self.bg_color = (15, 15, 22)
        self.border_color = (180, 180, 180)
        self.text_color = (230, 230, 230)

        # ----- Posições -----
        self.padding = 12
        self.pos = (10, 10)

    def update(self, dt):
        pass

    def draw(self):
        player = self.world.get_local_player()
        if not player:
            return

        # --- Fundo com borda arredondada ---
        x, y = self.pos
        rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(self.screen, self.bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.border_color, rect, 2, border_radius=8)

        # --- Texto ---
        lines = [
            f"{player.get('asset_type', 'Unknown')} - {player.get('class_name', 'Unknown')} - Lvl {player.get('level', 1)}",
            f"HP: {player.get('current_health', 0)}/{player.get('max_health', 0)}",
            f"STR:{player.get('strength', 0)}  AGI:{player.get('agility', 0)}  VIT:{player.get('vitality', 0)}",
            f"INT:{player.get('intelligence', 0)}  DEX:{player.get('dexterity', 0)}  LUK:{player.get('luck', 0)}",
            f"SP: {player.get('stat_points', 0)}"
        ]

        text_y = y + self.padding
        for line in lines:
            text_surface = self.font.render(line, True, self.text_color)
            self.screen.blit(text_surface, (x + self.padding, text_y))
            text_y += self.font.get_height() + 4
