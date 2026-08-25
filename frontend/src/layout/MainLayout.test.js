import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '../store/user'
import router from '../router'
import MainLayout from './MainLayout.vue'

// 接口层全部替换为假实现（不发起真实网络请求）
vi.mock('../api', () => ({
  unreadCount: vi.fn().mockResolvedValue({ count: 0 }),
  listNotifications: vi.fn().mockResolvedValue([]),
  markRead: vi.fn().mockResolvedValue({}),
  markAllRead: vi.fn().mockResolvedValue({}),
}))
vi.mock('element-plus', () => ({
  ElMessageBox: { confirm: vi.fn().mockResolvedValue('confirm') },
}))

// Element Plus 组件全部用"渲染插槽"的假组件替代，只保留菜单文字便于断言
const SlotStub = { template: '<div><slot /></div>' }
const stubs = {}
for (const name of [
  'el-container', 'el-aside', 'el-menu', 'el-menu-item', 'el-icon',
  'el-header', 'el-breadcrumb', 'el-breadcrumb-item', 'el-badge',
  'el-popover', 'el-button', 'el-avatar', 'el-tag', 'el-dropdown',
  'el-dropdown-menu', 'el-dropdown-item', 'el-main', 'TagsView',
  'OfficeBuilding', 'Bell', 'ArrowDown',
]) {
  stubs[name] = SlotStub
}
stubs.RouterView = { template: '<div />' }

async function mountAs(role, username = role) {
  setActivePinia(createPinia())
  const store = useUserStore()
  store.setLogin('t-' + role, { username, role })
  // 每个角色导航到自己的默认首页
  const home = role === 'admin' ? '/users' : role === 'hr' ? '/dashboard' : '/my-dashboard'
  await router.push(home)
  return mount(MainLayout, {
    global: { plugins: [router], stubs },
  })
}

describe('侧边菜单：按角色过滤', () => {
  beforeEach(async () => {
    localStorage.clear()
    setActivePinia(createPinia())
    await router.push('/login')
  })

  it('admin 只看到用户管理和无限制菜单', async () => {
    const wrapper = await mountAs('admin')
    const text = wrapper.text()
    expect(text).toContain('用户管理')
    expect(text).toContain('公告中心')
    expect(text).not.toContain('数据看板')
    expect(text).not.toContain('我的工作台')
    expect(text).not.toContain('部门管理')
    // 菜单里不应有"员工管理"（标题"员工管理系统"除外）
    expect(text.replace('员工管理系统', '').includes('员工管理')).toBe(false)
    wrapper.unmount()
  })

  it('hr 看到人事业务菜单，看不到用户管理', async () => {
    const wrapper = await mountAs('hr')
    const text = wrapper.text()
    expect(text).toContain('数据看板')
    expect(text).toContain('部门管理')
    expect(text).toContain('员工管理')
    expect(text).toContain('薪资管理')
    expect(text).toContain('待我审批')
    expect(text).toContain('公告中心')
    expect(text).not.toContain('用户管理')
    expect(text).not.toContain('我的工作台')
    wrapper.unmount()
  })

  it('manager 看到工作台/审批/绩效菜单，看不到人事管理菜单', async () => {
    const wrapper = await mountAs('manager')
    const text = wrapper.text()
    expect(text).toContain('我的工作台')
    expect(text).toContain('待我审批')
    expect(text).toContain('绩效管理')
    expect(text).toContain('考勤打卡')
    expect(text).toContain('公告中心')
    expect(text).not.toContain('数据看板')
    expect(text).not.toContain('部门管理')
    expect(text).not.toContain('用户管理')
    wrapper.unmount()
  })

  it('员工看到个人业务菜单，看不到任何管理菜单', async () => {
    const wrapper = await mountAs('employee')
    const text = wrapper.text()
    expect(text).toContain('我的工作台')
    expect(text).toContain('考勤打卡')
    expect(text).toContain('发起申请')
    expect(text).toContain('我的申请')
    expect(text).toContain('公告中心')
    expect(text).not.toContain('数据看板')
    expect(text).not.toContain('部门管理')
    expect(text).not.toContain('用户管理')
    expect(text).not.toContain('待我审批')
    wrapper.unmount()
  })
})
