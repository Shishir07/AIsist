import { useMealPlan, type MealPlanEntry } from '../hooks/useAppData'

const MEAL_CONFIG: Record<string, { emoji: string; color: string; bg: string; time: string }> = {
  breakfast: { emoji: '🍳', color: 'text-amber-400',   bg: 'rgba(245,158,11,0.12)',  time: '8:00 AM'  },
  lunch:     { emoji: '🥗', color: 'text-emerald-400', bg: 'rgba(52,211,153,0.12)', time: '12:00 PM' },
  dinner:    { emoji: '🍽️', color: 'text-violet-400',  bg: 'rgba(139,92,246,0.12)', time: '6:30 PM'  },
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T12:00:00')
  return { day: DAYS[d.getDay()], num: d.getDate(), month: MONTHS[d.getMonth()] }
}

function groupByDate(entries: MealPlanEntry[]) {
  const groups: Record<string, MealPlanEntry[]> = {}
  for (const e of entries) {
    if (!groups[e.date]) groups[e.date] = []
    groups[e.date].push(e)
  }
  return groups
}

export function MealPlanPage() {
  const { data, loading, refetch } = useMealPlan(7)

  const entries = data?.entries ?? []
  const grouped = groupByDate(entries)
  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="flex flex-col flex-1 min-h-0 animate-fade-in">
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-center justify-between">
        <div>
          <h2 className="text-slate-100 font-bold text-lg">Meal Plan</h2>
          <p className="text-slate-500 text-xs">Next 7 days</p>
        </div>
        <button
          onClick={refetch}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          ↻
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-5 pb-4 space-y-4">
        {loading && (
          <div className="space-y-3">
            {[1,2,3].map(i => <div key={i} className="shimmer h-24 rounded-2xl" />)}
          </div>
        )}

        {!loading && entries.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-5">
            <div className="text-5xl animate-float">📅</div>
            <div className="text-center">
              <p className="text-slate-300 font-medium">No meal plan yet</p>
              <p className="text-slate-600 text-sm mt-1">Generate one by voice</p>
            </div>
            <div
              className="px-5 py-3 rounded-2xl space-y-1.5 w-full"
              style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)' }}
            >
              {[
                '"Generate a meal plan for this week"',
                '"Plan dinners for 7 days"',
                '"Add meals to my calendar"',
              ].map((s, i) => (
                <p key={i} className="text-[11px] text-violet-400/70 text-center">{s}</p>
              ))}
            </div>
          </div>
        )}

        {Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([dateStr, dayEntries]) => {
            const { day, num, month } = formatDate(dateStr)
            const isToday = dateStr === today

            return (
              <div key={dateStr} className="animate-slide-up">
                {/* Date header */}
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`w-12 h-12 rounded-2xl flex flex-col items-center justify-center flex-shrink-0 ${
                      isToday ? '' : ''
                    }`}
                    style={isToday
                      ? { background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }
                      : { background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }
                    }
                  >
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${isToday ? 'text-violet-200' : 'text-slate-500'}`}>
                      {day}
                    </span>
                    <span className={`text-lg font-bold leading-none ${isToday ? 'text-white' : 'text-slate-300'}`}>
                      {num}
                    </span>
                  </div>

                  <div>
                    <p className={`text-sm font-semibold ${isToday ? 'text-violet-300' : 'text-slate-300'}`}>
                      {isToday ? 'Today' : `${day}, ${month} ${num}`}
                    </p>
                    <p className="text-[10px] text-slate-600">
                      {dayEntries.length} meal{dayEntries.length !== 1 ? 's' : ''} planned
                    </p>
                  </div>
                </div>

                {/* Meal cards */}
                <div className="space-y-2 ml-15" style={{ marginLeft: '3.75rem' }}>
                  {dayEntries
                    .sort((a, b) => {
                      const o = ['breakfast', 'lunch', 'dinner']
                      return o.indexOf(a.meal_type) - o.indexOf(b.meal_type)
                    })
                    .map(entry => {
                      const cfg = MEAL_CONFIG[entry.meal_type] || {
                        emoji: '🍴', color: 'text-slate-400', bg: 'rgba(100,116,139,0.12)', time: ''
                      }
                      return (
                        <div
                          key={entry.id}
                          className="px-4 py-3 rounded-2xl flex items-start gap-3 transition-all hover:scale-[1.01]"
                          style={{
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid rgba(255,255,255,0.07)',
                          }}
                        >
                          <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                            style={{ background: cfg.bg }}
                          >
                            <span className="text-lg">{cfg.emoji}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-[10px] font-semibold uppercase tracking-wider ${cfg.color}`}>
                              {entry.meal_type}
                            </p>
                            <p className="text-slate-100 text-sm font-semibold leading-tight mt-0.5 truncate">
                              {entry.recipe_name}
                            </p>
                            {entry.description && (
                              <p className="text-slate-500 text-[11px] mt-0.5 truncate">{entry.description}</p>
                            )}
                          </div>
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            {entry.calendar_event_id && (
                              <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-0.5">
                                📅 synced
                              </span>
                            )}
                            <span className="text-[10px] text-slate-600">×{entry.serves}</span>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>
            )
          })}
      </div>

      {/* Voice hint */}
      <div
        className="mx-5 mb-3 px-4 py-2 rounded-xl text-center"
        style={{ background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)' }}
      >
        <p className="text-[11px] text-violet-400/70">
          🎙️ "Generate a meal plan" · "Add meals to calendar" · "Build a grocery list"
        </p>
      </div>
    </div>
  )
}
