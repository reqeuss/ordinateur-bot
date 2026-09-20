import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = "&"
BOT_NAME = "Ordinateur"
CURRENCY_NAME = "Cookies"
CURRENCY_EMOJI = "🍪"

STARTING_COOKIES = 250
DAILY_REWARD = 150
WORK_MIN = 60
WORK_MAX = 180
WORK_COOLDOWN = 60 * 60
FREE_COFFEE_COOLDOWN = 24 * 60 * 60
DAILY_COOLDOWN = 24 * 60 * 60
MESSAGE_XP_MIN = 8
MESSAGE_XP_MAX = 18

DB_PATH = "data/ordinateur.db"
