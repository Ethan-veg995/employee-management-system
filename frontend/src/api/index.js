import request from '../utils/request'

// 认证
export const loginApi = (data) => request.post('/auth/login', data)
export const meApi = () => request.get('/auth/me')
export const resetPasswordApi = (data) => request.post('/auth/reset-password', data)

// 部门
export const listDepartments = () => request.get('/departments')
export const createDepartment = (data) => request.post('/departments', data)
export const updateDepartment = (id, data) => request.put(`/departments/${id}`, data)
export const deleteDepartment = (id) => request.delete(`/departments/${id}`)

// 职位
export const listPositions = () => request.get('/positions')
export const createPosition = (data) => request.post('/positions', data)
export const updatePosition = (id, data) => request.put(`/positions/${id}`, data)
export const deletePosition = (id) => request.delete(`/positions/${id}`)

// 员工
export const listEmployees = (params) => request.get('/employees', { params })
export const allEmployees = () => request.get('/employees/all')
export const createEmployee = (data) => request.post('/employees', data)
export const updateEmployee = (id, data) => request.put(`/employees/${id}`, data)
export const deleteEmployee = (id) => request.delete(`/employees/${id}`)
export const exportEmployeesUrl = (params) => {
  const q = new URLSearchParams(params || {}).toString()
  return `/api/v1/employees/export/excel${q ? `?${q}` : ''}`
}
export const importEmployees = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/employees/import/excel', form)
}

// 考勤
export const getAttendanceRule = () => request.get('/attendance/rules')
export const updateAttendanceRule = (data) => request.put('/attendance/rules', data)
export const punchApi = (type) => request.post('/attendance/punch', { type })
export const myAttendance = (params) => request.get('/attendance/my', { params })
export const attendanceRecords = (params) => request.get('/attendance/records', { params })
export const monthlyAttendance = (params) => request.get('/attendance/monthly', { params })

// 审批（请假/加班/报销/出差）
export const createApproval = (data) => request.post('/approvals', data)
export const myApprovals = (params) => request.get('/approvals/my', { params })
export const pendingApprovals = () => request.get('/approvals/pending')
export const allApprovals = (params) => request.get('/approvals', { params })
export const approveRequest = (id, data) => request.post(`/approvals/${id}/approve`, data)

// 消息通知
export const listNotifications = (params) => request.get('/notifications', { params })
export const unreadCount = () => request.get('/notifications/unread-count')
export const markRead = (id) => request.post(`/notifications/${id}/read`)
export const markAllRead = () => request.post('/notifications/read-all')

// 绩效
export const listPerformance = (params) => request.get('/performance', { params })
export const myPerformance = () => request.get('/performance/my')
export const perfSuggest = (params) => request.get('/performance/suggest', { params })
export const createPerformance = (data) => request.post('/performance', data)
export const updatePerformance = (id, data) => request.put(`/performance/${id}`, data)
export const deletePerformance = (id) => request.delete(`/performance/${id}`)

// 公告
export const listAnnouncements = () => request.get('/announcements')
export const createAnnouncement = (data) => request.post('/announcements', data)
export const updateAnnouncement = (id, data) => request.put(`/announcements/${id}`, data)
export const deleteAnnouncement = (id) => request.delete(`/announcements/${id}`)

// 薪资
export const salaryYears = () => request.get('/salaries/years')
export const listSalaries = (params) => request.get('/salaries', { params })
export const mySalaries = () => request.get('/salaries/my')
export const createSalary = (data) => request.post('/salaries', data)
export const updateSalary = (id, data) => request.put(`/salaries/${id}`, data)
export const deleteSalary = (id) => request.delete(`/salaries/${id}`)

// 用户
export const listUsers = () => request.get('/users')
export const createUser = (data) => request.post('/users', data)
export const updateUser = (id, data) => request.put(`/users/${id}`, data)
export const deleteUser = (id) => request.delete(`/users/${id}`)

// 看板
export const dashboardSummary = () => request.get('/dashboard/summary')
export const myDashboard = () => request.get('/dashboard/my')
export const alertsApi = () => request.get('/alerts')
