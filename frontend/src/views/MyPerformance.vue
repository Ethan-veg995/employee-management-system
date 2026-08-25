<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card shadow="hover">
        <template #header><b>我的绩效</b></template>
        <template v-if="latest">
          <div style="text-align:center;padding:10px 0 20px">
            <div style="font-size:14px;color:#909399">最近一次绩效（{{ latest.year }}年{{ latest.month }}月）</div>
            <el-tag :type="levelType(latest.level)" size="large" style="font-size:22px;padding:6px 18px;margin-top:10px">
              {{ latest.level }}级
            </el-tag>
            <div style="margin-top:10px;font-size:26px;font-weight:700;color:#303133">{{ latest.score }} 分</div>
          </div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="评分人">{{ latest.reviewer_name }}</el-descriptions-item>
            <el-descriptions-item label="绩效系数">{{ coeffOf(latest.level) }}</el-descriptions-item>
            <el-descriptions-item label="评语">{{ latest.comment || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>
        <el-empty v-else description="暂无绩效记录" />
      </el-card>
    </el-col>
    <el-col :span="14">
      <el-card shadow="hover">
        <template #header><b>历史绩效记录</b></template>
        <el-table :data="list" stripe>
          <el-table-column prop="year" label="月份" width="110">
            <template #default="{ row }">{{ row.year }}年{{ row.month }}月</template>
          </el-table-column>
          <el-table-column prop="score" label="评分" align="center" width="90" />
          <el-table-column label="等级" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="levelType(row.level)" size="small">{{ row.level }}级</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="评语" show-overflow-tooltip />
        </el-table>
        <el-alert type="info" :closable="false" style="margin-top:12px"
                  title="绩效等级说明：S(≥90分) 系数1.5 / A(≥80分) 系数1.2 / B(≥70分) 系数1.0 / C(<70分) 系数0.6；绩效奖金 = 系数 × 基本工资 × 20%，由主管评分后自动计入当月薪资。" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { myPerformance } from '../api'

const list = ref([])
const latest = computed(() => list.value[0] || null)

function levelType(l) {
  return { S: 'danger', A: 'warning', B: 'primary', C: 'info' }[l] || 'info'
}
function coeffOf(l) {
  return { S: 1.5, A: 1.2, B: 1.0, C: 0.6 }[l] || 1
}

onMounted(async () => {
  list.value = await myPerformance()
})
</script>
