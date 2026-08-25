import { describe, expect, it, vi } from 'vitest'
import { disposeChart, pieOption } from './chart'

describe('图表工具函数', () => {
  it('pieOption 生成饼图配置：标题和数据映射正确', () => {
    const opt = pieOption('部门分布', [
      { name: '技术部', value: 3 },
      { name: '人事部', value: 1 },
    ])
    expect(opt.title.text).toBe('部门分布')
    expect(opt.series[0].type).toBe('pie')
    expect(opt.series[0].data).toEqual([
      { name: '技术部', value: 3 },
      { name: '人事部', value: 1 },
    ])
  })

  it('pieOption 空数据也能生成配置（不报错）', () => {
    const opt = pieOption('测试', [])
    expect(opt.series[0].data).toEqual([])
  })

  it('disposeChart 对空值不报错', () => {
    expect(() => disposeChart(null)).not.toThrow()
    expect(() => disposeChart(undefined)).not.toThrow()
  })

  it('disposeChart 正常断开监听并销毁图表', () => {
    const ro = { disconnect: vi.fn() }
    const chart = { dispose: vi.fn() }
    disposeChart({ chart, ro })
    expect(ro.disconnect).toHaveBeenCalledTimes(1)
    expect(chart.dispose).toHaveBeenCalledTimes(1)
  })
})
