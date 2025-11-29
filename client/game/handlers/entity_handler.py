from shared.protocol import (
    PACKET_ENTITY_NEW,
    PACKET_ENTITY_UPDATE,
    PACKET_ENTITY_REMOVE,
)

from .base_handler import BaseHandler

class EntityHandler(BaseHandler):
    def __init__(self, client):
        self.client = client

    async def handle(self, packet):
        ptype = packet["type"]

        if ptype in (PACKET_ENTITY_NEW, PACKET_ENTITY_UPDATE):
            self.client.world_state.update_entity(packet)

            if ptype == PACKET_ENTITY_NEW and packet.get("asset_type") == self.client.username:
                self.client.world_state.set_local_player(packet["entity_id"])
                print(f"[CLIENT] Local player ID set to {packet['entity_id']}")
                if hasattr(self.client, "renderer"):
                    self.client.renderer.player_entity_id = packet["entity_id"]

        elif ptype == PACKET_ENTITY_REMOVE:
            entity_id = packet["entity_id"]
            self.client.world_state.remove_entity(entity_id)
            print(f"[CLIENT] Entity {entity_id} removed.")
