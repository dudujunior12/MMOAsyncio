# server/db/npcs.py

import random
import asyncpg
from shared.logger import get_logger

logger = get_logger(__name__)

# Nota: Assumimos que o db_pool será passado ou importado de database.py
# Para simplificar e seguir o padrão de injeção de dependência que você usa em outros lugares,
# vamos fazer a função aceitar o db_pool.

async def get_initial_spawns(db_pool: asyncpg.pool.Pool):
    """
    Busca todas as zonas de spawn do banco de dados, calcula posições aleatórias
    dentro da zona e retorna uma lista de monstros para o WorldInitializer.
    """
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        return []

    # Query que busca dados da zona (coordenadas e limite) e dados do template (stats)
    query = """
    SELECT 
        z.zone_name, z.min_x, z.max_x, z.min_y, z.max_y, z.max_mobs_in_zone,
        t.asset_type, t.level, t.base_health, t.strength, t.vitality
    FROM spawn_zones z
    JOIN monster_templates t ON z.monster_asset_type = t.asset_type;
    """
    
    async with db_pool.acquire() as connection:
        try:
            records = await connection.fetch(query)
            
            spawn_data_list = []
            
            for record in records:
                # Gerar 'max_mobs_in_zone' entidades para inicialização
                for _ in range(record['max_mobs_in_zone']): 
                    
                    # Gera uma posição aleatória (uniform) dentro dos limites X e Y da zona
                    random_x = random.uniform(record['min_x'], record['max_x'])
                    random_y = random.uniform(record['min_y'], record['max_y'])
                    
                    spawn_data_list.append({
                        'x': random_x, 
                        'y': random_y, 
                        'asset_type': record['asset_type'], 
                        'level': record['level'], 
                        'base_health': record['base_health'], 
                        'strength': record['strength'], 
                        'vitality': record['vitality']
                    })
            
            logger.info(f"Generated {len(spawn_data_list)} initial monster entities from spawn zones.")
            return spawn_data_list
        
        except Exception as e:
            logger.error(f"Error retrieving monster spawn zone data: {e}")
            return []