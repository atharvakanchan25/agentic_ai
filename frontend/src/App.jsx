import { useState, useEffect } from 'react'
import { ToastProvider } from './components/Toast'
import AuthPage      from './pages/AuthPage'
import DataPage      from './pages/DataPage'
import TimetablePage from './pages/TimetablePage'
import ChatPage      from './pages/ChatPage'
import SettingsPage  from './pages/SettingsPage'
import './App.css'

const TABS = [
  { id: 'Data',      icon: '🗂️',  label: 'Data',      tooltip: 'Manage entities' },
  { id: 'Timetable', icon: '📅',  label: 'Timetable', tooltip: 'Generate & view schedule' },
  { id: 'Chat',      icon: '💬',  label: 'Chat',      tooltip: 'Ask the AI assistant' },
  { id: 'Settings',  icon: '⚙️',  label: 'Settings',  tooltip: 'Preferences & account' },
]

export default function App() {
  // ── Session persistence ──
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tt_user')) || null } catch { return null }
  })

  // ── Dark mode persistence ──
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('tt_dark') === 'true')

  const [tab, setTab] = useState('Data')

  // Apply dark mode token to <html>
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
    localStorage.setItem('tt_dark', darkMode)
  }, [darkMode])

  const handleAuth = (u) => {
    setUser(u)
    localStorage.setItem('tt_user', JSON.stringify(u))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('tt_user')
    setTab('Data')
  }

  if (!user) {
    return (
      <ToastProvider>
        <AuthPage onAuth={handleAuth} />
      </ToastProvider>
    )
  }

  return (
    <ToastProvider>
      <div className="app">
        <header className="header">
          <div className="header-inner">
            <div className="logo">
              <div className="logo-icon">🎓</div>
              <span className="logo-text">Timetable AI</span>
              <span className="logo-sub">Multi-Agent Scheduling</span>
            </div>

            <nav className="nav">
              {TABS.map(t => (
                <button
                  key={t.id}
                  className={`nav-btn ${tab === t.id ? 'active' : ''}`}
                  onClick={() => setTab(t.id)}
                  data-tooltip={t.tooltip}
                >
                  <span className="nav-icon">{t.icon}</span>
                  {t.label}
                </button>
              ))}
            </nav>

            <div className="header-user">
              <button
                className="dark-toggle"
                onClick={() => setDarkMode(d => !d)}
                data-tooltip={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                aria-label="Toggle dark mode"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
              <div
                className="user-avatar"
                data-tooltip={user.email}
                onClick={() => setTab('Settings')}
                style={{cursor:'pointer'}}
              >
                {user.name?.[0]?.toUpperCase() || '?'}
              </div>
              <span className="user-name">{user.name}</span>
              <button className="btn-logout" onClick={handleLogout} data-tooltip="Sign out">
                ⎋ Logout
              </button>
            </div>
          </div>
        </header>

        <main className="main">
          {tab === 'Data'      && <DataPage />}
          {tab === 'Timetable' && <TimetablePage />}
          {tab === 'Chat'      && <ChatPage />}
          {tab === 'Settings'  && (
            <SettingsPage
              user={user}
              darkMode={darkMode}
              onToggleDark={() => setDarkMode(d => !d)}
              onLogout={handleLogout}
            />
          )}
        </main>
      </div>
    </ToastProvider>
  )
}
