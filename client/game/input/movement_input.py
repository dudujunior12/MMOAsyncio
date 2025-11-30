import pygame
import math # Importar math
from shared.protocol import PACKET_MOVE
from shared.constants import PLAYER_MOVE_SPEED
# Estado atual das teclas de movimento
movement_state = {
    "up": False,
    "down": False,
    "left": False,
    "right": False
}

MAX_CLIENT_SPEED = PLAYER_MOVE_SPEED

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

def get_movement_packet():
    """Retorna um pacote de movimento se houver movimento ativo, normalizado pela velocidade."""
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

    # 1. Calcula a distância (magnitude) bruta do movimento requisitado.
    distance_raw = math.sqrt(dx**2 + dy**2)

    # 2. Normaliza (Redimensiona o vetor)
    if distance_raw > MAX_CLIENT_SPEED:
        # Fator de escala: (Velocidade Desejada / Velocidade Bruta)
        scale_factor = MAX_CLIENT_SPEED / distance_raw
        dx_final = dx * scale_factor
        dy_final = dy * scale_factor
    else:
        # Movimento em linha reta (distance_raw = 1.0), apenas aplica a velocidade máxima.
        # Isso cobre o caso em que distance_raw é 1.0 (ortogonal) e também o caso
        # em que distance_raw é 0.707 (se você usasse um SPEED menor no início).
        # Como dx e dy são 1.0 (ou -1.0) para movimento ortogonal, e queremos que a velocidade
        # final seja MAX_CLIENT_SPEED (0.9), multiplicamos.
        
        # Corrigindo para o caso ortogonal (W, A, S ou D):
        # distance_raw é 1.0. dx=1.0. dy=0.0.
        # dx_final = 1.0 * (0.9 / 1.0) = 0.9
        # dy_final = 0.0 * (0.9 / 1.0) = 0.0
        
        scale_factor = MAX_CLIENT_SPEED / distance_raw
        dx_final = dx * scale_factor
        dy_final = dy * scale_factor


    return {
        "type": PACKET_MOVE,
        "dx": dx_final,
        "dy": dy_final
    }