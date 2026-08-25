<template>
  <el-card shadow="hover">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <b>绩效管理</b>
        <div>
          <el-select v-model="query.month" style="width:130px;margin-right:8px" @change="load">
            <el-option v-for="m in months" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
          <el-select v-if="isHr" v-model="query.department_id" placeholder="全部部门" clearable style="width:130px;margin-right:8px" @change="load">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="openScore()">绩效评分</el-button>
        </div>
      </div>
    </template>

    <el-alert type="info" :closable="false" style="margin-bottom:12px"
              title="绩效等级规则：S(≥90分) 系数1.5 / A(≥80分) 系数1.2 / B(≥70分) 系数1.0 / C(<70分) 系数0.6；绩效奖金 = 系数 × 基本工资 × 20%，薪资录入时自动带出。" />

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="employee_no" label="工号" width="100" />
      <el-table-column prop="employee_name" label="姓名" width="100" />
      <el-table-column prop="department_name" label="部门" width="110" />
      <el-table-column prop="year" label="月份" width="100">
        <template #default="{ row }">{{ row.year }}年{{ row.month }}月</template>
      </el-table-column>
      <el-table-column prop="score" label="评分" width="100" align="center">
        <template #default="{ row }"><b>{{ row.score }}</b></template>
      </el-table-column>
      <el-table-column label="绩效等级" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="levelType(row.level)" size="large">{{ row.level }}级</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="comment" label="评语" min-width="160" show-overflow-tooltip />
      <el-table-column prop="reviewer_name" label="评分人" width="100" />
      <el-table-column v-if="isHr" label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :icon="Edit" @click="openScore(row)">编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!list.length && !loading" description="本月暂无绩效记录，点击右上角「绩效评分」开始" />

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑绩效' : '绩效评分'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="员工" prop="employee_id">
          <el-select v-model="form.employee_id" filterable style="width:100%" :disabled="!!form.id" @change="onEmpChange">
            <el-option v-for="e in targets" :key="e.id"
                       :label="`${e.name} (${e.employee_no})`" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="评分(0-100)" prop="score">
              <el-input-number v-model="form.score" :min="0" :max="100" style="width:100%" @change="onScoreChange" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="绩效等级">
              <el-tag v-if="form.score !== null" :type="levelType(levelOf(form.score))" size="large">
                {{ levelOf(form.score) }}级（系数 {{ coeffOf(form.score) }}）
              </el-tag>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="薪资联动" v-if="suggest">
          <el-descriptions :column="3" size="small" border style="width:100%">
            <el-descriptions-item label="基本工资">¥{{ suggest.base_salary }}</el-descriptions-item>
            <el-descriptions-item label="建议绩效奖金">¥{{ suggest.suggested_bonus }}</el-descriptions-item>
            <el-descriptions-item label="绩效系数">{{ suggest.coefficient }}</el-descriptions-item>
          </el-descriptions>
        </el-form-item>
        <el-form-item label="评语">
          <el-input v-model="form.comment" type="textarea" :rows="2" placeholder="绩效评语（可选）" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPerformance, listDepartments, allEmployees, createPerformance,
         updatePerformance, deletePerformance, perfSuggest } from '../api'
import { useUserStore } from '../store/user'

const store = useUserStore()
const isHr = computed(() => ['hr'].includes(store.user?.role))
const list = ref([])
const departments = ref([])
const targets = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const suggest = ref(null)
const now = new Date()
const months = Array.from({ length: 6 }, (_, i) => {
  const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
  return { value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, label: `${d.getFullYear()}年${d.getMonth() + 1}月` }
})
const query = reactive({ month: months[0].value, department_id: null })
const form = reactive({ id: null, employee_id: null, year: 0, month: 0, score: null, comment: '' })
const rules = {
  employee_id: [{ required: true, message: '请选择员工', trigger: 'change' }],
  score: [{ required: true, message: '请输入评分', trigger: 'blur' }],
}

function levelOf(score) {
  if (score >= 90) return 'S'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  return 'C'
}
function coeffOf(score) {
  return { S: 1.5, A: 1.2, B: 1.0, C: 0.6 }[levelOf(score)]
}
function levelType(l) {
  return { S: 'danger', A: 'warning', B: 'primary', C: 'info' }[l] || 'info'
}

async function load() {
  loading.value = true
  try {
    const [y, m] = query.month.split('-')
    list.value = await listPerformance({ year: +y, month: +m, department_id: query.department_id || undefined })
  } finally { loading.value = false }
}

async function loadRefs() {
  departments.value = await listDepartments()
  targets.value = (await allEmployees()).filter((e) => e.status === '在职')
}

async function openScore(row) {
  Object.assign(form, row ? {
    id: row.id, employee_id: row.employee_id, year: row.year, month: row.month,
    score: row.score, comment: row.comment,
  } : {
    id: null, employee_id: null, year: +query.month.split('-')[0],
    month: +query.month.split('-')[1], score: null, comment: '',
  })
  suggest.value = null
  dialogVisible.value = true
  if (row) await onEmpChange(row.employee_id)
}

async function onEmpChange(empId) {
  if (!empId || !form.year) return
  try {
    suggest.value = await perfSuggest({ employee_id: empId, year: form.year, month: form.month })
  } catch { suggest.value = null }
}

function onScoreChange() {
  if (form.employee_id && form.score !== null) onEmpChange(form.employee_id)
}

async function onSave() {
  await formRef.value.validate()
  const data = { employee_id: form.employee_id, year: form.year, month: form.month,
                 score: form.score, comment: form.comment }
  if (form.id) {
    await updatePerformance(form.id, data)
    ElMessage.success('修改成功')
  } else {
    await createPerformance(data)
    ElMessage.success('评分成功')
  }
  dialogVisible.value = false
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除 ${row.employee_name} ${row.year}年${row.month}月 的绩效记录吗？`, '提示', { type: 'warning' })
  await deletePerformance(row.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(async () => {
  await loadRefs()
  load()
})
</script>
