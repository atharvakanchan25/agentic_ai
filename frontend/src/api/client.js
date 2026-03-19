import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ── JWT interceptor — attach token to every request ──────────────────────────
api.interceptors.request.use(config => {
  try {
    const user = JSON.parse(localStorage.getItem('tt_user'))
    if (user?.token) config.headers.Authorization = `Bearer ${user.token}`
  } catch {}
  return config
})

// ── Auth ──────────────────────────────────────────────────────────────────────
export const register = (data)  => api.post('/auth/register', data)
export const login    = (data)  => api.post('/auth/login', data)
export const getMe    = ()      => api.get('/auth/me')

// ── Departments ───────────────────────────────────────────────────────────────
export const getDepartments   = ()         => api.get('/departments')
export const createDepartment = (data)     => api.post('/departments', data)
export const updateDepartment = (id, data) => api.put(`/departments/${id}`, data)
export const deleteDepartment = (id)       => api.delete(`/departments/${id}`)

// ── Subjects ──────────────────────────────────────────────────────────────────
export const getSubjects   = ()         => api.get('/subjects')
export const createSubject = (data)     => api.post('/subjects', data)
export const updateSubject = (id, data) => api.put(`/subjects/${id}`, data)
export const deleteSubject = (id)       => api.delete(`/subjects/${id}`)

// ── Rooms ─────────────────────────────────────────────────────────────────────
export const getRooms   = ()         => api.get('/rooms')
export const createRoom = (data)     => api.post('/rooms', data)
export const updateRoom = (id, data) => api.put(`/rooms/${id}`, data)
export const deleteRoom = (id)       => api.delete(`/rooms/${id}`)

// ── Faculty ───────────────────────────────────────────────────────────────────
export const getFaculty   = ()         => api.get('/faculty')
export const createFaculty = (data)    => api.post('/faculty', data)
export const updateFaculty = (id, data) => api.put(`/faculty/${id}`, data)
export const deleteFaculty = (id)      => api.delete(`/faculty/${id}`)

// ── Divisions ─────────────────────────────────────────────────────────────────
export const getDivisions   = ()         => api.get('/divisions')
export const createDivision = (data)     => api.post('/divisions', data)
export const updateDivision = (id, data) => api.put(`/divisions/${id}`, data)
export const deleteDivision = (id)       => api.delete(`/divisions/${id}`)

// ── Timeslots ─────────────────────────────────────────────────────────────────
export const getTimeslots = () => api.get('/timeslots')

// ── Timetable ─────────────────────────────────────────────────────────────────
export const generateTimetable    = (department_ids, save = false, name = null) =>
  api.post('/timetable/generate', { department_ids, save, name })

export const getSavedTimetables   = ()    => api.get('/timetable/saved')
export const getSavedTimetable    = (id)  => api.get(`/timetable/saved/${id}`)
export const deleteSavedTimetable = (id)  => api.delete(`/timetable/saved/${id}`)

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendChat = (message) => api.post('/chat', { message })
