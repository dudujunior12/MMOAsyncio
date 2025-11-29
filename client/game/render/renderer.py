# client/game/render/renderer.py
import pygame
from client.game.systems.camera_system import Camera
from client.game.systems.chat_system import ChatSystem
from client.game.ui.chat_ui import ChatUI
from client.game.ui.status_bar import StatusBar
from shared.constants import SPRITE_SIZE
from shared.logger import get_logger

logger = get_logger(__name__)

class GameRenderer:
    def __init__(self, world, screen, player_entity_id):

        self.world = world
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.chat_ui = ChatUI(screen)
        self.camera = Camera(self.screen.get_width(), self.screen.get_height())
        self.player_entity_id = player_entity_id

        self.colors = {
            "dudu": (0, 200, 255),
            "Green_Slime": (0, 255, 0),
            "Wolf_Pack_Leader": (160, 160, 160),
        }
        
        self.status_bar = StatusBar(screen, player_entity_id, world)

    def draw(self):
        self.screen.fill((25, 25, 35))

        for y in range(self.world.map_height):
            for x in range(self.world.map_width):
                tile_type = self.world.get_tile_type(x, y)
                if not tile_type:
                    continue
                metadata = self.world.tile_metadata.get(tile_type, {})
                asset_id = metadata.get("asset_id", 0)
                color = (100, 100, 100)
                if tile_type == "grass":
                    color = (50, 200, 50)
                elif tile_type == "water":
                    color = (50, 50, 200)
                elif tile_type == "mountain":
                    color = (150, 150, 150)
                elif tile_type == "rocky_path":
                    color = (120, 100, 80)
                elif tile_type == "forest_floor":
                    color = (34, 139, 34)
                elif tile_type == "swamp":
                    color = (70, 50, 30)

                draw_x, draw_y = self.camera.apply(x * SPRITE_SIZE, y * SPRITE_SIZE)
                pygame.draw.rect(
                    self.screen,
                    color,
                    (draw_x, draw_y, SPRITE_SIZE, SPRITE_SIZE)
                )

        player = self.world.get_local_player()
        if player:
            self.camera.update(player)
            
        speed = 5.0
        for ent in self.world.get_all_entities():
            ent["x_visual"] += (ent["x"] - ent["x_visual"]) * min(1, speed * self.dt)
            ent["y_visual"] += (ent["y"] - ent["y_visual"]) * min(1, speed * self.dt)

            draw_x, draw_y = self.camera.apply(
                int(ent["x_visual"] * SPRITE_SIZE),
                int(ent["y_visual"] * SPRITE_SIZE)
            )

            color = self.colors.get(ent.get("asset_type"), (255, 255, 255))
            pygame.draw.rect(
                self.screen,
                color,
                (draw_x, draw_y, SPRITE_SIZE, SPRITE_SIZE)
            )
            
        self.chat_ui.draw()

        self.status_bar.draw()
        pygame.display.flip()
