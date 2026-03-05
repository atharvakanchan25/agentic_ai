function TimetableView({ data, loading, onStartOver }) {
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <h3>Generating Timetable...</h3>
        <p>AI agents are working to create an optimal schedule</p>
        <div className="agent-status">
          <div className="agent-step">🤖 Resource Allocation Agent - Matching rooms...</div>
          <div className="agent-step">⚡ Optimization Agent - Running solver...</div>
          <div className="agent-step">✅ Constraint Agent - Validating rules...</div>
          <div className="agent-step">🔧 Conflict Resolution Agent - Resolving issues...</div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="error-container">
        <h3>No Data Available</h3>
        <p>Unable to load timetable data. Please try again.</p>
        <button className="btn-primary" onClick={onStartOver}>Start Over</button>
      </div>
    )
  }

  const { status, timetable, constraints, utilization, message_log, error } = data

  const handleExport = () => {
    try {
      if (!timetable || timetable.length === 0) {
        alert('No timetable data to export')
        return
      }
      
      const headers = 'Division,Subject,Room,Faculty,Day,Time\n'
      const csvContent = headers + timetable.map(entry => 
        `${entry.division_name || entry.division_id},${entry.subject_name || entry.subject_id},${entry.room_number || entry.room_id},${entry.faculty_name || entry.faculty_id},${entry.day || 'N/A'},${entry.start_time || 'N/A'}`
      ).join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `timetable_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Failed to export timetable. Please try again.')
    }
  }

  const handleApprove = () => {
    if (confirm('Are you sure you want to approve this timetable? This will finalize the schedule.')) {
      // Here you would typically send approval to backend
      alert('Timetable approved successfully! 🎉')
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'success': return '#28a745'
      case 'conflicts_detected': return '#ffc107'
      case 'failed': return '#dc3545'
      default: return '#6c757d'
    }
  }

  const getStatusText = (status) => {
    switch(status) {
      case 'success': return '✅ SUCCESS'
      case 'conflicts_detected': return '⚠️ CONFLICTS DETECTED'
      case 'failed': return '❌ GENERATION FAILED'
      default: return '❓ UNKNOWN STATUS'
    }
  }

  return (
    <div className="timetable-container">
      <div className="result-header">
        <h2>Step 3: Generated Timetable</h2>
        <div className="status-badge" style={{ backgroundColor: getStatusColor(status) }}>
          {getStatusText(status)}
        </div>
      </div>

      {status === 'success' && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">{timetable?.length || 0}</div>
              <div className="metric-label">Total Classes Scheduled</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{((utilization?.slot_utilization || 0) * 100).toFixed(1)}%</div>
              <div className="metric-label">Slot Utilization</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{constraints?.filter(c => !c.violated).length || 0}</div>
              <div className="metric-label">Constraints Satisfied</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{constraints?.filter(c => c.violated).length || 0}</div>
              <div className="metric-label">Violations</div>
            </div>
          </div>

          <div className="timetable-section">
            <div className="section-header">
              <h3>📅 Generated Schedule</h3>
              <div className="action-buttons">
                <button className="btn-secondary" onClick={handleExport} disabled={!timetable || timetable.length === 0}>
                  📊 Export CSV
                </button>
                <button className="btn-success" onClick={handleApprove} disabled={constraints?.some(c => c.violated)}>
                  ✅ Approve Timetable
                </button>
              </div>
            </div>
            
            {timetable && timetable.length > 0 ? (
              <div className="table-container">
                <table className="timetable-table">
                  <thead>
                    <tr>
                      <th>Division</th>
                      <th>Subject</th>
                      <th>Room</th>
                      <th>Faculty</th>
                      <th>Day</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {timetable.map((entry, idx) => (
                      <tr key={idx}>
                        <td>{entry.division_name || entry.division_id}</td>
                        <td>{entry.subject_name || entry.subject_id}</td>
                        <td>{entry.room_number || entry.room_id}</td>
                        <td>{entry.faculty_name || entry.faculty_id}</td>
                        <td>{entry.day || 'N/A'}</td>
                        <td>{entry.start_time ? `${entry.start_time} - ${entry.end_time}` : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="no-data">
                <p>No timetable entries generated</p>
              </div>
            )}
          </div>
        </>
      )}

      {status === 'conflicts_detected' && (
        <div className="conflicts-section">
          <h3>⚠️ Conflicts Detected</h3>
          <p>The system found some scheduling conflicts. Review the issues below:</p>
          
          {data.resolution && (
            <div className="resolution-strategies">
              <h4>Suggested Solutions:</h4>
              <ul>
                {data.resolution.resolution_strategies?.map((strategy, idx) => (
                  <li key={idx}>
                    <strong>{strategy.type}:</strong> {strategy.suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {constraints && constraints.length > 0 && (
        <div className="constraints-section">
          <h3>🔍 Constraint Validation Report</h3>
          <div className="constraints-grid">
            {constraints.map((c, idx) => (
              <div key={idx} className={`constraint-card ${c.violated ? 'violated' : 'satisfied'}`}>
                <div className="constraint-header">
                  <strong>{c.type.replace('_', ' ').toUpperCase()}</strong>
                  <span className={`status-icon ${c.violated ? 'error' : 'success'}`}>
                    {c.violated ? '❌' : '✅'}
                  </span>
                </div>
                <div className="constraint-details">{c.details}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {utilization && (
        <div className="utilization-section">
          <h3>📊 Resource Utilization</h3>
          <div className="utilization-grid">
            <div className="util-card">
              <h4>Room Usage</h4>
              {Object.entries(utilization.room_utilization || {}).map(([roomId, usage]) => (
                <div key={roomId} className="usage-item">
                  <span>Room {roomId}:</span>
                  <span>{usage} classes</span>
                </div>
              ))}
            </div>
            
            {utilization.faculty_utilization && (
              <div className="util-card">
                <h4>Faculty Load</h4>
                {Object.entries(utilization.faculty_utilization).map(([facultyId, load]) => (
                  <div key={facultyId} className="usage-item">
                    <span>Faculty {facultyId}:</span>
                    <span>{load} classes</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {message_log && message_log.length > 0 && (
        <div className="agent-log-section">
          <h3>🤖 Agent Communication Log</h3>
          <p className="section-description">Real-time collaboration between AI agents</p>
          <div className="log-container">
            {message_log.map((msg, idx) => (
              <div key={idx} className="log-entry">
                <span className="log-timestamp">{new Date().toLocaleTimeString()}</span>
                <span className="log-sender">{msg.sender}</span>
                <span className="log-arrow">→</span>
                <span className="log-receiver">{msg.receiver}</span>
                <span className="log-message">{msg.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="error-section">
          <h3>❌ Generation Failed</h3>
          <p>Unable to generate a feasible timetable with the provided constraints.</p>
          {error && <p className="error-details">Error: {error}</p>}
          <div className="error-suggestions">
            <h4>Suggestions:</h4>
            <ul>
              <li>Ensure you have enough rooms for all classes</li>
              <li>Check that room capacities match student counts</li>
              <li>Verify lab subjects have lab rooms available</li>
              <li>Consider adding more faculty members</li>
              <li>Reduce hours per week for some subjects</li>
            </ul>
          </div>
        </div>
      )}

      <div className="action-bar">
        <button className="btn-secondary" onClick={onStartOver}>
          🔄 Start Over
        </button>
        {status === 'success' && (
          <button className="btn-primary" onClick={() => window.print()}>
            🖨️ Print Schedule
          </button>
        )}
      </div>
    </div>
  )
}

export default TimetableView
