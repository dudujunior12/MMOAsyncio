import time
from shared.logger import get_logger

logger = get_logger(__name__)

class ClientWorldState:
    def __init__(self):
        self.entities = {}
        self.local_player_id = None
        
        self.map_name = None
        self.map_width = 0
        self.map_height = 0
        self.tile_data = []  # 2D list
        self.tile_metadata = {}  # info de cada tile

    def update_entity(self, entity_data: dict):
        entity_id = entity_data.get('id') or entity_data.get('entity_id')
        if not entity_id:
            return

        is_new = entity_id not in self.entities
        current_data = self.entities.get(entity_id, {'id': entity_id})
        
        old_x, old_y = current_data.get('x'), current_data.get('y')
        
        current_data['x'] = entity_data.get('x', current_data.get('x'))
        current_data['y'] = entity_data.get('y', current_data.get('y'))
        if is_new:
            current_data['x_visual'] = current_data['x']
            current_data['y_visual'] = current_data['y']
        
        current_data['asset_type'] = entity_data.get('asset_type', current_data.get('asset_type'))
        current_data['last_update'] = time.time()
        
        
        
        for key in ['max_health', 'current_health', 'level', 'strength', 'agility', 
                    'vitality', 'intelligence', 'dexterity', 'luck', 'stat_points', 'class_name']:
            if key in entity_data:
                current_data[key] = entity_data[key]
        
        self.entities[entity_id] = current_data
        
        if is_new:
            health_info = f"HP: {current_data.get('current_health', 'N/A')}/{current_data.get('max_health', 'N/A')}"
            logger.info(f"[WORLD] New Entity {entity_id} created for asset '{current_data['asset_type']}' at ({current_data['x']:.1f}, {current_data['y']:.1f}). {health_info}")
        # elif old_x != current_data['x'] or old_y != current_data['y']:
        #     logger.debug(f"[WORLD] Entity {entity_id} moved to ({current_data['x']:.1f}, {current_data['y']:.1f})")
            
        
    def remove_entity(self, entity_id: int):
        if entity_id in self.entities:
            del self.entities[entity_id]

    def get_entity_data(self, entity_id: int):
        return self.entities.get(entity_id)

    def get_all_entities(self):
        return self.entities.values()
    
    def set_local_player(self, entity_id: int):
        self.local_player_id = entity_id
    
    def get_local_player(self):
        if self.local_player_id is None:
            return None
        return self.entities.get(self.local_player_id)
    
    def set_map(self, map_packet: dict):
        self.map_name = map_packet.get("map_name")
        self.map_width = map_packet.get("width", 0)
        self.map_height = map_packet.get("height", 0)
        self.tile_data = map_packet.get("tiles", [])
        self.tile_metadata = map_packet.get("metadata", {})
        logger.info(f"[WORLD] Loaded map '{self.map_name}' ({self.map_width}x{self.map_height}) with {len(self.tile_metadata)} tile types.")
    
    def get_tile_type(self, x: int, y: int):
        if 0 <= y < self.map_height and 0 <= x < self.map_width:
            return self.tile_data[y][x]
        return None
    
    def is_walkable(self, x: int, y: int) -> bool:
        tile_type = self.get_tile_type(x, y)
        if not tile_type:
            return False
        metadata = self.tile_metadata.get(tile_type, {})
        return metadata.get("is_walkable", True)