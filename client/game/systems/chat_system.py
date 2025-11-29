from shared.protocol import (
    PACKET_CHAT_MESSAGE,
    PACKET_SYSTEM_MESSAGE,
)

class ChatSystem:
    def __init__(self, client, chat_ui, username):
        self.client = client
        self.chat_ui = chat_ui
        self.username = username

    async def send_message(self, message):
        if message.startswith("/"):
            await self.handle_command(message)
            return

        packet = {
            "type": PACKET_CHAT_MESSAGE,
            "sender": self.username,
            "content": message
        }
        await self.client.send_message(packet)

    async def handle_command(self, message: str):
        parts = message.split()
        cmd = parts[0].lower()

        if cmd == "/evolve":
            target = parts[1] if len(parts) > 1 else ""
            await self.client.send_message({
                "type": PACKET_CHAT_MESSAGE,
                "sender": self.username,
                "content": f"/evolve {target}"
            })
            return

        if cmd == "/add":
            stat = parts[1] if len(parts) > 1 else None
            if stat:
                await self.client.send_message({
                    "type": PACKET_CHAT_MESSAGE,
                    "sender": self.username,
                    "content": f"/add {stat}"
                })
            else:
                self.chat_ui.add_message("System", "Use: /add <str|agi|int>")
            return

        self.chat_ui.add_message("System", f"Unknown command: {cmd}")

    def receive_message(self, sender, text):
        self.chat_ui.add_message(sender, text)
