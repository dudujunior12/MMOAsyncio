import asyncpg
from shared.constants import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from shared.logger import get_logger
from server.db.data_loader import load_monster_data
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
        await create_monster_tables()
        await load_monster_data(db_pool)
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
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        class_name TEXT DEFAULT 'Warrior', 
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
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
            
            
async def create_monster_tables():
    global db_pool
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return
        
    async with db_pool.acquire() as connection:
        try:
            # Tabela 1: monster_templates (Armazena os stats e o asset_type)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS monster_templates (
                    asset_type VARCHAR(50) PRIMARY KEY, -- Ex: 'Green_Slime'
                    level INTEGER NOT NULL,
                    base_health INTEGER NOT NULL,
                    strength INTEGER NOT NULL,
                    vitality INTEGER NOT NULL,
                    type VARCHAR(20) DEFAULT 'monster' NOT NULL
                );
            """)

            # Tabela 2: monster_spawns (Armazena os locais onde o spawn deve ocorrer)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS spawn_zones (
                    id SERIAL PRIMARY KEY,
                    zone_name VARCHAR(100) NOT NULL,
                    monster_asset_type VARCHAR(50) REFERENCES monster_templates(asset_type) ON DELETE CASCADE NOT NULL,
                    map_name VARCHAR(50) NOT NULL,
                    min_x REAL NOT NULL,
                    max_x REAL NOT NULL,
                    min_y REAL NOT NULL,
                    max_y REAL NOT NULL,
                    max_mobs_in_zone INTEGER DEFAULT 1,
                    respawn_time_seconds INTEGER DEFAULT 30,
                    UNIQUE(zone_name, monster_asset_type)
                );
            """)
            logger.info("Monster template and spawn zones tables ensured in database.")
            
            
        except Exception as e:
            logger.error(f"Error creating monster tables: {e}")
