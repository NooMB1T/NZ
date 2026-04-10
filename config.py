import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

DATABASE_PATH = "academy.db"

ROLES = {
    "ученик": 0,
    "саппорт": 1,
    "куратор": 2,
    "админ": 3
}

MAX_WARNINGS = 3
TASKS_PER_PAGE = 5