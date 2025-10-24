from shared.logger import get_logger

logger = get_logger(__name__)

async def update_player_position(db_pool, username: str, x: float, y: float):
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return
    
    query = """
    UPDATE users SET pos_x = $1, pos_y = $2
    WHERE username = $3;
    """
    async with db_pool.acquire() as connection:
        await connection.execute(query, x, y, username)

async def get_player_data(db_pool, username: str):
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return None

    query = """
    SELECT pos_x, pos_y
    FROM users
    WHERE username = $1;
    """
    async with db_pool.acquire() as connection:
        record = await connection.fetchrow(query, username)
        if record:
            return {
                'pos_x': record['pos_x'],
                'pos_y': record['pos_y'],
            }
        return None