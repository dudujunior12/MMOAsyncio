import asyncio
from shared.protocol import encode_message, decode_message
from shared.logger import get_logger
from client.game.world_state import ClientWorldState

logger = get_logger(__name__)

class GameClient:
    def __init__(self, host, port, data_payload_size):
        self.host = host
        self.port = port
        self.data_payload_size = data_payload_size
        self.reader = None
        self.writer = None
        self.world_state = ClientWorldState()
        self.is_closed = False
        
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port, limit=self.data_payload_size)
            logger.info(f"Connected to server at {(self.host, self.port)}")
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            
    async def send_message(self, message):
        try:
            encoded_message = encode_message(message)
            self.writer.write(encoded_message)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.close()
            
    async def receive_message(self):
        if not self.reader: return None
        try:
            data = await self.reader.readuntil(b'\n') 
            
            if not data:
                logger.info("Server closed the connection gracefully.")
                self.close()
                return None
            
            decoded_message = decode_message(data.strip())
            return decoded_message
            
        except asyncio.LimitOverrunError as e:
            
            logger.error(f"Error receiving message: Packet exceeded configured size limit ({self.data_payload_size} bytes).")
            
            try:
                await self.reader.readuntil(b'\n')
            except Exception:
                pass
            self.close()
            return None
        
        except (ConnectionResetError, asyncio.IncompleteReadError) as e:
            logger.info("Connection closed by server (Expected disconnect after kick message).")
            self.close()
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self.close()
            return None
    
    def close(self):
        if not self.is_closed:
            self.is_closed = True
            if self.writer:
                self.writer.close()
            logger.info("Connection closed.")