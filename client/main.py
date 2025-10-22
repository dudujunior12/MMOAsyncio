from client.network.client import GameClient
from client.input.login_input import get_auth_choice, get_credentials, display_message
from shared.protocol import (
    PACKET_AUTH,
    PACKET_AUTH_SUCCESS,
    PACKET_CHAT_MESSAGE,
    PACKET_REGISTER,
    PACKET_REGISTER_SUCCESS,
    PACKET_SYSTEM_MESSAGE
)
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE
import asyncio
from shared.logger import get_logger

logger = get_logger(__name__)

async def main():
    client = GameClient(IP, PORT, DATA_PAYLOAD_SIZE)
    await client.connect()

    while True:
        choice = await get_auth_choice()
        if choice is None:
            return

        is_register = choice == 'R'
        creds = await get_credentials(is_register)
        if creds is None:
            return
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
            break

    asyncio.create_task(receive_loop(client))

    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
        if msg.lower() in ["quit", "exit"]:
            client.close()
            return
        chat_packet = {
            "type": PACKET_CHAT_MESSAGE,
            "content": msg
        }
        await client.send_message(chat_packet)


async def receive_loop(client):
    while True:
        packet = await client.receive_message()
        if packet is None:
            continue
        content = packet.get("content")
        if packet.get("type") == PACKET_CHAT_MESSAGE and content:
            print(f"\n[CHAT] {content}\n> ", end='', flush=True)
        elif packet.get("type") == PACKET_SYSTEM_MESSAGE and content:
            print(f"\n[SYSTEM] {content}\n> ", end='', flush=True)
        else:
            print(f"\n[UNKNOWN] {content}\n> ", end='', flush=True)


if __name__ == "__main__":
    asyncio.run(main())
