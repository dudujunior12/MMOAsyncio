from shared.logger import get_logger

logger = get_logger(__name__)

class EvolveHandler:
    def __init__(self, client):
        self.client = client

    async def handle(self, packet):
        self.client.world_state.update_entity(packet)

