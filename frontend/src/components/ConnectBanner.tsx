interface Props {
  loginUrl: string
}

export function ConnectBanner({ loginUrl }: Props) {
  return (
    <div className="mx-4 my-3 rounded-2xl overflow-hidden animate-slide-up">
      <div
        className="px-4 py-3 flex items-center justify-between gap-3"
        style={{
          background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(234,88,12,0.08))',
          border: '1px solid rgba(245,158,11,0.2)',
        }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(245,158,11,0.15)' }}
          >
            <span className="text-base">📅</span>
          </div>
          <div>
            <p className="text-amber-300 text-xs font-semibold">Connect Google Calendar</p>
            <p className="text-amber-500/70 text-[10px]">Enable scheduling & event management</p>
          </div>
        </div>
        <a
          href={loginUrl}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg whitespace-nowrap transition-all duration-150 hover:scale-105 active:scale-95"
          style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)', color: '#000' }}
        >
          Connect →
        </a>
      </div>
    </div>
  )
}
