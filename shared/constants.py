from dotenv import load_dotenv
import os

# carrega o .env
load_dotenv()

IP = os.getenv("IP", "localhost")
PORT = int(os.getenv("PORT", "8080"))
DATA_PAYLOAD_SIZE = int(os.getenv("DATA_PAYLOAD_SIZE", "262144"))

GAME_TICK_RATE = 30 
TICK_INTERVAL = 1.0 / GAME_TICK_RATE

A_O_I_RANGE = 25.0

DB_NAME = os.getenv("DB_NAME", "mmo_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))