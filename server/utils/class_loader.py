import json
import os
from shared.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSES_METADATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'classes_metadata.json')

_CLASS_DATA_CACHE = None 

def load_all_class_metadata() -> dict:
    """Carrega e retorna todos os metadados de classes do arquivo JSON."""
    global _CLASS_DATA_CACHE
    
    if _CLASS_DATA_CACHE:
        return _CLASS_DATA_CACHE

    if not os.path.exists(CLASSES_METADATA_PATH):
        logger.error(f"FATAL: Class metadata file not found at {CLASSES_METADATA_PATH}")
        return {}
        
    try:
        with open(CLASSES_METADATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _CLASS_DATA_CACHE = data
            logger.info(f"Loaded {len(data)} classes metadata successfully.")
            return data
            
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: Error decoding classes_metadata.json: {e}")
        return {}
    except Exception as e:
        logger.error(f"FATAL: Unexpected error loading classes metadata: {e}")
        return {}

def get_class_metadata(class_name: str) -> dict | None:
    """Retorna os metadados de uma classe específica pelo nome."""
    all_classes = load_all_class_metadata()
    return all_classes.get(class_name)