<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon :size="22" color="#409EFF"><OfficeBuilding /></el-icon>
        <span>员工管理系统</span>
      </div>
      <el-menu :default-active="$route.path" router background-color="#001529"
               text-color="#a6adb4" active-text-color="#ffffff" style="border-right: none">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display:flex;align-items:center;gap:14px">
          <el-badge :value="unread" :hidden="!unread" :max="99">
            <el-popover placement="bottom-end" :width="340" trigger="click" @show="refreshUnread">
              <template #reference>
                <el-icon :size="20" class="bell" @click="refreshUnread"><Bell /></el-icon>
              </template>
              <div class="notif-panel">
                <div class="notif-head">
                  <b>消息通知</b>
                  <el-button link type="primary" size="small" @click="onAllRead">全部已读</el-button>
                </div>
                <div v-if="!notifs.length" class="notif-empty">暂无消息</div>
                <div v-for="n in notifs" :key="n.id" class="notif-item"
                     :class="{ unread: !n.is_read }" @click="onNotifClick(n)">
                  <el-icon :size="16" :color="typeColor(n.type)" style="margin-top:2px">
                    <component :is="typeIcon(n.type)" />
                  </el-icon>
                  <div class="notif-body">
                    <div class="notif-title">{{ n.title }}</div>
                    <div class="notif-content">{{ n.content }}</div>
                    <div class="notif-time">{{ timeStr(n.created_at) }}</div>
                  </div>
                </div>
                <div class="notif-foot">
                  <el-button link type="primary" size="small" @click="$router.push('/notifications')">
                    查看全部消息
                  </el-button>
                </div>
              </div>
            </el-popover>
          </el-badge>
          <el-dropdown @command="onCommand">
            <span class="user-info">
              <el-avatar :size="32" style="background:#409EFF">{{ store.user?.username?.[0]?.toUpperCase() }}</el-avatar>
              <span class="uname">{{ store.user?.username }}</span>
              <el-tag size="small" type="info">{{ store.roleName }}</el-tag>
              <el-icon style="margin-left:4px"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <TagsView />
      <el-main style="background:#f0f2f5; overflow-y: auto">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessageBox } from 'element-plus'
import { unreadCount, listNotifications, markRead, markAllRead } from '../api'
import TagsView from '../components/TagsView.vue'

const store = useUserStore()
const router = useRouter()
const unread = ref(0)
const notifs = ref([])
let pollTimer = null

const ALL_MENUS = [
  { path: '/dashboard', title: '数据看板', icon: 'DataAnalysis', roles: ['hr', 'admin'] },
  { path: '/my-dashboard', title: '我的工作台', icon: 'HomeFilled', roles: ['employee', 'manager'] },
  { path: '/departments', title: '部门管理', icon: 'OfficeBuilding', roles: ['hr', 'admin'] },
  { path: '/positions', title: '职位管理', icon: 'Briefcase', roles: ['hr', 'admin'] },
  { path: '/employees', title: '员工管理', icon: 'User', roles: ['hr', 'admin'] },
  { path: '/attendance/punch', title: '考勤打卡', icon: 'AlarmClock', roles: ['employee', 'manager'] },
  { path: '/attendance/rule', title: '考勤规则', icon: 'SetUp', roles: ['hr', 'admin'] },
  { path: '/attendance/monthly', title: '月度考勤', icon: 'Calendar', roles: ['hr', 'admin'] },
  { path: '/approval/apply', title: '发起申请', icon: 'EditPen', roles: ['employee', 'manager'] },
  { path: '/approval/mine', title: '我的申请', icon: 'Tickets', roles: ['employee', 'manager'] },
  { path: '/approval/approve', title: '待我审批', icon: 'Stamp', roles: ['manager', 'hr', 'admin'] },
  { path: '/approval/all', title: '审批记录', icon: 'DocumentChecked', roles: ['hr', 'admin'] },
  { path: '/performance/manage', title: '绩效管理', icon: 'Trophy', roles: ['manager', 'hr', 'admin'] },
  { path: '/performance/my', title: '我的绩效', icon: 'Medal', roles: ['employee', 'manager'] },
  { path: '/announcements', title: '公告中心', icon: 'Bell' },
  { path: '/notifications', title: '消息中心', icon: 'Message', roles: [] },
  { path: '/salary/manage', title: '薪资管理', icon: 'Money', roles: ['hr', 'admin'] },
  { path: '/salary/my', title: '我的薪资', icon: 'Wallet', roles: ['employee', 'manager'] },
  { path: '/users', title: '用户管理', icon: 'UserFilled', roles: ['admin'] },
]

const menus = computed(() =>
  ALL_MENUS.filter((m) => !m.roles || m.roles.includes(store.user?.role))
)

function typeIcon(t) {
  return { todo: 'Stamp', result: 'CircleCheck', announcement: 'Bell' }[t] || 'Bell'
}
function typeColor(t) {
  return { todo: '#E6A23C', result: '#67C23A', announcement: '#409EFF' }[t] || '#409EFF'
}
function timeStr(s) {
  return s ? s.replace('T', ' ').slice(0, 16) : ''
}

async function refreshUnread() {
  try {
    unread.value = (await unreadCount()).count
    if (unread.value) notifs.value = await listNotifications({ limit: 10 })
  } catch { /* 忽略轮询错误 */ }
}

async function onNotifClick(n) {
  if (!n.is_read) {
    await markRead(n.id)
    n.is_read = 1
    await refreshUnread()
  }
  if (n.type === 'todo' && store.user.role !== 'employee') router.push('/approval/approve')
  else if (n.type === 'announcement') router.push('/announcements')
}

async function onAllRead() {
  await markAllRead()
  notifs.value.forEach((n) => (n.is_read = 1))
  await refreshUnread()
}

async function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
    store.logout()
    router.push('/login')
  }
}

onMounted(() => {
  refreshUnread()
  pollTimer = setInterval(refreshUnread, 30000)
})
onBeforeUnmount(() => clearInterval(pollTimer))
</script>

<style scoped>
.aside { background: #001529; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; gap: 8px; color: #fff; font-size: 17px; font-weight: 600; }
.header { background: #fff; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 4px rgba(0,21,41,.08); }
.user-info { display: flex; align-items: center; cursor: pointer; }
.uname { margin-left: 8px; font-size: 14px; }
.bell { cursor: pointer; color: #606266; }
.bell:hover { color: #409EFF; }
.notif-panel { max-height: 420px; display: flex; flex-direction: column; }
.notif-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.notif-empty { text-align: center; color: #909399; padding: 20px 0; }
.notif-item { display: flex; gap: 10px; padding: 10px 8px; border-radius: 6px; cursor: pointer; }
.notif-item:hover { background: #f5f7fa; }
.notif-item.unread { background: #ecf5ff; }
.notif-body { flex: 1; min-width: 0; }
.notif-title { font-size: 13px; font-weight: 600; color: #303133; }
.notif-content { font-size: 12px; color: #606266; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.notif-time { font-size: 11px; color: #c0c4cc; margin-top: 4px; }
.notif-foot { text-align: center; padding-top: 8px; border-top: 1px solid #f0f0f0; }
</style>
