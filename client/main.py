from client.network.client import GameClient
from client.input.login_input import get_auth_choice, get_credentials, display_message, prompt_for_game_action
from shared.protocol import (
    PACKET_AUTH,
    PACKET_AUTH_SUCCESS,
    PACKET_CHAT_MESSAGE,
    PACKET_REGISTER,
    PACKET_REGISTER_SUCCESS,
    PACKET_SYSTEM_MESSAGE,
    PACKET_POSITION_UPDATE,
)
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE
import asyncio
from shared.logger import get_logger
import sys

logger = get_logger(__name__)

async def handle_server_messages(client: GameClient):
    while True:
        try:
            message = await client.receive_message()
            if message:
                if isinstance(message, str):
                    await display_message(message, is_system=False)
                elif isinstance(message, dict):
                    pkt_type = message.get("type")
                    if pkt_type == PACKET_SYSTEM_MESSAGE:
                        content = message.get("content", "")
                        await display_message(content, is_system=True)
                    elif pkt_type == PACKET_CHAT_MESSAGE:
                        content = message.get("content", "")
                        await display_message(content, is_system=False)
                        
                    elif pkt_type == PACKET_POSITION_UPDATE:
                        entity_id = message.get("entity_id")
                        x = message.get("x")
                        y = message.get("y")
                        await display_message(f"Entity {entity_id} moved to ({x}, {y}).", is_system=True)
                else:
                    await display_message(message, is_system=True)
            else:
                logger.warning("Server closed connection.")
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            break            

async def handle_user_input(client: GameClient):
    while True:
        try:
            action_packet = await prompt_for_game_action()
            if action_packet is None:
                logger.info("User requested to quit.")
                break
            if action_packet:
                await client.send_message(action_packet)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in input loop: {e}")
            break

    client.close()
    
async def authenticate(client: GameClient):
    while True:
        choice = await get_auth_choice()
        if choice is None:
            return False

        is_register = choice == 'R'
        creds = await get_credentials(is_register=(choice == 'R'))
        if creds is None:
            return False
        
        username, password = creds

        auth_packet = {
            "type": PACKET_REGISTER if is_register else PACKET_AUTH,
            "username": username,
            "password": password
        }
        await client.send_message(auth_packet)
        response = await client.receive_message()
        if response.get("type") in [PACKET_AUTH_SUCCESS, PACKET_REGISTER_SUCCESS]:
            await display_message(f"Authentication successful. Welcome {username}!", is_system=True)
            return True
        else:
            await display_message("Authentication failed. Please try again.", is_system=True)

async def main():
    client = GameClient(IP, PORT, DATA_PAYLOAD_SIZE)
    await client.connect()

    if not client.writer:
        logger.error("Failed to connect to server. Exiting.")
        return
    
    auth_success = await authenticate(client)
    if not auth_success:
        logger.info("Authentication failed or cancelled. Exiting.")
        client.close()
        return
    
    logger.info("Starting game interaction loops...")
    
    input_task = asyncio.create_task(handle_user_input(client))
    message_task = asyncio.create_task(handle_server_messages(client))
    
    try:
        await asyncio.gather(input_task, message_task)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        if not input_task.done():
            input_task.cancel()
        if not message_task.done():
            message_task.cancel()
        client.close()
        
    logger.info("Client shutdown complete.")
    


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client interrupted and shutting down.")
        sys.exit(0)
