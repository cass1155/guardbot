from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from bot.core.config import settings
from bot.core.redis import redis_client
from bot.core.memory_cache import MemoryCache

bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

if isinstance(redis_client, MemoryCache):
    storage = MemoryStorage()
else:
    storage = RedisStorage(redis=redis_client)

dp = Dispatcher(storage=storage)
