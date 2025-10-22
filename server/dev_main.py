from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE
from server.network.server import ServerSocket
import hupper
from server.main import main
import asyncio

if __name__ == "__main__":
    reloader = hupper.start_reloader("server.main.sync_main")