<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>职位管理</b>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增职位</el-button>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="职位名称" />
      <el-table-column prop="department_name" label="所属部门" width="140" />
      <el-table-column label="职级" width="120">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)" size="small">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑职位' : '新增职位'" width="420px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="职位名称" prop="name">
          <el-input v-model="form.name" placeholder="如：后端工程师" />
        </el-form-item>
        <el-form-item label="所属部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="请选择部门" style="width:100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="职级" prop="level">
          <el-select v-model="form.level" style="width:100%">
            <el-option v-for="l in ['初级', '中级', '高级', '资深']" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPositions, listDepartments, createPosition, updatePosition, deletePosition } from '../api'

const list = ref([])
const departments = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({ id: null, name: '', department_id: null, level: '初级' })
const rules = {
  name: [{ required: true, message: '请输入职位名称', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
}

function levelType(l) {
  return { 初级: 'info', 中级: 'primary', 高级: 'warning', 资深: 'danger' }[l] || 'info'
}

async function load() {
  loading.value = true
  try {
    list.value = await listPositions()
    departments.value = await listDepartments()
  } finally { loading.value = false }
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', department_id: null, level: '初级' })
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  const data = { name: form.name, department_id: form.department_id, level: form.level }
  if (form.id) {
    await updatePosition(form.id, data)
    ElMessage.success('修改成功')
  } else {
    await createPosition(data)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除职位「${row.name}」吗？`, '提示', { type: 'warning' })
  await deletePosition(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>
