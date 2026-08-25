<template>
  <el-card shadow="hover">
    <template #header>
      <b>待我审批</b>
      <el-badge :value="list.length" style="margin-left:10px" />
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="employee_name" label="申请人" width="100" />
      <el-table-column prop="department_name" label="部门" width="110" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <el-tag :type="{ 请假: 'warning', 加班: 'primary', 报销: 'success', 出差: 'info' }[row.request_type]" size="small">
            {{ row.request_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="130" show-overflow-tooltip />
      <el-table-column label="金额/天数" width="110">
        <template #default="{ row }">
          <span v-if="row.amount">¥{{ row.amount }}</span>
          <span v-else-if="row.days">{{ row.days }} 天</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="起止日期" width="175">
        <template #default="{ row }">
          {{ row.start_date ? `${row.start_date} ~ ${row.end_date}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" min-width="120" show-overflow-tooltip />
      <el-table-column prop="created_at" label="申请时间" width="150">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" :icon="Check" @click="onApprove(row, '通过')">通过</el-button>
          <el-button size="small" type="danger" :icon="Close" @click="onApprove(row, '驳回')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!list.length && !loading" description="暂无待审批的申请" />
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Check, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { pendingApprovals, approveRequest } from '../api'

const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { list.value = await pendingApprovals() } finally { loading.value = false }
}

async function onApprove(row, action) {
  const { value } = await ElMessageBox.prompt(
    `${action}「${row.employee_name}」的${row.request_type}申请「${row.title}」？`, action, {
    inputPlaceholder: '审批意见（可选）',
  })
  await approveRequest(row.id, { action, comment: value || '' })
  ElMessage.success(`已${action}，结果已通知申请人`)
  load()
}

onMounted(load)
</script>
