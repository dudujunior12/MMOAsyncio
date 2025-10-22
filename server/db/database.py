import asyncpg
from shared.constants import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from shared.logger import get_logger

logger = get_logger(__name__)

db_pool = None

async def init_db_pool():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
            min_size=1,
            max_size=20
        )
        logger.info("Database connection pool created successfully.")
        await create_user_table()
        return db_pool
    except Exception as e:
        logger.error(f"Error creating database connection pool: {e}")
        db_pool = None
        await close_db_pool()
        return None

async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed.")
        db_pool = None

async def create_user_table():
    global db_pool
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    async with db_pool.acquire() as connection:
        try:
            await connection.execute(create_table_query)
            logger.info("User table ensured in database.")
        except Exception as e:
            logger.error(f"Error creating user table: {e}")
