import { useState } from 'react'
import AuthPage from './pages/AuthPage'
import DataPage from './pages/DataPage'
import TimetablePage from './pages/TimetablePage'
import ChatPage from './pages/ChatPage'
import './App.css'

const TABS = [
  { id: 'Data',      icon: '🗂️',  label: 'Data',      tooltip: 'Manage entities' },
  { id: 'Timetable', icon: '📅',  label: 'Timetable', tooltip: 'Generate & view schedule' },
  { id: 'Chat',      icon: '💬',  label: 'Chat',      tooltip: 'Ask the AI assistant' },
]

export default function App() {
  const [user, setUser] = useState(null)   // null = not authenticated
  const [tab,  setTab]  = useState('Data')

  if (!user) {
    return <AuthPage onAuth={u => setUser(u)} />
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🎓</span>
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
            <div className="user-avatar" data-tooltip={user.email}>
              {user.name?.[0]?.toUpperCase() || '?'}
            </div>
            <span className="user-name">{user.name}</span>
            <button
              className="btn-logout"
              onClick={() => setUser(null)}
              data-tooltip="Sign out"
            >
              ⎋ Logout
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        {tab === 'Data'      && <DataPage />}
        {tab === 'Timetable' && <TimetablePage />}
        {tab === 'Chat'      && <ChatPage />}
      </main>
    </div>
  )
}
