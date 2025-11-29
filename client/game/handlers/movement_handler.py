from shared.protocol import PACKET_POSITION_UPDATE
from .base_handler import BaseHandler

class MovementHandler(BaseHandler):
    def __init__(self, client):
        self.client = client

    async def handle(self, packet):
        if packet["type"] == PACKET_POSITION_UPDATE:
            self.client.world_state.update_entity(packet)
