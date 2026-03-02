import { useState } from 'react'
import './App.css'
import DataInput from './components/DataInput'
import ReviewData from './components/ReviewData'
import TimetableView from './components/TimetableView'
import Chatbot from './components/Chatbot'

function App() {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    departments: [],
    subjects: [],
    rooms: [],
    faculty: [],
    divisions: []
  })
  const [timetable, setTimetable] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showChatbot, setShowChatbot] = useState(false)

  const handleDataComplete = (data) => {
    setFormData(data)
    setCurrentStep(2)
  }

  const handleBackToInput = () => {
    setCurrentStep(1)
  }

  const handleGenerate = async (deptIds) => {
    setLoading(true)
    setCurrentStep(3)
    try {
      const response = await fetch('/api/generate-timetable/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ department_ids: deptIds })
      })
      const result = await response.json()
      setTimetable(result)
    } catch (error) {
      console.error('Error generating timetable:', error)
      setTimetable({ status: 'failed', error: error.message })
    }
    setLoading(false)
  }

  const handleStartOver = () => {
    setCurrentStep(1)
    setFormData({
      departments: [],
      subjects: [],
      rooms: [],
      faculty: [],
      divisions: []
    })
    setTimetable(null)
  }

  return (
    <div className="App">
      <header>
        <h1>University Timetable Management System</h1>
        <p>Automated Scheduling with AI-Powered Agents</p>
      </header>

      <div className="progress-bar">
        <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
          <div className="step-number">1</div>
          <div className="step-label">Input Data</div>
        </div>
        <div className="progress-line"></div>
        <div className={`step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
          <div className="step-number">2</div>
          <div className="step-label">Review & Verify</div>
        </div>
        <div className="progress-line"></div>
        <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
          <div className="step-number">3</div>
          <div className="step-label">Generate Timetable</div>
        </div>
      </div>
      
      <main>
        {currentStep === 1 && (
          <DataInput 
            initialData={formData}
            onComplete={handleDataComplete}
          />
        )}

        {currentStep === 2 && (
          <ReviewData 
            data={formData}
            onBack={handleBackToInput}
            onGenerate={handleGenerate}
            loading={loading}
          />
        )}

        {currentStep === 3 && (
          <TimetableView 
            data={timetable}
            loading={loading}
            onStartOver={handleStartOver}
          />
        )}
      </main>

      <button 
        className="chatbot-toggle"
        onClick={() => setShowChatbot(!showChatbot)}
        title="Open AI Assistant"
      >
        {showChatbot ? '×' : '💬'}
      </button>

      {showChatbot && <Chatbot onClose={() => setShowChatbot(false)} />}

      <footer>
        <p>Powered by Multi-Agent AI System | MCP Protocol | Constraint Programming</p>
      </footer>
    </div>
  )
}

export default App
