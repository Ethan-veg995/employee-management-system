<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <b>薪资管理</b>
        <div>
          <el-select v-model="query.year" placeholder="年份" clearable style="width:100px;margin-right:8px" @change="load">
            <el-option v-for="y in years" :key="y" :label="y" :value="y" />
          </el-select>
          <el-select v-model="query.month" placeholder="月份" clearable style="width:90px;margin-right:8px" @change="load">
            <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="m" />
          </el-select>
          <el-select v-model="query.department_id" placeholder="全部部门" clearable style="width:130px;margin-right:8px" @change="load">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="openDialog()">录入薪资</el-button>
        </div>
      </div>
    </template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="employee_no" label="工号" width="100" />
      <el-table-column prop="employee_name" label="姓名" width="100" />
      <el-table-column prop="department_name" label="部门" width="110" />
      <el-table-column label="月份" width="100">
        <template #default="{ row }">{{ row.year }}年{{ row.month }}月</template>
      </el-table-column>
      <el-table-column prop="base_salary" label="基本工资" width="110" align="right">
        <template #default="{ row }">¥{{ row.base_salary }}</template>
      </el-table-column>
      <el-table-column prop="bonus" label="绩效奖金" width="110" align="right">
        <template #default="{ row }">¥{{ row.bonus }}</template>
      </el-table-column>
      <el-table-column prop="deduction" label="扣款" width="100" align="right">
        <template #default="{ row }">¥{{ row.deduction }}</template>
      </el-table-column>
      <el-table-column prop="actual_salary" label="实发工资" width="120" align="right">
        <template #default="{ row }"><b style="color:#E6A23C">¥{{ row.actual_salary }}</b></template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑薪资' : '录入薪资'" width="480px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="员工" prop="employee_id">
          <el-select v-model="form.employee_id" filterable style="width:100%" @change="onPerfLink">
            <el-option v-for="e in employees" :key="e.id" :label="`${e.name} (${e.employee_no})`" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="年份" prop="year">
              <el-input-number v-model="form.year" :min="2020" :max="2035" style="width:100%" @change="onPerfLink" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="月份" prop="month">
              <el-input-number v-model="form.month" :min="1" :max="12" style="width:100%" @change="onPerfLink" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基本工资" prop="base_salary">
              <el-input-number v-model="form.base_salary" :min="0" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="绩效奖金">
              <el-input-number v-model="form.bonus" :min="0" :step="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="扣款">
              <el-input-number v-model="form.deduction" :min="0" :step="50" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实发工资">
              <el-tag type="warning" size="large">¥{{ form.base_salary + form.bonus - form.deduction }}</el-tag>
            </el-form-item>
          </el-col>
        </el-row>
        <el-alert v-if="perfHint" type="success" :closable="false" style="margin-bottom:0"
                  :title="perfHint" />
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
import { listSalaries, salaryYears, listDepartments, allEmployees,
         createSalary, updateSalary, deleteSalary, perfSuggest } from '../api'

const list = ref([])
const years = ref([])
const departments = ref([])
const employees = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const perfHint = ref('')
const query = reactive({ year: null, month: null, department_id: null })
const form = reactive({
  id: null, employee_id: null, year: new Date().getFullYear(),
  month: new Date().getMonth() + 1, base_salary: 0, bonus: 0, deduction: 0,
})
const rules = {
  employee_id: [{ required: true, message: '请选择员工', trigger: 'change' }],
  year: [{ required: true, message: '请输入年份', trigger: 'blur' }],
  month: [{ required: true, message: '请输入月份', trigger: 'blur' }],
  base_salary: [{ required: true, message: '请输入基本工资', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    list.value = await listSalaries(query)
    years.value = await salaryYears()
  } finally { loading.value = false }
}

async function openDialog(row) {
  Object.assign(form, row || { id: null, employee_id: null, year: new Date().getFullYear(),
    month: new Date().getMonth() + 1, base_salary: 0, bonus: 0, deduction: 0 })
  if (!employees.value.length) employees.value = await allEmployees()
  perfHint.value = ''
  dialogVisible.value = true
  if (form.id) await onPerfLink()
}

// 绩效→薪资联动：选择员工/月份后自动带入建议绩效奖金（可修改）
async function onPerfLink() {
  perfHint.value = ''
  if (!form.employee_id || !form.year || !form.month) return
  try {
    const s = await perfSuggest({ employee_id: form.employee_id, year: form.year, month: form.month })
    if (s.level) {
      form.bonus = s.suggested_bonus
      perfHint.value = `该员工 ${form.year}年${form.month}月绩效 ${s.level} 级（系数 ${s.coefficient}），已自动带入建议绩效奖金 ¥${s.suggested_bonus}（可修改）`
    }
  } catch { perfHint.value = '' }
}

async function onSave() {
  await formRef.value.validate()
  const data = {
    employee_id: form.employee_id, year: form.year, month: form.month,
    base_salary: form.base_salary, bonus: form.bonus, deduction: form.deduction,
  }
  if (form.id) {
    await updateSalary(form.id, data)
    ElMessage.success('修改成功')
  } else {
    await createSalary(data)
    ElMessage.success('录入成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除 ${row.employee_name} ${row.year}年${row.month}月 的薪资记录吗？`, '提示', { type: 'warning' })
  await deleteSalary(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(async () => {
  departments.value = await listDepartments()
  load()
})
</script>
