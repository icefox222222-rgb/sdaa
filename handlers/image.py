import logging
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from ai import generate
from database import check_ratelimit
import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("image"))
async def cmd_image(message: Message):
    uid = message.from_user.id

    # Получаем описание из команды
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "🖼 *Генерация картинок*\n\n"
            "Напиши описание после команды:\n"
            "`/image красивый закат над морем`\n\n"
            "Можно писать по-русски или по-английски!",
            parse_mode="Markdown"
        )
        return

    prompt = parts[1].strip()

    # Проверка rate limit
    ok = await check_ratelimit(uid, config.MAX_RPM)
    if not ok:
        await message.answer(f"⚠️ Слишком много запросов! Подожди минуту.")
        return

    gen_msg = await message.answer("🎨 Генерирую изображение...\n⏳ Это займёт 10-30 секунд")

    try:
        image_bytes = await generate(prompt)

        if not image_bytes:
            await gen_msg.delete()
            await message.answer("❌ Не удалось сгенерировать изображение. Попробуй ещё раз.")
            return

        await gen_msg.delete()

        photo = BufferedInputFile(image_bytes, filename="image.png")
        await message.answer_photo(
            photo,
            caption=f"🖼 *Готово!*\n📝 _{prompt}_",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        await gen_msg.delete()
        await message.answer("❌ Ошибка при генерации изображения. Попробуй позже.")
