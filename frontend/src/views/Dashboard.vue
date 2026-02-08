<template>
  <div class="dashboard-container">
    <el-row :gutter="24">
      <el-col :span="6" v-for="stat in dashboardStats" :key="stat.key">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="32">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="charts-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>执行次数趋势</span>
              <el-radio-group v-model="timeRange" size="small">
                <el-radio-button label="1h">1小时</el-radio-button>
                <el-radio-button label="6h">6小时</el-radio-button>
                <el-radio-button label="24h">24小时</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <div class="mock-line-chart">
              <svg viewBox="0 0 800 200" class="chart-svg">
                <defs>
                  <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#409eff;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:#409eff;stop-opacity:0" />
                  </linearGradient>
                </defs>
                <path
                  :d="generateLinePath()"
                  fill="url(#chartGradient)"
                  stroke="#409eff"
                  stroke-width="2"
                />
              </svg>
            </div>
            <div class="chart-legend">
              <span class="legend-item">
                <span class="legend-color" style="background: #409eff"></span>
                执行次数
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>任务状态分布</span>
            </div>
          </template>
          <div class="pie-chart">
            <div class="pie-legend">
              <div class="legend-item" v-for="item in statusDistribution" :key="item.label">
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span class="legend-label">{{ item.label }}</span>
                <span class="legend-value">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>覆盖率排行</span>
            </div>
          </template>
          <div class="coverage-ranking">
            <div
              v-for="(item, index) in coverageRanking"
              :key="item.taskId"
              class="ranking-item"
            >
              <span class="ranking-index" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
              <span class="task-name">{{ item.taskName }}</span>
              <div class="coverage-bar">
                <div
                  class="bar-fill"
                  :style="{ width: item.coverage + '%', background: getCoverageColor(item.coverage) }"
                ></div>
              </div>
              <span class="coverage-value">{{ item.coverage }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>实时崩溃监控</span>
            </div>
          </template>
          <div class="crash-monitor">
            <div class="crash-stats">
              <div class="crash-stat-item">
                <div class="stat-label">今日新增</div>
                <div class="stat-value highlight">{{ todayCrashes }}</div>
              </div>
              <div class="crash-stat-item">
                <div class="stat-label">严重漏洞</div>
                <div class="stat-value danger">{{ criticalCrashes }}</div>
              </div>
            </div>
            <div class="recent-crashes">
              <div class="crash-item" v-for="crash in recentCrashes" :key="crash.id">
                <el-icon class="crash-icon"><WarningFilled /></el-icon>
                <div class="crash-info">
                  <div class="crash-type">{{ crash.type }}</div>
                  <div class="crash-time">{{ crash.time }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataLine,
  TrendCharts,
  WarningFilled,
  SuccessFilled,
  Loading,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import socketClient from '@/utils/socket'
import { getDashboardStats } from '@/api/tasks'

const route = useRoute()
const timeRange = ref('1h')

const statsData = ref({
  total_tasks: 0,
  running_tasks: 0,
  pending_tasks: 0,
  completed_tasks: 0,
  failed_tasks: 0,
  total_crashes: 0,
  total_executions: 0,
  avg_coverage: 0
})

const todayCrashes = ref(3)
const criticalCrashes = ref(5)

const recentCrashes = ref([
  { id: 1, type: 'Heap Overflow', time: '5分钟前' },
  { id: 2, type: 'Stack Overflow', time: '12分钟前' },
  { id: 3, type: 'Use After Free', time: '25分钟前' }
])

const dashboardStats = computed(() => [
  {
    key: 'total_tasks',
    label: '总任务数',
    value: statsData.value.total_tasks,
    icon: DataLine,
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    key: 'running_tasks',
    label: '运行中',
    value: statsData.value.running_tasks,
    icon: Loading,
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    key: 'total_crashes',
    label: '发现漏洞',
    value: statsData.value.total_crashes,
    icon: WarningFilled,
    color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  },
  {
    key: 'avg_coverage',
    label: '平均覆盖率',
    value: statsData.value.avg_coverage + '%',
    icon: TrendCharts,
    color: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
  }
])

const statusDistribution = computed(() => [
  { label: '运行中', value: statsData.value.running_tasks, color: '#67c23a' },
  { label: '等待中', value: statsData.value.pending_tasks, color: '#909399' },
  { label: '已完成', value: statsData.value.completed_tasks, color: '#409eff' },
  { label: '失败', value: statsData.value.failed_tasks, color: '#f56c6c' }
])

const coverageRanking = computed(() => [
  { taskId: 3, taskName: 'buffer_overflow_test', coverage: 92.3 },
  { taskId: 1, taskName: 'test_whitebox_vuln', coverage: 67.5 },
  { taskId: 4, taskName: 'format_string_bug', coverage: 34.2 },
  { taskId: 2, taskName: 'test_blackbox_app', coverage: 12.3 }
])

const generateLinePath = () => {
  const points = []
  const values = [10, 25, 45, 52, 67, 78, 85, 92, 88, 95]
  const width = 800
  const height = 200
  const padding = 20

  for (let i = 0; i < values.length; i++) {
    const x = padding + (i / (values.length - 1)) * (width - 2 * padding)
    const y = height - padding - (values[i] / 100) * (height - 2 * padding)
    points.push(`${i === 0 ? 'M' : 'L'} ${x} ${y}`)
  }

  return points.join(' ') + ` L ${width - padding} ${height - padding} L ${padding} ${height - padding} Z`
}

const getCoverageColor = (coverage) => {
  if (coverage >= 80) return '#67c23a'
  if (coverage >= 50) return '#e6a23c'
  return '#f56c6c'
}

const loadDashboardStats = async () => {
  try {
    const response = await getDashboardStats()
    statsData.value = response.data
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  }
}

const handleDashboardUpdate = (data) => {
  if (data.stats) {
    statsData.value = data.stats
  }
}

onMounted(async () => {
  await loadDashboardStats()

  // 连接 WebSocket
  try {
    await socketClient.connect()

    // 订阅仪表盘更新
    socketClient.subscribeDashboard()
    socketClient.on('dashboard_update', handleDashboardUpdate)
  } catch (error) {
    console.error('WebSocket 连接失败:', error)
  }
})

onUnmounted(() => {
  socketClient.removeAllListeners('dashboard_update')
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px 0;
}

.stat-card {
  margin-bottom: 24px;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.charts-row {
  margin-bottom: 24px;
}

.chart-card {
  height: 320px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mock-line-chart {
  width: 100%;
  height: 200px;
}

.chart-svg {
  width: 100%;
  height: 100%;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.pie-chart {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-legend {
  width: 100%;
}

.pie-legend .legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 12px;
}

.legend-label {
  flex: 1;
  color: #606266;
}

.legend-value {
  font-weight: bold;
  color: #303133;
}

.coverage-ranking {
  padding: 8px 0;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  color: white;
}

.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
}

.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #a0a0a0 100%);
}

.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #a05a2c 100%);
}

.rank-1, .rank-2, .rank-3 {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.task-name {
  flex: 1;
  color: #606266;
  font-size: 14px;
}

.coverage-bar {
  width: 100px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.coverage-value {
  width: 50px;
  text-align: right;
  font-weight: bold;
  color: #303133;
}

.crash-monitor {
  height: 220px;
  display: flex;
  flex-direction: column;
}

.crash-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.crash-stat-item {
  flex: 1;
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.crash-stat-item .stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.crash-stat-item .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.crash-stat-item .stat-value.highlight {
  color: #e6a23c;
}

.crash-stat-item .stat-value.danger {
  color: #f56c6c;
}

.recent-crashes {
  flex: 1;
  overflow-y: auto;
}

.crash-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  background: #fef0f0;
  margin-bottom: 8px;
}

.crash-icon {
  color: #f56c6c;
  font-size: 18px;
}

.crash-info {
  flex: 1;
}

.crash-type {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.crash-time {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
</style>
