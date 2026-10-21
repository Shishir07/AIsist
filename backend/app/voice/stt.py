import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEEPGRAM_STT_URL = "https://api.deepgram.com/v1/listen"


async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using Deepgram Nova-2.
    Uses REST API directly to ensure correct Content-Type header for WebM/Opus.
    """
    if not audio_bytes:
        return ""

    logger.info(f"STT: received {len(audio_bytes)} bytes of audio")

    try:
        params = {
            "model": settings.deepgram_stt_model,
            "language": "en-IN",
            "smart_format": "true",
            "punctuate": "true",
        }
        headers = {
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "audio/webm",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPGRAM_STT_URL,
                params=params,
                headers=headers,
                content=audio_bytes,
            )
            response.raise_for_status()
            data = response.json()

        transcript = (
            data["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
        logger.info(f"STT transcript: {transcript!r}")
        return transcript

    except Exception as e:
        logger.error(f"STT error: {e}", exc_info=True)
        return ""
