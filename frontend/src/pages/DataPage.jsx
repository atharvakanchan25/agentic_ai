import { useState, useEffect } from 'react'
import EntityTable from '../components/EntityTable'
import {
  getDepartments, createDepartment, updateDepartment, deleteDepartment,
  getSubjects,    createSubject,    updateSubject,    deleteSubject,
  getRooms,       createRoom,       updateRoom,       deleteRoom,
  getFaculty,     createFaculty,    updateFaculty,    deleteFaculty,
  getDivisions,   createDivision,   updateDivision,   deleteDivision,
  getTimeslots
} from '../api/client'
import './DataPage.css'

const SECTIONS = [
  { id: 'Departments', icon: '🏛️' },
  { id: 'Subjects',    icon: '📚' },
  { id: 'Rooms',       icon: '🚪' },
  { id: 'Faculty',     icon: '👨🏫' },
  { id: 'Divisions',   icon: '👥' },
  { id: 'Timeslots',   icon: '🕐' },
]

export default function DataPage() {
  const [active, setActive]           = useState('Departments')
  const [departments, setDepartments] = useState([])
  const [timeslots, setTimeslots]     = useState([])
  const [tsLoading, setTsLoading]     = useState(false)

  useEffect(() => {
    getDepartments().then(r => setDepartments(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (active !== 'Timeslots') return
    setTsLoading(true)
    getTimeslots().then(r => setTimeslots(r.data)).catch(() => {}).finally(() => setTsLoading(false))
  }, [active])

  return (
    <div className="data-page">
      <div className="section-tabs">
        {SECTIONS.map(s => (
          <button
            key={s.id}
            className={`section-tab ${active === s.id ? 'active' : ''}`}
            onClick={() => setActive(s.id)}
          >
            {s.icon} {s.id}
          </button>
        ))}
      </div>

      <div className="card">
        {active === 'Departments' && (
          <EntityTable
            title="Department" emptyIcon="🏛️"
            fetchFn={getDepartments} createFn={createDepartment}
            updateFn={updateDepartment} deleteFn={deleteDepartment}
            columns={[
              { key: 'id',   label: 'ID' },
              { key: 'name', label: 'Name' },
              { key: 'code', label: 'Code' },
            ]}
            fields={[
              { name: 'name', label: 'Department Name', required: true, placeholder: 'e.g. Computer Science' },
              { name: 'code', label: 'Code',            required: true, placeholder: 'e.g. CS' },
            ]}
          />
        )}

        {active === 'Subjects' && (
          <EntityTable
            title="Subject" emptyIcon="📚"
            fetchFn={getSubjects} createFn={createSubject}
            updateFn={updateSubject} deleteFn={deleteSubject}
            extraData={{ departments }}
            columns={[
              { key: 'name',           label: 'Name' },
              { key: 'code',           label: 'Code' },
              { key: 'hours_per_week', label: 'Hrs/Week' },
              { key: 'is_lab',         label: 'Type',
                render: v => v
                  ? <span className="badge badge-blue">🔬 Lab</span>
                  : <span className="badge badge-gray">📖 Theory</span>
              },
            ]}
            fields={[
              { name: 'name',           label: 'Subject Name',  required: true, placeholder: 'e.g. Data Structures' },
              { name: 'code',           label: 'Subject Code',  required: true, placeholder: 'e.g. CS301' },
              { name: 'hours_per_week', label: 'Hours / Week',  required: true, type: 'number', valueType: 'int', min: 1, max: 10 },
              { name: 'is_lab',         label: 'Lab Subject?',  type: 'checkbox', checkLabel: 'This is a lab subject' },
              { name: 'department_id',  label: 'Department',    required: true, type: 'select', optionsKey: 'departments', valueType: 'int' },
            ]}
          />
        )}

        {active === 'Rooms' && (
          <EntityTable
            title="Room" emptyIcon="🚪"
            fetchFn={getRooms} createFn={createRoom}
            updateFn={updateRoom} deleteFn={deleteRoom}
            columns={[
              { key: 'room_number', label: 'Room No.' },
              { key: 'floor',       label: 'Floor' },
              { key: 'capacity',    label: 'Capacity' },
              { key: 'is_lab',      label: 'Type',
                render: v => v
                  ? <span className="badge badge-blue">🔬 Lab</span>
                  : <span className="badge badge-gray">🏫 Class</span>
              },
            ]}
            fields={[
              { name: 'room_number', label: 'Room Number', required: true, placeholder: 'e.g. 101 or L01' },
              { name: 'floor',       label: 'Floor',       required: true, type: 'number', valueType: 'int', min: 0, max: 20 },
              { name: 'capacity',    label: 'Capacity',    required: true, type: 'number', valueType: 'int', min: 10, max: 500 },
              { name: 'is_lab',      label: 'Lab Room?',   type: 'checkbox', checkLabel: 'This is a lab room' },
            ]}
          />
        )}

        {active === 'Faculty' && (
          <EntityTable
            title="Faculty" emptyIcon="👨🏫"
            fetchFn={getFaculty} createFn={createFaculty}
            updateFn={updateFaculty} deleteFn={deleteFaculty}
            extraData={{ departments }}
            columns={[
              { key: 'name',        label: 'Name' },
              { key: 'employee_id', label: 'Employee ID' },
            ]}
            fields={[
              { name: 'name',          label: 'Full Name',   required: true, placeholder: 'e.g. Dr. Sharma' },
              { name: 'employee_id',   label: 'Employee ID', required: true, placeholder: 'e.g. CS001' },
              { name: 'department_id', label: 'Department',  required: true, type: 'select', optionsKey: 'departments', valueType: 'int' },
            ]}
          />
        )}

        {active === 'Divisions' && (
          <EntityTable
            title="Division" emptyIcon="👥"
            fetchFn={getDivisions} createFn={createDivision}
            updateFn={updateDivision} deleteFn={deleteDivision}
            extraData={{ departments }}
            columns={[
              { key: 'name',          label: 'Name' },
              { key: 'year',          label: 'Year' },
              { key: 'student_count', label: 'Students' },
            ]}
            fields={[
              { name: 'name',          label: 'Division Name', required: true, placeholder: 'e.g. CS-A' },
              { name: 'year',          label: 'Year',          required: true, type: 'number', valueType: 'int', min: 1, max: 4 },
              { name: 'student_count', label: 'Student Count', required: true, type: 'number', valueType: 'int', min: 1, max: 200 },
              { name: 'department_id', label: 'Department',    required: true, type: 'select', optionsKey: 'departments', valueType: 'int' },
            ]}
          />
        )}

        {active === 'Timeslots' && (
          <div className="entity-section fade-in">
            <div className="entity-header">
              <h3 className="section-title">🕐 Weekly Timeslots</h3>
              {!tsLoading && <span className="row-count badge badge-purple">{timeslots.length} slots</span>}
            </div>
            <p style={{fontSize:13, color:'var(--text-muted)', marginBottom:16}}>
              Timeslots are auto-seeded (Mon–Fri, 6 slots/day). Run
              <code style={{background:'var(--bg-subtle)',padding:'1px 6px',borderRadius:4,margin:'0 4px'}}>python scripts/seed.py</code>
              to populate.
            </p>
            {tsLoading ? (
              <div className="skeleton-table">
                {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{height:44,marginBottom:6}} />)}
              </div>
            ) : timeslots.length === 0 ? (
              <div className="empty-state">
                <span className="empty-state-icon">🕐</span>
                <span>No timeslots found — run the seed script</span>
              </div>
            ) : (() => {
              const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday']
              const slots = [...new Map(timeslots.map(t => [t.slot_number, {slot_number: t.slot_number, start_time: t.start_time, end_time: t.end_time}])).values()].sort((a,b) => a.slot_number - b.slot_number)
              const grid = {}
              timeslots.forEach(t => { grid[`${t.day}_${t.slot_number}`] = t })
              return (
                <div className="table-wrapper">
                  <table className="ts-grid">
                    <thead>
                      <tr>
                        <th style={{width:110}}>⏰ Time</th>
                        {DAYS.map(d => <th key={d}>{d.slice(0,3)}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {slots.map(s => (
                        <tr key={s.slot_number}>
                          <td style={{fontWeight:600, fontSize:12, color:'var(--text-muted)', whiteSpace:'nowrap'}}>
                            <span className="badge badge-purple" style={{marginRight:4}}>#{s.slot_number}</span>
                            {s.start_time}–{s.end_time}
                          </td>
                          {DAYS.map(d => {
                            const t = grid[`${d}_${s.slot_number}`]
                            return (
                              <td key={d} style={{textAlign:'center'}}>
                                {t
                                  ? <span className="badge badge-green" style={{fontSize:11}}>✓ Active</span>
                                  : <span style={{color:'var(--text-muted)',fontSize:12}}>—</span>
                                }
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
      </div>
    </div>
  )
}
