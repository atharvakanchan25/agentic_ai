import { useState, useEffect } from 'react'
import './Toast.css'

let toastId = 0
const toastListeners = []

export const showToast = (message, type = 'info') => {
  toastListeners.forEach(listener => listener({ id: toastId++, message, type }))
}

function Toast() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const listener = (toast) => {
      setToasts(prev => [...prev, toast])
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id))
      }, 3000)
    }
    toastListeners.push(listener)
    return () => {
      const index = toastListeners.indexOf(listener)
      if (index > -1) toastListeners.splice(index, 1)
    }
  }, [])

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div key={toast.id} className={`toast toast-${toast.type}`}>
          <span className="toast-icon">
            {toast.type === 'success' && '✓'}
            {toast.type === 'error' && '✕'}
            {toast.type === 'info' && 'ℹ'}
          </span>
          <span className="toast-message">{toast.message}</span>
        </div>
      ))}
    </div>
  )
}

export default Toast
