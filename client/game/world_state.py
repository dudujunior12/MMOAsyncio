import time
from shared.logger import get_logger

logger = get_logger(__name__)

class ClientWorldState:
    def __init__(self):
        self.entities = {} 

    def update_entity(self, entity_data: dict):
        entity_id = entity_data.get('id') or entity_data.get('entity_id')
        if not entity_id:
            return

        is_new = entity_id not in self.entities
        current_data = self.entities.get(entity_id, {'id': entity_id})
        
        old_x, old_y = current_data.get('x'), current_data.get('y')
        
        new_x = entity_data.get('x', current_data.get('x'))
        new_y = entity_data.get('y', current_data.get('y'))
        
        current_data['x'] = new_x
        current_data['y'] = new_y
        current_data['asset_type'] = entity_data.get('asset_type', current_data.get('asset_type'))
        current_data['last_update'] = time.time()
        
        self.entities[entity_id] = current_data
        
        if is_new:
            logger.info(f"[WORLD] New Entity {entity_id} created for asset '{current_data['asset_type']}' at ({new_x:.1f}, {new_y:.1f})")
        elif old_x != new_x or old_y != new_y:
            logger.debug(f"[WORLD] Entity {entity_id} moved to ({new_x:.1f}, {new_y:.1f})")
        
    def remove_entity(self, entity_id: int):
        if entity_id in self.entities:
            del self.entities[entity_id]

    def get_entity_data(self, entity_id: int):
        return self.entities.get(entity_id)

    def get_all_entities(self):
        return self.entities.values()