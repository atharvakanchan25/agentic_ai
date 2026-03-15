import { useState, useEffect } from 'react'
import { getDepartments, generateTimetable } from '../api/client'
import './TimetablePage.css'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

const METRICS_CONFIG = [
  { key: 'total_assignments', label: 'Total Assignments', icon: '📋', tooltip: 'Total subject-division-room-slot assignments' },
  { key: 'conflicts_found',   label: 'Conflicts Found',   icon: '⚠️', tooltip: 'Scheduling conflicts detected and resolved' },
  { key: 'solve_time',        label: 'Solve Time',        icon: '⏱️', tooltip: 'Time taken by the CP-SAT solver' },
  { key: 'score',             label: 'Quality Score',     icon: '⭐', tooltip: 'Overall timetable quality (0–100)' },
]

export default function TimetablePage() {
  const [departments, setDepartments]   = useState([])
  const [selectedDepts, setSelectedDepts] = useState([])
  const [result, setResult]             = useState(null)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [viewDivision, setViewDivision] = useState('')
  const [activeTab, setActiveTab]       = useState('timetable')

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
      setActiveTab('timetable')
    } catch (err) {
      setError(err.response?.data?.detail || 'Generation failed. Check that all required data is added.')
    } finally {
      setLoading(false)
    }
  }

  const toggleDept = (id) =>
    setSelectedDepts(prev => prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id])

  const buildGrid = (timetable, division) => {
    const entries = timetable.filter(e => e.division_name === division)
    const slots   = [...new Set(entries.map(e => e.slot_number))].sort((a, b) => a - b)
    const grid    = {}
    entries.forEach(e => { grid[`${e.day}_${e.slot_number}`] = e })
    return { slots, grid }
  }

  const divisions = result?.timetable
    ? [...new Set(result.timetable.map(e => e.division_name))]
    : []

  const metricValues = result ? {
    total_assignments: result.total_assignments,
    conflicts_found:   result.conflicts_found,
    solve_time:        `${result.solve_time?.toFixed(2)}s`,
    score:             `${result.report?.performance_metrics?.overall_score ?? '—'}%`,
  } : {}

  return (
    <div className="tt-page">

      {/* ── Controls ── */}
      <div className="card tt-controls">
        <h3>📅 Generate Timetable</h3>
        {departments.length === 0 ? (
          <div className="empty-state" style={{padding: '16px 0'}}>
            <span className="empty-state-icon">🏛️</span>
            <span>No departments found — add data in the Data tab first</span>
          </div>
        ) : (
          <div className="dept-checkboxes">
            {departments.map(d => (
              <label
                key={d.id}
                className={`dept-check ${selectedDepts.includes(d.id) ? 'checked' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedDepts.includes(d.id)}
                  onChange={() => toggleDept(d.id)}
                />
                {d.name} <span className="badge badge-gray">{d.code}</span>
              </label>
            ))}
          </div>
        )}
        <button
          className="btn-generate"
          onClick={handleGenerate}
          disabled={loading || !selectedDepts.length}
        >
          {loading ? <><span className="spinner" /> Generating…</> : '⚡ Generate Timetable'}
        </button>
        {error && <p className="error-msg">⚠ {error}</p>}
      </div>

      {/* ── Results ── */}
      {result && (
        <div className="fade-in">

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
              <div className="metrics-row" style={{marginTop: 12}}>
                {METRICS_CONFIG.map(m => (
                  <div key={m.key} className="metric-card card" data-tooltip={m.tooltip}>
                    <div className="metric-value">{m.icon} {metricValues[m.key]}</div>
                    <div className="metric-label">{m.label}</div>
                  </div>
                ))}
              </div>

              {/* Tabs */}
              <div className="result-tabs" style={{marginTop: 12}}>
                {[
                  { id: 'timetable', label: '📅 Timetable' },
                  { id: 'insights',  label: '💡 Insights' },
                  { id: 'agents',    label: '🤖 Agent Log' },
                ].map(t => (
                  <button
                    key={t.id}
                    className={`section-tab ${activeTab === t.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* ── Timetable Grid ── */}
              {activeTab === 'timetable' && (
                <div className="card" style={{marginTop: 12}}>
                  <div className="division-selector">
                    <label>👥 Division:</label>
                    <select value={viewDivision} onChange={e => setViewDivision(e.target.value)}>
                      {divisions.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    <span className="badge badge-purple" style={{marginLeft: 'auto'}}>
                      {result.timetable.filter(e => e.division_name === viewDivision).length} classes
                    </span>
                  </div>

                  {viewDivision && (() => {
                    const { slots, grid } = buildGrid(result.timetable, viewDivision)
                    return (
                      <div className="tt-grid-wrapper">
                        <table className="tt-grid">
                          <thead>
                            <tr>
                              <th>Time</th>
                              {DAYS.map(d => <th key={d}>{d}</th>)}
                            </tr>
                          </thead>
                          <tbody>
                            {slots.map(slot => {
                              const sample = result.timetable.find(e => e.slot_number === slot)
                              return (
                                <tr key={slot}>
                                  <td className="slot-label">
                                    {sample?.start_time && sample?.end_time
                                      ? `${sample.start_time}–${sample.end_time}`
                                      : `Slot ${slot}`}
                                  </td>
                                  {DAYS.map(day => {
                                    const entry = grid[`${day}_${slot}`]
                                    return (
                                      <td key={day} className={entry ? 'has-class' : ''}>
                                        {entry ? (
                                          <div
                                            className={`class-cell ${entry.is_lab ? 'lab' : ''}`}
                                            data-tooltip={entry.faculty_name ? `Faculty: ${entry.faculty_name}` : undefined}
                                          >
                                            <div className="class-subject">{entry.subject_name}</div>
                                            <div className="class-room">🏫 {entry.room_number}</div>
                                          </div>
                                        ) : (
                                          <span className="free-slot">—</span>
                                        )}
                                      </td>
                                    )
                                  })}
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* ── Insights ── */}
              {activeTab === 'insights' && (
                <div className="card" style={{marginTop: 12}}>
                  <h4 style={{marginBottom: 12, fontWeight: 700}}>💡 Analytics Insights</h4>
                  {(result.report?.insights || []).length > 0 ? (
                    <ul className="insights-list">
                      {result.report.insights.map((ins, i) => <li key={i}>{ins}</li>)}
                    </ul>
                  ) : (
                    <p style={{color: 'var(--text-muted)', fontSize: 14}}>No insights available.</p>
                  )}

                  <h4 style={{marginTop: 20, marginBottom: 10, fontWeight: 700}}>📊 Day Distribution</h4>
                  <div className="day-dist">
                    {Object.entries(result.report?.summary?.day_distribution || {}).map(([day, count]) => (
                      <div key={day} className="day-bar">
                        <span>{day.slice(0, 3)}</span>
                        <div className="bar" style={{width: `${Math.min(count * 10, 240)}px`}}>{count}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Agent Pipeline Log ── */}
              {activeTab === 'agents' && (
                <div className="card" style={{marginTop: 12}}>
                  <h4 style={{marginBottom: 12, fontWeight: 700}}>🤖 Agent Pipeline Log</h4>
                  <div className="pipeline-log">
                    {(result.pipeline_log || []).map((entry, i) => (
                      <div key={i} className={`log-entry ${entry.status}`}>
                        <span className="log-agent">🔹 {entry.agent}</span>
                        <span className="log-step">{entry.step}</span>
                        <span className={`badge ${entry.status === 'success' ? 'badge-green' : 'badge-red'}`}>
                          {entry.status === 'success' ? '✓' : '✗'} {entry.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Failure details */}
          {result.status === 'failed' && (
            <div className="card" style={{marginTop: 12}}>
              <h4 style={{marginBottom: 10, fontWeight: 700, color: 'var(--danger)'}}>⚠️ Issues Detected</h4>
              <ul className="insights-list">
                {(result.issues || result.errors || result.missing || []).map((issue, i) => (
                  <li key={i} style={{borderLeftColor: 'var(--danger)'}}>
                    {issue.message || issue}
                  </li>
                ))}
              </ul>
              {result.suggestions?.length > 0 && (
                <>
                  <h4 style={{marginTop: 16, marginBottom: 8, fontWeight: 700}}>💡 Suggestions</h4>
                  <ul className="insights-list">
                    {result.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Initial empty state */}
      {!result && !loading && (
        <div className="card">
          <div className="empty-state">
            <span className="empty-state-icon">📅</span>
            <span>No timetable generated yet</span>
            <span style={{fontSize: 12, color: 'var(--text-muted)'}}>
              Select departments above and click Generate Timetable
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
