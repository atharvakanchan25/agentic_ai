import { createContext, useContext, useState, useCallback } from 'react'
import './Toast.css'

const ToastContext = createContext(null)

export function useToast() {
  return useContext(ToastContext)
}

let _id = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((message, type = 'info', duration = 3500) => {
    const id = ++_id
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
  }, [])

  const dismiss = (id) => setToasts(prev => prev.filter(t => t.id !== id))

  const ICONS = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="toast-container" role="region" aria-label="Notifications">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type} fade-in`} role="alert">
            <span className="toast-icon">{ICONS[t.type]}</span>
            <span className="toast-msg">{t.message}</span>
            <button className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss">✕</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
