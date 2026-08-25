<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card shadow="hover">
        <template #header><b>今日打卡</b></template>
        <div class="punch-panel">
          <el-statistic title="当前时间" :value="now" :formatter="() => timeStr" style="margin-bottom:24px" />
          <div style="display:flex;gap:16px;justify-content:center">
            <el-button type="primary" size="large" :icon="Clock" :disabled="!!today?.check_in"
                       :loading="punching" @click="punch('check_in')">
              {{ today?.check_in ? `上班已打卡 ${today.check_in}` : '上班打卡' }}
            </el-button>
            <el-button type="success" size="large" :icon="Clock" :disabled="!today?.check_in || !!today?.check_out"
                       :loading="punching" @click="punch('check_out')">
              {{ today?.check_out ? `下班已打卡 ${today.check_out}` : '下班打卡' }}
            </el-button>
          </div>
          <el-tag v-if="today?.status" :type="tagType(today.status)" size="large" style="margin-top:20px">
            今日状态：{{ today.status }}
          </el-tag>
        </div>
      </el-card>
    </el-col>
    <el-col :span="14">
      <el-card shadow="hover">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <b>本月打卡记录</b>
            <el-date-picker v-model="month" type="month" value-format="YYYY-MM" style="width:140px"
                            @change="load" />
          </div>
        </template>
        <el-table :data="data.records" stripe max-height="480">
          <el-table-column prop="date" label="日期" width="110" />
          <el-table-column prop="check_in" label="上班打卡" width="120">
            <template #default="{ row }">{{ row.check_in || '-' }}</template>
          </el-table-column>
          <el-table-column prop="check_out" label="下班打卡" width="120">
            <template #default="{ row }">{{ row.check_out || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态">
            <template #default="{ row }">
              <el-tag :type="tagType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { punchApi, myAttendance } from '../api'

const month = ref(new Date().toISOString().slice(0, 7))
const data = ref({ records: [] })
const today = ref(null)
const punching = ref(false)
const timeStr = ref('')
let timer = null

function tagType(s) {
  return { 正常: 'success', 迟到: 'warning', 早退: 'warning', 缺卡: 'danger' }[s] || 'info'
}

function tick() {
  timeStr.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

async function load() {
  data.value = await myAttendance({ month: month.value })
  today.value = data.value.records.find((r) => r.date === new Date().toISOString().slice(0, 10)) || null
}

async function punch(type) {
  punching.value = true
  try {
    const res = await punchApi(type)
    ElMessage.success(res.message)
    await load()
  } finally { punching.value = false }
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
  load()
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.punch-panel { text-align: center; padding: 20px 0; }
</style>
