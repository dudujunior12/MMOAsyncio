from shared.protocol import (
    PACKET_AUTH,
    PACKET_ENTITY_REMOVE,
    PACKET_SYSTEM_MESSAGE,
    encode_message,
    decode_message, 
    PACKET_CHAT_MESSAGE,
    PACKET_REGISTER_SUCCESS,
    PACKET_REGISTER_FAIL,
    PACKET_AUTH_SUCCESS,
    PACKET_AUTH_FAIL,
    PACKET_REGISTER
)
from shared.logger import get_logger
import asyncio
from server.db.login import authenticate_user, create_user

logger = get_logger(__name__)

class ServerSocket:
    def __init__(self, host, port, data_payload_size, db_pool, game_engine):
        self.host = host
        self.port = port
        self.server_address = (host, port)
        self.data_payload_size = data_payload_size
        self.clients = {}
        self.game_engine = game_engine
        self.db_pool = db_pool
        self.server = None
    
    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"Server started at {self.server_address}")
        async with self.server:
            await self.server.serve_forever()
    
    async def send_packet(self, writer: asyncio.StreamWriter, packet: dict):
        try:
            writer.write(encode_message(packet))
            await writer.drain()
        except Exception as e:
            logger.error(f"Error sending packet to {writer.get_extra_info('peername')}: {e}")
            
    async def handle_authentication(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        while True:
            try:
                data = await reader.readline()
                if not data:
                    return None
                
                packet = decode_message(data.strip())
                
                if isinstance(packet, dict):
                    pkt_type = packet.get('type')
                    username = packet.get('username')
                    raw_password = packet.get('password')
                    if pkt_type == PACKET_AUTH:
                        logger.info(f"Authentication attempt from {addr} with username: {username}")
                        if await authenticate_user(self.db_pool, username, raw_password):
                            await self.send_packet(writer, {'type': PACKET_AUTH_SUCCESS, 'status': 'success'})
                            logger.info(f"User '{username}' authenticated successfully from {addr}")
                            return username
                        else:
                            await self.send_packet(writer, {'type': PACKET_AUTH_FAIL, 'status': 'failure'})
                            logger.warning(f"User '{username}' failed to authenticate from {addr}")
                            continue
                    elif pkt_type == PACKET_REGISTER:
                        logger.info(f"Registration attempt from {addr} with username: {username}")
                        if await create_user(self.db_pool, username, raw_password):
                            await self.send_packet(writer, {'type': PACKET_REGISTER_SUCCESS, 'status': 'success'})
                            logger.info(f"User '{username}' registered successfully from {addr}")
                            return username
                        else:
                            await self.send_packet(writer, {'type': PACKET_REGISTER_FAIL, 'status': 'failure'})
                            logger.warning(f"User '{username}' failed to register from {addr}")
                            continue
                    else:
                        await self.send_packet(writer, {'type': PACKET_AUTH_FAIL, 'message': 'Invalid authentication packet'})
                        logger.warning(f"Invalid authentication packet from {addr}: {packet}")
            except Exception as e:
                logger.error(f"Error during authentication from {addr}: {e}")
                return None
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        authenticated_user = None
        
        logger.info(f"New connection from {addr}. Starting authentication.")
        authenticated_user = await self.handle_authentication(reader, writer)
        
        if authenticated_user:
            user_info = {'user': authenticated_user, 'addr': addr}
            self.clients[writer] = user_info
            logger.info(f"User {authenticated_user} connected from {addr}")
            await self.game_engine.player_connected(writer, authenticated_user)
            
            await self.broadcast_system_message(f"User {authenticated_user} has joined.", exclude_writer=writer)
        
            try:
                while True:
                    data = await reader.readline()
                        
                    if not data:
                        break
                    
                    packet = decode_message(data.strip())
                    if isinstance(packet, dict):
                        pkt_type = packet.get('type')
                    
                        if pkt_type in [PACKET_AUTH, PACKET_REGISTER]:
                            logger.warning(f"Received unexpected auth/register packet from authenticated user {authenticated_user} at {addr}")
                            continue
                    
                        await self.game_engine.process_network_packet(writer, packet)

                    else:
                        logger.warning(f"Unknown or malformed packet from {addr}: {packet}")

            except (OSError, ConnectionResetError) as e:
                pass
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
            finally:
                user_info = self.clients.pop(writer, None)
                user = user_info['user'] if user_info else authenticated_user

                if user:
                    logger.info(f"User {user} disconnected from {addr}")
                    entity_id, asset_type = await self.game_engine.player_disconnected(user)
                    if entity_id:
                        removal_packet = {
                            'type': PACKET_ENTITY_REMOVE,
                            'entity_id': entity_id,
                            'asset_type': asset_type,
                        }
                        await self.broadcast_game_update(removal_packet, exclude_writer=writer)
                    await self.broadcast_system_message(f"User {user} has left.", exclude_writer=writer)


                writer.close()
                try:
                    await writer.wait_closed()
                except (OSError, ConnectionResetError) as e:
                    pass
                logger.info(f"Connection closed from {addr}")
                
    def get_user_by_writer(self, writer: asyncio.StreamWriter):
        user_info = self.clients.get(writer)
        return user_info['user'] if user_info else None
            
    async def broadcast_chat_message(self, message: str, exclude_writer=None):
        chat_packet = {'type': PACKET_CHAT_MESSAGE, 'content': message}
        encoded_message = encode_message(chat_packet)
        for writer in self.clients.keys():
            if writer != exclude_writer:
                try:
                    writer.write(encoded_message)
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")

    async def broadcast_system_message(self, message: str, exclude_writer=None):
        system_packet = {'type': PACKET_SYSTEM_MESSAGE, 'content': message}
        encoded_message = encode_message(system_packet)
        for writer in self.clients.keys():
            if writer != exclude_writer:
                try:
                    writer.write(encoded_message)
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Error broadcasting system message: {e}")
                    
    async def broadcast_game_update(self, packet: dict, exclude_writer=None):
        try: 
            encoded_message = encode_message(packet)
            
            for writer in self.clients.keys():
                if writer != exclude_writer:
                    try:
                        writer.write(encoded_message)
                        await writer.drain()
                    except Exception:
                        logger.error(f"Error sending broadcast: {e}")
        except Exception as e:
            logger.error(f"Error during game update broadcast: {e}")
    
    async def shutdown(self):
        logger.info("Server shutting down.")
        for writer in self.clients:
            writer.close()
            await writer.wait_closed()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("Server has been shut down.")