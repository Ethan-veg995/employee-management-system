import { beforeEach, describe, expect, it, vi } from 'vitest'

// 用假的 ElMessage / 路由 / store 替换真实依赖，只测 axios 拦截器本身
const { ElMessageMock, routerMock, storeMock } = vi.hoisted(() => ({
  ElMessageMock: { error: vi.fn(), success: vi.fn() },
  routerMock: { push: vi.fn() },
  storeMock: { token: 'mock-token', logout: vi.fn(), user: { role: 'employee' } },
}))

vi.mock('element-plus', () => ({ ElMessage: ElMessageMock }))
vi.mock('../router', () => ({ default: routerMock }))
vi.mock('../store/user', () => ({ useUserStore: () => storeMock }))

import request from './request'

describe('请求封装 request', () => {
  const reqHandler = request.interceptors.request.handlers[0].fulfilled
  const respErrorHandler = request.interceptors.response.handlers[0].rejected

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('请求前自动带上登录令牌', () => {
    const config = reqHandler({ headers: {} })
    expect(config.headers.Authorization).toBe('Bearer mock-token')
  })

  it('未登录时请求不带头部（不报错）', () => {
    storeMock.token = ''
    const config = reqHandler({ headers: {} })
    expect(config.headers.Authorization).toBeUndefined()
    storeMock.token = 'mock-token'
  })

  it('接口返回 401 时：登出并跳转登录页、提示用户', async () => {
    const err = { response: { status: 401, data: { detail: '未登录' } } }
    await expect(respErrorHandler(err)).rejects.toBe(err)
    expect(storeMock.logout).toHaveBeenCalledTimes(1)
    expect(routerMock.push).toHaveBeenCalledWith('/login')
    expect(ElMessageMock.error).toHaveBeenCalled()
  })

  it('普通业务错误：提示后端返回的 detail 信息', async () => {
    const err = { response: { status: 400, data: { detail: '用户名或密码错误' } } }
    await expect(respErrorHandler(err)).rejects.toBe(err)
    expect(ElMessageMock.error).toHaveBeenCalledWith('用户名或密码错误')
  })

  it('detail 为对象时取 message 字段', async () => {
    const err = { response: { status: 400, data: { detail: { message: '参数有误' } } } }
    await expect(respErrorHandler(err)).rejects.toBe(err)
    expect(ElMessageMock.error).toHaveBeenCalledWith('参数有误')
  })
})
