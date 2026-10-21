import { useEffect, useState } from 'react'

interface AppStatus {
  google_calendar_connected: boolean
  google_login_url: string
}

export function useStatus() {
  const [status, setStatus] = useState<AppStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()
      setStatus(data)
    } catch (e) {
      console.error('Status fetch failed:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    // Re-check every 10s in case user just connected
    const interval = setInterval(fetchStatus, 10000)
    return () => clearInterval(interval)
  }, [])

  return { status, loading, refetch: fetchStatus }
}
