import asyncio
import pygame
import sys

from shared.logger import get_logger
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH, TICK_INTERVAL

from client.network.client import GameClient
from client.game.engine.client_engine import ClientEngine
from client.game.render.renderer import GameRenderer
from client.game.input.movement_input import get_movement_packet, handle_key_event

from client.game.ui.login_ui import LoginUI
from shared.protocol import PACKET_AUTH, PACKET_REGISTER

logger = get_logger(__name__)

async def show_login_screen(client):
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("MMO - Login")
    clock = pygame.time.Clock()

    login_ui = LoginUI(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # frame delta
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            result = login_ui.handle_event(event)
            if result == "submit":
                return login_ui.username, login_ui.password

        login_ui.draw()
        pygame.display.flip()
        await asyncio.sleep(0)  # deixa o asyncio rodar


async def network_loop(client_engine):
    while True:
        packet = await client_engine.client.receive_message()
        if packet is None:
            logger.info("Network loop ending: connection closed.")
            break
        await client_engine.process_packet(packet)


async def game_loop(client, client_engine, renderer):
    running = True
    accumulator = 0.0

    while running and not client.is_closed:
        dt = renderer.clock.tick(60) / 1000.0
        renderer.dt = dt
        accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("[DEBUG] Exiting game loop...")
                running = False
            handle_key_event(event)

        while accumulator >= TICK_INTERVAL:
            move_packet = get_movement_packet()
            if move_packet:
                await client.send_message(move_packet)
            accumulator -= TICK_INTERVAL

        renderer.draw()
        await asyncio.sleep(0)

    pygame.quit()
    client.close()
    sys.exit(0)

async def main():
    logger.info("[DEBUG] Starting client...")
    
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MMO")

    client = GameClient(IP, PORT, DATA_PAYLOAD_SIZE)
    await client.connect()
    
    if not client.writer:
        logger.error("Failed to connect to server.")
        return
    
    client_engine = ClientEngine(client)

    username, password = await show_login_screen(screen)
    client.username = username

    packet = {
        "type": PACKET_AUTH,
        "username": username,
        "password": password
    }
    await client.send_message(packet)

    response = await client.receive_message()
    if response.get("type") != "AUTH_SUCCESS":
        logger.error("Authentication failed")
        return

    logger.info(f"Welcome {username}!")

    asyncio.create_task(network_loop(client_engine))
    
    renderer = GameRenderer(client.world_state, screen, None)
    client.renderer = renderer
    await game_loop(client, client_engine, renderer)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
