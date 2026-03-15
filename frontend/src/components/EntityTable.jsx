import { useState, useEffect } from 'react'

export default function EntityTable({
  title, columns, fetchFn, createFn, deleteFn,
  fields, extraData = {}, emptyIcon = '📭'
}) {
  const [rows, setRows]       = useState([])
  const [form, setForm]       = useState({})
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError]     = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    setFetching(true)
    try {
      const res = await fetchFn()
      setRows(res.data)
    } catch {
      setError('Failed to load data. Please refresh.')
    } finally {
      setFetching(false)
    }
  }

  useEffect(() => { load() }, [])

  // Auto-clear feedback after 3s
  useEffect(() => {
    if (!success && !error) return
    const t = setTimeout(() => { setSuccess(''); setError('') }, 3500)
    return () => clearTimeout(t)
  }, [success, error])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    setLoading(true)
    try {
      await createFn(form)
      setSuccess(`${title} added successfully ✓`)
      setForm({})
      load()
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to add ${title.toLowerCase()}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id, label) => {
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return
    try {
      await deleteFn(id)
      load()
    } catch {
      setError('Failed to delete. It may be referenced by other records.')
    }
  }

  const setField = (name, value) => setForm(f => ({ ...f, [name]: value }))

  return (
    <div className="entity-section fade-in">
      <div className="entity-header">
        <h3 className="section-title">{title}s</h3>
        {!fetching && (
          <span className="row-count badge badge-purple">{rows.length} record{rows.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {/* ── Add Form ── */}
      <form className="entity-form" onSubmit={handleSubmit} noValidate>
        {fields.map(f => (
          <div key={f.name} className="form-field">
            <label htmlFor={`field-${f.name}`}>{f.label}{f.required && <span className="required-star">*</span>}</label>

            {f.type === 'select' ? (
              <select
                id={`field-${f.name}`}
                value={form[f.name] ?? ''}
                onChange={e => setField(f.name, f.valueType === 'int' ? parseInt(e.target.value) : e.target.value)}
                required={f.required}
              >
                <option value="">— Select {f.label} —</option>
                {(extraData[f.optionsKey] || []).map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.name || opt.code}</option>
                ))}
              </select>
            ) : f.type === 'checkbox' ? (
              <label className="checkbox-label" htmlFor={`field-${f.name}`}>
                <input
                  id={`field-${f.name}`}
                  type="checkbox"
                  checked={!!form[f.name]}
                  onChange={e => setField(f.name, e.target.checked)}
                />
                <span>{f.checkLabel || f.label}</span>
              </label>
            ) : (
              <input
                id={`field-${f.name}`}
                type={f.type || 'text'}
                placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}`}
                value={form[f.name] ?? ''}
                onChange={e => setField(f.name, f.valueType === 'int' ? (parseInt(e.target.value) || '') : e.target.value)}
                required={f.required}
                min={f.min}
                max={f.max}
                autoComplete="off"
              />
            )}
          </div>
        ))}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <><span className="spinner" />Adding…</> : `＋ Add ${title}`}
        </button>
      </form>

      {error   && <p className="error-msg">⚠ {error}</p>}
      {success && <p className="success-msg">✓ {success}</p>}

      {/* ── Table ── */}
      {fetching ? (
        <div className="skeleton-table">
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{height: 40, marginBottom: 6}} />)}
        </div>
      ) : rows.length > 0 ? (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                {columns.map(c => <th key={c.key}>{c.label}</th>)}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.id}>
                  {columns.map(c => (
                    <td key={c.key}>
                      {c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '—')}
                    </td>
                  ))}
                  <td>
                    <button
                      className="btn-danger-sm"
                      onClick={() => handleDelete(row.id, row.name || row.room_number || row.employee_id || row.id)}
                      data-tooltip="Delete this record"
                    >
                      🗑 Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <span className="empty-state-icon">{emptyIcon}</span>
          <span>No {title.toLowerCase()}s added yet</span>
          <span style={{fontSize: 12, color: 'var(--text-muted)'}}>Use the form above to add your first {title.toLowerCase()}</span>
        </div>
      )}
    </div>
  )
}
