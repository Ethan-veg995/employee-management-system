<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <div class="stat-card" :style="{ background: c.gradient }">
          <div class="stat-left">
            <div class="stat-num">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
          <el-icon :size="44" color="rgba(255,255,255,.85)"><component :is="c.icon" /></el-icon>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <div ref="deptChart" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <div ref="levelChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <div ref="leaveChart" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <div ref="salaryChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 智能提醒 -->
    <el-card shadow="hover" style="margin-top:16px">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px">
          <el-icon :size="18" color="#E6A23C"><MagicStick /></el-icon>
          <b>智能考勤异常提醒</b>
          <el-tag size="small" type="warning">规则引擎自动检测</el-tag>
        </div>
      </template>
      <el-empty v-if="!alerts.length" description="暂无异常，所有员工考勤状态良好" />
      <el-table v-else :data="alerts" stripe>
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <el-tag :type="row.level === 'danger' ? 'danger' : 'warning'" size="small">
              {{ row.level === 'danger' ? '严重' : '提醒' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="类型" width="140" />
        <el-table-column prop="employee_name" label="涉及员工" width="120">
          <template #default="{ row }">{{ row.employee_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { dashboardSummary, alertsApi } from '../api'
import { renderChart, disposeChart, pieOption, PIE_COLORS } from '../utils/chart'

const deptChart = ref()
const levelChart = ref()
const leaveChart = ref()
const salaryChart = ref()
const summary = ref(null)
const alerts = ref([])
const renders = []

const cards = computed(() => {
  const s = summary.value
  if (!s) return []
  return [
    { label: '在职员工总数', value: s.total_employees, icon: 'User', gradient: 'linear-gradient(135deg,#409EFF,#3375c9)' },
    { label: '本月入职', value: s.hired_this_month, icon: 'Plus', gradient: 'linear-gradient(135deg,#67C23A,#4d9e28)' },
    { label: '累计离职', value: s.left_this_month, icon: 'Minus', gradient: 'linear-gradient(135deg,#F56C6C,#d94a4a)' },
    { label: `本月出勤率 (上月${s.last_month_rate}%)`, value: `${s.attendance_rate}%`, icon: 'AlarmClock', gradient: 'linear-gradient(135deg,#E6A23C,#c9821f)' },
  ]
})

onMounted(async () => {
  summary.value = await dashboardSummary()
  alerts.value = await alertsApi()
  const s = summary.value
  renders.push(renderChart(deptChart.value, pieOption('部门人数分布', s.dept_distribution)))
  renders.push(renderChart(levelChart.value, pieOption('职级比例', s.level_distribution)))
  renders.push(renderChart(leaveChart.value, {
    title: { text: '本月请假统计（各类型天数）', left: 'center', textStyle: { fontSize: 15 } },
    tooltip: {},
    grid: { left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: s.leave_stats.map((d) => d.name) },
    yAxis: { type: 'value', name: '天数' },
    color: PIE_COLORS,
    series: [{ type: 'bar', barWidth: 40, data: s.leave_stats.map((d) => d.value),
               itemStyle: { borderRadius: [6, 6, 0, 0] } }],
  }))
  renders.push(renderChart(salaryChart.value, {
    title: { text: '薪资总额趋势（近6个月）', left: 'center', textStyle: { fontSize: 15 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: s.salary_trend.map((d) => d.month) },
    yAxis: { type: 'value', name: '元' },
    series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.15 },
               data: s.salary_trend.map((d) => d.total) }],
  }))
})

onBeforeUnmount(() => renders.forEach(disposeChart))
</script>

<style scoped>
.stat-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 22px 24px; border-radius: 10px; color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, .12);
}
.stat-num { font-size: 30px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 13px; opacity: .9; margin-top: 6px; }
</style>
