import { useState, useRef, useEffect } from 'react'

function Chatbot({ onClose }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I am your timetable assistant. I can help you add data, generate timetables, or answer questions. Try saying "help" to see what I can do.' }
  ])
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      })
      const data = await response.json()

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: data.message,
        data: data.data,
        action: data.action
      }])

      if (data.timetable_result) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: 'Timetable generated successfully! Check the main view for details.',
          timetable: data.timetable_result
        }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: 'Sorry, I encountered an error. Please try again.' 
      }])
    }

    setLoading(false)
  }

  const handleInputChange = async (e) => {
    const value = e.target.value
    setInput(value)

    if (value.length > 2) {
      try {
        const response = await fetch(`/api/chat/suggestions/?partial=${encodeURIComponent(value)}`)
        const data = await response.json()
        setSuggestions(data.suggestions || [])
      } catch (error) {
        setSuggestions([])
      }
    } else {
      setSuggestions([])
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion)
    setSuggestions([])
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickActions = [
    'Add a department',
    'Add a subject',
    'Generate timetable',
    'Show all data',
    'Help'
  ]

  return (
    <div className="chatbot-overlay">
      <div className="chatbot-container">
        <div className="chatbot-header">
          <div>
            <h3>Timetable Assistant</h3>
            <span className="status-indicator">Online</span>
          </div>
          <button className="close-chat-btn" onClick={onClose}>×</button>
        </div>

        <div className="chatbot-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <p>{msg.text}</p>
                {msg.data && (
                  <div className="message-data">
                    <pre>{JSON.stringify(msg.data, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-content typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="quick-actions">
          {quickActions.map((action, idx) => (
            <button 
              key={idx} 
              className="quick-action-btn"
              onClick={() => {
                setInput(action)
                handleSend()
              }}
            >
              {action}
            </button>
          ))}
        </div>

        {suggestions.length > 0 && (
          <div className="suggestions">
            {suggestions.map((suggestion, idx) => (
              <div 
                key={idx} 
                className="suggestion-item"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </div>
            ))}
          </div>
        )}

        <div className="chatbot-input">
          <textarea
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (e.g., 'Add a new department' or 'Generate timetable')"
            rows="2"
          />
          <button onClick={handleSend} disabled={!input.trim() || loading}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default Chatbot
