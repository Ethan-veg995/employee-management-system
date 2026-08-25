<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>用户管理（系统管理员）</b>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增用户</el-button>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="{ admin: 'danger', hr: 'primary', manager: 'warning', employee: 'info' }[row.role]" size="small">
            {{ row.role_name }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="employee_name" label="关联员工" width="120">
        <template #default="{ row }">{{ row.employee_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新增用户'" width="460px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="密码" :prop="form.id ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password
                    :placeholder="form.id ? '留空则不修改密码' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="系统管理员" value="admin" />
            <el-option label="HR" value="hr" />
            <el-option label="部门主管" value="manager" />
            <el-option label="普通员工" value="employee" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联员工">
          <el-select v-model="form.employee_id" clearable filterable placeholder="选择员工档案（可选）" style="width:100%">
            <el-option v-for="e in employees" :key="e.id" :label="`${e.name} (${e.employee_no})`" :value="e.id" />
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
import { listUsers, createUser, updateUser, deleteUser, allEmployees } from '../api'

const list = ref([])
const employees = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({ id: null, username: '', password: '', role: 'employee', employee_id: null })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function load() {
  loading.value = true
  try { list.value = await listUsers() } finally { loading.value = false }
}

async function openDialog(row) {
  Object.assign(form, row || { id: null, username: '', password: '', role: 'employee', employee_id: null })
  form.password = ''
  if (!employees.value.length) employees.value = await allEmployees()
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  const data = {
    username: form.username,
    password: form.password || undefined,
    role: form.role,
    employee_id: form.employee_id,
  }
  if (form.id) {
    if (!form.password) delete data.password
    await updateUser(form.id, data)
    ElMessage.success('修改成功')
  } else {
    await createUser(data)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>
