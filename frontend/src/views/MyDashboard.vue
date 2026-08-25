<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header><b>我的信息</b></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ data.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="工号">{{ data.employee_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="部门">{{ data.department || '-' }}</el-descriptions-item>
            <el-descriptions-item label="职位">{{ data.position || '-' }}</el-descriptions-item>
            <el-descriptions-item label="今日考勤状态">
              <el-tag :type="statusType(data.today_status)">{{ data.today_status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="本月请假天数">{{ data.month_leave_days }} 天</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><b>快捷操作</b></template>
          <div style="display:flex;flex-direction:column;gap:12px">
            <el-button type="primary" size="large" @click="$router.push('/attendance/punch')">
              <el-icon style="margin-right:6px"><AlarmClock /></el-icon>去打卡
            </el-button>
            <el-button type="success" size="large" @click="$router.push('/approval/apply')">
              <el-icon style="margin-right:6px"><EditPen /></el-icon>申请请假
            </el-button>
            <el-button size="large" @click="$router.push('/salary/my')">
              <el-icon style="margin-right:6px"><Wallet /></el-icon>查看薪资
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top:16px">
      <template #header><b>本月考勤统计</b></template>
      <el-row :gutter="16">
        <el-col :span="4" v-for="s in statItems" :key="s.label">
          <div class="mini-stat">
            <div class="mini-num" :style="{ color: s.color }">{{ s.value }}</div>
            <div class="mini-label">{{ s.label }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="data.latest_salary" shadow="hover" style="margin-top:16px">
      <template #header><b>最近薪资（{{ data.latest_salary.year }}年{{ data.latest_salary.month }}月）</b></template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="基本工资">¥{{ data.latest_salary.base_salary }}</el-descriptions-item>
        <el-descriptions-item label="绩效奖金">¥{{ data.latest_salary.bonus }}</el-descriptions-item>
        <el-descriptions-item label="扣款">¥{{ data.latest_salary.deduction }}</el-descriptions-item>
        <el-descriptions-item label="实发工资">
          <b style="color:#E6A23C">¥{{ data.latest_salary.actual_salary }}</b>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="hover" style="margin-top:16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b>最新公告</b>
          <el-button link type="primary" size="small" @click="$router.push('/announcements')">查看全部</el-button>
        </div>
      </template>
      <div v-for="a in announcements" :key="a.id" class="ann-item">
        <el-icon color="#409EFF" style="margin-top:2px"><Bell /></el-icon>
        <div style="flex:1;min-width:0">
          <div class="ann-title">{{ a.title }}</div>
          <div class="ann-meta">{{ a.publisher_name }} · {{ a.created_at?.replace('T', ' ').slice(0, 10) }}</div>
        </div>
      </div>
      <el-empty v-if="!announcements.length" description="暂无公告" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { myDashboard, listAnnouncements } from '../api'

const data = ref({})
const announcements = ref([])
const statItems = computed(() => {
  const s = data.value.month_attendance || {}
  return [
    { label: '应出勤天数', value: s.workdays ?? '-', color: '#409EFF' },
    { label: '实际出勤', value: s.attended ?? '-', color: '#67C23A' },
    { label: '迟到次数', value: s.late ?? '-', color: '#E6A23C' },
    { label: '早退次数', value: s.early ?? '-', color: '#E6A23C' },
    { label: '缺卡次数', value: s.missing_punch ?? '-', color: '#F56C6C' },
    { label: '出勤率', value: `${s.rate ?? '-'}%`, color: '#409EFF' },
  ]
})

function statusType(s) {
  return { 正常: 'success', 迟到: 'warning', 早退: 'warning', 缺卡: 'danger', 未打卡: 'info', 已打卡: 'success' }[s] || 'info'
}

onMounted(async () => {
  data.value = await myDashboard()
  announcements.value = (await listAnnouncements()).slice(0, 3)
})
</script>

<style scoped>
.mini-stat { text-align: center; padding: 8px 0; }
.mini-num { font-size: 24px; font-weight: 700; }
.mini-label { font-size: 13px; color: #909399; margin-top: 4px; }
.ann-item { display: flex; gap: 10px; padding: 10px 4px; border-bottom: 1px dashed #eee; }
.ann-item:last-child { border-bottom: none; }
.ann-title { font-size: 14px; color: #303133; }
.ann-meta { font-size: 12px; color: #c0c4cc; margin-top: 2px; }
</style>
