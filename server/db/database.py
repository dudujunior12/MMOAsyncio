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
    # ... (Verificação do pool) ...
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        pos_x REAL DEFAULT 10.0,
        pos_y REAL DEFAULT 10.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        -- Novos campos serão adicionados via ALTER TABLE para idempotência
    );
    """
    async with db_pool.acquire() as connection:
        try:
            await connection.execute(create_table_query)
            
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS experience INTEGER DEFAULT 0;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS current_health INTEGER DEFAULT NULL;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS strength INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS agility INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vitality INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS intelligence INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS dexterity INTEGER DEFAULT 1;")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS luck INTEGER DEFAULT 1;")
            
            logger.info("User table and player stats ensured in database.")
        except Exception as e:
            logger.error(f"Error creating user table or stats columns: {e}")
