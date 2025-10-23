import asyncio
from shared.logger import get_logger
from server.core.application import Application

logger = get_logger(__name__)

async def main():
    app = Application()
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C)...")
    except Exception as e:
        logger.error(f"Fatal error during application runtime: {e}")
    finally:
        # Garante que o shutdown seja chamado em qualquer caso de interrupção ou erro.
        await app.shutdown()
          
def sync_main():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Se Ctrl+C for pressionado antes do asyncio.run() iniciar, ele é capturado aqui
        pass

if __name__ == "__main__":
    sync_main()
