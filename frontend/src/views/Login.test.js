import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import router from '../router'
import Login from './Login.vue'

const { loginApiMock } = vi.hoisted(() => ({ loginApiMock: vi.fn() }))
vi.mock('../api', () => ({ loginApi: loginApiMock }))
vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
}))

// Element Plus 表单相关组件的轻量替身
const stubs = {
  'el-card': { template: '<div><slot /></div>' },
  'el-form': {
    template: '<form><slot /></form>',
    methods: { validate: () => Promise.resolve() },
  },
  'el-form-item': { template: '<div><slot /></div>' },
  'el-input': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
  'el-button': { template: '<button type="button"><slot /></button>' },
  'el-divider': { template: '<div />' },
  'el-icon': { template: '<span><slot /></span>' },
}

async function doLogin(role) {
  const pinia = createPinia()
  setActivePinia(pinia)
  loginApiMock.mockResolvedValue({
    token: 't-' + role,
    user: { username: role, role },
  })
  const wrapper = mount(Login, { global: { plugins: [router, pinia], stubs } })
  await router.isReady()
  const inputs = wrapper.findAll('input')
  await inputs[0].setValue(role)
  await inputs[1].setValue('123456')
  await wrapper.findAll('button')[0].trigger('click')
  await flushPromises()
  return wrapper
}

describe('登录页', () => {
  beforeEach(async () => {
    localStorage.clear()
    setActivePinia(createPinia())
    await router.push('/login')
  })

  it('登录成功后登录信息写入本地存储', async () => {
    await doLogin('employee')
    expect(localStorage.getItem('token')).toBe('t-employee')
    expect(JSON.parse(localStorage.getItem('user')).role).toBe('employee')
  })
})
