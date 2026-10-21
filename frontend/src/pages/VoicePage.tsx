import { useVoiceSession } from '../hooks/useVoiceSession'
import { useStatus } from '../hooks/useStatus'
import { MicButton } from '../components/MicButton'
import { ChatView } from '../components/ChatView'
import { StatusBar } from '../components/StatusBar'
import { ConnectBanner } from '../components/ConnectBanner'

export function VoicePage() {
  const { status, messages, isConnected, startRecording, stopRecording } = useVoiceSession()
  const { status: appStatus, loading: statusLoading, refetch } = useStatus()

  const calendarConnected = appStatus?.google_calendar_connected ?? true

  const handleDisconnectCalendar = async () => {
    await fetch('/api/auth/google/disconnect', { method: 'DELETE' })
    refetch()
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Google Calendar connect banner */}
      {!statusLoading && !calendarConnected && (
        <ConnectBanner loginUrl={appStatus!.google_login_url} />
      )}

      {/* Status strip */}
      <div className="flex items-center justify-between px-5 py-1.5">
        {/* WS indicator */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full transition-colors ${
              isConnected ? 'bg-emerald-400' : 'bg-red-500'
            }`}
          />
          <span className="text-[10px] text-slate-600">
            {isConnected ? 'Live' : 'Offline'}
          </span>
        </div>

        {/* Calendar disconnect */}
        {!statusLoading && calendarConnected && (
          <button
            onClick={handleDisconnectCalendar}
            className="text-[10px] text-slate-600 hover:text-red-400 transition-colors flex items-center gap-1"
          >
            📅 Calendar ✕
          </button>
        )}
      </div>

      {/* Chat transcript */}
      <ChatView messages={messages} />

      {/* Controls */}
      <div className="pb-safe">
        <StatusBar status={status} />
        <div className="flex justify-center pb-8 pt-3">
          <MicButton status={status} onStart={startRecording} onStop={stopRecording} />
        </div>
        <p className="text-center text-[10px] text-slate-700 pb-3 tracking-wide uppercase">
          {status === 'speaking'
            ? 'Hold to interrupt'
            : 'Hold to speak · Release to send'}
        </p>
      </div>
    </div>
  )
}
