<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <b>员工管理</b>
        <div style="display:flex;gap:8px">
          <el-upload :show-file-list="false" :http-request="onImport" accept=".xlsx" style="display:inline-block">
            <el-button :icon="Upload" :loading="importing">Excel 导入</el-button>
          </el-upload>
          <el-button :icon="Download" @click="onExport">Excel 导出</el-button>
          <el-button type="primary" :icon="Plus" @click="openDialog()">新增员工</el-button>
        </div>
      </div>
    </template>

    <el-form inline style="margin-bottom:12px">
      <el-form-item label="关键词">
        <el-input v-model="query.keyword" placeholder="姓名 / 工号" clearable style="width:160px"
                  @keyup.enter="load" @clear="load" />
      </el-form-item>
      <el-form-item label="部门">
        <el-select v-model="query.department_id" placeholder="全部" clearable style="width:140px" @change="load">
          <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status" placeholder="全部" clearable style="width:110px" @change="load">
          <el-option label="在职" value="在职" />
          <el-option label="离职" value="离职" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="load">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="employee_no" label="工号" width="100" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="gender" label="性别" width="70" align="center" />
      <el-table-column prop="department_name" label="部门" width="110" />
      <el-table-column prop="position_name" label="职位" width="130" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="hire_date" label="入职日期" width="110" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '在职' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px;justify-content:flex-end" background
                   layout="total, prev, pager, next" :total="total" :page-size="query.size"
                   v-model:current-page="query.page" @current-change="load" />

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑员工' : '新增员工'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name"><el-input v-model="form.name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工号" prop="employee_no"><el-input v-model="form.employee_no" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-radio-group v-model="form.gender">
                <el-radio value="男">男</el-radio>
                <el-radio value="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入职日期" prop="hire_date"><el-date-picker v-model="form.hire_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" prop="department_id">
              <el-select v-model="form.department_id" style="width:100%" @change="onDeptChange">
                <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位" prop="position_id">
              <el-select v-model="form.position_id" style="width:100%">
                <el-option v-for="p in deptPositions" :key="p.id" :label="`${p.name}(${p.level})`" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option label="在职" value="在职" />
                <el-option label="离职" value="离职" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus, Edit, Delete, Search, Upload, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listEmployees, listDepartments, listPositions, createEmployee, updateEmployee,
         deleteEmployee, exportEmployees, importEmployees } from '../api'

const list = ref([])
const total = ref(0)
const departments = ref([])
const positions = ref([])
const loading = ref(false)
const importing = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const query = reactive({ keyword: '', department_id: null, status: '', page: 1, size: 10 })
const form = reactive({
  id: null, name: '', employee_no: '', gender: '男', phone: '', email: '',
  department_id: null, position_id: null, hire_date: '', status: '在职',
})
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  employee_no: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择部门', trigger: 'change' }],
  position_id: [{ required: true, message: '请选择职位', trigger: 'change' }],
  hire_date: [{ required: true, message: '请选择入职日期', trigger: 'change' }],
}

const deptPositions = computed(() =>
  positions.value.filter((p) => p.department_id === form.department_id)
)

async function load() {
  loading.value = true
  try {
    const data = await listEmployees(query)
    list.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}

async function loadRefs() {
  departments.value = await listDepartments()
  positions.value = await listPositions()
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', employee_no: '', gender: '男', phone: '', email: '',
    department_id: null, position_id: null, hire_date: '', status: '在职' })
  dialogVisible.value = true
}

function onDeptChange() {
  form.position_id = null
}

async function onSave() {
  await formRef.value.validate()
  const data = { ...form }
  delete data.id
  if (form.id) {
    await updateEmployee(form.id, data)
    ElMessage.success('修改成功')
  } else {
    await createEmployee(data)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除员工「${row.name}(${row.employee_no})」吗？`, '提示', { type: 'warning' })
  await deleteEmployee(row.id)
  ElMessage.success('删除成功')
  load()
}

async function onExport() {
  const blob = await exportEmployees(query)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'employees_export.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

async function onImport({ file }) {
  importing.value = true
  try {
    const res = await importEmployees(file)
    ElMessageBox.alert(res.message + (res.failed?.length ? `\n${res.failed.slice(0, 5).join('\n')}` : ''), '导入结果')
    load()
  } finally { importing.value = false }
}

onMounted(async () => {
  await loadRefs()
  load()
})
</script>
