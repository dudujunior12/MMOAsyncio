import json
import os
import random

from server.utils.tile_loader import load_tileset
from shared.logger import get_logger

logger = get_logger(__name__)

class GameMap:
    _tile_data: list[list[str]] = []
    tile_metadata: dict[str, dict] = {}

    def __init__(self, map_name: str, map_data: dict, load_from_file=True):
        self.MAP_WIDTH = map_data["width"]
        self.MAP_HEIGHT = map_data["height"]
        self.MAP_NAME = map_name
        self.MAP_FILE_PATH = os.path.join("server", "maps", map_data["file"])
        map_dir = os.path.dirname(self.MAP_FILE_PATH)

        # Tileset
        tileset_key = map_data.get("tileset_key", "base")
        self.tile_metadata = load_tileset(tileset_key)
        if not self.tile_metadata:
            logger.error(f"FATAL: Could not load tileset '{tileset_key}' for map {map_name}. Using fallback.")
            self.tile_metadata = {"grass": {"is_walkable": True, "speed_modifier": 1.0, "asset_id": 1}}

        default_tile = next(iter(self.tile_metadata.keys()), "grass")
        self._tile_data = [[default_tile for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        if not os.path.exists(map_dir):
            os.makedirs(map_dir, exist_ok=True)
            logger.info(f"Created map directory: {map_dir}")

        if load_from_file and os.path.exists(self.MAP_FILE_PATH):
            self.load_map_data()
            # Corrige tiles inválidos automaticamente
            self._tile_data = [
                [t if t in self.tile_metadata else default_tile for t in row]
                for row in self._tile_data
            ]
            logger.info(f"Loaded and sanitized map '{self.MAP_NAME}' from file.")
        else:
            if load_from_file:
                logger.warning(f"Map file {self.MAP_FILE_PATH} not found. Generating default map for {self.MAP_NAME}...")
            self.patterns = map_data.get("patterns", {})
            self._generate_default_map()
            if load_from_file:
                self.save_map_data()

        logger.info(f"Game Map initialized: {self.MAP_WIDTH}x{self.MAP_HEIGHT} with tileset '{tileset_key}'.")

    def _generate_default_map(self):
        default_tile = next(iter(self.tile_metadata.keys()), "grass")
        self._tile_data = [[default_tile for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        # Função de segurança para tiles
        def safe_tile(tile_name: str):
            return tile_name if tile_name in self.tile_metadata else default_tile

        # --- Bordas ---
        border_tile = safe_tile(self.patterns.get("borders", default_tile))
        for y in range(self.MAP_HEIGHT):
            for x in range(self.MAP_WIDTH):
                if y == 0 or y == self.MAP_HEIGHT - 1 or x == 0 or x == self.MAP_WIDTH - 1:
                    self._tile_data[y][x] = border_tile

        # --- Área central ---
        center = self.patterns.get("center")
        if center:
            x_start, x_end = center.get("x_start", 0), center.get("x_end", self.MAP_WIDTH)
            y_start, y_end = center.get("y_start", 0), center.get("y_end", self.MAP_HEIGHT)
            center_tile = safe_tile(center.get("tile", default_tile))
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    self._tile_data[y][x] = center_tile

        # --- Tiles aleatórios ---
        random_cfg = self.patterns.get("random", {})
        random_tiles = [safe_tile(t) for t in random_cfg.get("tiles", [])]
        density = random_cfg.get("density", 0.05)
        for y in range(self.MAP_HEIGHT):
            for x in range(self.MAP_WIDTH):
                if self._tile_data[y][x] == default_tile and random_tiles:
                    if random.random() < density:
                        self._tile_data[y][x] = random.choice(random_tiles)

        logger.info(f"Default map for '{self.MAP_NAME}' generated with safe tiles.")

    def save_map_data(self):
        data = {
            "width": self.MAP_WIDTH,
            "height": self.MAP_HEIGHT,
            "tiles": self._tile_data,
        }
        with open(self.MAP_FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Map data saved to {self.MAP_FILE_PATH}.")

    def load_map_data(self):
        with open(self.MAP_FILE_PATH, "r") as f:
            data = json.load(f)
            self.MAP_WIDTH = data["width"]
            self.MAP_HEIGHT = data["height"]
            self._tile_data = data["tiles"]
        logger.info(f"Map data loaded from {self.MAP_FILE_PATH}: {self.MAP_WIDTH}x{self.MAP_HEIGHT}")

    def get_tile_type(self, x: float, y: float) -> str | None:
        tile_x, tile_y = int(x), int(y)
        if not (0 <= tile_x < self.MAP_WIDTH and 0 <= tile_y < self.MAP_HEIGHT):
            return None
        return self._tile_data[tile_y][tile_x]

    def is_walkable(self, x: float, y: float) -> bool:
        tile_type = self.get_tile_type(x, y)
        if tile_type is None:
            return False
        metadata = self.tile_metadata.get(tile_type)
        if not metadata:
            logger.error(f"Tile type '{tile_type}' has no metadata!")
            return False
        return metadata["is_walkable"]

    def get_map_data_for_client(self) -> dict:
        return {
            "width": self.MAP_WIDTH,
            "height": self.MAP_HEIGHT,
            "tiles": self._tile_data,
            "metadata": self.tile_metadata
        }
