from shared.protocol import PACKET_HEALTH_UPDATE
from .base_handler import BaseHandler

class HealthHandler:
    def __init__(self, client):
        self.client = client

    async def handle(self, packet):
        self.client.world_state.update_entity(packet)