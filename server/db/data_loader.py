# server/db/data_loader.py

import json
import os
from shared.logger import get_logger

logger = get_logger(__name__)

MONSTER_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'monster_templates.json')

async def load_monster_data(db_pool):

    if db_pool is None:
        logger.error("Database pool is not initialized. Cannot load monster data.")
        return
        
    if not os.path.exists(MONSTER_DATA_FILE):
        logger.error(f"Monster data file not found at: {MONSTER_DATA_FILE}")
        return

    try:
        with open(MONSTER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        templates = data.get('templates', [])
        spawn_zones = data.get('spawn_zones', [])
        
        async with db_pool.acquire() as connection:
            template_values = [
                (t['asset_type'], t['level'], t['base_health'], t['strength'], t['vitality'])
                for t in templates
            ]
            
            await connection.executemany("""
                INSERT INTO monster_templates (asset_type, level, base_health, strength, vitality)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (asset_type) DO UPDATE SET 
                    level = EXCLUDED.level, base_health = EXCLUDED.base_health, strength = EXCLUDED.strength, vitality = EXCLUDED.vitality;
            """, template_values)
            
            logger.info(f"Loaded and updated {len(templates)} monster templates.")

            await connection.execute("DELETE FROM spawn_zones;") 
            logger.info("Cleared existing monster spawn zones.")


            zone_values = [
                (
                    z['zone_name'], z['monster_asset_type'], z['map_name'],
                    z['min_x'], z['max_x'], z['min_y'], z['max_y'],
                    z.get('max_mobs_in_zone', 1), z.get('respawn_time_seconds', 30)
                )
                for z in spawn_zones
            ]

            # Inserção massiva de zonas
            await connection.executemany("""
                INSERT INTO spawn_zones (zone_name, monster_asset_type, map_name, min_x, max_x, min_y, max_y, max_mobs_in_zone, respawn_time_seconds)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, zone_values)
            
            logger.info(f"Loaded {len(spawn_zones)} monster spawn zones.")
            
    except Exception as e:
        logger.error(f"Failed to load monster data from JSON to DB: {e}")