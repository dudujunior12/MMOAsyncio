import pygame
from client.game.ui.base_ui import BaseUI
from shared.logger import get_logger

logger = get_logger(__name__)

class StatusBar(BaseUI):
    def __init__(self, screen, player_entity_id, world, font_size=16, padding=5):
        super().__init__(screen)
        self.player_entity_id = player_entity_id
        self.world = world
        self.font = pygame.font.SysFont("Arial", font_size)
        self.padding = padding
        self.bg_color = (20, 20, 30, 200)  # semi-transparente
        self.text_color = (255, 255, 255)
        self.width = 220
        self.height = 100
        self.pos = (10, 10)  # canto superior esquerdo

    def update(self, dt):
        # Por enquanto não precisa atualizar nada, mas você poderia animar barras
        pass

    def draw(self):
        player_data = self.world.get_local_player()
        if not player_data:
            return

        # Caixa de fundo
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill(self.bg_color)
        self.screen.blit(s, self.pos)

        x, y = self.pos
        lines = [
            f"{player_data.get('asset_type', 'Unknown')} - {player_data.get('class_name', 'Unknown')} - Lvl {player_data.get('level', 1)}",
            f"HP: {player_data.get('current_health', 0)}/{player_data.get('max_health', 0)}",
            f"STR:{player_data.get('strength', 0)} AGI:{player_data.get('agility', 0)} VIT:{player_data.get('vitality', 0)}",
            f"INT:{player_data.get('intelligence', 0)} DEX:{player_data.get('dexterity', 0)} LUK:{player_data.get('luck', 0)}",
            f"SP: {player_data.get('stat_points', 0)}"
        ]

        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, self.text_color)
            self.screen.blit(text_surf, (x + self.padding, y + self.padding + i * (self.font.get_height() + 2)))
