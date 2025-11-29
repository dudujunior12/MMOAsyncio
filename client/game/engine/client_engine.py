from client.game.handlers.chat_handler import ChatHandler
from client.game.handlers.damage_handler import DamageHandler
from client.game.handlers.entity_handler import EntityHandler
from client.game.handlers.evolve_handler import EvolveHandler
from client.game.handlers.health_handler import HealthHandler
from client.game.handlers.movement_handler import MovementHandler
from client.game.handlers.system_handler import SystemHandler
from client.game.handlers.world_state_handler import WorldStateHandler
from client.game.systems.chat_system import ChatSystem
from shared.protocol import decode_message
from shared.protocol import (PACKET_POSITION_UPDATE, PACKET_AUTH_SUCCESS, PACKET_REGISTER, PACKET_AUTH, 
                             PACKET_REGISTER_SUCCESS, PACKET_REGISTER_FAIL, PACKET_AUTH_FAIL, PACKET_CHAT_MESSAGE, PACKET_SYSTEM_MESSAGE, 
                             PACKET_ENTITY_NEW, PACKET_ENTITY_UPDATE, PACKET_ENTITY_REMOVE, PACKET_WORLD_STATE, PACKET_MAP_DATA, 
                             PACKET_HEALTH_UPDATE, PACKET_DAMAGE, PACKET_EVOLVE, PACKET_MOVE, PACKET_ITEM_USE)
from shared.logger import get_logger
logger = get_logger(__name__)

class ClientEngine:
    def __init__(self, client):
        self.client = client

        self.handlers = {
            PACKET_ENTITY_NEW: EntityHandler(client),
            PACKET_ENTITY_UPDATE: EntityHandler(client),
            PACKET_ENTITY_REMOVE: EntityHandler(client),
            PACKET_POSITION_UPDATE: MovementHandler(client),
            PACKET_HEALTH_UPDATE: HealthHandler(client),
            PACKET_DAMAGE: DamageHandler(client),
            PACKET_EVOLVE: EvolveHandler(client),
            PACKET_CHAT_MESSAGE: ChatHandler(client),
            PACKET_SYSTEM_MESSAGE: ChatHandler(client),
            PACKET_MAP_DATA: SystemHandler(client),
            PACKET_WORLD_STATE: WorldStateHandler(client),
        }

    async def process_packet(self, packet):
        ptype = packet.get("type")
        handler = self.handlers.get(ptype)
        if handler:
            await handler.handle(packet)
        else:
            logger.warning(f"Unknown packet type: {ptype}")

    async def process_incoming_packets(self):
        while True:
            raw = await self.client.reader.readuntil(b"\n")
            packet = decode_message(raw)

            handler = self.handlers.get(packet["type"])
            if handler:
                await handler.handle(packet)
            else:
                logger.warning(f"Unknown packet type: {packet['type']}")
