<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>月度考勤统计</b>
        <div>
          <el-select v-model="query.department_id" placeholder="全部部门" clearable style="width:140px;margin-right:8px" @change="load">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
          <el-date-picker v-model="query.month" type="month" value-format="YYYY-MM" style="width:140px" @change="load" />
        </div>
      </div>
    </template>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="employee_no" label="工号" width="100" />
      <el-table-column prop="employee_name" label="姓名" width="100" />
      <el-table-column prop="department" label="部门" width="110" />
      <el-table-column prop="workdays" label="应出勤" width="80" align="center" />
      <el-table-column prop="attended" label="实际出勤" width="90" align="center" />
      <el-table-column label="迟到" width="80" align="center">
        <template #default="{ row }"><span :style="{ color: row.late ? '#E6A23C' : '' }">{{ row.late }}</span></template>
      </el-table-column>
      <el-table-column label="早退" width="80" align="center">
        <template #default="{ row }"><span :style="{ color: row.early ? '#E6A23C' : '' }">{{ row.early }}</span></template>
      </el-table-column>
      <el-table-column label="缺卡" width="80" align="center">
        <template #default="{ row }"><span :style="{ color: row.missing_punch ? '#F56C6C' : '' }">{{ row.missing_punch }}</span></template>
      </el-table-column>
      <el-table-column label="请假天数" width="90" align="center">
        <template #default="{ row }">{{ row.leave_days }}</template>
      </el-table-column>
      <el-table-column label="出勤率" width="110" align="center">
        <template #default="{ row }">
          <el-progress :percentage="row.rate" :color="row.rate >= 90 ? '#67C23A' : '#E6A23C'" :stroke-width="10" />
        </template>
      </el-table-column>
    </el-table>
    <el-alert style="margin-top:12px" type="info" :closable="false"
              title="说明：应出勤=当月工作日(周一至周五)；出勤率=实际出勤÷(应出勤-已通过请假天数)" />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { monthlyAttendance, listDepartments } from '../api'

const items = ref([])
const departments = ref([])
const loading = ref(false)
const query = reactive({ month: new Date().toISOString().slice(0, 7), department_id: null })

async function load() {
  loading.value = true
  try {
    const data = await monthlyAttendance(query)
    items.value = data.items
  } finally { loading.value = false }
}

onMounted(async () => {
  departments.value = await listDepartments()
  load()
})
</script>
