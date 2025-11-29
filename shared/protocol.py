import json
from shared.logger import get_logger

PACKET_AUTH_SUCCESS = "AUTH_SUCCESS"
PACKET_AUTH_FAIL = "AUTH_FAIL"
PACKET_CHAT_MESSAGE = "CHAT_MESSAGE"
PACKET_REGISTER_SUCCESS = "REGISTER_SUCCESS"
PACKET_REGISTER_FAIL = "REGISTER_FAIL"
PACKET_SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
PACKET_AUTH = "AUTH"
PACKET_REGISTER = "REGISTER"
PACKET_MOVE = "MOVE"
PACKET_ITEM_USE = "ITEM_USE"
PACKET_POSITION_UPDATE = "POS_UPDATE"
PACKET_WORLD_STATE = "WORLD_STATE"
PACKET_ENTITY_REMOVE = "ENTITY_REMOVE"
PACKET_ENTITY_NEW = "ENTITY_NEW"
PACKET_ENTITY_UPDATE = "ENTITY_UPDATE"
PACKET_MAP_DATA = "MAP_DATA"
PACKET_HEALTH_UPDATE = 'HEALTH_UPDATE'
PACKET_DAMAGE = "DAMAGE"
PACKET_EVOLVE = "EVOLVE"

logger = get_logger(__name__)

def encode_message(data) -> bytes:
    try:
        if isinstance(data, dict):
            json_string = json.dumps(data) + '\n' 
        else:
            json_string = str(data) + '\n'
            
        return json_string.encode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding message: {e}")
        return b''

def decode_message(data: bytes):
    try:
        decoded_string = data.decode('utf-8')
        if not decoded_string:
            return None

        return json.loads(decoded_string)
    except json.JSONDecodeError:
        return decoded_string
    except Exception as e:
        logger.error(f"Error decoding message: {e}")
        return data

