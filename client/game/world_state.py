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
        
        # --- Lógica de Posição/Asset (EXISTENTE) ---
        old_x, old_y = current_data.get('x'), current_data.get('y')
        
        current_data['x'] = entity_data.get('x', current_data.get('x'))
        current_data['y'] = entity_data.get('y', current_data.get('y'))
        current_data['asset_type'] = entity_data.get('asset_type', current_data.get('asset_type'))
        current_data['last_update'] = time.time()
        
        # --- Lógica de VIDA (NOVO) ---
        # Atualiza a vida máxima e atual, se presente no pacote
        if 'max_health' in entity_data:
            current_data['max_health'] = entity_data['max_health']
        if 'current_health' in entity_data:
            current_data['current_health'] = entity_data['current_health']
        
        self.entities[entity_id] = current_data
        
        if is_new:
            health_info = f"HP: {current_data.get('current_health', 'N/A')}/{current_data.get('max_health', 'N/A')}"
            logger.info(f"[WORLD] New Entity {entity_id} created for asset '{current_data['asset_type']}' at ({current_data['x']:.1f}, {current_data['y']:.1f}). {health_info}")
        elif old_x != current_data['x'] or old_y != current_data['y']:
            logger.debug(f"[WORLD] Entity {entity_id} moved to ({current_data['x']:.1f}, {current_data['y']:.1f})")
        
    def remove_entity(self, entity_id: int):
        if entity_id in self.entities:
            del self.entities[entity_id]

    def get_entity_data(self, entity_id: int):
        return self.entities.get(entity_id)

    def get_all_entities(self):
        return self.entities.values()