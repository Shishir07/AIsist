import { useCallback, useEffect, useRef, useState } from 'react'

export type Status = 'idle' | 'recording' | 'listening' | 'thinking' | 'speaking' | 'error'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: Date
}

export function useVoiceSession() {
  const [status, setStatus] = useState<Status>('idle')
  const [messages, setMessages] = useState<Message[]>([])
  const [isConnected, setIsConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  // Track the active audio source so we can stop it on interrupt
  const activeSourceRef = useRef<AudioBufferSourceNode | null>(null)
  // Track current status without stale-closure issues
  const statusRef = useRef<Status>('idle')

  const updateStatus = (s: Status) => {
    statusRef.current = s
    setStatus(s)
  }

  // Connect WebSocket
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/voice`)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data)

        if (msg.type === 'status') {
          updateStatus(msg.value as Status)
        }

        if (msg.type === 'transcript') {
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: msg.role,
              text: msg.value,
              timestamp: new Date(),
            },
          ])
        }

        if (msg.type === 'error') {
          updateStatus('error')
          console.error('Agent error:', msg.value)
        }
      }

      // Binary = TTS audio
      if (event.data instanceof Blob) {
        const arrayBuffer = await event.data.arrayBuffer()
        playAudio(arrayBuffer)
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const stopCurrentAudio = useCallback(() => {
    if (activeSourceRef.current) {
      try {
        activeSourceRef.current.stop()
      } catch {
        // Already stopped — ignore
      }
      activeSourceRef.current = null
    }
  }, [])

  const playAudio = async (buffer: ArrayBuffer) => {
    try {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new AudioContext()
      }
      const ctx = audioContextRef.current

      // Resume if suspended (browser autoplay policy)
      if (ctx.state === 'suspended') {
        await ctx.resume()
      }

      // Stop any currently playing audio
      stopCurrentAudio()

      const decoded = await ctx.decodeAudioData(buffer.slice(0))
      const source = ctx.createBufferSource()
      source.buffer = decoded
      source.connect(ctx.destination)

      activeSourceRef.current = source

      source.onended = () => {
        // Only go idle if this source is still the active one
        if (activeSourceRef.current === source) {
          activeSourceRef.current = null
          // Only reset to idle if we're still in speaking state
          // (not if the user already started recording)
          if (statusRef.current === 'speaking') {
            updateStatus('idle')
          }
        }
      }

      source.start()
    } catch (e) {
      console.error('Audio playback error:', e)
      updateStatus('idle')
    }
  }

  const startRecording = useCallback(async () => {
    // Stop any playing audio immediately (interrupt)
    stopCurrentAudio()
    // If backend still thinks we're speaking, it's already back at receive()
    // so we can safely start a new recording turn.

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      mediaRecorderRef.current = recorder
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const buffer = await blob.arrayBuffer()
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(buffer)
        }
        stream.getTracks().forEach((t) => t.stop())
      }

      recorder.start()
      updateStatus('recording')
    } catch (e) {
      console.error('Microphone error:', e)
      updateStatus('error')
    }
  }, [stopCurrentAudio])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
      updateStatus('listening')
    }
  }, [])

  return {
    status,
    messages,
    isConnected,
    startRecording,
    stopRecording,
  }
}
