import { useState } from 'react'
import { usePantry, type PantryItem } from '../hooks/useAppData'

const CATEGORY_META: Record<string, { emoji: string; color: string; bg: string }> = {
  protein:    { emoji: '🥩', color: 'text-rose-400',    bg: 'rgba(244,63,94,0.12)'   },
  grain:      { emoji: '🌾', color: 'text-amber-400',   bg: 'rgba(245,158,11,0.12)'  },
  vegetable:  { emoji: '🥦', color: 'text-emerald-400', bg: 'rgba(52,211,153,0.12)'  },
  fruit:      { emoji: '🍎', color: 'text-red-400',     bg: 'rgba(239,68,68,0.12)'   },
  dairy:      { emoji: '🧀', color: 'text-yellow-400',  bg: 'rgba(234,179,8,0.12)'   },
  condiment:  { emoji: '🫙', color: 'text-orange-400',  bg: 'rgba(249,115,22,0.12)'  },
  spice:      { emoji: '🧂', color: 'text-pink-400',    bg: 'rgba(236,72,153,0.12)'  },
  beverage:   { emoji: '☕', color: 'text-brown-400',   bg: 'rgba(120,80,40,0.2)'    },
  other:      { emoji: '📦', color: 'text-slate-400',   bg: 'rgba(100,116,139,0.12)' },
}

function groupByCategory(items: PantryItem[]) {
  const groups: Record<string, PantryItem[]> = {}
  for (const item of items) {
    const cat = item.category || 'other'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return groups
}

function SkeletonRow() {
  return <div className="shimmer h-12 rounded-xl" />
}

export function PantryPage() {
  const { data, loading, refetch } = usePantry()
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const items = data?.items ?? []
  const categories = [...new Set(items.map(i => i.category || 'other'))].sort()

  const filtered = items.filter(i => {
    const matchSearch = !search || i.name.includes(search.toLowerCase())
    const matchCat = !activeCategory || (i.category || 'other') === activeCategory
    return matchSearch && matchCat
  })

  const grouped = groupByCategory(filtered)

  return (
    <div className="flex flex-col flex-1 min-h-0 animate-fade-in">
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-slate-100 font-bold text-lg">Pantry</h2>
            <p className="text-slate-500 text-xs">{items.length} ingredient{items.length !== 1 ? 's' : ''} tracked</p>
          </div>
          <button
            onClick={refetch}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            ↻
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">🔍</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search ingredients…"
            className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm text-slate-100 placeholder-slate-600 outline-none transition-all"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
            onFocus={e => (e.currentTarget.style.borderColor = 'rgba(139,92,246,0.5)')}
            onBlur={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)')}
          />
        </div>

        {/* Category chips */}
        {categories.length > 1 && (
          <div className="flex gap-2 mt-3 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setActiveCategory(null)}
              className={`flex-shrink-0 text-[11px] px-3 py-1 rounded-full transition-all font-medium ${
                !activeCategory
                  ? 'text-white'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
              style={!activeCategory
                ? { background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }
                : { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.06)' }
              }
            >
              All
            </button>
            {categories.map(cat => {
              const meta = CATEGORY_META[cat] || CATEGORY_META.other
              const isActive = activeCategory === cat
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(isActive ? null : cat)}
                  className={`flex-shrink-0 text-[11px] px-3 py-1 rounded-full transition-all font-medium flex items-center gap-1 ${
                    isActive ? meta.color : 'text-slate-500 hover:text-slate-300'
                  }`}
                  style={isActive
                    ? { background: meta.bg, border: `1px solid ${meta.bg}` }
                    : { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.06)' }
                  }
                >
                  {meta.emoji} {cat}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-5 pb-4 space-y-5">
        {loading && (
          <div className="space-y-2">
            {[1,2,3,4,5].map(i => <SkeletonRow key={i} />)}
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="text-5xl animate-float">🧺</div>
            <div className="text-center">
              <p className="text-slate-300 font-medium">Your pantry is empty</p>
              <p className="text-slate-600 text-sm mt-1">Say "add chicken breast to my pantry"</p>
            </div>
            <div
              className="px-4 py-2 rounded-xl text-xs text-slate-500"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              Try speaking to add ingredients
            </div>
          </div>
        )}

        {!loading && filtered.length === 0 && items.length > 0 && (
          <p className="text-slate-500 text-sm text-center py-8">No items match "{search}"</p>
        )}

        {Object.entries(grouped).sort().map(([cat, catItems]) => {
          const meta = CATEGORY_META[cat] || CATEGORY_META.other
          return (
            <div key={cat}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-bold uppercase tracking-wider ${meta.color}`}>
                  {meta.emoji} {cat}
                </span>
                <span className="text-slate-700 text-xs">({catItems.length})</span>
              </div>
              <div className="space-y-1.5">
                {catItems.map(item => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between px-3.5 py-2.5 rounded-xl transition-all hover:scale-[1.01]"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <span className="text-slate-100 text-sm capitalize font-medium">{item.name}</span>
                    <span
                      className={`text-[11px] px-2.5 py-1 rounded-full font-medium ${meta.color}`}
                      style={{ background: meta.bg }}
                    >
                      {item.quantity}
                    </span>
                  </div>
                ))}
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
          🎙️ Add or remove items by voice
        </p>
      </div>
    </div>
  )
}
