import { useState } from 'react'
import { useFamilyProfile, type FamilyMember, type FamilyPrefs } from '../hooks/useAppData'

const RESTRICTION_COLORS: Record<string, { color: string; bg: string }> = {
  vegetarian:  { color: 'text-emerald-400', bg: 'rgba(52,211,153,0.12)'  },
  vegan:       { color: 'text-green-400',   bg: 'rgba(74,222,128,0.12)'  },
  gluten: { color: 'text-amber-400',   bg: 'rgba(245,158,11,0.12)'  },
  'nut allergy': { color: 'text-red-400', bg: 'rgba(239,68,68,0.12)' },
  dairy:       { color: 'text-yellow-400',  bg: 'rgba(234,179,8,0.12)'   },
  halal:       { color: 'text-blue-400',    bg: 'rgba(96,165,250,0.12)'  },
  kosher:      { color: 'text-indigo-400',  bg: 'rgba(129,140,248,0.12)' },
}

function getRestrictionStyle(r: string) {
  const key = Object.keys(RESTRICTION_COLORS).find(k => r.toLowerCase().includes(k))
  return key ? RESTRICTION_COLORS[key] : { color: 'text-slate-400', bg: 'rgba(100,116,139,0.12)' }
}

function Avatar({ name }: { name: string; role: string }) {
  const initials = name.slice(0, 2).toUpperCase()
  const colors = [
    ['#8b5cf6', '#4f46e5'],
    ['#ec4899', '#8b5cf6'],
    ['#06b6d4', '#4f46e5'],
    ['#f59e0b', '#ef4444'],
    ['#10b981', '#4f46e5'],
  ]
  const idx = name.charCodeAt(0) % colors.length
  const [from, to] = colors[idx]
  return (
    <div
      className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 font-bold text-white text-sm shadow-glow-sm"
      style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
    >
      {initials}
    </div>
  )
}

function MemberCard({ member }: { member: FamilyMember }) {
  return (
    <div
      className="px-4 py-3.5 rounded-2xl transition-all hover:scale-[1.01]"
      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
    >
      <div className="flex items-start gap-3">
        <Avatar name={member.name} role={member.role} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-slate-100 font-semibold text-sm">{member.name}</p>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium text-slate-400"
              style={{ background: 'rgba(255,255,255,0.06)' }}
            >
              {member.role}{member.age ? ` · ${member.age}y` : ''}
            </span>
          </div>

          {member.dietary_restrictions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {member.dietary_restrictions.map(r => {
                const style = getRestrictionStyle(r)
                return (
                  <span
                    key={r}
                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-medium ${style.color}`}
                    style={{ background: style.bg }}
                  >
                    {r}
                  </span>
                )
              })}
            </div>
          )}

          <div className="mt-2 space-y-0.5">
            {member.likes.length > 0 && (
              <p className="text-[11px] text-slate-500">
                <span className="text-emerald-500">♥ </span>
                {member.likes.join(' · ')}
              </p>
            )}
            {member.dislikes.length > 0 && (
              <p className="text-[11px] text-slate-500">
                <span className="text-red-500">✕ </span>
                {member.dislikes.join(' · ')}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function PrefRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="flex items-center justify-between px-4 py-3 rounded-xl"
      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <span className="text-slate-500 text-xs">{label}</span>
      <span className="text-slate-200 text-sm font-medium">{value}</span>
    </div>
  )
}

function PrefsPanel({ prefs }: { prefs: FamilyPrefs }) {
  const mealIcons: Record<string, string> = { breakfast: '🍳', lunch: '🥗', dinner: '🍽️' }
  return (
    <div className="space-y-2">
      <PrefRow label="Planning" value={prefs.meals_to_plan.map(m => `${mealIcons[m] || ''} ${m}`).join('  ')} />
      <PrefRow label="Days ahead" value={`${prefs.plan_days_ahead} days`} />
      <PrefRow label="Breakfast" value={prefs.breakfast_time} />
      <PrefRow label="Lunch" value={prefs.lunch_time} />
      <PrefRow label="Dinner" value={prefs.dinner_time} />
      <PrefRow
        label="Cuisines"
        value={prefs.preferred_cuisines.length > 0 ? prefs.preferred_cuisines.join(' · ') : 'Any'}
      />
      <div
        className="flex items-center justify-between px-4 py-3 rounded-xl"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <span className="text-slate-500 text-xs">Setup complete</span>
        <span className={`text-sm font-medium ${prefs.setup_complete ? 'text-emerald-400' : 'text-amber-400'}`}>
          {prefs.setup_complete ? '✓ Yes' : '○ No'}
        </span>
      </div>
    </div>
  )
}

export function FamilyPage() {
  const { data, loading, refetch } = useFamilyProfile()
  const [tab, setTab] = useState<'members' | 'prefs'>('members')

  const members = data?.members ?? []
  const prefs = data?.prefs ?? null

  return (
    <div className="flex flex-col flex-1 min-h-0 animate-fade-in">
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-center justify-between">
        <div>
          <h2 className="text-slate-100 font-bold text-lg">Family</h2>
          <p className="text-slate-500 text-xs">{members.length} member{members.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={refetch}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          ↻
        </button>
      </div>

      {/* Tabs */}
      <div className="px-5 mb-3">
        <div
          className="flex p-1 rounded-2xl gap-1"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          {(['members', 'prefs'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all duration-200 capitalize ${
                tab === t ? 'text-white' : 'text-slate-500 hover:text-slate-400'
              }`}
              style={tab === t
                ? { background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }
                : {}
              }
            >
              {t === 'members' ? `Members (${members.length})` : 'Meal Preferences'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        {loading && (
          <div className="space-y-3">
            {[1, 2].map(i => <div key={i} className="shimmer h-24 rounded-2xl" />)}
          </div>
        )}

        {/* Members tab */}
        {!loading && tab === 'members' && (
          members.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="text-5xl animate-float">👨‍👩‍👧</div>
              <div className="text-center">
                <p className="text-slate-300 font-medium">No family members yet</p>
                <p className="text-slate-600 text-sm mt-1">Add family members by voice</p>
              </div>
              <div
                className="px-5 py-3 rounded-2xl space-y-1.5 w-full"
                style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)' }}
              >
                <p className="text-[11px] text-violet-400/70 text-center">
                  "Add Priya as an adult, she's vegetarian"
                </p>
                <p className="text-[11px] text-violet-400/70 text-center">
                  "Add Arjun as a child, age 8, he hates broccoli"
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {members.map(m => <MemberCard key={m.id} member={m} />)}
            </div>
          )
        )}

        {/* Prefs tab */}
        {!loading && tab === 'prefs' && (
          !prefs ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="text-5xl animate-float">⚙️</div>
              <div className="text-center">
                <p className="text-slate-300 font-medium">No preferences set</p>
                <p className="text-slate-600 text-sm mt-1">Set them up by voice</p>
              </div>
              <div
                className="px-5 py-3 rounded-2xl w-full"
                style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)' }}
              >
                <p className="text-[11px] text-violet-400/70 text-center">
                  "Plan dinners for 7 days, dinner at 6:30pm, we like Italian and Asian"
                </p>
              </div>
            </div>
          ) : (
            <PrefsPanel prefs={prefs} />
          )
        )}
      </div>

      {/* Voice hint */}
      <div
        className="mx-5 mb-3 px-4 py-2 rounded-xl text-center"
        style={{ background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)' }}
      >
        <p className="text-[11px] text-violet-400/70">
          🎙️ Manage your family profile by voice
        </p>
      </div>
    </div>
  )
}
