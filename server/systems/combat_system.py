# server/systems/combat_system.py

from server.game_engine.components.health import HealthComponent
from server.game_engine.components.stats import StatsComponent
from server.game_engine.components.position import PositionComponent
from server.game_engine.components.type import TypeComponent
from server.game_engine.components.network import NetworkComponent
from server.systems.movement_system import calculate_distance
from shared.logger import get_logger
from shared.protocol import (
    PACKET_HEALTH_UPDATE,
    PACKET_ENTITY_NEW,
    PACKET_POSITION_UPDATE,
    PACKET_ENTITY_REMOVE,
    PACKET_SYSTEM_MESSAGE
)

logger = get_logger(__name__)

class CombatSystem:
    def __init__(self, world, network_manager, send_aoi_update_func, send_system_message_func):
        self.world = world
        self.network_manager = network_manager
        self.send_aoi_update = send_aoi_update_func
        self.send_system_message = send_system_message_func
        self.AOI_RANGE = 25.0
        self.ATTACK_RANGE = 2.0

    async def handle_damage_request(self, source_entity_id: int, target_entity_id: int):
        """
        Ponto de entrada do sistema de combate, chamado pelo GameEngine ao receber um PACKET_DAMAGE.
        """
        source_pos = self.world.get_component(source_entity_id, PositionComponent)
        target_pos = self.world.get_component(target_entity_id, PositionComponent)
        
        source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
        source_user = source_network_comp.username if source_network_comp else f"Entity {source_entity_id}"
        
        if not source_pos or not target_pos:
            await self.send_system_message(source_entity_id, "Server error: Target or self position not found.")
            return
        
        if source_entity_id == target_entity_id:
            source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
            if source_network_comp:
                await self.network_manager.send_packet(source_network_comp.writer, {
                    "type": PACKET_SYSTEM_MESSAGE,
                    "content": "You cannot attack yourself."
            })
            return

        distance = calculate_distance(source_pos, target_pos)
        
        if distance > self.ATTACK_RANGE:
            await self.send_system_message(source_entity_id, "Target is too far to attack.")
            return
        
        damage_amount = self._calculate_final_damage(source_entity_id, target_entity_id)
        
        is_dead = await self._apply_damage(target_entity_id, damage_amount, source_entity_id)

        if not is_dead:
            logger.info(f"Combat: {source_user} (Entity {source_entity_id}) attacked Entity {target_entity_id} for {damage_amount} damage.")


    def _calculate_final_damage(self, source_id: int, target_id: int) -> int:
        """Calcula o dano final usando atributos totais (base + bônus da classe)."""

        source_stats: StatsComponent = self.world.get_component(source_id, StatsComponent)
        target_stats: StatsComponent = self.world.get_component(target_id, StatsComponent)

        if not source_stats or not target_stats:
            return 1

        # --- ATAQUE (correta: usa total_strength) ---
        raw_attack = source_stats.get_attack_power()

        # --- DEFESA correta usando total_vitality ---
        BASE_DEFENSE = 5
        DEFENSE_PER_VIT = 1

        total_defense = BASE_DEFENSE + (target_stats.total_vitality * DEFENSE_PER_VIT)

        # --- DANO FINAL ---
        final_damage = raw_attack - total_defense

        return max(1, final_damage)


    async def _apply_damage(self, target_entity_id: int, damage_amount: int, source_entity_id: int = None):
        """Aplica o dano à entidade e broadcasta a atualização de HP."""
        health_comp = self.world.get_component(target_entity_id, HealthComponent)
        
        if not health_comp or health_comp.is_dead:
            return False

        damage_dealt = health_comp.take_damage(damage_amount)
        
        logger.info(f"Entity {target_entity_id} took {damage_dealt} damage. HP: {health_comp.current_health}/{health_comp.max_health}")
        
        await self._broadcast_health_update(target_entity_id, health_comp)
        
        # Obter nomes para as mensagens do sistema
        source_user = "Unknown"
        if source_entity_id:
            source_network_comp = self.world.get_component(source_entity_id, NetworkComponent)
            if source_network_comp:
                source_user = source_network_comp.username

        target_network_comp = self.world.get_component(target_entity_id, NetworkComponent)
        target_user = target_network_comp.username if target_network_comp else f"Entity {target_entity_id}"

        if source_entity_id:
            await self.send_system_message(source_entity_id, f"You dealt {damage_dealt} of damage to {target_user}.")

        await self.send_system_message(target_entity_id, f"You received {damage_dealt} of damage from {source_user}. Health left: {health_comp.current_health}/{health_comp.max_health}")


        if health_comp.is_dead:
            logger.info(f"Entity {target_entity_id} has died.")
            
            await self.network_manager.broadcast_system_message(f"{target_user} has been defeated!", exclude_writer=None)
            
            RESPAWN_X = 10.0 
            RESPAWN_Y = 10.0 
            
            await self._handle_entity_death(target_entity_id, target_user, RESPAWN_X, RESPAWN_Y, source_id=source_entity_id)
            
            return True
            
        return False
        
    async def _broadcast_health_update(self, entity_id: int, health_comp: HealthComponent):
        """Envia o pacote de atualização de HP para a entidade e sua AOI."""
        health_update_packet = {
            "type": PACKET_HEALTH_UPDATE,
            "entity_id": entity_id,
            "current_health": health_comp.current_health,
            "max_health": health_comp.max_health
        }
        
        target_network_comp = self.world.get_component(entity_id, NetworkComponent)
        target_writer = target_network_comp.writer if target_network_comp else None
        
        if target_writer:
            await self.network_manager.send_packet(target_writer, health_update_packet)

        # Usando a callback para notificar a AOI (Area of Interest)
        await self.send_aoi_update(entity_id, health_update_packet, exclude_writer=target_writer)
            
    async def _handle_entity_death(self, entity_id: int, target_name: str, initial_x: float = 10.0, initial_y: float = 10.0, source_id: int = None):
        """Lida com as ações de morte, como respawn do jogador ou remoção de NPC."""
        
        type_comp = self.world.get_component(entity_id, TypeComponent)
        entity_type = type_comp.entity_type if type_comp else "unknown"

        if entity_type == 'player':
            # Lógica de Respawn do Jogador
            pos_comp = self.world.get_component(entity_id, PositionComponent)
            health_comp = self.world.get_component(entity_id, HealthComponent)
            
            if pos_comp and health_comp:
                pos_comp.x = initial_x
                pos_comp.y = initial_y
                
                health_comp.heal_to_full() 
                
                await self.send_system_message(entity_id, "You have been defeated! Returning to spawn.")
                
                # Sincroniza nova posição
                respawn_pos_packet = {
                    "type": PACKET_POSITION_UPDATE,
                    "entity_id": entity_id,
                    "x": pos_comp.x,
                    "y": pos_comp.y,
                    "asset_type": target_name # (Nome do Player)
                }
                await self.send_aoi_update(entity_id, respawn_pos_packet, exclude_writer=None) 
                
                # Sincroniza HP cheio
                await self._broadcast_health_update(entity_id, health_comp)
            else:
                logger.error(f"Cannot respawn Player {entity_id}: Missing Position or Health Component.")
                
        elif entity_type == 'monster':
            
            logger.info(f"Monster {target_name} (Entity {entity_id}) died. Removing entity.")
            
            # TODO: Adicionar lógica de EXP para o source_id (jogador que matou)
            # TODO: Adicionar lógica de Drop de Itens
            
            # 1. Enviar pacote de remoção para a AOI
            remove_packet = {
                "type": PACKET_ENTITY_REMOVE,
                "entity_id": entity_id,
                "asset_type": target_name
            }
            await self.send_aoi_update(entity_id, remove_packet) 

            # 2. Remover do World
            self.world.remove_entity(entity_id)
            
            # TODO: Adicionar temporizador de respawn (WorldInitializer ou RespawnSystem faria isso)
            
        else:
            logger.warning(f"Entity {entity_id} died but its type ({entity_type}) is unknown. Ignoring death logic.")