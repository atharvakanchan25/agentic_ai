import { useState, useEffect } from 'react'
import { useToast } from './Toast'

export default function EntityTable({
  title, columns, fetchFn, createFn, deleteFn, updateFn,
  fields, extraData = {}, emptyIcon = '📭'
}) {
  const toast = useToast()

  const [rows, setRows]         = useState([])
  const [form, setForm]         = useState({})
  const [loading, setLoading]   = useState(false)
  const [fetching, setFetching] = useState(true)
  const [editId, setEditId]     = useState(null)
  const [editForm, setEditForm] = useState({})

  const load = async () => {
    setFetching(true)
    try {
      const res = await fetchFn()
      setRows(res.data)
    } catch {
      toast('Failed to load data. Please refresh.', 'error')
    } finally {
      setFetching(false)
    }
  }

  useEffect(() => { load() }, [])

  /* ── Add ── */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await createFn(form)
      toast(`${title} added successfully`, 'success')
      setForm({})
      load()
    } catch (err) {
      toast(err.response?.data?.detail || `Failed to add ${title.toLowerCase()}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  /* ── Delete ── */
  const handleDelete = async (id, label) => {
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return
    try {
      await deleteFn(id)
      toast(`${title} deleted`, 'warning')
      load()
    } catch {
      toast('Failed to delete. It may be referenced by other records.', 'error')
    }
  }

  /* ── Edit ── */
  const startEdit = (row) => {
    setEditId(row.id)
    setEditForm({ ...row })
  }

  const cancelEdit = () => { setEditId(null); setEditForm({}) }

  const handleUpdate = async (id) => {
    if (!updateFn) return
    try {
      await updateFn(id, editForm)
      toast(`${title} updated`, 'success')
      setEditId(null)
      load()
    } catch (err) {
      toast(err.response?.data?.detail || `Failed to update ${title.toLowerCase()}`, 'error')
    }
  }

  const setField     = (name, value) => setForm(f => ({ ...f, [name]: value }))
  const setEditField = (name, value) => setEditForm(f => ({ ...f, [name]: value }))

  const renderInput = (f, value, onChange) => {
    if (f.type === 'select') return (
      <select value={value ?? ''} onChange={e => onChange(f.name, f.valueType === 'int' ? parseInt(e.target.value) : e.target.value)} required={f.required}>
        <option value="">— Select {f.label} —</option>
        {(extraData[f.optionsKey] || []).map(opt => (
          <option key={opt.id} value={opt.id}>{opt.name || opt.code}</option>
        ))}
      </select>
    )
    if (f.type === 'checkbox') return (
      <label className="checkbox-label">
        <input type="checkbox" checked={!!value} onChange={e => onChange(f.name, e.target.checked)} />
        <span>{f.checkLabel || f.label}</span>
      </label>
    )
    return (
      <input
        type={f.type || 'text'}
        placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}`}
        value={value ?? ''}
        onChange={e => onChange(f.name, f.valueType === 'int' ? (parseInt(e.target.value) || '') : e.target.value)}
        required={f.required}
        min={f.min}
        max={f.max}
        autoComplete="off"
      />
    )
  }

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
            <label htmlFor={`field-${f.name}`}>
              {f.label}{f.required && <span className="required-star">*</span>}
            </label>
            {renderInput(f, form[f.name], setField)}
          </div>
        ))}
        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <><span className="spinner" />Adding…</> : `＋ Add ${title}`}
          </button>
          <button type="button" className="btn-reset" onClick={() => setForm({})} disabled={loading}>
            ✕ Clear
          </button>
        </div>
      </form>

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
                  {editId === row.id ? (
                    <>
                      {columns.map(c => {
                        const f = fields.find(f => f.name === c.key)
                        return (
                          <td key={c.key}>
                            {f ? renderInput(f, editForm[c.key], setEditField)
                               : <span>{String(row[c.key] ?? '—')}</span>}
                          </td>
                        )
                      })}
                      <td>
                        <div className="action-btns">
                          <button className="btn-save-sm" onClick={() => handleUpdate(row.id)}>✓ Save</button>
                          <button className="btn-cancel-sm" onClick={cancelEdit}>✕</button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      {columns.map(c => (
                        <td key={c.key}>
                          {c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '—')}
                        </td>
                      ))}
                      <td>
                        <div className="action-btns">
                          {updateFn && (
                            <button className="btn-edit-sm" onClick={() => startEdit(row)} data-tooltip="Edit this record">
                              ✏️ Edit
                            </button>
                          )}
                          <button
                            className="btn-danger-sm"
                            onClick={() => handleDelete(row.id, row.name || row.room_number || row.employee_id || row.id)}
                            data-tooltip="Delete this record"
                          >
                            🗑
                          </button>
                        </div>
                      </td>
                    </>
                  )}
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
