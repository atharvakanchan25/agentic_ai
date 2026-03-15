import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api/client'
import './ChatPage.css'

const SUGGESTIONS = [
  { label: '⚡ Generate timetable', value: 'generate timetable' },
  { label: '🏛️ Departments',        value: 'show departments' },
  { label: '📚 Subjects',           value: 'show subjects' },
  { label: '🚪 Rooms',              value: 'show rooms' },
  { label: '👨🏫 Faculty',           value: 'show faculty' },
  { label: '👥 Divisions',          value: 'show divisions' },
]

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: "Hi! I'm the Timetable AI assistant 🤖\n\nI can generate timetables and show you data. Try one of the suggestions below or type your own message.",
      time: new Date()
    }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef             = useRef(null)
  const inputRef              = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return

    const userMsg = { role: 'user', text: msg, time: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res  = await sendChat(msg)
      const data = res.data
      let botText = data.reply

      if (data.action === 'timetable_generated' && data.data?.status === 'success') {
        botText += `\n\n📊 Generated ${data.data.total_assignments} assignments in ${data.data.generation_time}s.\nSwitch to the Timetable tab to view the full schedule.`
      } else if (data.action === 'show_data' && Array.isArray(data.data) && data.data.length > 0) {
        botText += '\n\n' + data.data
          .map(d => `• ${d.name || d.room_number || d.employee_id}`)
          .join('\n')
      }

      setMessages(prev => [...prev, { role: 'bot', text: botText, time: new Date() }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: '⚠️ Something went wrong. Please check the backend is running and try again.',
        time: new Date()
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="chat-page">
      <div className="card chat-container">

        {/* ── Header ── */}
        <div className="chat-header">
          <span>🤖 Timetable AI Assistant</span>
          <div className="online-indicator">
            <span className="online-dot" />
            Online
          </div>
        </div>

        {/* ── Messages ── */}
        <div className="chat-messages" role="log" aria-live="polite">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role} fade-in`}>
              <div className="message-meta">
                {m.role === 'bot' ? '🤖 Assistant' : '👤 You'} · {formatTime(m.time)}
              </div>
              <div className="bubble">{m.text}</div>
            </div>
          ))}

          {loading && (
            <div className="message bot">
              <div className="message-meta">🤖 Assistant · typing…</div>
              <div className="bubble typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* ── Suggestions ── */}
        <div className="suggestions">
          <span className="suggestions-label">Quick actions</span>
          {SUGGESTIONS.map(s => (
            <button
              key={s.value}
              className="suggestion-chip"
              onClick={() => send(s.value)}
              disabled={loading}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* ── Input ── */}
        <div className="chat-input-row">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Type a message… (Enter to send)"
            disabled={loading}
            aria-label="Chat message input"
          />
          <button
            className="send-btn"
            onClick={() => send()}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            Send ➤
          </button>
        </div>
      </div>
    </div>
  )
}
