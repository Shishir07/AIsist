import { useEffect, useRef } from 'react'
import type { Message } from '../hooks/useVoiceSession'

const SUGGESTIONS = [
  "What's on my calendar tomorrow?",
  "Add milk to my grocery list",
  "Generate a meal plan for the week",
  "What's in my pantry?",
]

export function ChatView({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8 animate-fade-in">
        {/* Waveform illustration */}
        <div className="relative animate-float">
          <div className="flex items-end gap-1.5 h-14">
            {[3, 6, 10, 14, 10, 18, 10, 14, 10, 6, 3].map((h, i) => (
              <div
                key={i}
                className="rounded-full animate-pulse"
                style={{
                  width: 4,
                  height: `${h * 3}px`,
                  background: `linear-gradient(to top, #7c3aed, #818cf8)`,
                  opacity: 0.7 + (i % 3) * 0.1,
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: `${1.2 + (i % 3) * 0.3}s`,
                }}
              />
            ))}
          </div>
          {/* Glow under waveform */}
          <div
            className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-24 h-6 blur-xl opacity-50"
            style={{ background: 'radial-gradient(ellipse, #7c3aed, transparent)' }}
          />
        </div>

        <div className="text-center">
          <p className="text-slate-200 font-medium text-base mb-1">How can I help you today?</p>
          <p className="text-slate-500 text-sm">Hold the button below and speak</p>
        </div>

        {/* Suggestion chips */}
        <div className="flex flex-col gap-2 w-full max-w-xs">
          {SUGGESTIONS.map((s, i) => (
            <div
              key={i}
              className="glass rounded-xl px-4 py-2.5 text-xs text-slate-400 text-center cursor-default"
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              "{s}"
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex chat-bubble ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          {/* AI avatar */}
          {msg.role === 'assistant' && (
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1 self-end"
              style={{ background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }}
            >
              <span className="text-xs">✨</span>
            </div>
          )}

          <div
            className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'rounded-br-sm text-white'
                : 'glass rounded-bl-sm text-slate-100'
            }`}
            style={
              msg.role === 'user'
                ? { background: 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)' }
                : {}
            }
          >
            {msg.text}
            <div className="text-[10px] mt-1.5 opacity-40 text-right">
              {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
