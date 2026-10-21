import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// StrictMode intentionally removed — it double-mounts effects in dev,
// causing two WebSocket connections and double TTS playback.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)
