import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api/client'
import './ChatPage.css'

const SUGGESTIONS = [
  'generate timetable',
  'show departments',
  'show subjects',
  'show rooms',
  'show faculty',
  'show divisions'
]

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hi! I'm the Timetable AI assistant. I can generate timetables and show you data. Try: 'generate timetable' or 'show departments'." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg) return

    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setInput('')
    setLoading(true)

    try {
      const res = await sendChat(msg)
      const data = res.data
      let botText = data.reply

      if (data.action === 'timetable_generated' && data.data?.status === 'success') {
        botText += `\n\n📊 Generated ${data.data.total_assignments} assignments in ${data.data.generation_time}s.`
      } else if (data.action === 'show_data' && data.data) {
        botText += `\n\n${data.data.map(d => `• ${d.name || d.room_number || d.employee_id}`).join('\n')}`
      }

      setMessages(prev => [...prev, { role: 'bot', text: botText }])
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: 'Something went wrong. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <div className="card chat-container">
        <div className="chat-header">
          <span>🤖 Timetable AI Assistant</span>
          <span className="online-dot">● Online</span>
        </div>

        <div className="chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="message bot">
              <div className="bubble typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="suggestions">
          {SUGGESTIONS.map(s => (
            <button key={s} className="suggestion-chip" onClick={() => send(s)}>{s}</button>
          ))}
        </div>

        <div className="chat-input-row">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Type a message..."
            disabled={loading}
          />
          <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
