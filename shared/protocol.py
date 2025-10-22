import json

# --- Tipos de Pacotes (Protocolo) ---
# Usados para o cliente e o servidor saberem o que fazer com a mensagem.
# A primeira mensagem do cliente DEVE ser um pacote de LOGIN.
PACKET_LOGIN = "LOGIN"
PACKET_AUTH_SUCCESS = "AUTH_SUCCESS"
PACKET_AUTH_FAIL = "AUTH_FAIL"
PACKET_CHAT_MESSAGE = "CHAT_MESSAGE"
PACKET_REGISTER_SUCCESS = "REGISTER_SUCCESS"
PACKET_REGISTER_FAIL = "REGISTER_FAIL"
PACKET_SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
PACKET_AUTH = "AUTH"
PACKET_REGISTER = "REGISTER"
# PACKET_MOVE, PACKET_ITEM_USE, etc., viriam aqui mais tarde.

# --- Funções de Codificação/Decodificação ---

def encode_message(data) -> bytes:
    try:
        if isinstance(data, dict):
            json_string = json.dumps(data) + '\n' 
        else:
            json_string = str(data) + '\n'
            
        return json_string.encode('utf-8')
    except Exception as e:
        print(f"Erro ao codificar a mensagem: {e}")
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
        print(f"Erro ao decodificar a mensagem: {e}")
        return data

