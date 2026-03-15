import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDepartments  = () => api.get('/departments')
export const createDepartment = (data) => api.post('/departments', data)
export const deleteDepartment = (id) => api.delete(`/departments/${id}`)

export const getSubjects    = () => api.get('/subjects')
export const createSubject  = (data) => api.post('/subjects', data)
export const deleteSubject  = (id) => api.delete(`/subjects/${id}`)

export const getRooms       = () => api.get('/rooms')
export const createRoom     = (data) => api.post('/rooms', data)
export const deleteRoom     = (id) => api.delete(`/rooms/${id}`)

export const getFaculty     = () => api.get('/faculty')
export const createFaculty  = (data) => api.post('/faculty', data)
export const deleteFaculty  = (id) => api.delete(`/faculty/${id}`)

export const getDivisions   = () => api.get('/divisions')
export const createDivision = (data) => api.post('/divisions', data)
export const deleteDivision = (id) => api.delete(`/divisions/${id}`)

export const getTimeslots   = () => api.get('/timeslots')

export const generateTimetable = (department_ids) =>
  api.post('/timetable/generate', { department_ids })

export const sendChat = (message) => api.post('/chat', { message })
