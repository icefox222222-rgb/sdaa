import httpx
import urllib.parse
import random
import logging

logger = logging.getLogger(__name__)


async def generate(prompt: str) -> bytes | None:
    """
    Генерация через Pollinations.ai
    Полностью бесплатно, без API ключа.
    """
    try:
        encoded = urllib.parse.quote(prompt)
        seed = random.randint(1, 999999)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1024&height=1024&seed={seed}&nologo=true"
        )
        logger.info(f"Запрос: {url[:80]}")

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(url)
            logger.info(f"Статус: {resp.status_code}, размер: {len(resp.content)} байт")

            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content

            logger.error(f"Плохой ответ: {resp.status_code}, {len(resp.content)} байт")
            return None

    except Exception as e:
        logger.error(f"Ошибка Pollinations: {e}")
        return None
