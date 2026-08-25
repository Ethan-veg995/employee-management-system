<template>
  <div class="tags-view">
    <el-scrollbar class="tags-scroll">
      <div class="tags-wrap">
        <router-link v-for="t in tags" :key="t.path" :to="t.path"
                     class="tag-item" :class="{ active: t.path === $route.path }">
          {{ t.title }}
          <el-icon v-if="t.path !== '/dashboard' && t.path !== '/my-dashboard'"
                   class="tag-close" @click.prevent.stop="closeTag(t)">
            <Close />
          </el-icon>
        </router-link>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

function firstTitle() {
  const store = JSON.parse(localStorage.getItem('user') || 'null')
  return store && store.role === 'hr'
    ? { path: '/dashboard', title: '数据看板' }
    : (store && store.role === 'admin'
      ? { path: '/users', title: '用户管理' }
      : { path: '/my-dashboard', title: '我的工作台' })
}

const tags = ref([firstTitle()])

watch(
  () => route.path,
  (path) => {
    const title = route.meta.title
    if (!title || path === '/dashboard' || path === '/my-dashboard') return
    if (!tags.value.some((t) => t.path === path)) {
      tags.value.push({ path, title })
    }
  },
  { immediate: true }
)

function closeTag(tag) {
  const idx = tags.value.findIndex((t) => t.path === tag.path)
  tags.value.splice(idx, 1)
  if (route.path === tag.path) {
    const next = tags.value[idx - 1] || tags.value[tags.value.length - 1] || firstTitle()
    router.push(next.path)
  }
}
</script>

<style scoped>
.tags-view {
  background: #fff; padding: 6px 12px; border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 3px rgba(0, 21, 41, .06); z-index: 5;
}
.tags-scroll { width: 100%; }
.tags-wrap { display: flex; gap: 8px; white-space: nowrap; }
.tag-item {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px; font-size: 13px; color: #606266; border-radius: 4px;
  border: 1px solid #d9d9d9; background: #fff; cursor: pointer; text-decoration: none;
}
.tag-item.active { background: #409EFF; border-color: #409EFF; color: #fff; }
.tag-close { font-size: 12px; }
.tag-close:hover { color: #F56C6C; }
</style>
