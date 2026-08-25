import { beforeEach, describe, expect, it } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '../store/user'
import router from '../router'
import TagsView from './TagsView.vue'

const stubs = {
  RouterLink: { template: '<a><slot /></a>' },
  'el-scrollbar': { template: '<div><slot /></div>' },
  'el-icon': { template: '<span><slot /></span>' },
  Close: true,
}

async function mountAt(role, path) {
  setActivePinia(createPinia())
  useUserStore().setLogin('t-' + role, { username: role, role })
  await router.push(path)
  return mount(TagsView, { global: { plugins: [router], stubs } })
}

describe('标签栏 TagsView：初始标签按角色区分', () => {
  beforeEach(async () => {
    localStorage.clear()
    setActivePinia(createPinia())
    await router.push('/login')
  })

  it('hr 的初始标签是数据看板', async () => {
    const wrapper = await mountAt('hr', '/dashboard')
    expect(wrapper.text()).toContain('数据看板')
    expect(wrapper.text()).not.toContain('用户管理')
    expect(wrapper.text()).not.toContain('我的工作台')
  })

  it('admin 的初始标签是用户管理', async () => {
    const wrapper = await mountAt('admin', '/users')
    expect(wrapper.text()).toContain('用户管理')
    expect(wrapper.text()).not.toContain('数据看板')
  })

  it('员工和主管的初始标签是我的工作台', async () => {
    const wrapper = await mountAt('employee', '/my-dashboard')
    expect(wrapper.text()).toContain('我的工作台')
    const wrapper2 = await mountAt('manager', '/my-dashboard')
    expect(wrapper2.text()).toContain('我的工作台')
  })

  it('访问新页面时自动追加标签（数据看板除外）', async () => {
    const wrapper = await mountAt('hr', '/dashboard')
    await router.push('/announcements')
    await flushPromises()
    expect(wrapper.text()).toContain('数据看板')
    expect(wrapper.text()).toContain('公告中心')
  })

  it('关闭当前标签后跳转到前一个标签', async () => {
    const wrapper = await mountAt('employee', '/my-dashboard')
    await router.push('/announcements')
    await flushPromises()
    expect(wrapper.findAll('a')).toHaveLength(2)

    // 点击公告中心标签上的关闭按钮
    await wrapper.findAll('a')[1].find('span').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/my-dashboard')
    expect(wrapper.findAll('a')).toHaveLength(1)
  })
})
