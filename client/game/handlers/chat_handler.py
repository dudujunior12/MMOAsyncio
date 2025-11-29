from shared.protocol import (
    PACKET_CHAT_MESSAGE,
    PACKET_SYSTEM_MESSAGE,
)

from .base_handler import BaseHandler

from shared.logger import get_logger
logger = get_logger(__name__)

class ChatHandler(BaseHandler):

    async def handle(self, packet):
        if packet["type"] == PACKET_CHAT_MESSAGE:
            sender = packet.get("sender", "???")
            content = packet.get("content", "")
            logger.info(f"[CHAT] {sender}: {content}")
            self.client.renderer.chat_ui.add_message(sender, content)

        elif packet["type"] == PACKET_SYSTEM_MESSAGE:
            logger.info(f"[SYSTEM] {packet['content']}")
            self.client.renderer.chat_ui.add_message("System", packet["content"])
