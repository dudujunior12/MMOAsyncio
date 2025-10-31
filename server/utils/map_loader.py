# server/game_engine/engine.py ou um novo módulo utilitário (ex: server/utils/map_loader.py)

import json
import os

MAP_METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'map_metadata.json')

def load_map_metadata(map_name: str) -> dict | None:
    if not os.path.exists(MAP_METADATA_PATH):
        return None
        
    try:
        with open(MAP_METADATA_PATH, 'r', encoding='utf-8') as f:
            all_maps = json.load(f)
            
        for map_data in all_maps:
            if map_data.get("name") == map_name:
                return map_data
                
        return None
        
    except Exception as e:
        return None