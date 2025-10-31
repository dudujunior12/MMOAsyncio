import json
import os

from server.utils.tile_loader import load_tileset
from shared.logger import get_logger

logger = get_logger(__name__)

class GameMap:
    _tile_data: list[list[str]] = []
    tile_metadata: dict[str, dict] = {}

    def __init__(self, map_name: str, map_data: dict, load_from_file=True,):
        self.MAP_WIDTH = map_data["width"]
        self.MAP_HEIGHT = map_data["height"]
        self.MAP_NAME = map_name
        self.MAP_FILE_PATH = os.path.join("server", "maps", map_data["file"])
        map_dir = os.path.dirname(self.MAP_FILE_PATH)
        
        tileset_key = map_data.get("tileset_key", "base")
        self.tile_metadata = load_tileset(tileset_key)
        
        if not self.tile_metadata:
            logger.error(f"FATAL: Could not load tileset '{tileset_key}' for map {map_name}. Using critical fallback.")
            self.tile_metadata = {"grass": {"is_walkable": True, "speed_modifier": 1.0, "asset_id": 1}}
            
        default_tile_type = next(iter(self.tile_metadata.keys()), "grass") 

        if not os.path.exists(map_dir):
            os.makedirs(map_dir, exist_ok=True)
            logger.info(f"Created map directory: {map_dir}")
            
        self._tile_data = [[default_tile_type for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        if load_from_file and os.path.exists(self.MAP_FILE_PATH):
            self.load_map_data()
        else:
            if load_from_file:
                logger.warning(f"Map file {self.MAP_FILE_PATH} not found. Generating default map structure for {self.MAP_NAME}...")
            
            self._generate_default_map() 
            
            if load_from_file:
                self.save_map_data() 
            
        logger.info(f"Game Map initialized: {self.MAP_WIDTH}x{self.MAP_HEIGHT} grid with tileset '{tileset_key}'.")


    def _generate_default_map(self):
        
        available_tiles = list(self.tile_metadata.keys())
        
        if self.MAP_NAME == "Starting_Area":
            logger.info("Generating Starter Map structure: Water and simple borders.")

            if "water" in available_tiles:
                for y in range(40, 50):
                    for x in range(50, 60):
                        self._tile_data[y][x] = "water"
            
            border_tile = "mountain" if "mountain" in available_tiles else available_tiles[0] 
            for i in range(self.MAP_WIDTH):
                self._tile_data[0][i] = border_tile
                self._tile_data[self.MAP_HEIGHT - 1][i] = border_tile
            for i in range(self.MAP_HEIGHT):
                self._tile_data[i][0] = border_tile
                self._tile_data[i][self.MAP_WIDTH - 1] = border_tile

        elif self.MAP_NAME == "Dark_Forest":
            logger.info("Generating Dark Forest structure: Rocky paths and dense unpassable areas.")
            
            if "mountain" in available_tiles:
                for y in range(self.MAP_HEIGHT // 2 - 10, self.MAP_HEIGHT // 2 + 10):
                    for x in range(10, self.MAP_WIDTH - 10):
                        if (x % 5 == 0) or (y % 7 == 0):
                            self._tile_data[y][x] = "mountain"
        
        else:
            logger.warning(f"No specific default generation logic for map: {self.MAP_NAME}. Using flat default tile.")

        logger.info(f"Default map structure generated successfully for {self.MAP_NAME}.")


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
        tile_x = int(x)
        tile_y = int(y)
        
        if not (0 <= tile_x < self.MAP_WIDTH and 0 <= tile_y < self.MAP_HEIGHT):
            return None 
            
        return self._tile_data[tile_y][tile_x]
        
    def is_walkable(self, x: float, y: float) -> bool:
        tile_type = self.get_tile_type(x, y)
        
        if tile_type is None:
            return False 
            
        metadata = self.tile_metadata.get(tile_type)
        
        if not metadata:
             logger.error(f"Tile type '{tile_type}' in map data has no metadata in tileset!")
             return False
             
        return metadata["is_walkable"]
    
    def get_map_data_for_client(self) -> dict:
        return {
            "width": self.MAP_WIDTH,
            "height": self.MAP_HEIGHT,
            "tiles": self._tile_data, 
            "metadata": self.tile_metadata
        }