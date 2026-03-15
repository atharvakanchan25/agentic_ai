import { useState, useEffect } from 'react'

export default function EntityTable({ title, columns, fetchFn, createFn, deleteFn, fields, extraData = {} }) {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    try {
      const res = await fetchFn()
      setRows(res.data)
    } catch {
      setError('Failed to load data')
    }
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    setLoading(true)
    try {
      await createFn(form)
      setSuccess(`${title} added successfully`)
      setForm({})
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this entry?')) return
    try {
      await deleteFn(id)
      load()
    } catch {
      setError('Failed to delete')
    }
  }

  return (
    <div className="entity-section">
      <h3 className="section-title">{title}</h3>

      {/* Form */}
      <form className="entity-form" onSubmit={handleSubmit}>
        {fields.map(f => (
          <div key={f.name} className="form-field">
            <label>{f.label}</label>
            {f.type === 'select' ? (
              <select
                value={form[f.name] || ''}
                onChange={e => setForm({ ...form, [f.name]: f.valueType === 'int' ? parseInt(e.target.value) : e.target.value })}
                required={f.required}
              >
                <option value="">Select {f.label}</option>
                {(extraData[f.optionsKey] || []).map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.name || opt.code}</option>
                ))}
              </select>
            ) : f.type === 'checkbox' ? (
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={!!form[f.name]}
                  onChange={e => setForm({ ...form, [f.name]: e.target.checked })}
                />
                <span>{f.checkLabel || f.label}</span>
              </label>
            ) : (
              <input
                type={f.type || 'text'}
                placeholder={f.placeholder || f.label}
                value={form[f.name] || ''}
                onChange={e => setForm({ ...form, [f.name]: f.valueType === 'int' ? parseInt(e.target.value) || '' : e.target.value })}
                required={f.required}
                min={f.min}
                max={f.max}
              />
            )}
          </div>
        ))}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Adding...' : `Add ${title}`}
        </button>
      </form>

      {error   && <p className="error-msg">{error}</p>}
      {success && <p className="success-msg">{success}</p>}

      {/* Table */}
      {rows.length > 0 ? (
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
                    {c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '-')}
                  </td>
                ))}
                <td>
                  <button className="btn-danger-sm" onClick={() => handleDelete(row.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="empty-msg">No {title.toLowerCase()} added yet.</p>
      )}
    </div>
  )
}
