<template>
  <el-row :gutter="16">
    <el-col :span="13">
      <el-card shadow="hover">
        <template #header><b>发起申请</b></template>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
          <el-form-item label="申请类型" prop="request_type">
            <el-radio-group v-model="form.request_type" @change="onTypeChange">
              <el-radio-button v-for="t in types" :key="t" :value="t">{{ t }}</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="申请标题" prop="title">
            <el-input v-model="form.title" :placeholder="titlePlaceholder" maxlength="50" show-word-limit />
          </el-form-item>
          <el-form-item v-if="form.request_type === '请假'" label="请假类型" prop="leave_type">
            <el-select v-model="form.leave_type" style="width:100%">
              <el-option v-for="t in ['事假', '病假', '年假', '调休', '婚假']" :key="t" :label="t" :value="t" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.request_type === '报销'" label="报销金额" prop="amount">
            <el-input-number v-model="form.amount" :min="0.01" :precision="2" :step="50" style="width:220px" />
            <span style="margin-left:10px;color:#909399;font-size:12px">元（报销单需保留发票）</span>
          </el-form-item>
          <el-form-item v-if="needDates" label="开始日期" prop="start_date">
            <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item v-if="needDates" label="结束日期" prop="end_date">
            <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item v-if="needDates" label="天数">
            <el-tag type="info" size="large">{{ days }} 天</el-tag>
            <span style="margin-left:8px;color:#909399;font-size:12px">按自然日计算（含周末）</span>
          </el-form-item>
          <el-form-item label="申请事由" prop="reason">
            <el-input v-model="form.reason" type="textarea" :rows="3" :placeholder="reasonPlaceholder" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="onSubmit">提交申请</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
    <el-col :span="11">
      <el-card shadow="hover">
        <template #header><b>审批流程说明</b></template>
        <el-steps direction="vertical" :active="1">
          <el-step title="员工发起申请" description="按类型填写信息并提交" />
          <el-step title="部门主管审批" description="主管在「待我审批」中通过或驳回" />
          <el-step title="结果实时通知" description="审批结果自动推送消息，申请人可随时查看" />
        </el-steps>
        <el-alert type="warning" :closable="false" style="margin-top:16px"
                  title="注意：请假同一时间段存在待审批申请时无法重复提交；年度请假额度年假 5 天、事假 10 天，超限会触发智能提醒。" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createApproval } from '../api'

const types = ['请假', '加班', '报销', '出差']
const formRef = ref()
const submitting = ref(false)
const form = reactive({
  request_type: '请假', title: '', leave_type: '事假', amount: null,
  start_date: '', end_date: '', reason: '',
})
const rules = {
  title: [{ required: true, message: '请填写申请标题', trigger: 'blur' }],
  leave_type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  amount: [{ required: true, message: '请填写报销金额', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  reason: [{ required: true, message: '请填写申请事由', trigger: 'blur' }],
}

const needDates = computed(() => ['请假', '加班', '出差'].includes(form.request_type))
const titlePlaceholder = computed(() => ({
  请假: '如：年度年假出行', 加班: '如：版本上线加班', 报销: '如：项目打车费报销', 出差: '如：客户现场支持',
}[form.request_type]))
const reasonPlaceholder = computed(() => ({
  请假: '请填写请假原因', 加班: '请填写加班工作内容', 报销: '请填写报销明细说明', 出差: '请填写出差任务说明',
}[form.request_type]))

const days = computed(() => {
  if (!form.start_date || !form.end_date) return 0
  const s = new Date(form.start_date)
  const e = new Date(form.end_date)
  return e >= s ? Math.round((e - s) / 86400000) + 1 : 0
})

function onTypeChange() {
  form.title = ''
  form.leave_type = '事假'
  form.amount = null
  form.start_date = ''
  form.end_date = ''
  form.reason = ''
  formRef.value?.clearValidate()
}

async function onSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    await createApproval({ ...form })
    ElMessage.success('申请已提交，等待主管审批')
    onTypeChange()
  } finally { submitting.value = false }
}
</script>
