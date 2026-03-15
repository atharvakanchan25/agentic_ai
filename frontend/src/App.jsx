import { useState } from 'react'
import DataPage from './pages/DataPage'
import TimetablePage from './pages/TimetablePage'
import ChatPage from './pages/ChatPage'
import './App.css'

const TABS = [
  { id: 'Data',      icon: '🗂️',  label: 'Data' },
  { id: 'Timetable', icon: '📅',  label: 'Timetable' },
  { id: 'Chat',      icon: '💬',  label: 'Chat' },
]

export default function App() {
  const [tab, setTab] = useState('Data')

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
                data-tooltip={t.id === 'Data' ? 'Manage entities' : t.id === 'Timetable' ? 'Generate & view schedule' : 'Ask the AI assistant'}
              >
                <span className="nav-icon">{t.icon}</span>
                {t.label}
              </button>
            ))}
          </nav>
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
