import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from database import init_db
from handlers import start, chat, image, photo, models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def make_bot():
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )


def make_dp():
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(image.router)   # /image — до chat чтобы не перехватил
    dp.include_router(models.router)  # /models
    dp.include_router(photo.router)   # фото
    dp.include_router(chat.router)    # текст — последним
    return dp


async def run_polling():
    bot = make_bot()
    dp = make_dp()

    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"Запуск в режиме POLLING")

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


async def run_webhook():
    bot = make_bot()
    dp = make_dp()

    await init_db()

    webhook_url = f"{config.WEBHOOK_URL}/webhook"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    logger.info(f"Webhook: {webhook_url}")

    app = web.Application()

    async def health(req):
        return web.Response(text="OK")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", config.PORT).start()

    logger.info(f"Сервер запущен на порту {config.PORT}")
    await asyncio.Event().wait()


def main():
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        sys.exit(1)

    if config.WEBHOOK_URL:
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
