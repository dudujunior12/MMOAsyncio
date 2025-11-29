from shared.protocol import PACKET_MAP_DATA
from .base_handler import BaseHandler
from shared.logger import get_logger

logger = get_logger(__name__)

class SystemHandler(BaseHandler):

    async def handle(self, packet):
        if packet["type"] == PACKET_MAP_DATA:
            self.client.world_state.set_map(packet)
            logger.info(f"[CLIENT] Loaded map: {packet['map_name']}")