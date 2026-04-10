# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from config import 8742739517:AAHceosxCaq1QB261YX24Oi5tTgwH_1_Xf4
from database import init_db
from handlers import common, tasks, top, faq, profile, info, dev, admin

logging.basicConfig(level=logging.INFO)

async def handle_healthcheck(request):
    return web.Response(text="OK")

async def handle_index(request):
    return web.Response(text="Academy Support Bot is running.")

async def main():
    await init_db()
    bot = Bot(token=8742739517:AAHceosxCaq1QB261YX24Oi5tTgwH_1_Xf4)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(top.router)
    dp.include_router(faq.router)
    dp.include_router(profile.router)
    dp.include_router(info.router)
    dp.include_router(dev.router)
    dp.include_router(admin.router)
    
    logging.info("Starting bot polling...")
    asyncio.create_task(dp.start_polling(bot))

    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/healthcheck', handle_healthcheck)
    
    port = int(os.environ.get("PORT", 8000))
    logging.info(f"Starting web server on port {port}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
