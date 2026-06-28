import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import ensure_user, get_history, add_message, check_ratelimit
from ai import ask
import config

logger = logging.getLogger(__name__)
router = Router()

OCR_WORDS = {"ocr", "текст", "распознай", "прочитай", "text", "read", "extract"}


@router.message(F.photo)
async def handle_photo(message: Message, bot):
    uid = message.from_user.id
    caption = message.caption or ""

    await ensure_user(uid, message.from_user.username, message.from_user.first_name)

    ok = await check_ratelimit(uid, config.MAX_RPM)
    if not ok:
        await message.answer("⚠️ Слишком много запросов! Подожди минуту.")
        return

    # Определяем режим
    is_ocr = caption.lower().strip() in OCR_WORDS or any(w in caption.lower() for w in OCR_WORDS)

    if is_ocr:
        status = await message.answer("📝 Распознаю текст на фото...")
        prompt = (
            "Внимательно извлеки ВЕСЬ текст с этого изображения. "
            "Сохрани форматирование и структуру. "
            "Отвечай только извлечённым текстом, без комментариев."
        )
    elif caption:
        status = await message.answer("🔍 Анализирую фото...")
        prompt = caption
    else:
        status = await message.answer("🔍 Анализирую фото...")
        prompt = (
            "Подробно опиши что изображено на фото: "
            "объекты, люди, место, цвета, настроение. "
            "Если есть текст — прочитай его."
        )

    try:
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_io = await bot.download_file(file.file_path)
        image_bytes = file_io.read() if hasattr(file_io, "read") else bytes(file_io)

        # История для контекста
        history = await get_history(uid, limit=4)
        user_log = f"[Фото] {caption}" if caption else "[Фото без подписи]"
        await add_message(uid, "user", user_log)

        messages = history + [{"role": "user", "content": prompt}]
        response = await ask(messages, image_bytes=image_bytes)

        await add_message(uid, "assistant", response)
        await status.delete()

        if is_ocr:
            await message.answer(f"📝 *Распознанный текст:*\n\n{response}", parse_mode="Markdown")
        else:
            await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await status.delete()
        await message.answer(
            "❌ Ошибка при анализе фото.\n\n"
            f"Детали: `{str(e)[:200]}`",
            parse_mode="Markdown"
        )
