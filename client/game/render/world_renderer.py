import pygame
from client.game.systems.camera_system import Camera
from client.game.ui.chat_ui import ChatUI
from client.game.ui.status_bar import StatusBar
from shared.constants import SPRITE_SIZE
from shared.logger import get_logger

logger = get_logger(__name__)

SMOOTHING_FACTOR = 2.0

class WorldRenderer:
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
        
    def draw_server_debug_colliders(self, world):
        """
        Desenha as AABBs que o servidor calcula.
        Usa a posição INTERPOLADA (x_visual, y_visual) para estar sincronizado com o sprite.
        """
        for ent in world.get_all_entities():
            col = ent.get("collider")
            if not col:
                continue

            # --- USANDO POSIÇÃO INTERPOLADA (VISUAL) ---
            px = ent.get("x_visual", ent.get("x", 0)) 
            py = ent.get("y_visual", ent.get("y", 0))
            # -------------------------------------------

            # pega extensões (metade da largura e altura)
            if col["type"] == "box" or col["type"] == "sprite":
                hw = col.get("width", 1) / 2
                hh = col.get("height", 1) / 2 
                offset_x = col.get("offset_x", 0)
                offset_y = col.get("offset_y", 0)

                # converte para pixels e aplica camera
                draw_center_x, draw_center_y = self.camera.apply(px * SPRITE_SIZE, py * SPRITE_SIZE)

                # converte extensões para pixels
                width_px = hw * 2 * SPRITE_SIZE
                height_px = hh * 2 * SPRITE_SIZE
                offset_px_x = offset_x * SPRITE_SIZE
                offset_px_y = offset_y * SPRITE_SIZE

                # AABB do servidor desenhada em vermelho
                col_rect = pygame.Rect(
                    draw_center_x + offset_px_x - width_px / 2,
                    draw_center_y + offset_px_y - height_px / 2,
                    width_px,
                    height_px
                )
                pygame.draw.rect(self.screen, (255, 0, 0), col_rect, 2)

            elif col["type"] == "circle":
                offset_x = col.get("offset_x", 0)
                offset_y = col.get("offset_y", 0)
                radius = col.get("radius", 0.5) * SPRITE_SIZE
                
                draw_x, draw_y = self.camera.apply(px * SPRITE_SIZE + offset_x * SPRITE_SIZE,
                                                   py * SPRITE_SIZE + offset_y * SPRITE_SIZE)
                pygame.draw.circle(self.screen, (255, 0, 0), (int(draw_x), int(draw_y)), int(radius), 2)

    def draw(self):
        self.screen.fill((25, 25, 35))

        # --- 1. Desenho do Mapa ---
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

        # --- 2. Atualização da Câmera ---
        player = self.world.get_local_player()
        if player:
            # Garante que a câmera rastreia a Posição VISUAL INTERPOLADA do jogador.
            self.camera.update({"x": player.get("x_visual", player["x"]), 
                                "y": player.get("y_visual", player["y"])}, self.dt)
            
        # --- 3. Desenho e Interpolação de Entidades (Lerp) ---
        for ent in self.world.get_all_entities():
            
            # 3a. Inicializa a posição visual se for a primeira vez
            if "x_visual" not in ent:
                ent["x_visual"] = ent["x"]
                ent["y_visual"] = ent["y"]
            
            move_speed = ent.get("movement_speed", 1.0)
            lerp_factor = min(1.0, move_speed * SMOOTHING_FACTOR * self.dt)
            
            ent["x_visual"] += (ent["x"] - ent["x_visual"]) * lerp_factor
            ent["y_visual"] += (ent["y"] - ent["y_visual"]) * lerp_factor

            x_center = ent["x_visual"] * SPRITE_SIZE
            y_center = ent["y_visual"] * SPRITE_SIZE

            draw_center_x, draw_center_y = self.camera.apply(x_center, y_center)

            # Desenho do Sprite (retângulo simples com pivot nos pés)
            color = self.colors.get(ent.get("asset_type"), (255, 255, 255))
            pygame.draw.rect(
                self.screen,
                color,
                # Começa meia-largura e meia-altura acima do centro
                (draw_center_x - SPRITE_SIZE/2, draw_center_y - SPRITE_SIZE/2, SPRITE_SIZE, SPRITE_SIZE)
            )
            # Desenho do Collider de Entidade
            collider = ent.get("collider")
            if collider and collider["type"] == "box":
                width = collider["width"] * SPRITE_SIZE
                height = collider["height"] * SPRITE_SIZE
                offset_x = collider.get("offset_x", 0) * SPRITE_SIZE
                offset_y = collider.get("offset_y", 0) * SPRITE_SIZE

                col_rect = pygame.Rect(
                    draw_center_x + offset_x - width/2,
                    draw_center_y + offset_y - height/2, 
                    width,
                    height
                )
            
        # --- 4. Elementos de UI e Debug ---
        self.chat_ui.draw()
        
        # Desenha o debug do servidor na posição visual
        self.draw_server_debug_colliders(self.world) 
        
        self.status_bar.draw()
        pygame.display.flip()
        