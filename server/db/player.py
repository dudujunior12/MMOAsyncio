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
        
        
async def update_player_data(db_pool, username: str, 
                             x: float, y: float, 
                             current_health: int,
                             level: int, experience: int,
                             strength: int, agility: int, vitality: int, 
                             intelligence: int, dexterity: int, luck: int):
    
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return
    
    query = """
    UPDATE users SET 
        pos_x = $1, 
        pos_y = $2,
        current_health = $3,
        level = $4,
        experience = $5,
        strength = $6,
        agility = $7,
        vitality = $8,
        intelligence = $9,
        dexterity = $10,
        luck = $11
    WHERE username = $12;
    """
    async with db_pool.acquire() as connection:
        await connection.execute(query, 
                                 x, y, 
                                 current_health, 
                                 level, experience, 
                                 strength, agility, vitality, 
                                 intelligence, dexterity, luck, 
                                 username)

async def get_player_data(db_pool, username: str):
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return None

    query = """
    SELECT pos_x, pos_y, 
           level, experience, 
           current_health, 
           strength, agility, vitality, 
           intelligence, dexterity, luck
    FROM users
    WHERE username = $1;
    """
    async with db_pool.acquire() as connection:
        record = await connection.fetchrow(query, username)
        if record:
            return {
                'pos_x': record['pos_x'],
                'pos_y': record['pos_y'],
                'level': record['level'],
                'experience': record['experience'],
                'current_health': record['current_health'],
                'strength': record['strength'],
                'agility': record['agility'],
                'vitality': record['vitality'],
                'intelligence': record['intelligence'],
                'dexterity': record['dexterity'],
                'luck': record['luck'],
            }
        return None