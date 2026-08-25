import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '../store/user'
import router from './index'

// 登录指定角色（写入真实 store + localStorage）
function loginAs(role, username = role) {
  const store = useUserStore()
  store.setLogin('token-' + role, { username, role })
}

describe('路由守卫：按角色拦截和重定向', () => {
  beforeEach(async () => {
    localStorage.clear()
    setActivePinia(createPinia())
    await router.push('/login')
    router.currentRoute.value = router.currentRoute.value // 确保导航完成
  })

  it('未登录访问受保护页面 -> 跳转登录页', async () => {
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('未登录访问登录页本身 -> 放行', async () => {
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('admin 访问用户管理 -> 放行', async () => {
    loginAs('admin')
    await router.push('/users')
    expect(router.currentRoute.value.path).toBe('/users')
  })

  it('admin 访问人事页面 -> 重定向到用户管理', async () => {
    loginAs('admin')
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/users')
  })

  it('admin 访问根路径 -> 重定向到用户管理', async () => {
    loginAs('admin')
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/users')
  })

  it('hr 访问数据看板 -> 放行', async () => {
    loginAs('hr')
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('hr 访问用户管理 -> 重定向到数据看板', async () => {
    loginAs('hr')
    await router.push('/users')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('员工访问我的工作台 -> 放行', async () => {
    loginAs('employee')
    await router.push('/my-dashboard')
    expect(router.currentRoute.value.path).toBe('/my-dashboard')
  })

  it('员工访问人事页面 -> 重定向到我的工作台', async () => {
    loginAs('employee')
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/my-dashboard')
  })

  it('员工访问根路径 -> 重定向到我的工作台', async () => {
    loginAs('employee')
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/my-dashboard')
  })

  it('主管访问待我审批 -> 放行', async () => {
    loginAs('manager')
    await router.push('/approval/approve')
    expect(router.currentRoute.value.path).toBe('/approval/approve')
  })

  it('主管访问薪资管理(仅hr) -> 重定向到我的工作台', async () => {
    loginAs('manager')
    await router.push('/salary/manage')
    expect(router.currentRoute.value.path).toBe('/my-dashboard')
  })

  it('无角色限制的公告中心 -> 所有登录角色可访问', async () => {
    loginAs('employee')
    await router.push('/announcements')
    expect(router.currentRoute.value.path).toBe('/announcements')
  })

  it('本地只有令牌但用户信息缺失时 -> 守卫重定向到登录页', async () => {
    // 模拟 token 还在但 user 数据丢失的异常状态
    localStorage.setItem('token', 'orphan-token')
    setActivePinia(createPinia())
    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/login')
  })
})
