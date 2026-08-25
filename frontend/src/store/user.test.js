import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from './user'

describe('用户登录状态 store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('初始状态：未登录', () => {
    const store = useUserStore()
    expect(store.isLogin).toBe(false)
    expect(store.roleName).toBe('')
  })

  it('setLogin 保存令牌和用户信息到本地存储', () => {
    const store = useUserStore()
    store.setLogin('token-abc', { username: 'hr', role: 'hr' })
    expect(store.token).toBe('token-abc')
    expect(store.user.username).toBe('hr')
    expect(localStorage.getItem('token')).toBe('token-abc')
    expect(JSON.parse(localStorage.getItem('user')).role).toBe('hr')
  })

  it('登录后 isLogin 为真，roleName 显示中文角色名', () => {
    const store = useUserStore()
    store.setLogin('t', { username: 'admin', role: 'admin' })
    expect(store.isLogin).toBe(true)
    expect(store.roleName).toBe('系统管理员')
  })

  it('logout 清空登录状态和本地存储', () => {
    const store = useUserStore()
    store.setLogin('t', { username: 'hr', role: 'hr' })
    store.logout()
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(store.isLogin).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('页面刷新后从本地存储恢复登录状态', () => {
    localStorage.setItem('token', 'saved-token')
    localStorage.setItem('user', JSON.stringify({ username: 'employee', role: 'employee' }))
    const store = useUserStore()
    expect(store.token).toBe('saved-token')
    expect(store.isLogin).toBe(true)
    expect(store.roleName).toBe('普通员工')
  })

  it('未知角色 roleName 返回空串', () => {
    localStorage.setItem('token', 't')
    localStorage.setItem('user', JSON.stringify({ username: 'x', role: 'boss' }))
    const store = useUserStore()
    expect(store.roleName).toBe('')
  })
})
