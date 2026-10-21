import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',        icon: '🎙️', label: 'Voice'   },
  { to: '/pantry',  icon: '🧺', label: 'Pantry'  },
  { to: '/grocery', icon: '🛒', label: 'Grocery' },
  { to: '/meals',   icon: '🍽️', label: 'Meals'   },
  { to: '/family',  icon: '👨‍👩‍👧', label: 'Family'  },
]

export function BottomNav() {
  return (
    <nav
      className="flex flex-shrink-0 pb-safe"
      style={{
        background: 'rgba(8,8,24,0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {links.map(({ to, icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center py-2.5 gap-1 text-[10px] font-medium transition-all duration-200 ${
              isActive
                ? 'text-violet-400'
                : 'text-slate-600 hover:text-slate-400'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <span
                className={`text-xl leading-none transition-transform duration-200 ${
                  isActive ? 'scale-110' : 'scale-100'
                }`}
              >
                {icon}
              </span>
              <span className={isActive ? 'text-violet-400' : ''}>{label}</span>
              {/* Active dot indicator */}
              {isActive && (
                <span
                  className="w-1 h-1 rounded-full"
                  style={{ background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }}
                />
              )}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
