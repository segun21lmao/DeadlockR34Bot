import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import admin, api_parser, user

load_dotenv()
token = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(token=str(token))
    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.include_router(api_parser.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
