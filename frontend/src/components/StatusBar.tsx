import type { Status } from '../hooks/useVoiceSession'

const STATUS_CONFIG: Record<Status, {
  label: string
  color: string
  bg: string
  pulse: boolean
  emoji: string
}> = {
  idle:      { label: 'Ready to listen',  color: 'text-slate-400',  bg: 'rgba(100,116,139,0.15)', pulse: false, emoji: '○' },
  recording: { label: 'Listening…',       color: 'text-red-400',    bg: 'rgba(239,68,68,0.15)',   pulse: true,  emoji: '●' },
  listening: { label: 'Processing audio', color: 'text-amber-400',  bg: 'rgba(245,158,11,0.15)',  pulse: true,  emoji: '◉' },
  thinking:  { label: 'Thinking…',        color: 'text-violet-400', bg: 'rgba(139,92,246,0.15)',  pulse: true,  emoji: '◈' },
  speaking:  { label: 'Speaking',         color: 'text-emerald-400',bg: 'rgba(52,211,153,0.15)',  pulse: true,  emoji: '◉' },
  error:     { label: 'Something went wrong', color: 'text-red-500', bg: 'rgba(239,68,68,0.15)', pulse: false, emoji: '✕' },
}

export function StatusBar({ status }: { status: Status }) {
  const cfg = STATUS_CONFIG[status]
  return (
    <div className="flex justify-center px-4 py-2">
      <div
        className="flex items-center gap-2 px-4 py-1.5 rounded-full transition-all duration-300"
        style={{ background: cfg.bg, border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <span
          className={`text-xs font-mono ${cfg.color} ${cfg.pulse ? 'animate-pulse' : ''}`}
          style={{ fontSize: '10px' }}
        >
          {cfg.emoji}
        </span>
        <span className={`text-xs ${cfg.color} font-medium tracking-wide`}>
          {cfg.label}
        </span>
      </div>
    </div>
  )
}
