<template>
  <div>
    <el-card shadow="hover" v-if="canManage">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b>发布公告</b>
        </div>
      </template>
      <el-form :model="publishForm" :rules="rules" ref="publishRef" label-width="70px" inline style="align-items:flex-start">
        <el-form-item label="标题" prop="title" style="width:360px">
          <el-input v-model="publishForm.title" placeholder="公告标题" maxlength="50" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="publishForm.content" type="textarea" :rows="2" style="width:600px"
                    placeholder="公告正文（发布后将自动通知全体员工）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="publishing" @click="onPublish">发布</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" style="margin-top:16px">
      <template #header><b>公告列表</b><el-badge :value="list.length" style="margin-left:10px" /></template>
      <el-timeline v-loading="loading">
        <el-timeline-item v-for="a in list" :key="a.id" :timestamp="timeStr(a.created_at)" placement="top" type="primary">
          <el-card shadow="never" class="ann-card">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <b style="font-size:15px">{{ a.title }}</b>
              <div>
                <el-tag size="small" type="info">发布人：{{ a.publisher_name }}</el-tag>
                <el-button v-if="canManage" size="small" :icon="Edit" style="margin-left:8px" @click="onEdit(a)">编辑</el-button>
                <el-button v-if="canManage" size="small" type="danger" :icon="Delete" @click="onDelete(a)">删除</el-button>
              </div>
            </div>
            <div class="ann-content">{{ a.content }}</div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!list.length && !loading" description="暂无公告" />
    </el-card>

    <el-dialog v-model="editVisible" title="编辑公告" width="520px">
      <el-form :model="publishForm" label-width="70px">
        <el-form-item label="标题">
          <el-input v-model="publishForm.title" maxlength="50" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="publishForm.content" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="onEditSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement } from '../api'
import { useUserStore } from '../store/user'

const store = useUserStore()
const canManage = computed(() => ['hr', 'admin'].includes(store.user?.role))
const list = ref([])
const loading = ref(false)
const publishing = ref(false)
const editVisible = ref(false)
const editId = ref(null)
const publishRef = ref()
const publishForm = reactive({ title: '', content: '' })
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

function timeStr(s) {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}

async function load() {
  loading.value = true
  try { list.value = await listAnnouncements() } finally { loading.value = false }
}

async function onPublish() {
  await publishRef.value.validate()
  publishing.value = true
  try {
    await createAnnouncement(publishForm)
    ElMessage.success('公告已发布，已通知全体员工')
    publishForm.title = ''
    publishForm.content = ''
    load()
  } finally { publishing.value = false }
}

function onEdit(a) {
  editId.value = a.id
  publishForm.title = a.title
  publishForm.content = a.content
  editVisible.value = true
}

async function onEditSave() {
  await updateAnnouncement(editId.value, publishForm)
  ElMessage.success('修改成功')
  editVisible.value = false
  load()
}

async function onDelete(a) {
  await ElMessageBox.confirm(`确定删除公告「${a.title}」吗？`, '提示', { type: 'warning' })
  await deleteAnnouncement(a.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.ann-content {
  margin-top: 8px; color: #606266; font-size: 13px; line-height: 1.8;
  white-space: pre-wrap;
}
</style>
