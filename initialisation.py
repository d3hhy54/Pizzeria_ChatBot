from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(
    token=os.getenv("TOKEN_BOT"),
    parse_mode=ParseMode.HTML
)
dp = Dispatcher(
    bot,
    storage=MemoryStorage()
)

CHAT_URL = os.getenv("CHAT_URL")