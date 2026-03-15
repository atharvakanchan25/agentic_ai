import { useState, useEffect } from 'react'
import { getTimeslots } from '../api/client'
import { useToast } from '../components/Toast'
import './SettingsPage.css'

export default function SettingsPage({ user, darkMode, onToggleDark, onLogout }) {
  const toast     = useToast()
  const [timeslots, setTimeslots]   = useState([])
  const [tsLoading, setTsLoading]   = useState(true)
  const [displayName, setDisplayName] = useState(user?.name || '')
  const [saved, setSaved]           = useState(false)

  useEffect(() => {
    getTimeslots()
      .then(r => setTimeslots(r.data))
      .catch(() => toast('Failed to load timeslots', 'error'))
      .finally(() => setTsLoading(false))
  }, [])

  const handleSaveProfile = (e) => {
    e.preventDefault()
    if (!displayName.trim()) { toast('Name cannot be empty', 'error'); return }
    setSaved(true)
    toast('Profile updated successfully', 'success')
    setTimeout(() => setSaved(false), 2000)
  }

  const days = [...new Set(timeslots.map(t => t.day))]

  return (
    <div className="settings-page fade-in">

      {/* ── Profile ── */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <span className="settings-section-icon">👤</span>
          <div>
            <h3>Profile</h3>
            <p>Your account information</p>
          </div>
        </div>

        <div className="profile-avatar-row">
          <div className="profile-avatar">{displayName?.[0]?.toUpperCase() || '?'}</div>
          <div>
            <div className="profile-name">{displayName}</div>
            <div className="profile-email">{user?.email}</div>
          </div>
        </div>

        <form className="settings-form" onSubmit={handleSaveProfile}>
          <div className="settings-field">
            <label>Display Name</label>
            <input
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              placeholder="Your name"
            />
          </div>
          <div className="settings-field">
            <label>Email</label>
            <input value={user?.email || ''} disabled />
            <span className="field-note">Email cannot be changed in demo mode</span>
          </div>
          <button type="submit" className="btn-settings-save" disabled={saved}>
            {saved ? '✓ Saved' : '💾 Save Profile'}
          </button>
        </form>
      </div>

      {/* ── Appearance ── */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <span className="settings-section-icon">🎨</span>
          <div>
            <h3>Appearance</h3>
            <p>Customize how the app looks</p>
          </div>
        </div>

        <div className="settings-row">
          <div className="settings-row-info">
            <span className="settings-row-label">Dark Mode</span>
            <span className="settings-row-desc">Switch between light and dark theme</span>
          </div>
          <button
            className={`toggle-switch ${darkMode ? 'on' : ''}`}
            onClick={onToggleDark}
            aria-label={darkMode ? 'Disable dark mode' : 'Enable dark mode'}
            role="switch"
            aria-checked={darkMode}
          >
            <span className="toggle-thumb" />
            <span className="toggle-label">{darkMode ? '🌙 Dark' : '☀️ Light'}</span>
          </button>
        </div>
      </div>

      {/* ── Timeslots ── */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <span className="settings-section-icon">🕐</span>
          <div>
            <h3>Timeslots</h3>
            <p>View the weekly schedule slots used for timetable generation</p>
          </div>
          <span className="badge badge-purple" style={{marginLeft:'auto'}}>
            {timeslots.length} slots
          </span>
        </div>

        {tsLoading ? (
          <div className="skeleton-table">
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:36, marginBottom:6}} />)}
          </div>
        ) : timeslots.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🕐</span>
            <span>No timeslots found — run the seed script first</span>
          </div>
        ) : (
          <div className="timeslots-grid">
            {days.map(day => (
              <div key={day} className="timeslot-day-col">
                <div className="timeslot-day-header">{day}</div>
                {timeslots
                  .filter(t => t.day === day)
                  .sort((a, b) => a.slot_number - b.slot_number)
                  .map(t => (
                    <div key={t.id} className="timeslot-chip">
                      <span className="ts-slot">#{t.slot_number}</span>
                      <span className="ts-time">{t.start_time} – {t.end_time}</span>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Preferences ── */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <span className="settings-section-icon">⚙️</span>
          <div>
            <h3>Preferences</h3>
            <p>Application behaviour settings</p>
          </div>
        </div>

        {[
          { label: 'Show agent pipeline log after generation', key: 'showLog',    default: true },
          { label: 'Auto-select all departments on load',      key: 'autoSelect', default: true },
          { label: 'Confirm before deleting records',          key: 'confirmDel', default: true },
        ].map(pref => (
          <PrefToggle key={pref.key} label={pref.label} storageKey={pref.key} defaultVal={pref.default} toast={toast} />
        ))}
      </div>

      {/* ── About ── */}
      <div className="settings-section card">
        <div className="settings-section-header">
          <span className="settings-section-icon">ℹ️</span>
          <div>
            <h3>About</h3>
            <p>System information</p>
          </div>
        </div>
        <div className="about-grid">
          {[
            ['App',      'Timetable AI'],
            ['Version',  'v1.0.0'],
            ['Solver',   'OR-Tools CP-SAT'],
            ['Backend',  'FastAPI + SQLAlchemy'],
            ['Frontend', 'React + Vite'],
            ['Agents',   '5 AI Agents'],
          ].map(([k, v]) => (
            <div key={k} className="about-row">
              <span className="about-key">{k}</span>
              <span className="about-val">{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Danger zone ── */}
      <div className="settings-section card danger-zone">
        <div className="settings-section-header">
          <span className="settings-section-icon">⚠️</span>
          <div>
            <h3>Danger Zone</h3>
            <p>Irreversible actions</p>
          </div>
        </div>
        <div className="danger-row">
          <div>
            <div className="settings-row-label">Sign Out</div>
            <div className="settings-row-desc">You will be returned to the login screen</div>
          </div>
          <button className="btn-danger-outline" onClick={onLogout}>⎋ Sign Out</button>
        </div>
      </div>

    </div>
  )
}

/* ── Preference toggle row ── */
function PrefToggle({ label, storageKey, defaultVal, toast }) {
  const [on, setOn] = useState(() => {
    const stored = localStorage.getItem(`pref_${storageKey}`)
    return stored !== null ? stored === 'true' : defaultVal
  })

  const toggle = () => {
    const next = !on
    setOn(next)
    localStorage.setItem(`pref_${storageKey}`, String(next))
    toast(`Preference updated`, 'info', 1800)
  }

  return (
    <div className="settings-row">
      <div className="settings-row-info">
        <span className="settings-row-label">{label}</span>
      </div>
      <button
        className={`toggle-switch ${on ? 'on' : ''}`}
        onClick={toggle}
        role="switch"
        aria-checked={on}
        aria-label={label}
      >
        <span className="toggle-thumb" />
      </button>
    </div>
  )
}
