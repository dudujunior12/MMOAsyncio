import asyncio
from shared.protocol import encode_message, decode_message
from shared.logger import get_logger

logger = get_logger(__name__)

class GameClient:
    def __init__(self, host, port, data_payload_size):
        self.host = host
        self.port = port
        self.data_payload_size = data_payload_size
        self.reader = None
        self.writer = None
        
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
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
        try:
            data = await self.reader.readline()
            if data:
                decoded_message = decode_message(data.strip())
                return decoded_message
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self.close()
            return None
    
    def close(self):
        if self.writer:
            self.writer.close()
            logger.info("Connection closed.")