<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>部门管理</b>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增部门</el-button>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="部门名称" />
      <el-table-column prop="description" label="部门描述" />
      <el-table-column prop="employee_count" label="人员数量" width="110" align="center">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ row.employee_count }} 人</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑部门' : '新增部门'" width="420px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="如：技术部" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="部门职责说明（可选）" />
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
import { listDepartments, createDepartment, updateDepartment, deleteDepartment } from '../api'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({ id: null, name: '', description: '' })
const rules = { name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try { list.value = await listDepartments() } finally { loading.value = false }
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', description: '' })
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  if (form.id) {
    await updateDepartment(form.id, { name: form.name, description: form.description })
    ElMessage.success('修改成功')
  } else {
    await createDepartment({ name: form.name, description: form.description })
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除部门「${row.name}」吗？`, '提示', { type: 'warning' })
  await deleteDepartment(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>
