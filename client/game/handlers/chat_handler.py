from shared.protocol import (
    PACKET_CHAT_MESSAGE,
    PACKET_SYSTEM_MESSAGE,
)

from .base_handler import BaseHandler

class ChatHandler(BaseHandler):

    async def handle(self, packet):
        if packet["type"] == PACKET_CHAT_MESSAGE:
            print(packet["content"])

        elif packet["type"] == PACKET_SYSTEM_MESSAGE:
            print(f"[SYSTEM] {packet['content']}")
