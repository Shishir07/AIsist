import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { BottomNav } from './components/BottomNav'
import { VoicePage } from './pages/VoicePage'
import { PantryPage } from './pages/PantryPage'
import { GroceryPage } from './pages/GroceryPage'
import { MealPlanPage } from './pages/MealPlanPage'
import { FamilyPage } from './pages/FamilyPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-full flex flex-col max-w-lg mx-auto">
        {/* Header */}
        <header
          className="flex items-center px-5 py-3.5 flex-shrink-0"
          style={{
            background: 'rgba(8,8,24,0.7)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #8b5cf6, #4f46e5)' }}
            >
              <span className="text-sm">✨</span>
            </div>
            <span className="font-bold text-base gradient-text tracking-tight">AIsist4U</span>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 flex flex-col min-h-0">
          <Routes>
            <Route path="/"        element={<VoicePage />} />
            <Route path="/pantry"  element={<PantryPage />} />
            <Route path="/grocery" element={<GroceryPage />} />
            <Route path="/meals"   element={<MealPlanPage />} />
            <Route path="/family"  element={<FamilyPage />} />
          </Routes>
        </div>

        {/* Bottom navigation */}
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
