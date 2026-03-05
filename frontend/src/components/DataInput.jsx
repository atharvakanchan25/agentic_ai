import { useState } from 'react'
import { showToast } from './Toast'

function DataInput({ initialData, onComplete }) {
  const [activeTab, setActiveTab] = useState('departments')
  const [formData, setFormData] = useState(initialData)
  const [showForm, setShowForm] = useState(null)
  const [currentForm, setCurrentForm] = useState({})

  const openForm = (type) => {
    setShowForm(type)
    setCurrentForm({})
  }

  const closeForm = () => {
    setShowForm(null)
    setCurrentForm({})
  }

  const handleFormChange = (field, value) => {
    setCurrentForm(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (type) => {
    const newItem = { ...currentForm, id: Date.now() }
    setFormData(prev => ({
      ...prev,
      [type]: [...prev[type], newItem]
    }))
    showToast(`${type.slice(0, -1)} added successfully!`, 'success')
    closeForm()
  }

  const handleDelete = (type, id) => {
    if (confirm('Are you sure you want to delete this item?')) {
      setFormData(prev => ({
        ...prev,
        [type]: prev[type].filter(item => item.id !== id)
      }))
      showToast('Item deleted', 'info')
    }
  }

  const handleProceed = async () => {
    for (const dept of formData.departments) {
      await fetch('/api/departments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dept)
      })
    }

    for (const subj of formData.subjects) {
      await fetch('/api/subjects/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subj)
      })
    }

    for (const room of formData.rooms) {
      await fetch('/api/rooms/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(room)
      })
    }

    for (const fac of formData.faculty) {
      await fetch('/api/faculty/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fac)
      })
    }

    for (const div of formData.divisions) {
      await fetch('/api/divisions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(div)
      })
    }

    onComplete(formData)
  }

  const canProceed = formData.departments.length > 0 && 
                     formData.subjects.length > 0 && 
                     formData.rooms.length > 0 && 
                     formData.faculty.length > 0 && 
                     formData.divisions.length > 0

  return (
    <div className="data-input-container">
      <div className="input-header">
        <h2>Step 1: Input University Data</h2>
        <p>Please provide complete information for all categories</p>
      </div>

      <div className="tabs">
        <button 
          className={activeTab === 'departments' ? 'active' : ''} 
          onClick={() => setActiveTab('departments')}
        >
          Departments ({formData.departments.length})
        </button>
        <button 
          className={activeTab === 'subjects' ? 'active' : ''} 
          onClick={() => setActiveTab('subjects')}
        >
          Subjects ({formData.subjects.length})
        </button>
        <button 
          className={activeTab === 'rooms' ? 'active' : ''} 
          onClick={() => setActiveTab('rooms')}
        >
          Rooms ({formData.rooms.length})
        </button>
        <button 
          className={activeTab === 'faculty' ? 'active' : ''} 
          onClick={() => setActiveTab('faculty')}
        >
          Faculty ({formData.faculty.length})
        </button>
        <button 
          className={activeTab === 'divisions' ? 'active' : ''} 
          onClick={() => setActiveTab('divisions')}
        >
          Divisions ({formData.divisions.length})
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'departments' && (
          <div className="tab-panel">
            <div className="panel-header">
              <h3>Departments</h3>
              <button className="add-btn" onClick={() => openForm('departments')}>+ Add Department</button>
            </div>
            <div className="items-grid">
              {formData.departments.map(d => (
                <div key={d.id} className="item-card">
                  <div className="card-header">
                    <strong>{d.name}</strong>
                    <button className="delete-btn" onClick={() => handleDelete('departments', d.id)}>×</button>
                  </div>
                  <div className="card-body">
                    <span className="badge">{d.code}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'subjects' && (
          <div className="tab-panel">
            <div className="panel-header">
              <h3>Subjects</h3>
              <button className="add-btn" onClick={() => openForm('subjects')}>+ Add Subject</button>
            </div>
            <div className="items-grid">
              {formData.subjects.map(s => (
                <div key={s.id} className="item-card">
                  <div className="card-header">
                    <strong>{s.name}</strong>
                    <button className="delete-btn" onClick={() => handleDelete('subjects', s.id)}>×</button>
                  </div>
                  <div className="card-body">
                    <span className="badge">{s.code}</span>
                    <span className="info">{s.hours_per_week}h/week</span>
                    {s.is_lab && <span className="badge lab">LAB</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'rooms' && (
          <div className="tab-panel">
            <div className="panel-header">
              <h3>Rooms & Labs</h3>
              <button className="add-btn" onClick={() => openForm('rooms')}>+ Add Room</button>
            </div>
            <div className="items-grid">
              {formData.rooms.map(r => (
                <div key={r.id} className="item-card">
                  <div className="card-header">
                    <strong>Room {r.room_number}</strong>
                    <button className="delete-btn" onClick={() => handleDelete('rooms', r.id)}>×</button>
                  </div>
                  <div className="card-body">
                    <span className="info">Floor {r.floor}</span>
                    <span className="info">Capacity: {r.capacity}</span>
                    <span className="info">Benches: {r.bench_count}</span>
                    {r.is_lab && <span className="badge lab">LAB</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'faculty' && (
          <div className="tab-panel">
            <div className="panel-header">
              <h3>Faculty Members</h3>
              <button className="add-btn" onClick={() => openForm('faculty')}>+ Add Faculty</button>
            </div>
            <div className="items-grid">
              {formData.faculty.map(f => (
                <div key={f.id} className="item-card">
                  <div className="card-header">
                    <strong>{f.name}</strong>
                    <button className="delete-btn" onClick={() => handleDelete('faculty', f.id)}>×</button>
                  </div>
                  <div className="card-body">
                    <span className="badge">{f.employee_id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'divisions' && (
          <div className="tab-panel">
            <div className="panel-header">
              <h3>Student Divisions</h3>
              <button className="add-btn" onClick={() => openForm('divisions')}>+ Add Division</button>
            </div>
            <div className="items-grid">
              {formData.divisions.map(d => (
                <div key={d.id} className="item-card">
                  <div className="card-header">
                    <strong>{d.name}</strong>
                    <button className="delete-btn" onClick={() => handleDelete('divisions', d.id)}>×</button>
                  </div>
                  <div className="card-body">
                    <span className="info">Year {d.year}</span>
                    <span className="info">{d.student_count} students</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={closeForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add {showForm.slice(0, -1).charAt(0).toUpperCase() + showForm.slice(1, -1)}</h3>
              <button className="close-btn" onClick={closeForm}>×</button>
            </div>
            <div className="modal-body">
              {showForm === 'departments' && (
                <>
                  <input placeholder="Department Name" onChange={(e) => handleFormChange('name', e.target.value)} />
                  <input placeholder="Department Code" onChange={(e) => handleFormChange('code', e.target.value)} />
                </>
              )}
              {showForm === 'subjects' && (
                <>
                  <input placeholder="Subject Name" onChange={(e) => handleFormChange('name', e.target.value)} />
                  <input placeholder="Subject Code" onChange={(e) => handleFormChange('code', e.target.value)} />
                  <input type="number" placeholder="Hours per Week" onChange={(e) => handleFormChange('hours_per_week', parseInt(e.target.value))} />
                  <select onChange={(e) => handleFormChange('department_id', parseInt(e.target.value))}>
                    <option value="">Select Department</option>
                    {formData.departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                  <label>
                    <input type="checkbox" onChange={(e) => handleFormChange('is_lab', e.target.checked)} />
                    Is Lab Subject
                  </label>
                </>
              )}
              {showForm === 'rooms' && (
                <>
                  <input placeholder="Room Number" onChange={(e) => handleFormChange('room_number', e.target.value)} />
                  <input type="number" placeholder="Floor" onChange={(e) => handleFormChange('floor', parseInt(e.target.value))} />
                  <input type="number" placeholder="Capacity" onChange={(e) => handleFormChange('capacity', parseInt(e.target.value))} />
                  <input type="number" placeholder="Bench Count" onChange={(e) => handleFormChange('bench_count', parseInt(e.target.value))} />
                  <label>
                    <input type="checkbox" onChange={(e) => {
                      handleFormChange('is_lab', e.target.checked)
                      handleFormChange('room_type', e.target.checked ? 'Lab' : 'Classroom')
                    }} />
                    Is Lab Room
                  </label>
                </>
              )}
              {showForm === 'faculty' && (
                <>
                  <input placeholder="Faculty Name" onChange={(e) => handleFormChange('name', e.target.value)} />
                  <input placeholder="Employee ID" onChange={(e) => handleFormChange('employee_id', e.target.value)} />
                  <select onChange={(e) => handleFormChange('department_id', parseInt(e.target.value))}>
                    <option value="">Select Department</option>
                    {formData.departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </>
              )}
              {showForm === 'divisions' && (
                <>
                  <input placeholder="Division Name (e.g., CS-A)" onChange={(e) => handleFormChange('name', e.target.value)} />
                  <input type="number" placeholder="Year" onChange={(e) => handleFormChange('year', parseInt(e.target.value))} />
                  <input type="number" placeholder="Student Count" onChange={(e) => handleFormChange('student_count', parseInt(e.target.value))} />
                  <select onChange={(e) => handleFormChange('department_id', parseInt(e.target.value))}>
                    <option value="">Select Department</option>
                    {formData.departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeForm}>Cancel</button>
              <button className="btn-primary" onClick={() => handleSubmit(showForm)}>Add</button>
            </div>
          </div>
        </div>
      )}

      <div className="action-bar">
        <div className="summary">
          <h4>Data Summary</h4>
          <p>{formData.departments.length} Departments | {formData.subjects.length} Subjects | {formData.rooms.length} Rooms | {formData.faculty.length} Faculty | {formData.divisions.length} Divisions</p>
        </div>
        <button 
          className="proceed-btn" 
          onClick={handleProceed}
          disabled={!canProceed}
        >
          Proceed to Review
        </button>
      </div>
    </div>
  )
}

export default DataInput
