import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ai import get_models

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("models"))
async def cmd_models(message: Message):
    msg = await message.answer("🔄 Загружаю список моделей...")
    try:
        models = await get_models()
        lines = [f"• `{m['id']}`" for m in models]
        text = (
            "🤖 *Бесплатные модели OpenRouter:*\n\n"
            + "\n".join(lines)
            + "\n\n_Модель меняется через переменную_ `OPENROUTER_MODEL` _на Railway_"
        )
        await msg.delete()
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await msg.delete()
        await message.answer(f"❌ Ошибка: {e}")
