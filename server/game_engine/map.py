# server/game_engine/map.py
import json
import os # Para verificar a existência do arquivo

from shared.logger import get_logger
from shared.constants import MAP_WIDTH, MAP_HEIGHT 

logger = get_logger(__name__)

MAP_FILE_NAME = "map_data.json"


TILE_TYPE_GRASS = "grass"
TILE_TYPE_MOUNTAIN = "mountain"
TILE_TYPE_WATER = "water"

TILE_METADATA = {
    TILE_TYPE_GRASS: {
        "is_walkable": True,
        "speed_modifier": 1.0, 
        "asset_id": 1,         
    },
    TILE_TYPE_MOUNTAIN: {
        "is_walkable": False,
        "speed_modifier": 0.0,
        "asset_id": 2,
    },
    TILE_TYPE_WATER: {
        "is_walkable": False, 
        "speed_modifier": 0.0,
        "asset_id": 3,
    },
}


class GameMap:
    _tile_data: list[list[str]] = []
    
    def __init__(self, load_from_file=True):
        self.MAP_WIDTH = MAP_WIDTH
        self.MAP_HEIGHT = MAP_HEIGHT
        self._tile_data = [[TILE_TYPE_GRASS for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        if load_from_file and os.path.exists(MAP_FILE_NAME):
            self.load_map_data()
        else:
            if load_from_file:
                logger.warning(f"Map file {MAP_FILE_NAME} not found. Generating default map...")
            
            self._generate_default_map()
            
            if load_from_file:
                self.save_map_data() 
            
        logger.info(f"Game Map initialized: {self.MAP_WIDTH}x{self.MAP_HEIGHT} grid.")


    def _generate_default_map(self):
        
        self._tile_data = [[TILE_TYPE_GRASS for _ in range(self.MAP_WIDTH)] for _ in range(self.MAP_HEIGHT)]

        for y in range(20, 30):
            for x in range(20, 30):
                self._tile_data[y][x] = TILE_TYPE_MOUNTAIN 
                    
        for y in range(40, 50):
            for x in range(50, 60):
                self._tile_data[y][x] = TILE_TYPE_WATER 

        for i in range(self.MAP_WIDTH):
            self._tile_data[0][i] = TILE_TYPE_MOUNTAIN
            self._tile_data[self.MAP_HEIGHT - 1][i] = TILE_TYPE_MOUNTAIN
            self._tile_data[i][0] = TILE_TYPE_MOUNTAIN
            self._tile_data[i][self.MAP_WIDTH - 1] = TILE_TYPE_MOUNTAIN
        
        logger.info("Default Game Map generated successfully.")


    def save_map_data(self):
        data = self.get_map_data_for_client()

        del data["metadata"] 
        
        with open(MAP_FILE_NAME, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Map data saved to {MAP_FILE_NAME}.")

    def load_map_data(self):
        with open(MAP_FILE_NAME, "r") as f:
            data = json.load(f)
            self.MAP_WIDTH = data["width"]
            self.MAP_HEIGHT = data["height"]
            self._tile_data = data["tiles"]
        logger.info(f"Map data loaded from {MAP_FILE_NAME}: {self.MAP_WIDTH}x{self.MAP_HEIGHT}")


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
            
        metadata = TILE_METADATA.get(tile_type)
        
        if not metadata:
             logger.error(f"Tile type {tile_type} has no metadata!")
             return False
             
        return metadata["is_walkable"]
    
    def get_map_data_for_client(self) -> dict:
        return {
            "width": self.MAP_WIDTH,
            "height": self.MAP_HEIGHT,
            "tiles": self._tile_data, 
            "metadata": TILE_METADATA 
        }