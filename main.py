import asyncio

from aiogram import types, F
from aiogram.filters import Command

from core import database
from core.handlers import basic, vacancy, courses
from core.config import dp, bot


async def main():
    dp.db_pool = await database.get_db_pool()
    # dp.update.middleware(BasicMiddleware())
    dp.message.register(basic.start, Command('start'))
    dp.message.register(basic.delete_account_confirm, Command('delete_account'))
    dp.callback_query.register(vacancy.search_vacancy, F.data == 'search_vacancy')
    dp.callback_query.register(courses.search_course, F.data == 'search_course')

    await bot.set_my_commands([types.BotCommand(command="start", description="Старт"),
                               types.BotCommand(command="delete_account", description="Удалить аккаунт")])
    await dp.start_polling(bot)


print('Start working')
if __name__ == "__main__":
    asyncio.run(main())
