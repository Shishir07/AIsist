import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"


async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech using Deepgram Aura TTS.
    Returns raw MP3 audio bytes.
    """
    try:
        params = {"model": settings.deepgram_tts_model}
        headers = {
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"text": text}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPGRAM_TTS_URL,
                params=params,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.content

    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        return b""
