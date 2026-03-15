import { useState, useEffect } from 'react'
import EntityTable from '../components/EntityTable'
import {
  getDepartments, createDepartment, deleteDepartment,
  getSubjects, createSubject, deleteSubject,
  getRooms, createRoom, deleteRoom,
  getFaculty, createFaculty, deleteFaculty,
  getDivisions, createDivision, deleteDivision
} from '../api/client'
import './DataPage.css'

const SECTIONS = ['Departments', 'Subjects', 'Rooms', 'Faculty', 'Divisions']

export default function DataPage() {
  const [active, setActive] = useState('Departments')
  const [departments, setDepartments] = useState([])

  useEffect(() => {
    getDepartments().then(r => setDepartments(r.data)).catch(() => {})
  }, [])

  return (
    <div className="data-page">
      <div className="section-tabs">
        {SECTIONS.map(s => (
          <button
            key={s}
            className={`section-tab ${active === s ? 'active' : ''}`}
            onClick={() => setActive(s)}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="card">
        {active === 'Departments' && (
          <EntityTable
            title="Department"
            fetchFn={getDepartments}
            createFn={createDepartment}
            deleteFn={deleteDepartment}
            columns={[
              { key: 'id', label: 'ID' },
              { key: 'name', label: 'Name' },
              { key: 'code', label: 'Code' }
            ]}
            fields={[
              { name: 'name', label: 'Department Name', required: true },
              { name: 'code', label: 'Code (e.g. CS)', required: true, placeholder: 'CS' }
            ]}
          />
        )}

        {active === 'Subjects' && (
          <EntityTable
            title="Subject"
            fetchFn={getSubjects}
            createFn={createSubject}
            deleteFn={deleteSubject}
            extraData={{ departments }}
            columns={[
              { key: 'name', label: 'Name' },
              { key: 'code', label: 'Code' },
              { key: 'hours_per_week', label: 'Hours/Week' },
              { key: 'is_lab', label: 'Lab', render: v => v ? <span className="badge badge-blue">Lab</span> : <span className="badge badge-gray">Theory</span> }
            ]}
            fields={[
              { name: 'name', label: 'Subject Name', required: true },
              { name: 'code', label: 'Code (e.g. CS301)', required: true },
              { name: 'hours_per_week', label: 'Hours/Week', type: 'number', valueType: 'int', min: 1, max: 10, required: true },
              { name: 'is_lab', label: 'Is Lab?', type: 'checkbox', checkLabel: 'Lab Subject' },
              { name: 'department_id', label: 'Department', type: 'select', optionsKey: 'departments', valueType: 'int', required: true }
            ]}
          />
        )}

        {active === 'Rooms' && (
          <EntityTable
            title="Room"
            fetchFn={getRooms}
            createFn={createRoom}
            deleteFn={deleteRoom}
            columns={[
              { key: 'room_number', label: 'Room No.' },
              { key: 'floor', label: 'Floor' },
              { key: 'capacity', label: 'Capacity' },
              { key: 'is_lab', label: 'Type', render: v => v ? <span className="badge badge-blue">Lab</span> : <span className="badge badge-gray">Class</span> }
            ]}
            fields={[
              { name: 'room_number', label: 'Room Number', required: true },
              { name: 'floor', label: 'Floor', type: 'number', valueType: 'int', min: 0, max: 20, required: true },
              { name: 'capacity', label: 'Capacity', type: 'number', valueType: 'int', min: 10, max: 500, required: true },
              { name: 'is_lab', label: 'Is Lab?', type: 'checkbox', checkLabel: 'Lab Room' }
            ]}
          />
        )}

        {active === 'Faculty' && (
          <EntityTable
            title="Faculty"
            fetchFn={getFaculty}
            createFn={createFaculty}
            deleteFn={deleteFaculty}
            extraData={{ departments }}
            columns={[
              { key: 'name', label: 'Name' },
              { key: 'employee_id', label: 'Employee ID' }
            ]}
            fields={[
              { name: 'name', label: 'Full Name', required: true },
              { name: 'employee_id', label: 'Employee ID', required: true },
              { name: 'department_id', label: 'Department', type: 'select', optionsKey: 'departments', valueType: 'int', required: true }
            ]}
          />
        )}

        {active === 'Divisions' && (
          <EntityTable
            title="Division"
            fetchFn={getDivisions}
            createFn={createDivision}
            deleteFn={deleteDivision}
            extraData={{ departments }}
            columns={[
              { key: 'name', label: 'Name' },
              { key: 'year', label: 'Year' },
              { key: 'student_count', label: 'Students' }
            ]}
            fields={[
              { name: 'name', label: 'Division Name (e.g. CS-A)', required: true },
              { name: 'year', label: 'Year', type: 'number', valueType: 'int', min: 1, max: 4, required: true },
              { name: 'student_count', label: 'Student Count', type: 'number', valueType: 'int', min: 1, max: 200, required: true },
              { name: 'department_id', label: 'Department', type: 'select', optionsKey: 'departments', valueType: 'int', required: true }
            ]}
          />
        )}
      </div>
    </div>
  )
}
