import { useState, useEffect } from 'react'
import { getDepartments, generateTimetable } from '../api/client'
import './TimetablePage.css'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

export default function TimetablePage() {
  const [departments, setDepartments] = useState([])
  const [selectedDepts, setSelectedDepts] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [viewDivision, setViewDivision] = useState('')
  const [activeTab, setActiveTab] = useState('timetable')

  useEffect(() => {
    getDepartments().then(r => {
      setDepartments(r.data)
      setSelectedDepts(r.data.map(d => d.id))
    }).catch(() => {})
  }, [])

  const handleGenerate = async () => {
    if (!selectedDepts.length) { setError('Select at least one department'); return }
    setError(''); setLoading(true); setResult(null)
    try {
      const res = await generateTimetable(selectedDepts)
      setResult(res.data)
      if (res.data.timetable?.length) {
        const divs = [...new Set(res.data.timetable.map(e => e.division_name))]
        setViewDivision(divs[0] || '')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const toggleDept = (id) => {
    setSelectedDepts(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  // Build grid: rows = slots, cols = days
  const buildGrid = (timetable, division) => {
    const entries = timetable.filter(e => e.division_name === division)
    const slots = [...new Set(entries.map(e => e.slot_number))].sort((a, b) => a - b)
    const grid = {}
    entries.forEach(e => {
      const key = `${e.day}_${e.slot_number}`
      grid[key] = e
    })
    return { slots, grid }
  }

  const divisions = result?.timetable
    ? [...new Set(result.timetable.map(e => e.division_name))]
    : []

  return (
    <div className="tt-page">
      {/* Controls */}
      <div className="card tt-controls">
        <h3>Generate Timetable</h3>
        <div className="dept-checkboxes">
          {departments.map(d => (
            <label key={d.id} className="dept-check">
              <input
                type="checkbox"
                checked={selectedDepts.includes(d.id)}
                onChange={() => toggleDept(d.id)}
              />
              {d.name} ({d.code})
            </label>
          ))}
        </div>
        <button className="btn-generate" onClick={handleGenerate} disabled={loading}>
          {loading ? '⏳ Generating...' : '⚡ Generate Timetable'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Status bar */}
          <div className={`status-bar ${result.status === 'success' ? 'success' : 'failed'}`}>
            {result.status === 'success'
              ? `✅ Generated ${result.total_assignments} assignments in ${result.generation_time}s — Solver: ${result.solver_status}`
              : `❌ Failed at stage: ${result.stage} — ${result.message || ''}`
            }
          </div>

          {result.status === 'success' && (
            <>
              {/* Metrics */}
              <div className="metrics-row">
                {[
                  ['Total Assignments', result.total_assignments],
                  ['Conflicts Found', result.conflicts_found],
                  ['Solve Time', `${result.solve_time?.toFixed(2)}s`],
                  ['Overall Score', `${result.report?.performance_metrics?.overall_score ?? '-'}%`]
                ].map(([label, value]) => (
                  <div key={label} className="metric-card card">
                    <div className="metric-value">{value}</div>
                    <div className="metric-label">{label}</div>
                  </div>
                ))}
              </div>

              {/* Tabs */}
              <div className="result-tabs">
                {['timetable', 'insights', 'agents'].map(t => (
                  <button
                    key={t}
                    className={`section-tab ${activeTab === t ? 'active' : ''}`}
                    onClick={() => setActiveTab(t)}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>

              {/* Timetable Grid */}
              {activeTab === 'timetable' && (
                <div className="card">
                  <div className="division-selector">
                    <label>Division:</label>
                    <select value={viewDivision} onChange={e => setViewDivision(e.target.value)}>
                      {divisions.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>

                  {viewDivision && (() => {
                    const { slots, grid } = buildGrid(result.timetable, viewDivision)
                    return (
                      <div className="tt-grid-wrapper">
                        <table className="tt-grid">
                          <thead>
                            <tr>
                              <th>Slot</th>
                              {DAYS.map(d => <th key={d}>{d}</th>)}
                            </tr>
                          </thead>
                          <tbody>
                            {slots.map(slot => (
                              <tr key={slot}>
                                <td className="slot-label">
                                  {result.timetable.find(e => e.slot_number === slot)?.start_time || slot}
                                </td>
                                {DAYS.map(day => {
                                  const entry = grid[`${day}_${slot}`]
                                  return (
                                    <td key={day} className={entry ? 'has-class' : ''}>
                                      {entry ? (
                                        <div className={`class-cell ${entry.is_lab ? 'lab' : ''}`}>
                                          <div className="class-subject">{entry.subject_name}</div>
                                          <div className="class-room">🏫 {entry.room_number}</div>
                                        </div>
                                      ) : <span className="free-slot">—</span>}
                                    </td>
                                  )
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* Insights */}
              {activeTab === 'insights' && (
                <div className="card">
                  <h4>Analytics Insights</h4>
                  <ul className="insights-list">
                    {(result.report?.insights || []).map((ins, i) => (
                      <li key={i}>💡 {ins}</li>
                    ))}
                  </ul>
                  <h4 style={{marginTop: 16}}>Day Distribution</h4>
                  <div className="day-dist">
                    {Object.entries(result.report?.summary?.day_distribution || {}).map(([day, count]) => (
                      <div key={day} className="day-bar">
                        <span>{day.slice(0,3)}</span>
                        <div className="bar" style={{width: `${Math.min(count * 8, 200)}px`}}>{count}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Pipeline Log */}
              {activeTab === 'agents' && (
                <div className="card">
                  <h4>Agent Pipeline Log</h4>
                  <div className="pipeline-log">
                    {(result.pipeline_log || []).map((entry, i) => (
                      <div key={i} className={`log-entry ${entry.status}`}>
                        <span className="log-agent">{entry.agent}</span>
                        <span className="log-step">{entry.step}</span>
                        <span className={`badge ${entry.status === 'success' ? 'badge-green' : 'badge-red'}`}>
                          {entry.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Failure details */}
          {result.status === 'failed' && result.issues && (
            <div className="card">
              <h4>Issues</h4>
              <ul className="insights-list">
                {result.issues.map((issue, i) => (
                  <li key={i}>⚠️ {issue.message || issue}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
