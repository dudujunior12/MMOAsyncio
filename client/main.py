import asyncio
import pygame
import sys

from client.game.systems.chat_system import ChatSystem
from client.game.ui.register_ui import RegisterUI
from shared.logger import get_logger
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH, TICK_INTERVAL

from client.network.client import GameClient
from client.game.engine.client_engine import ClientEngine
from client.game.render.renderer import GameRenderer
from client.game.input.movement_input import get_movement_packet, handle_key_event

from client.game.ui.login_ui import LoginUI
from shared.protocol import PACKET_AUTH, PACKET_REGISTER

logger = get_logger(__name__)

async def show_auth_screen(screen): # Renomear para refletir Login/Register
    pygame.display.set_caption("MMO - Login/Register")
    clock = pygame.time.Clock()

    # Inicializa as duas UIs
    login_ui = LoginUI(screen)
    register_ui = RegisterUI(screen)
    
    current_ui = login_ui
    auth_type = "login"

    running = True
    while running:
        dt = clock.tick(60) / 1000.0 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            result = current_ui.handle_event(event)
            
            if result == "submit":
                if auth_type == "login":
                    return current_ui.username, current_ui.password, PACKET_AUTH
                else:
                    # Verifica se as senhas coincidem antes de retornar
                    if current_ui.password != current_ui.confirm_password:
                        current_ui.message = "Passwords do not match!"
                    else:
                        return current_ui.username, current_ui.password, PACKET_REGISTER

            # Lógica de alternância de tela
            elif result == "switch_to_register":
                current_ui = register_ui
                auth_type = "register"
                current_ui.message = "" # Limpa mensagem
                pygame.display.set_caption("MMO - Register")
            
            elif result == "switch_to_login":
                current_ui = login_ui
                auth_type = "login"
                current_ui.message = "" # Limpa mensagem
                pygame.display.set_caption("MMO - Login")
                

        current_ui.draw()
        pygame.display.flip()
        await asyncio.sleep(0)


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

    chat_system = ChatSystem(client, renderer.chat_ui, client.username)

    while running and not client.is_closed:
        dt = renderer.clock.tick(60) / 1000.0
        renderer.dt = dt
        accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("[DEBUG] Exiting game loop...")
                running = False
                break

            chat_result = renderer.chat_ui.handle_event(event)
            if chat_result is not None:
                if chat_result != "":
                    await chat_system.send_message(chat_result)
                continue

            if not renderer.chat_ui.active:
                handle_key_event(event)

        if not renderer.chat_ui.active:
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
    
    

    username, password, auth_type = await show_auth_screen(screen)
    client.username = username

    packet = {
        "type": auth_type,
        "username": username,
        "password": password
    }
    await client.send_message(packet)

    response = await client.receive_message()
    logger.info(f"Authentication response: {response}")
    if response.get("status") != "success":
        logger.error("Authentication failed")
        return

    logger.info(f"Welcome {username}!")

    client_engine = ClientEngine(client)
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
