<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>消息中心</b>
        <el-button type="primary" size="small" @click="onAllRead">全部已读</el-button>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="{ todo: 'warning', result: 'success', announcement: 'primary' }[row.type]" size="small">
            {{ { todo: '待办', result: '审批结果', announcement: '公告' }[row.type] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="标题" min-width="160">
        <template #default="{ row }">
          <span :class="{ 'unread-title': !row.is_read }">{{ row.title }}</span>
          <el-tag v-if="!row.is_read" type="danger" size="small" style="margin-left:8px">新</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="160">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <el-button v-if="!row.is_read" link type="primary" size="small" @click="onRead(row)">标记已读</el-button>
          <el-button link type="info" size="small" @click="onJump(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!list.length && !loading" description="暂无消息" />
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listNotifications, markRead, markAllRead } from '../api'
import { useUserStore } from '../store/user'

const router = useRouter()
const store = useUserStore()
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { list.value = await listNotifications({ limit: 100 }) } finally { loading.value = false }
}

async function onRead(row) {
  await markRead(row.id)
  row.is_read = 1
}

async function onAllRead() {
  await markAllRead()
  ElMessage.success('全部已读')
  load()
}

function onJump(row) {
  if (row.type === 'todo' && store.user.role !== 'employee') router.push('/approval/approve')
  else if (row.type === 'announcement') router.push('/announcements')
}

onMounted(load)
</script>

<style scoped>
.unread-title { font-weight: 600; color: #303133; }
</style>
