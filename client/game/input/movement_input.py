import pygame
import math # Importar math
from shared.protocol import PACKET_MOVE
from shared.constants import PLAYER_MOVE_SPEED, TICK_INTERVAL
# Estado atual das teclas de movimento
movement_state = {
    "up": False,
    "down": False,
    "left": False,
    "right": False
}

def handle_key_event(event):
    # (Seu código de manipulação de teclas - K_w, K_s, K_a, K_d - permanece igual)
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_w:
            movement_state["up"] = True
        if event.key == pygame.K_s:
            movement_state["down"] = True
        if event.key == pygame.K_a:
            movement_state["left"] = True
        if event.key == pygame.K_d:
            movement_state["right"] = True

    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_w:
            movement_state["up"] = False
        if event.key == pygame.K_s:
            movement_state["down"] = False
        if event.key == pygame.K_a:
            movement_state["left"] = False
        if event.key == pygame.K_d:
            movement_state["right"] = False

def get_movement_packet(player_data: dict):
    """Retorna um pacote de movimento se houver movimento ativo, normalizado pela velocidade."""
    
    client_move_speed = player_data.get('movement_speed')
    if client_move_speed is None:
        client_move_speed = PLAYER_MOVE_SPEED
        
    MAX_DISPLACEMENT_PER_TICK = client_move_speed * TICK_INTERVAL
    
    dx = dy = 0
    # O valor 1.0 aqui representa a intenção de movimento (direção), não a velocidade final.
    if movement_state["up"]:
        dy -= 1.0
    if movement_state["down"]:
        dy += 1.0
    if movement_state["left"]:
        dx -= 1.0
    if movement_state["right"]:
        dx += 1.0

    if dx == 0 and dy == 0:
        return None
    
    distance_raw = math.sqrt(dx**2 + dy**2)

    scale_factor = MAX_DISPLACEMENT_PER_TICK / distance_raw
    dx_final = dx * scale_factor
    dy_final = dy * scale_factor


    return {
        "type": PACKET_MOVE,
        "dx": dx_final,
        "dy": dy_final
    }