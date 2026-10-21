import type { Status } from '../hooks/useVoiceSession'

interface Props {
  status: Status
  onStart: () => void
  onStop: () => void
}

export function MicButton({ status, onStart, onStop }: Props) {
  const isRecording = status === 'recording'
  const isSpeaking = status === 'speaking'
  // Busy = backend is still processing (can't send new audio yet)
  // Speaking is NOT busy — user can interrupt by holding mic
  const isBusy = ['listening', 'thinking'].includes(status)

  return (
    <div className="relative flex items-center justify-center">
      {/* Ripple rings — only when recording */}
      {isRecording && (
        <>
          <span className="mic-ring absolute w-20 h-20" />
          <span className="mic-ring absolute w-20 h-20" />
          <span className="mic-ring absolute w-20 h-20" />
        </>
      )}

      {/* Ambient glow */}
      {!isRecording && !isBusy && (
        <span
          className="absolute w-24 h-24 rounded-full opacity-30 blur-xl"
          style={{
            background: isSpeaking
              ? 'radial-gradient(circle, #10b981, transparent)'
              : 'radial-gradient(circle, #7c3aed, transparent)',
          }}
        />
      )}

      <button
        onMouseDown={onStart}
        onMouseUp={onStop}
        onTouchStart={e => { e.preventDefault(); onStart() }}
        onTouchEnd={e => { e.preventDefault(); onStop() }}
        disabled={isBusy}
        className={`
          relative w-20 h-20 rounded-full flex items-center justify-center
          transition-all duration-200 select-none z-10
          ${isRecording
            ? 'scale-110 shadow-[0_0_50px_rgba(239,68,68,0.7)]'
            : isBusy
            ? 'opacity-40 cursor-not-allowed scale-95'
            : 'hover:scale-105 active:scale-95 shadow-glow hover:shadow-glow-lg'
          }
        `}
        style={
          isRecording
            ? { background: 'linear-gradient(135deg, #ef4444, #dc2626)' }
            : isBusy
            ? { background: 'rgba(255,255,255,0.08)' }
            : isSpeaking
            ? { background: 'linear-gradient(135deg, #10b981, #059669)' }
            : { background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }
        }
        aria-label={isRecording ? 'Release to send' : isSpeaking ? 'Hold to interrupt' : 'Hold to speak'}
      >
        {/* Inner highlight */}
        <span
          className="absolute inset-1 rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.5), transparent)',
          }}
        />

        {isBusy ? (
          <BusyIcon status={status} />
        ) : isRecording ? (
          <StopIcon />
        ) : isSpeaking ? (
          <InterruptIcon />
        ) : (
          <MicIcon />
        )}
      </button>
    </div>
  )
}

function MicIcon() {
  return (
    <svg className="w-8 h-8 text-white relative z-10" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v6a2 2 0 0 0 4 0V5a2 2 0 0 0-2-2zm7 8a1 1 0 0 1 1 1 8 8 0 0 1-7 7.93V21h2a1 1 0 0 1 0 2H9a1 1 0 0 1 0-2h2v-1.07A8 8 0 0 1 4 12a1 1 0 0 1 2 0 6 6 0 0 0 12 0 1 1 0 0 1 1-1z"/>
    </svg>
  )
}

function StopIcon() {
  return (
    <svg className="w-7 h-7 text-white relative z-10" fill="currentColor" viewBox="0 0 24 24">
      <rect x="5" y="5" width="14" height="14" rx="3" />
    </svg>
  )
}

function InterruptIcon() {
  return (
    // Sound wave bars that animate — tap to cut them off
    <div className="flex items-end gap-1 h-7 relative z-10 pb-0.5">
      {[4, 7, 10, 7, 4].map((h, i) => (
        <div
          key={i}
          className="rounded-full bg-white animate-pulse"
          style={{
            width: 3,
            height: `${h * 2.5}px`,
            animationDelay: `${i * 0.1}s`,
            animationDuration: '0.8s',
          }}
        />
      ))}
    </div>
  )
}

function BusyIcon({ status: _status }: { status: Status }) {
  const dots = [0, 0.15, 0.3]
  return (
    <div className="flex items-center gap-1 relative z-10">
      {dots.map((delay, i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-white animate-bounce"
          style={{ animationDelay: `${delay}s` }}
        />
      ))}
    </div>
  )
}
