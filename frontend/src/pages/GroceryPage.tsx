import { useState } from 'react'
import { useGrocery, type GroceryItem } from '../hooks/useAppData'

export function GroceryPage() {
  const { data, loading, refetch } = useGrocery()
  const [justChecked, setJustChecked] = useState<Set<number>>(new Set())

  const items = data?.items ?? []
  const unbought = items.filter(i => !i.bought)
  const bought = items.filter(i => i.bought)
  const total = items.length
  const doneCount = bought.length
  const progress = total > 0 ? (doneCount / total) * 100 : 0

  const handleCheck = async (item: GroceryItem) => {
    if (item.bought) return
    setJustChecked(prev => new Set(prev).add(item.id))
    await fetch(`/api/grocery/${item.id}/bought`, { method: 'PATCH' })
    setTimeout(() => {
      refetch()
      setJustChecked(prev => { const s = new Set(prev); s.delete(item.id); return s })
    }, 600)
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 animate-fade-in">
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-center justify-between mb-1">
          <div>
            <h2 className="text-slate-100 font-bold text-lg">Grocery List</h2>
            <p className="text-slate-500 text-xs">
              {doneCount} of {total} item{total !== 1 ? 's' : ''} done
            </p>
          </div>
          <button
            onClick={refetch}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            ↻
          </button>
        </div>

        {/* Progress bar */}
        {total > 0 && (
          <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: 'linear-gradient(90deg, #8b5cf6, #4f46e5)',
              }}
            />
          </div>
        )}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        {loading && (
          <div className="space-y-2 mt-2">
            {[1,2,3,4].map(i => (
              <div key={i} className="shimmer h-14 rounded-xl" />
            ))}
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="text-5xl animate-float">🛒</div>
            <div className="text-center">
              <p className="text-slate-300 font-medium">Your grocery list is empty</p>
              <p className="text-slate-600 text-sm mt-1">Say "add milk to my grocery list"</p>
            </div>
          </div>
        )}

        {/* Unbought items */}
        {unbought.length > 0 && (
          <div className="space-y-2 mt-1">
            {unbought.map(item => (
              <GroceryRow
                key={item.id}
                item={item}
                checking={justChecked.has(item.id)}
                onCheck={() => handleCheck(item)}
              />
            ))}
          </div>
        )}

        {/* Divider */}
        {bought.length > 0 && unbought.length > 0 && (
          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
            <span className="text-[10px] text-slate-600 uppercase tracking-wider font-medium">
              Done · {bought.length}
            </span>
            <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
          </div>
        )}

        {/* Bought items */}
        {bought.length > 0 && (
          <div className="space-y-2">
            {bought.map(item => (
              <GroceryRow
                key={item.id}
                item={item}
                checking={false}
                onCheck={() => {}}
              />
            ))}
          </div>
        )}
      </div>

      {/* Voice hint */}
      <div
        className="mx-5 mb-3 px-4 py-2 rounded-xl text-center"
        style={{ background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)' }}
      >
        <p className="text-[11px] text-violet-400/70">
          🎙️ "Add eggs" · "Mark milk as bought" · "Clear bought items"
        </p>
      </div>
    </div>
  )
}

function GroceryRow({
  item,
  checking,
  onCheck,
}: {
  item: GroceryItem
  checking: boolean
  onCheck: () => void
}) {
  const done = item.bought || checking

  return (
    <button
      onClick={onCheck}
      disabled={item.bought}
      className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
        item.bought ? 'opacity-40 cursor-default' : 'hover:scale-[1.01] active:scale-[0.99] cursor-pointer'
      }`}
      style={{
        background: done ? 'rgba(52,211,153,0.06)' : 'rgba(255,255,255,0.04)',
        border: done ? '1px solid rgba(52,211,153,0.15)' : '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Checkbox */}
      <span
        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
          done
            ? 'border-emerald-400 bg-emerald-400 scale-110'
            : 'border-slate-600'
        }`}
      >
        {done && (
          <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
          </svg>
        )}
      </span>

      <span className={`flex-1 text-sm capitalize font-medium transition-all ${
        done ? 'line-through text-slate-500' : 'text-slate-100'
      }`}>
        {item.name}
      </span>

      {item.quantity && (
        <span className="text-[11px] text-slate-500 flex-shrink-0">{item.quantity}</span>
      )}
    </button>
  )
}
