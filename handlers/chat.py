import logging
from aiogram import Router, F
from aiogram.types import Message
from database import ensure_user, get_history, add_message, check_ratelimit
from ai import ask
import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_chat(message: Message):
    uid = message.from_user.id
    text = message.text

    await ensure_user(uid, message.from_user.username, message.from_user.first_name)

    # Проверка rate limit
    ok = await check_ratelimit(uid, config.MAX_RPM)
    if not ok:
        await message.answer(
            f"⚠️ Слишком много запросов! Подожди минуту.\n"
            f"Лимит: {config.MAX_RPM} запросов в минуту."
        )
        return

    thinking = await message.answer("🤔 Думаю...")

    try:
        history = await get_history(uid, config.MAX_HISTORY)
        await add_message(uid, "user", text)

        messages = history + [{"role": "user", "content": text}]
        response = await ask(messages)

        await add_message(uid, "assistant", response)
        await thinking.delete()
        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка чата: {e}")
        await thinking.delete()
        await message.answer(
            "❌ Ошибка при обращении к AI.\n\n"
            f"Детали: `{str(e)[:200]}`",
            parse_mode="Markdown"
        )
