import asyncio
from server.db.database import init_db_pool
from shared.logger import get_logger

logger = get_logger(__name__)
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE
from server.network.server import ServerSocket

from server.game_engine.engine import GameEngine
        
class Application:
    def __init__(self):
        self.db_pool = None
        self.game_engine = None
        self.server_socket = None
        self.host = IP
        self.port = PORT
        self.data_payload_size = DATA_PAYLOAD_SIZE
        
    async def initialize(self):
        logger.info("Initializing Application...")
        self.db_pool = await init_db_pool()
        self.server_socket = ServerSocket(self.host, self.port, self.data_payload_size, self.db_pool, None)
        self.game_engine = GameEngine(self.db_pool, self.server_socket)
        self.server_socket.game_engine = self.game_engine

        logger.info("Application initialized.")
        
    async def start(self):
        await self.initialize()
        
        server_task = asyncio.create_task(self.server_socket.start())
        engine_task = asyncio.create_task(self.game_engine.start())
        
        await asyncio.gather(server_task, engine_task, return_exceptions=True)
        
    async def shutdown(self):
        logger.info("Shutting down Application...")
        shutdown_tasks = []
        if self.server_socket:
            shutdown_tasks.append(self.server_socket.shutdown())
        if self.game_engine:
            shutdown_tasks.append(self.game_engine.shutdown())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connection pool closed.")
            
        logger.info("Application shutdown complete.")
        