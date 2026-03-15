import { useState } from 'react'
import DataPage from './pages/DataPage'
import TimetablePage from './pages/TimetablePage'
import ChatPage from './pages/ChatPage'
import './App.css'

const TABS = ['Data', 'Timetable', 'Chat']

export default function App() {
  const [tab, setTab] = useState('Data')

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🎓</span>
            <span className="logo-text">Timetable AI</span>
            <span className="logo-sub">Multi-Agent Scheduling System</span>
          </div>
          <nav className="nav">
            {TABS.map(t => (
              <button
                key={t}
                className={`nav-btn ${tab === t ? 'active' : ''}`}
                onClick={() => setTab(t)}
              >
                {t}
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
