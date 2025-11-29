from shared.logger import get_logger

logger = get_logger(__name__)

class WorldStateHandler:
    def __init__(self, client):
        self.client = client

    async def handle(self, packet):
        entities = packet.get("entities", [])

        for ent in entities:
            self.client.world_state.update_entity(ent)
