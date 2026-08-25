<template>
  <el-card shadow="hover" style="max-width:560px">
    <template #header><b>个人中心</b></template>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="用户名">{{ store.user?.username }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ store.roleName }}</el-descriptions-item>
      <el-descriptions-item label="关联员工">
        {{ store.user?.employee_id ? `已关联（ID: ${store.user.employee_id}）` : '未关联员工档案' }}
      </el-descriptions-item>
    </el-descriptions>
    <el-divider>修改密码</el-divider>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" style="max-width:420px">
      <el-form-item label="原密码" prop="old_password">
        <el-input v-model="form.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm">
        <el-input v-model="form.confirm" type="password" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">修改密码</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { resetPasswordApi } from '../api'
import { useUserStore } from '../store/user'

const store = useUserStore()
const formRef = ref()
const saving = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm: '' })
const rules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' },
  ],
  confirm: [{
    validator: (rule, value, cb) => (value === form.new_password ? cb() : cb(new Error('两次输入的密码不一致'))),
    trigger: 'blur',
  }],
}

async function onSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    await resetPasswordApi({ old_password: form.old_password, new_password: form.new_password })
    ElMessage.success('密码修改成功')
    form.old_password = form.new_password = form.confirm = ''
  } finally { saving.value = false }
}
</script>
