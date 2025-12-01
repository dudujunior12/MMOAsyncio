# client/game/systems/client_input_system.py

import pygame
import math
from shared.constants import ATTACK_RANGE, SPRITE_SIZE
from shared.logger import get_logger
from shared.protocol import PACKET_DAMAGE

logger = get_logger(__name__)

# A função de utilidade de distância pode ser definida aqui, ou em um shared/utils.py
# Por simplicidade, vamos mantê-la aqui por enquanto, já que ela estava no arquivo original.
def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calcula a distância euclidiana entre dois pontos."""
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)

class ClientInputSystem:
    def __init__(self, world, camera, player_entity_id):
        self.world = world
        self.camera = camera
        self.player_entity_id = player_entity_id
        
    async def handle_mouse_attack_click(self, mouse_pos: tuple, client):
        """
        Converte a posição da tela para a posição do mundo e verifica colisões com entidades.
        Se acertar e estiver no alcance, envia o pacote de ataque.
        (Módulo movido do antigo GameRenderer.handle_click_attack)
        """
        
        # 1. Obter dados do jogador local
        player_data = self.world.get_local_player()
        if not player_data:
            logger.warning("Local player data not available for attack.")
            return

        # É bom usar a posição VISUAL (interpolada) do jogador para o clique inicial,
        # mas a posição REAL (server x, y) do alvo para o cálculo da distância, 
        # para evitar trapaças/problemas de latência.
        player_x = player_data["x_visual"]
        player_y = player_data["y_visual"]
        
        # 2. Converte a posição do mouse na tela para a coordenada do mundo (GRID)
        world_x_px = mouse_pos[0] + self.camera.x 
        world_y_px = mouse_pos[1] + self.camera.y

        world_x_grid = world_x_px / SPRITE_SIZE
        world_y_grid = world_y_px / SPRITE_SIZE
        
        # 3. Verifica se alguma entidade foi clicada
        target_entity_id = None
        for ent in self.world.get_all_entities():
            # Não pode atacar a si mesmo
            if ent["id"] == player_data["id"]:
                continue
            
            # Usamos a posição VISUAL (interpolada) da entidade para a verificação de clique na tela
            ent_x = ent.get("x_visual", ent["x"])
            ent_y = ent.get("y_visual", ent["y"])
            
            # Verifica se o clique está dentro do tile da entidade
            if abs(ent_x - world_x_grid) < 0.5 and abs(ent_y - world_y_grid) < 0.5:
                target_entity_id = ent["id"]
                break
        
        if target_entity_id is not None:
            # 4. Verifica o Alcance de Ataque usando a posição REAL do alvo (target_data["x"], target_data["y"])
            target_data = self.world.get_entity_data(target_entity_id)
            if target_data is None:
                return

            distance = calculate_distance(player_x, player_y, target_data["x"], target_data["y"])
            
            if distance <= ATTACK_RANGE:
                logger.info(f"Targeting Entity {target_entity_id}. Distance: {distance:.2f}. Attacking!")
                
                # 5. Envia o Pacote de Dano para o Servidor
                damage_packet = {
                    "type": PACKET_DAMAGE,
                    "target_entity_id": target_entity_id
                }
                await client.send_message(damage_packet)
                
            else:
                # Opcional: Feedback ao jogador
                print(f"Target {target_entity_id} is too far! Distance: {distance:.2f}")