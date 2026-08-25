<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <b>我的申请</b>
        <div>
          <el-select v-model="query.request_type" placeholder="全部类型" clearable style="width:120px;margin-right:8px" @change="load">
            <el-option v-for="t in ['请假', '加班', '报销', '出差']" :key="t" :label="t" :value="t" />
          </el-select>
          <el-select v-model="query.status" placeholder="全部状态" clearable style="width:120px" @change="load">
            <el-option v-for="s in ['待审批', '已通过', '已驳回']" :key="s" :label="s" :value="s" />
          </el-select>
        </div>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <el-tag :type="typeTag(row.request_type)" size="small">{{ row.request_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
      <el-table-column label="金额/天数" width="110">
        <template #default="{ row }">
          <span v-if="row.amount">¥{{ row.amount }}</span>
          <span v-else-if="row.days">{{ row.days }} 天</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="起止日期" width="180">
        <template #default="{ row }">
          {{ row.start_date ? `${row.start_date} ~ ${row.end_date}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="reason" label="事由" min-width="120" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="{ '待审批': 'warning', '已通过': 'success', '已驳回': 'danger' }[row.status]" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="approve_comment" label="审批意见" min-width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ row.approve_comment || '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="申请时间" width="150">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!list.length && !loading" description="暂无申请记录" />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { myApprovals } from '../api'

const list = ref([])
const loading = ref(false)
const query = reactive({ request_type: '', status: '' })

function typeTag(t) {
  return { 请假: 'warning', 加班: 'primary', 报销: 'success', 出差: 'info' }[t] || 'info'
}

async function load() {
  loading.value = true
  try {
    list.value = await myApprovals(query)
  } finally { loading.value = false }
}

onMounted(load)
</script>
