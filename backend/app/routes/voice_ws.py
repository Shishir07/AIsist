import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.orchestrator import run_agent
from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket voice pipeline:
    1. Receive raw audio chunks from browser (push-to-talk)
    2. Stream to Deepgram STT → text
    3. Pass text to LangGraph agent
    4. Stream Deepgram TTS audio back to browser
    """
    await websocket.accept()
    session_id = str(id(websocket))
    logger.info(f"Voice session started: {session_id}")

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive()

            if "bytes" in data:
                # Audio data received → transcribe
                audio_bytes = data["bytes"]
                await websocket.send_json({"type": "status", "value": "listening"})

                transcript = await transcribe_audio(audio_bytes)

                if not transcript or not transcript.strip():
                    await websocket.send_json({"type": "status", "value": "idle"})
                    continue

                # Send transcript back so UI can display it
                await websocket.send_json({
                    "type": "transcript",
                    "value": transcript,
                    "role": "user"
                })

                # Run agent
                await websocket.send_json({"type": "status", "value": "thinking"})
                agent_response = await run_agent(
                    session_id=session_id,
                    user_message=transcript,
                    websocket=websocket,
                )

                # Send text response to UI
                await websocket.send_json({
                    "type": "transcript",
                    "value": agent_response,
                    "role": "assistant"
                })

                # Synthesize and stream TTS audio
                await websocket.send_json({"type": "status", "value": "speaking"})
                audio_data = await synthesize_speech(agent_response)
                await websocket.send_bytes(audio_data)

                await websocket.send_json({"type": "status", "value": "idle"})

            elif "text" in data:
                # Control messages from frontend (e.g. confirmation yes/no)
                msg = json.loads(data["text"])
                if msg.get("type") == "confirm":
                    # Handle confirmation responses for write actions
                    agent_response = await run_agent(
                        session_id=session_id,
                        user_message=msg.get("value", ""),
                        websocket=websocket,
                    )
                    await websocket.send_json({
                        "type": "transcript",
                        "value": agent_response,
                        "role": "assistant"
                    })
                    audio_data = await synthesize_speech(agent_response)
                    await websocket.send_bytes(audio_data)
                    await websocket.send_json({"type": "status", "value": "idle"})

    except WebSocketDisconnect:
        logger.info(f"Voice session ended: {session_id}")
    except Exception as e:
        logger.error(f"Voice session error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "value": str(e)})
        except Exception:
            pass  # Connection already closed
