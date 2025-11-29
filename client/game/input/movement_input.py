import pygame
from shared.protocol import PACKET_MOVE

# Estado atual das teclas de movimento
movement_state = {
    "up": False,
    "down": False,
    "left": False,
    "right": False
}

# Velocidade por pacote
SPEED = 1

def handle_key_event(event):
    """Atualiza o estado das teclas ao pressionar ou soltar."""
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

def get_movement_packet():
    """Retorna um pacote de movimento se houver movimento ativo."""
    dx = dy = 0
    if movement_state["up"]:
        dy -= SPEED
    if movement_state["down"]:
        dy += SPEED
    if movement_state["left"]:
        dx -= SPEED
    if movement_state["right"]:
        dx += SPEED

    if dx == 0 and dy == 0:
        return None

    return {
        "type": PACKET_MOVE,
        "dx": dx,
        "dy": dy
    }
