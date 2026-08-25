import { describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
vi.mock('../utils/request', () => ({ default: { get: (...a) => getMock(...a) } }))
const { exportEmployees } = await import('./index')

describe('API 封装：导出员工 Excel（blob 下载）', () => {
  it('以 blob 方式请求导出接口并透传筛选参数', () => {
    exportEmployees({ keyword: '张', status: '在职' })
    expect(getMock).toHaveBeenCalledWith('/employees/export/excel', {
      params: { keyword: '张', status: '在职' },
      responseType: 'blob',
    })
  })
})
