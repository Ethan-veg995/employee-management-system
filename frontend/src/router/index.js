import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '数据看板', roles: ['hr'] } },
      { path: 'my-dashboard', component: () => import('../views/MyDashboard.vue'), meta: { title: '我的工作台', roles: ['employee', 'manager'] } },
      { path: 'departments', component: () => import('../views/Department.vue'), meta: { title: '部门管理', roles: ['hr'] } },
      { path: 'positions', component: () => import('../views/Position.vue'), meta: { title: '职位管理', roles: ['hr'] } },
      { path: 'employees', component: () => import('../views/Employee.vue'), meta: { title: '员工管理', roles: ['hr'] } },
      { path: 'attendance/punch', component: () => import('../views/AttendancePunch.vue'), meta: { title: '考勤打卡', roles: ['employee', 'manager'] } },
      { path: 'attendance/rule', component: () => import('../views/AttendanceRule.vue'), meta: { title: '考勤规则', roles: ['hr'] } },
      { path: 'attendance/monthly', component: () => import('../views/AttendanceMonthly.vue'), meta: { title: '月度考勤', roles: ['hr'] } },
      { path: 'approval/apply', component: () => import('../views/ApprovalApply.vue'), meta: { title: '发起申请', roles: ['employee', 'manager'] } },
      { path: 'approval/mine', component: () => import('../views/ApprovalMine.vue'), meta: { title: '我的申请', roles: ['employee', 'manager'] } },
      { path: 'approval/approve', component: () => import('../views/ApprovalApprove.vue'), meta: { title: '待我审批', roles: ['manager', 'hr'] } },
      { path: 'approval/all', component: () => import('../views/ApprovalAll.vue'), meta: { title: '审批记录', roles: ['hr'] } },
      { path: 'performance/manage', component: () => import('../views/PerformanceManage.vue'), meta: { title: '绩效管理', roles: ['manager', 'hr'] } },
      { path: 'performance/my', component: () => import('../views/MyPerformance.vue'), meta: { title: '我的绩效', roles: ['employee', 'manager'] } },
      { path: 'announcements', component: () => import('../views/Announcement.vue'), meta: { title: '公告中心' } },
      { path: 'notifications', component: () => import('../views/Notification.vue'), meta: { title: '消息中心' } },
      { path: 'salary/manage', component: () => import('../views/SalaryManage.vue'), meta: { title: '薪资管理', roles: ['hr'] } },
      { path: 'salary/my', component: () => import('../views/MySalary.vue'), meta: { title: '我的薪资', roles: ['employee', 'manager'] } },
      { path: 'users', component: () => import('../views/UserManage.vue'), meta: { title: '用户管理', roles: ['admin'] } },
      { path: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const store = useUserStore()
  document.title = to.meta.title ? `${to.meta.title} - 企业员工管理系统` : '企业员工管理系统'
  if (to.meta.public) return true
  if (!store.isLogin || !store.user) return '/login'
  if (to.meta.roles && !to.meta.roles.includes(store.user.role)) {
    if (store.user.role === 'admin') return '/users'
    return store.user.role === 'hr' ? '/dashboard' : '/my-dashboard'
  }
  return true
})

export default router
