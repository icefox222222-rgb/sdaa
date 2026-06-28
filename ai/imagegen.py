import httpx
import logging

logger = logging.getLogger(__name__)


async def generate(prompt: str) -> bytes | None:
    """Генерация через ModelsLab Nano Banana 2 (Gemini 3.1)."""
    import config
    api_key = getattr(config, "MODELSLAB_API_KEY", "")

    if not api_key:
        logger.error("MODELSLAB_API_KEY не задан")
        return None

    try:
        payload = {
            "key": api_key,
            "prompt": prompt,
            "negative_prompt": "blurry, bad quality, distorted, ugly",
            "width": "1024",
            "height": "1024",
            "samples": "1",
            "guidance_scale": 7.5,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://modelslab.com/api/v7/images/text-to-image",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"ModelsLab ответ: {data.get('status')}")

            if data.get("status") == "success":
                img_url = data["output"][0]
                img_resp = await client.get(img_url)
                img_resp.raise_for_status()
                return img_resp.content

            elif data.get("status") == "processing":
                import asyncio
                await asyncio.sleep(15)
                fetch_url = data.get("fetch_result")
                fetch_resp = await client.post(fetch_url, json={"key": api_key})
                fetch_data = fetch_resp.json()
                if fetch_data.get("status") == "success":
                    img_url = fetch_data["output"][0]
                    img_resp = await client.get(img_url)
                    return img_resp.content

            logger.error(f"Неожиданный ответ: {data}")
            return None

    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        return None
