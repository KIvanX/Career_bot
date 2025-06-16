
import os
import dotenv
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from together import Together

dotenv.load_dotenv()
bot = Bot(os.environ.get('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# storage = RedisStorage.from_url('redis://localhost:6379/7')
dp = Dispatcher()
client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))
LLM_MODEL_NAME = 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free'
