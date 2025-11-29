class BaseHandler:
    def __init__(self, client):
        self.client = client
        self.world = client.world_state

    async def handle(self, packet):
        raise NotImplementedError