import asyncio
from server.db.database import init_db_pool
from shared import logger
from shared.constants import IP, PORT, DATA_PAYLOAD_SIZE
from server.network.server import ServerSocket

async def main():
     db_pool = await init_db_pool()
     
     server = ServerSocket(IP, PORT, DATA_PAYLOAD_SIZE, db_pool)
     try:
          await server.start()
     except KeyboardInterrupt:
          logger.info("Server stopped by user...")
          await server.shutdown()
     except Exception as e:
         logger.error(f"Error starting server: {e}")
     finally:
           await server.shutdown()
           await db_pool.close()
         
def sync_main():
    asyncio.run(main())

if __name__ == "__main__":
    sync_main()