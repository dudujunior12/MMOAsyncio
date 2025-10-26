from client.network.client import GameClient
from client.input.login_input import get_auth_choice, get_credentials, display_message, prompt_for_game_action
from shared.protocol import (
    PACKET_AUTH,
    PACKET_AUTH_SUCCESS,
    PACKET_CHAT_MESSAGE,
    PACKET_ENTITY_NEW,
    PACKET_ENTITY_REMOVE,
    PACKET_REGISTER,
    PACKET_REGISTER_SUCCESS,
    PACKET_SYSTEM_MESSAGE,
    PACKET_POSITION_UPDATE,
    PACKET_WORLD_STATE,
)
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE, GAME_TICK_RATE, TICK_INTERVAL
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
                        user = message.get("asset_type")
                        await display_message(f"Entity {entity_id} ({user}) moved to ({x}, {y}).", is_system=True)
                        client.world_state.update_entity(message)
                    # elif pkt_type == PACKET_WORLD_STATE:
                    #     entities_data = message.get("entities", [])
                    #     for entity_data in entities_data:
                    #         client.world_state.update_entity(entity_data)
                    
                    elif pkt_type == PACKET_ENTITY_NEW:
                        client.world_state.update_entity(message)
                        entity_id = message.get("entity_id")
                        asset_type = message.get("asset_type")
                        x = message.get("x")
                        y = message.get("y")
                        await display_message(f"[SYSTEM] Teste New Entity {entity_id} ({asset_type}) joined at ({x}, {y}).", is_system=True)
                        
                    elif pkt_type == PACKET_ENTITY_REMOVE:
                        entity_id = message.get("entity_id")
                        asset_type = message.get('asset_type')
                        client.world_state.remove_entity(entity_id)
                        asset_to_display = asset_type if asset_type else f"Entity {entity_id}"
                        # remove player from world render
                        #await display_message(f"{asset_to_display} has left the world.", is_system=True)
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
    
    input_task = asyncio.create_task(handle_user_input(client))
    message_task = asyncio.create_task(handle_server_messages(client))
    
    try:
        done, pending = await asyncio.wait(
            [input_task, message_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    
    finally:
        if not client.writer.is_closing():
            client.close()
        
    logger.info("Client shutdown complete.")
    sys.exit(0)
    


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client interrupted and shutting down.")
        sys.exit(0)
