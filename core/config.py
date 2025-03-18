
import os
import dotenv
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from groq import AsyncGroq

dotenv.load_dotenv()
bot = Bot(os.environ.get('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# storage = RedisStorage.from_url('redis://localhost:6379/7')
dp = Dispatcher()
groq_client = AsyncGroq(api_key=os.environ.get('GROQ_API_KEY'))
LLM_MODEL_NAME = 'qwen-2.5-32b'
