import { useState, useEffect } from 'react'
import './AuthPage.css'

/* ── Password strength calculator ─────────────────────────────────────────── */
function getStrength(pw) {
  if (!pw) return { score: 0, label: '', cls: '' }
  let score = 0
  if (pw.length >= 8)            score++
  if (/[A-Z]/.test(pw))          score++
  if (/[0-9]/.test(pw))          score++
  if (/[^A-Za-z0-9]/.test(pw))   score++
  const map = ['', 'weak', 'fair', 'good', 'strong']
  const lbl = ['', 'Weak', 'Fair', 'Good', 'Strong']
  return { score, label: lbl[score], cls: map[score] }
}

const PW_RULES = [
  { label: 'At least 8 characters',      test: pw => pw.length >= 8 },
  { label: 'One uppercase letter (A–Z)',  test: pw => /[A-Z]/.test(pw) },
  { label: 'One number (0–9)',            test: pw => /[0-9]/.test(pw) },
  { label: 'One special character',       test: pw => /[^A-Za-z0-9]/.test(pw) },
]

/* ── Reusable input field ─────────────────────────────────────────────────── */
function Field({ label, icon, type = 'text', value, onChange, placeholder, required, hint, status }) {
  const [show, setShow] = useState(false)
  const isPassword = type === 'password'
  const inputType  = isPassword ? (show ? 'text' : 'password') : type

  const borderCls = status === 'valid' ? 'valid' : status === 'invalid' ? 'invalid' : ''

  return (
    <div className="auth-field">
      <label className="auth-label">
        {label}
        {required && <span className="required-star">*</span>}
      </label>
      <div className="input-wrapper">
        <span className="input-icon">{icon}</span>
        <input
          type={inputType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          autoComplete={isPassword ? 'current-password' : type === 'email' ? 'email' : 'off'}
          className={`${borderCls} ${!isPassword ? 'no-right-icon' : ''}`}
          aria-label={label}
        />
        {status && (
          <span className="input-status">
            {status === 'valid' ? '✅' : '❌'}
          </span>
        )}
        {isPassword && (
          <button
            type="button"
            className="toggle-password"
            onClick={() => setShow(s => !s)}
            aria-label={show ? 'Hide password' : 'Show password'}
            data-tooltip={show ? 'Hide password' : 'Show password'}
          >
            {show ? '🙈' : '👁️'}
          </button>
        )}
      </div>
      {hint && (
        <span className={`field-hint ${hint.type || ''}`}>
          {hint.text}
        </span>
      )}
    </div>
  )
}

/* ── Main AuthPage ────────────────────────────────────────────────────────── */
export default function AuthPage({ onAuth }) {
  const [mode, setMode]         = useState('signin')   // 'signin' | 'signup'
  const [loading, setLoading]   = useState(false)
  const [alert, setAlert]       = useState(null)        // { type, text }
  const [remember, setRemember] = useState(false)
  const [showRules, setShowRules] = useState(false)

  // Sign-in fields
  const [siEmail, setSiEmail]   = useState('')
  const [siPass,  setSiPass]    = useState('')

  // Sign-up fields
  const [suName,    setSuName]    = useState('')
  const [suEmail,   setSuEmail]   = useState('')
  const [suPass,    setSuPass]    = useState('')
  const [suConfirm, setSuConfirm] = useState('')

  // Clear alert when switching mode
  useEffect(() => { setAlert(null) }, [mode])

  /* ── Validation helpers ── */
  const emailValid = email => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  const siEmailStatus = siEmail ? (emailValid(siEmail) ? 'valid' : 'invalid') : ''
  const siPassStatus  = siPass  ? (siPass.length >= 6  ? 'valid' : 'invalid') : ''

  const suNameStatus    = suName    ? (suName.trim().length >= 2 ? 'valid' : 'invalid') : ''
  const suEmailStatus   = suEmail   ? (emailValid(suEmail)       ? 'valid' : 'invalid') : ''
  const strength        = getStrength(suPass)
  const suPassStatus    = suPass    ? (strength.score >= 2       ? 'valid' : 'invalid') : ''
  const suConfirmStatus = suConfirm ? (suConfirm === suPass      ? 'valid' : 'invalid') : ''

  /* ── Submit handlers ── */
  const handleSignIn = async (e) => {
    e.preventDefault()
    if (!emailValid(siEmail)) { setAlert({ type: 'error', text: 'Please enter a valid email address.' }); return }
    if (siPass.length < 6)    { setAlert({ type: 'error', text: 'Password must be at least 6 characters.' }); return }

    setLoading(true); setAlert(null)
    // Simulate API call — replace with real auth endpoint
    await new Promise(r => setTimeout(r, 1200))
    setLoading(false)

    // Demo: accept any valid-format credentials
    if (siEmail && siPass) {
      setAlert({ type: 'success', text: 'Signed in successfully! Redirecting…' })
      setTimeout(() => onAuth({ email: siEmail, name: siEmail.split('@')[0] }), 900)
    } else {
      setAlert({ type: 'error', text: 'Invalid email or password. Please try again.' })
    }
  }

  const handleSignUp = async (e) => {
    e.preventDefault()
    if (suNameStatus    === 'invalid') { setAlert({ type: 'error', text: 'Name must be at least 2 characters.' }); return }
    if (suEmailStatus   === 'invalid') { setAlert({ type: 'error', text: 'Please enter a valid email address.' }); return }
    if (strength.score  < 2)           { setAlert({ type: 'error', text: 'Password is too weak. Follow the rules below.' }); return }
    if (suConfirm !== suPass)          { setAlert({ type: 'error', text: 'Passwords do not match.' }); return }

    setLoading(true); setAlert(null)
    await new Promise(r => setTimeout(r, 1400))
    setLoading(false)

    setAlert({ type: 'success', text: 'Account created! Signing you in…' })
    setTimeout(() => onAuth({ email: suEmail, name: suName }), 900)
  }

  return (
    <div className="auth-page">

      {/* ── Left brand panel ── */}
      <div className="auth-brand">
        <div className="brand-logo">🎓</div>
        <div className="brand-title">Timetable AI</div>
        <div className="brand-sub">
          Multi-agent scheduling system powered by constraint programming and AI.
        </div>
        <div className="brand-features">
          {[
            { icon: '🤖', text: '5 AI agents working in pipeline' },
            { icon: '⚡', text: 'OR-Tools CP-SAT solver' },
            { icon: '📅', text: 'Conflict-free timetable generation' },
            { icon: '💬', text: 'Natural language chat interface' },
          ].map(f => (
            <div key={f.text} className="brand-feature">
              <div className="brand-feature-icon">{f.icon}</div>
              <span>{f.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="auth-form-panel">
        <div className="auth-card">

          {/* Header */}
          <div className="auth-header">
            <div className="auth-title">
              {mode === 'signin' ? 'Welcome back 👋' : 'Create account 🚀'}
            </div>
            <div className="auth-subtitle">
              {mode === 'signin'
                ? 'Sign in to access your timetable dashboard'
                : 'Join Timetable AI and start scheduling smarter'}
            </div>
          </div>

          {/* Tab switcher */}
          <div className="auth-tabs" role="tablist">
            <button
              className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
              onClick={() => setMode('signin')}
              role="tab"
              aria-selected={mode === 'signin'}
            >
              Sign In
            </button>
            <button
              className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => setMode('signup')}
              role="tab"
              aria-selected={mode === 'signup'}
            >
              Sign Up
            </button>
          </div>

          {/* Alert banner */}
          {alert && (
            <div className={`auth-alert ${alert.type}`} role="alert">
              <span>{alert.type === 'error' ? '⚠️' : '✅'}</span>
              <span>{alert.text}</span>
            </div>
          )}

          {/* ── SIGN IN FORM ── */}
          {mode === 'signin' && (
            <form className="auth-form" onSubmit={handleSignIn} noValidate>
              <Field
                label="Email address"
                icon="✉️"
                type="email"
                value={siEmail}
                onChange={e => setSiEmail(e.target.value)}
                placeholder="you@example.com"
                required
                status={siEmailStatus}
                hint={siEmail && siEmailStatus === 'invalid'
                  ? { type: 'error', text: '✗ Enter a valid email (e.g. name@domain.com)' }
                  : siEmailStatus === 'valid'
                  ? { type: 'ok', text: '✓ Looks good' }
                  : null}
              />

              <Field
                label="Password"
                icon="🔒"
                type="password"
                value={siPass}
                onChange={e => setSiPass(e.target.value)}
                placeholder="Enter your password"
                required
                status={siPassStatus}
                hint={siPass && siPassStatus === 'invalid'
                  ? { type: 'error', text: '✗ Password must be at least 6 characters' }
                  : null}
              />

              <div className="auth-row">
                <label className="remember-label">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={e => setRemember(e.target.checked)}
                  />
                  Remember me
                </label>
                <button type="button" className="forgot-link" onClick={() =>
                  setAlert({ type: 'success', text: 'Password reset link sent to your email (demo).' })
                }>
                  Forgot password?
                </button>
              </div>

              <button type="submit" className="btn-auth" disabled={loading}>
                {loading ? <><span className="spinner" /> Signing in…</> : 'Sign In →'}
              </button>

              <div className="auth-switch">
                Don't have an account?{' '}
                <button type="button" onClick={() => setMode('signup')}>Create one</button>
              </div>
            </form>
          )}

          {/* ── SIGN UP FORM ── */}
          {mode === 'signup' && (
            <form className="auth-form" onSubmit={handleSignUp} noValidate>
              <Field
                label="Full name"
                icon="👤"
                type="text"
                value={suName}
                onChange={e => setSuName(e.target.value)}
                placeholder="Dr. Sharma"
                required
                status={suNameStatus}
                hint={suName && suNameStatus === 'invalid'
                  ? { type: 'error', text: '✗ Name must be at least 2 characters' }
                  : suNameStatus === 'valid'
                  ? { type: 'ok', text: '✓ Looks good' }
                  : null}
              />

              <Field
                label="Email address"
                icon="✉️"
                type="email"
                value={suEmail}
                onChange={e => setSuEmail(e.target.value)}
                placeholder="you@university.edu"
                required
                status={suEmailStatus}
                hint={suEmail && suEmailStatus === 'invalid'
                  ? { type: 'error', text: '✗ Enter a valid email address' }
                  : suEmailStatus === 'valid'
                  ? { type: 'ok', text: '✓ Valid email' }
                  : null}
              />

              {/* Password with strength meter */}
              <div className="auth-field">
                <label className="auth-label">
                  Password <span className="required-star">*</span>
                </label>
                <div className="input-wrapper">
                  <span className="input-icon">🔒</span>
                  <input
                    type="password"
                    value={suPass}
                    onChange={e => { setSuPass(e.target.value); setShowRules(true) }}
                    onFocus={() => setShowRules(true)}
                    placeholder="Create a strong password"
                    required
                    autoComplete="new-password"
                    className={suPassStatus}
                    aria-label="Password"
                  />
                  {suPassStatus && (
                    <span className="input-status">
                      {suPassStatus === 'valid' ? '✅' : '❌'}
                    </span>
                  )}
                </div>

                {/* Strength bar */}
                {suPass && (
                  <>
                    <div className="strength-bar-wrap" aria-label={`Password strength: ${strength.label}`}>
                      {[1,2,3,4].map(i => (
                        <div
                          key={i}
                          className={`strength-segment ${i <= strength.score ? `filled-${strength.cls}` : ''}`}
                        />
                      ))}
                    </div>
                    {strength.label && (
                      <span className={`strength-label ${strength.cls}`}>
                        Strength: {strength.label}
                      </span>
                    )}
                  </>
                )}

                {/* Rules checklist */}
                {showRules && (
                  <div className="pw-rules" role="list" aria-label="Password requirements">
                    {PW_RULES.map(r => (
                      <div key={r.label} className={`pw-rule ${r.test(suPass) ? 'met' : ''}`} role="listitem">
                        <span className="pw-rule-icon">{r.test(suPass) ? '✓' : '○'}</span>
                        {r.label}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Field
                label="Confirm password"
                icon="🔐"
                type="password"
                value={suConfirm}
                onChange={e => setSuConfirm(e.target.value)}
                placeholder="Re-enter your password"
                required
                status={suConfirmStatus}
                hint={suConfirm && suConfirmStatus === 'invalid'
                  ? { type: 'error', text: '✗ Passwords do not match' }
                  : suConfirmStatus === 'valid'
                  ? { type: 'ok', text: '✓ Passwords match' }
                  : null}
              />

              <button type="submit" className="btn-auth" disabled={loading}>
                {loading ? <><span className="spinner" /> Creating account…</> : 'Create Account →'}
              </button>

              <div className="auth-switch">
                Already have an account?{' '}
                <button type="button" onClick={() => setMode('signin')}>Sign in</button>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  )
}
