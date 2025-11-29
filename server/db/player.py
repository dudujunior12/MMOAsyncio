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
                             stat_points: int,
                             class_name: str,
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
        class_name = $4,
        level = $5,
        experience = $6,
        strength = $7,
        agility = $8,
        vitality = $9,
        intelligence = $10,
        dexterity = $11,
        luck = $12,
        stat_points = $13
    WHERE username = $14;
    """
    async with db_pool.acquire() as connection:
        await connection.execute(query, 
                                 x, y, 
                                 current_health, 
                                 class_name, 
                                 level, experience, 
                                 strength, agility, vitality, 
                                 intelligence, dexterity, luck, stat_points,
                                 username)

async def get_player_data(db_pool, username: str):
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return None

    query = """
    SELECT pos_x, pos_y, 
           level, experience, stat_points,
           current_health, 
           strength, agility, vitality, 
           intelligence, dexterity, luck,
           class_name 
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
                'stat_points': record['stat_points'],
                'strength': record['strength'],
                'agility': record['agility'],
                'vitality': record['vitality'],
                'intelligence': record['intelligence'],
                'dexterity': record['dexterity'],
                'luck': record['luck'],
                'class_name': record['class_name']
            }
        return None