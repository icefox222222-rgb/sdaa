import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import ensure_user, clear_history

logger = logging.getLogger(__name__)
router = Router()


def main_kb():
    b = InlineKeyboardBuilder()
    b.button(text="🤖 Чат с AI", callback_data="m_chat")
    b.button(text="🖼 Генерация картинок", callback_data="m_image")
    b.button(text="📷 Анализ фото", callback_data="m_photo")
    b.button(text="📝 Распознать текст (OCR)", callback_data="m_ocr")
    b.button(text="🤖 Доступные модели", callback_data="m_models")
    b.button(text="❓ Помощь", callback_data="m_help")
    b.adjust(2, 2, 2)
    return b.as_markup()


START_TEXT = """👋 *Привет! Я AI-ассистент на базе OpenRouter*

Вот что я умею:

🤖 *Чат с AI* — задавай любые вопросы
🖼 *Генерация картинок* — опиши что нарисовать
📷 *Анализ фото* — отправь фото и задай вопрос
📝 *OCR* — распознаю текст на изображении

*Команды:*
/start — главное меню
/clear — очистить историю чата
/image описание — сгенерировать картинку
/models — список AI моделей
/help — помощь

👇 Выбери действие:"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    u = message.from_user
    await ensure_user(u.id, u.username, u.first_name, u.language_code or "ru")
    await message.answer(START_TEXT, parse_mode="Markdown", reply_markup=main_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = """*❓ Помощь*

*Чат:*
Просто напиши любое сообщение — я отвечу через AI.
Бот помнит историю разговора.

*Генерация картинок:*
`/image закат над морем` — напиши описание
или нажми кнопку 🖼

*Анализ фото:*
Отправь фото с подписью-вопросом.
Пример: отправь фото кота с подписью "что за порода?"

*OCR (распознавание текста):*
Отправь фото с подписью `ocr`

*Команды:*
/start — главное меню
/clear — очистить историю
/image — сгенерировать картинку
/models — список моделей"""
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("✅ История чата очищена!")


# Кнопки меню
@router.callback_query(F.data == "m_chat")
async def cb_chat(cb: CallbackQuery):
    await cb.message.answer("💬 Просто напиши мне любое сообщение!")
    await cb.answer()


@router.callback_query(F.data == "m_image")
async def cb_image(cb: CallbackQuery):
    await cb.message.answer(
        "🖼 *Генерация картинок*\n\n"
        "Напиши команду:\n`/image твоё описание`\n\n"
        "Пример:\n`/image красивый закат над горами в стиле аниме`",
        parse_mode="Markdown"
    )
    await cb.answer()


@router.callback_query(F.data == "m_photo")
async def cb_photo(cb: CallbackQuery):
    await cb.message.answer(
        "📷 *Анализ фото*\n\n"
        "Отправь мне фото с подписью-вопросом.\n\n"
        "Пример: отправь фото еды с подписью\n_«что это за блюдо и как его приготовить?»_",
        parse_mode="Markdown"
    )
    await cb.answer()


@router.callback_query(F.data == "m_ocr")
async def cb_ocr(cb: CallbackQuery):
    await cb.message.answer(
        "📝 *Распознавание текста (OCR)*\n\n"
        "Отправь фото с подписью `ocr`\n\n"
        "Я извлеку весь текст с изображения.",
        parse_mode="Markdown"
    )
    await cb.answer()


@router.callback_query(F.data == "m_help")
async def cb_help(cb: CallbackQuery):
    await cmd_help(cb.message)
    await cb.answer()


@router.callback_query(F.data == "m_models")
async def cb_models(cb: CallbackQuery):
    from ai import get_models
    await cb.answer("Загружаю список моделей...")
    try:
        models = await get_models()
        lines = [f"• `{m['id']}`" for m in models]
        text = "🤖 *Бесплатные модели OpenRouter:*\n\n" + "\n".join(lines)
        await cb.message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await cb.message.answer(f"❌ Не удалось загрузить модели: {e}")
