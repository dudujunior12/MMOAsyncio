from server.game_engine.components.ai import AIComponent
from server.game_engine.world import World
from server.game_engine.components.type import TypeComponent
from server.game_engine.components.position import PositionComponent
from server.systems.movement_system import MovementSystem
from shared.logger import get_logger
from shared.protocol import PACKET_POSITION_UPDATE

import random
import asyncio

logger = get_logger(__name__)

class AISystem:
    def __init__(self, world: World, movement_system: MovementSystem, send_aoi_update_func):
        self.world = world
        self.movement_system = movement_system
        self.send_aoi_update = send_aoi_update_func # Necessário para o broadcast de posição
        self.NPC_MOVEMENT_SPEED = 0.5 # Velocidade base de movimento por tick (unidades por segundo)
        self.WANDER_RADIUS = 5.0      # Raio de patrulha para NPCs

    async def run(self):
        target_components = (TypeComponent, PositionComponent, AIComponent)
        
        for entity_id, components_list in self.world.get_entities_with_components(target_components):
            type_comp, pos_comp, ai_comp = components_list
            
            if type_comp.entity_type == 'monster':
                await self._process_monster_ai(entity_id, pos_comp, ai_comp)
            # Adicione 'npc' ou outros tipos de entidades aqui
            
    async def _process_monster_ai(self, entity_id: int, pos_comp: PositionComponent, ai_comp: AIComponent):
        
        # Lógica baseada no estado da IA
        if ai_comp.state == 'wandering':
            
            if random.random() < 0.1: # 10% de chance de tentar mover
                
                # ... (Sua lógica de cálculo delta_x/delta_y existente)
                delta_x = random.uniform(-self.NPC_MOVEMENT_SPEED, self.NPC_MOVEMENT_SPEED)
                delta_y = random.uniform(-self.NPC_MOVEMENT_SPEED, self.NPC_MOVEMENT_SPEED)
                
                new_x = pos_comp.x + delta_x
                new_y = pos_comp.y + delta_y
                
                await self.movement_system.handle_npc_move(entity_id, new_x, new_y)
                
        elif ai_comp.state == 'idle':
            # Não faz nada
            pass
            
        elif ai_comp.state == 'chasing':
            # Futura lógica de perseguição de ai_comp.target_entity_id
            pass