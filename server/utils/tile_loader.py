import json
import os

TILESET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'tilesets.json')

def load_tileset(key: str) -> dict | None:
    try:
        with open(TILESET_PATH, 'r', encoding='utf-8') as f:
            all_tilesets = json.load(f)
            return all_tilesets.get(key)
    except FileNotFoundError:
        print(f"ERROR: Tileset file not found at {TILESET_PATH}")
        return None
    except Exception as e:
        print(f"ERROR loading tileset {key}: {e}")
        return None