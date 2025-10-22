import bcrypt
import asyncpg
from shared.logger import get_logger

logger = get_logger(__name__)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def verify_password(password: str, hashed: str) -> bool:
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError as e:
        logger.error(f"Error verifying password: {e}")
        return False

async def create_user(db_pool, username: str, password: str) -> bool:
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return False

    hashed_password = hash_password(password)

    async with db_pool.acquire() as connection:
        try:
            await connection.execute(
                "INSERT INTO users (username, password_hash) VALUES ($1, $2)",
                username,
                hashed_password
            )
            logger.info(f"User '{username}' created successfully.")
            return True
        except asyncpg.UniqueViolationError:
            logger.warning(f"Username '{username}' already exists.")
            return False
        except Exception as e:
            logger.error(f"Error creating user '{username}': {e}")
            return False
        
async def authenticate_user(db_pool, username: str, password: str) -> bool:
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return False
    
    query = "SELECT password_hash FROM users WHERE username = $1"

    async with db_pool.acquire() as connection:
        try:
            result = await connection.fetchrow(query, username)
            if result:
                stored_hash = result['password_hash']
                return await verify_password(password, stored_hash)
            else:
                return False
        except Exception as e:
            logger.error(f"Error verifying user {username}: {e}")
            return False