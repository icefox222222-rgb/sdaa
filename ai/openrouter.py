import httpx
import base64
import logging
import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты умный и дружелюбный AI-ассистент в Telegram боте.
Отвечай на том же языке, на котором пишет пользователь.
Если пишут по-русски — отвечай по-русски.
Если по-английски — по-английски.
Форматируй ответы для Telegram: используй *жирный*, _курсив_, `код` где уместно.
Будь кратким и по делу."""

# Бесплатные модели с поддержкой изображений
VISION_MODEL = "meta-llama/llama-3.1-8b-instruct"
TEXT_MODEL = "meta-llama/llama-3.1-8b-instruct"

HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://t.me/AIagentIcebot",
    "X-Title": "Telegram AI Bot",
}


async def ask(messages: list, image_bytes: bytes = None, image_mime: str = "image/jpeg") -> str:
    """
    Отправить запрос в OpenRouter.
    messages — список {"role": "user/assistant", "content": "..."}
    image_bytes — байты изображения (опционально)
    """
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не задан")

    headers = {**HEADERS, "Authorization": f"Bearer {api_key}"}

    # Выбираем модель
    if image_bytes:
        model = VISION_MODEL
        # Добавляем изображение к последнему сообщению
        b64 = base64.b64encode(image_bytes).decode()
        last = messages[-1]
        text = last["content"] if isinstance(last["content"], str) else ""
        messages = messages[:-1] + [{
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{b64}"}}
            ]
        }]
    else:
        model = TEXT_MODEL

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    payload = {
        "model": model,
        "messages": full_messages,
        "max_tokens": 1500,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if resp.status_code != 200:
            logger.error(f"OpenRouter {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        data = resp.json()

        # Проверяем на ошибку в теле ответа
        if "error" in data:
            raise Exception(f"OpenRouter error: {data['error']}")

        return data["choices"][0]["message"]["content"]


async def get_models() -> list:
    """Получить список бесплатных моделей."""
    headers = {**HEADERS, "Authorization": f"Bearer {config.OPENROUTER_API_KEY}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        free = [m for m in data.get("data", []) if ":free" in m.get("id", "")]
        return free[:8]
