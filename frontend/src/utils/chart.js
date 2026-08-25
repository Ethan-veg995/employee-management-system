import * as echarts from 'echarts'

export function renderChart(el, option) {
  const chart = echarts.init(el)
  chart.setOption(option)
  const ro = new ResizeObserver(() => chart.resize())
  ro.observe(el)
  return { chart, ro }
}

export function disposeChart(render) {
  if (!render) return
  render.ro?.disconnect()
  render.chart?.dispose()
}

export const PIE_COLORS = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9B59B6', '#1ABC9C', '#E67E22']

export function pieOption(title, data) {
  return {
    title: { text: title, left: 'center', textStyle: { fontSize: 15 } },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    color: PIE_COLORS,
    series: [{
      type: 'pie', radius: ['40%', '68%'], center: ['50%', '52%'],
      label: { formatter: '{b}\n{d}%' },
      data: data.map((d) => ({ name: d.name, value: d.value })),
    }],
  }
}
