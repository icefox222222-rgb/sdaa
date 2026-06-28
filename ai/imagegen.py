import httpx
import urllib.parse
import logging

logger = logging.getLogger(__name__)


async def generate(prompt: str) -> bytes | None:
    """
    Генерация изображения через Pollinations.ai
    Бесплатно, без API ключа.
    """
    try:
        # Если промпт на русском — переводим через простой транслит подсказки
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true&enhance=true"

        logger.info(f"Генерация изображения: {prompt[:50]}...")

        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            logger.info(f"Изображение получено: {len(resp.content)} байт")
            return resp.content

    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        return None
