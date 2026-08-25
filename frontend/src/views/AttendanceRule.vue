<template>
  <el-card shadow="hover" style="max-width:600px">
    <template #header><b>考勤规则配置</b></template>
    <el-form :model="form" label-width="140px" style="max-width:520px">
      <el-form-item label="上班时间">
        <el-time-select v-model="form.work_start" start="06:00" step="00:15" end="12:00" placeholder="上班时间" />
      </el-form-item>
      <el-form-item label="下班时间">
        <el-time-select v-model="form.work_end" start="14:00" step="00:15" end="23:45" placeholder="下班时间" />
      </el-form-item>
      <el-form-item label="迟到容忍时间(分钟)">
        <el-input-number v-model="form.late_tolerance_minutes" :min="0" :max="60" />
        <span style="margin-left:10px;color:#909399;font-size:12px">超过该时间打卡记为「迟到」</span>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">保存配置</el-button>
      </el-form-item>
    </el-form>
    <el-alert type="info" :closable="false" style="margin-top:12px"
              title="规则说明：员工在上班时间+容忍分钟内打卡记为「正常」，超过记为「迟到」；下班时间前打卡记为「早退」；只打上班卡记为「缺卡」。" />
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAttendanceRule, updateAttendanceRule } from '../api'

const form = reactive({ work_start: '09:00', work_end: '18:00', late_tolerance_minutes: 10 })
const saving = ref(false)

onMounted(async () => {
  Object.assign(form, await getAttendanceRule())
})

async function onSave() {
  saving.value = true
  try {
    await updateAttendanceRule(form)
    ElMessage.success('考勤规则已保存')
  } finally { saving.value = false }
}
</script>
