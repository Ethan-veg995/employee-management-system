<template>
  <div class="login-bg">
    <el-card class="login-card">
      <div class="login-title">
        <el-icon :size="30" color="#409EFF"><OfficeBuilding /></el-icon>
        <h2>企业员工管理系统</h2>
        <p>中小企业人事管理一体化平台</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" size="large" @keyup.enter="onLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" style="width:100%" size="large" :loading="loading" @click="onLogin">
          登 录
        </el-button>
      </el-form>
      <el-divider />
      <div class="demo-tip">
        <p>演示账号（点击快速填入）：</p>
        <div class="demo-btns">
          <el-button size="small" @click="fill('admin', 'admin123')">管理员</el-button>
          <el-button size="small" type="success" @click="fill('hr', 'hr123')">HR</el-button>
          <el-button size="small" type="warning" @click="fill('manager', 'manager123')">主管</el-button>
          <el-button size="small" type="info" @click="fill('employee', 'employee123')">员工</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { loginApi } from '../api'
import { useUserStore } from '../store/user'

const router = useRouter()
const store = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function fill(u, p) {
  form.username = u
  form.password = p
}

async function onLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await loginApi(form)
    store.setLogin(data.token, data.user)
    ElMessage.success('登录成功')
    router.push(data.user.role === 'admin' ? '/users' : (data.user.role === 'hr' ? '/dashboard' : '/my-dashboard'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-bg {
  height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #1f3b73 0%, #3a7bd5 100%);
}
.login-card { width: 400px; border-radius: 10px; padding: 10px 10px 0; }
.login-title { text-align: center; margin-bottom: 24px; }
.login-title h2 { margin: 8px 0 4px; color: #303133; }
.login-title p { color: #909399; font-size: 13px; }
.demo-tip p { color: #909399; font-size: 13px; margin-bottom: 8px; }
.demo-btns { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
