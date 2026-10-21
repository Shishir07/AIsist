/**
 * Hooks for Phase 2+3 data: family profile, pantry, grocery, meal plan.
 * All data comes from the agent's tools via REST endpoints.
 */
import { useEffect, useState, useCallback } from 'react'

// ─── Types ─────────────────────────────────────────────────────────────────

export interface FamilyMember {
  id: number
  name: string
  role: 'adult' | 'child'
  age?: number
  dietary_restrictions: string[]
  likes: string[]
  dislikes: string[]
}

export interface FamilyPrefs {
  meals_to_plan: string[]
  plan_days_ahead: number
  dinner_time: string
  lunch_time: string
  breakfast_time: string
  preferred_cuisines: string[]
  setup_complete: boolean
}

export interface FamilyProfile {
  members: FamilyMember[]
  prefs: FamilyPrefs | null
}

export interface PantryItem {
  id: number
  name: string
  quantity: string
  category?: string
  primary_nutrient?: string
  updated_at: string
}

export interface GroceryItem {
  id: number
  name: string
  quantity?: string
  bought: boolean
}

export interface MealPlanEntry {
  id: number
  date: string
  meal_type: string
  recipe_name: string
  description?: string
  serves: number
  calendar_event_id?: string
}

// ─── Generic fetcher ───────────────────────────────────────────────────────

function useFetch<T>(url: string, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
      setError(null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => {
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchData, ...deps])

  return { data, loading, error, refetch: fetchData }
}

// ─── Hooks ──────────────────────────────────────────────────────────────────

export function useFamilyProfile() {
  return useFetch<FamilyProfile>('/api/family')
}

export function usePantry() {
  return useFetch<{ items: PantryItem[] }>('/api/pantry')
}

export function useGrocery() {
  return useFetch<{ items: GroceryItem[] }>('/api/grocery')
}

export function useMealPlan(days = 7) {
  return useFetch<{ entries: MealPlanEntry[] }>(`/api/meal-plan?days=${days}`)
}
