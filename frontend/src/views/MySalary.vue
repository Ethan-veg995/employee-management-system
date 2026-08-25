<template>
  <el-card shadow="hover">
    <template #header><b>我的薪资</b></template>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column label="月份" width="130">
        <template #default="{ row }">{{ row.year }}年{{ row.month }}月</template>
      </el-table-column>
      <el-table-column prop="base_salary" label="基本工资" align="right">
        <template #default="{ row }">¥{{ row.base_salary }}</template>
      </el-table-column>
      <el-table-column prop="bonus" label="绩效奖金" align="right">
        <template #default="{ row }">¥{{ row.bonus }}</template>
      </el-table-column>
      <el-table-column prop="deduction" label="扣款" align="right">
        <template #default="{ row }">¥{{ row.deduction }}</template>
      </el-table-column>
      <el-table-column prop="actual_salary" label="实发工资" align="right">
        <template #default="{ row }"><b style="color:#E6A23C;font-size:15px">¥{{ row.actual_salary }}</b></template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!list.length && !loading" description="暂无薪资记录" />
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { mySalaries } from '../api'

const list = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try { list.value = await mySalaries() } finally { loading.value = false }
})
</script>
