<template>
  <div class="task-detail-container">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <div class="header-content">
          <span class="title">{{ task?.name || '加载中...' }}</span>
          <el-tag :type="getStatusType(task?.status)" size="large">
            {{ getStatusText(task?.status) }}
          </el-tag>
        </div>
      </template>
      <template #extra>
        <el-space>
          <el-button v-if="canStart" type="primary" :loading="starting" @click="handleStart">
            <el-icon><VideoPlay /></el-icon>
            启动
          </el-button>
          <el-button v-if="canPause" type="warning" @click="handlePause">
            <el-icon><VideoPause /></el-icon>
            暂停
          </el-button>
          <el-button v-if="canResume" type="success" @click="handleResume">
            <el-icon><VideoPlay /></el-icon>
            恢复
          </el-button>
          <el-button v-if="canStop" type="danger" @click="handleStop">
            <el-icon><VideoStop /></el-icon>
            停止
          </el-button>
        </el-space>
      </template>
    </el-page-header>

    <el-row :gutter="24" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.key">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="28" :color="stat.color">
              <component :is="stat.icon" />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>执行速率</span>
              <el-tag type="info">{{ stats[4]?.value || 0 }} execs/sec</el-tag>
            </div>
          </template>
          <div class="rate-chart">
            <div class="rate-bars">
              <div
                v-for="(value, index) in rateHistory"
                :key="index"
                class="rate-bar"
                :title="`时间点 ${index + 1}: ${value}`"
              >
                <div class="bar-fill" :style="{ height: (value / maxRate * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>覆盖率</span>
            </div>
          </template>
          <div class="coverage-display">
            <div class="coverage-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#e0e0e0" stroke-width="8" />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  :stroke="getCoverageColor(stats[3]?.value || 0)"
                  stroke-width="8"
                  :stroke-dasharray="251.2"
                  :stroke-dashoffset="251.2 * (1 - (stats[3]?.value || 0) / 100)"
                  stroke-linecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div class="coverage-value">{{ stats[3]?.value || 0 }}%</div>
            </div>
            <div class="coverage-labels">
              <div class="coverage-label">
                <span class="dot" style="background: #67c23a"></span>
                高 (>80%)
              </div>
              <div class="coverage-label">
                <span class="dot" style="background: #e6a23c"></span>
                中 (50-80%)
              </div>
              <div class="coverage-label">
                <span class="dot" style="background: #f56c6c"></span>
                低 (<50%)
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <span>任务信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="任务ID">
              {{ task?.id }}
            </el-descriptions-item>
            <el-descriptions-item label="任务类型">
              <el-tag :type="task?.type === 'whitebox' ? 'primary' : 'success'">
                {{ task?.type === 'whitebox' ? '白盒测试' : '黑盒测试' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="输入类型">
              {{ getInputTypeText(task?.inputType) }}
            </el-descriptions-item>
            <el-descriptions-item label="编译参数" v-if="task?.type === 'whitebox'">
              <code>{{ task?.compileArgs || '-' }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="Fuzz参数">
              <code>{{ task?.fuzzArgs || '-' }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(task?.createdAt) }}
            </el-descriptions-item>
            <el-descriptions-item label="启动时间">
              {{ formatDateTime(task?.startedAt) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="运行时长">
              {{ runTime }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="crashes-card">
          <template #header>
            <div class="card-header">
              <span>崩溃样本</span>
              <el-link type="primary" @click="viewAllCrashes">查看全部</el-link>
            </div>
          </template>
          <div class="crashes-list">
            <div v-if="recentCrashes.length === 0" class="empty-state">
              <el-empty description="暂无崩溃样本" />
            </div>
            <div v-else>
              <div
                v-for="crash in recentCrashes"
                :key="crash.crash_id"
                class="crash-item"
              >
                <el-icon class="crash-icon"><WarningFilled /></el-icon>
                <div class="crash-info">
                  <div class="crash-type">{{ crash.crash_type }}</div>
                  <div class="crash-time">{{ formatDateTime(crash.found_at) }}</div>
                </div>
                <el-button size="small" @click="downloadCrash(crash)">下载</el-button>
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPlay,
  VideoPause,
  VideoStop,
  Timer,
  WarningFilled,
  DataLine,
  SuccessFilled
} from '@element-plus/icons-vue'
import socketClient from '@/utils/socket'
import {
  getTaskDetail,
  startTask,
  pauseTask,
  resumeTask,
  stopTask,
  getTaskStats,
  getTaskCrashes
} from '@/api/tasks'

const route = useRoute()
const router = useRouter()

const task = ref(null)
const taskStats = ref(null)
const recentCrashes = ref([])
const starting = ref(false)

const rateHistory = ref([100, 150, 200, 180, 220, 250, 300, 280, 320, 350])
const runTime = ref('00:00:00')

const canStart = computed(() => task.value?.status === 'ready' || task.value?.status === 'stopped')
const canPause = computed(() => task.value?.status === 'running')
const canResume = computed(() => task.value?.status === 'paused')
const canStop = computed(() => task.value?.status === 'running')

const maxRate = computed(() => Math.max(...rateHistory.value, 1))

const stats = computed(() => [
  { key: 'exec_count', label: '执行次数', value: formatNumber(taskStats.value?.exec_count || task.value?.exec_count), icon: Timer, color: '#409eff' },
  { key: 'unique_crashes', label: '崩溃数', value: taskStats.value?.unique_crashes || task.value?.unique_crashes, icon: WarningFilled, color: '#f56c6c' },
  { key: 'corpus_count', label: '语料数', value: taskStats.value?.corpus_count || task.value?.corpus_count, icon: DataLine, color: '#67c23a' },
  { key: 'coverage', label: '覆盖率', value: taskStats.value?.coverage || task.value?.coverage, icon: SuccessFilled, color: '#e6a23c' },
  { key: 'execs_per_sec', label: '执行速率', value: taskStats.value?.execs_per_sec?.toFixed(2) || task.value?.execs_per_sec?.toFixed(2) || 0, icon: VideoPlay, color: '#909399' }
])

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    compiling: 'warning',
    ready: 'success',
    running: 'success',
    paused: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    compiling: '编译中',
    ready: '就绪',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止'
  }
  return map[status] || status
}

const getInputTypeText = (inputType) => {
  const map = {
    stdin: '标准输入',
    file: '文件输入',
    args: '命令行参数'
  }
  return map[inputType] || inputType
}

const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num
}

const formatDateTime = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

const getCoverageColor = (coverage) => {
  if (coverage >= 80) return '#67c23a'
  if (coverage >= 50) return '#e6a23c'
  return '#f56c6c'
}

const goBack = () => {
  router.push('/tasks')
}

const viewAllCrashes = () => {
  router.push('/results')
}

const downloadCrash = (crash) => {
  ElMessage.success(`下载崩溃样本: ${crash.crash_id}`)
}

const handleStart = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要启动任务 "${task.value.name}" 吗？`,
      '确认启动',
      {
        confirmButtonText: '启动',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    starting.value = true
    await startTask(route.params.id, 1)
    ElMessage.success('任务启动成功')

    // 订阅任务更新
    socketClient.subscribeTask(route.params.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '启动失败')
    }
  } finally {
    starting.value = false
  }
}

const handlePause = async () => {
  try {
    await pauseTask(route.params.id)
    ElMessage.success('任务已暂停')
    task.value.status = 'paused'
  } catch (error) {
    ElMessage.error(error.message || '暂停失败')
  }
}

const handleResume = async () => {
  try {
    await resumeTask(route.params.id)
    ElMessage.success('任务已恢复')
    task.value.status = 'running'
  } catch (error) {
    ElMessage.error(error.message || '恢复失败')
  }
}

const handleStop = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要停止任务 "${task.value.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '停止',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await stopTask(route.params.id)
    ElMessage.success('任务已停止')
    task.value.status = 'stopped'

    // 取消订阅
    socketClient.unsubscribeTask(route.params.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '停止失败')
    }
  }
}

const handleTaskUpdate = (data) => {
  if (data.task_id === parseInt(route.params.id)) {
    if (data.stats) {
      taskStats.value = data.stats
      rateHistory.value.push(data.stats.execs_per_sec || 0)
      if (rateHistory.value.length > 20) {
        rateHistory.value.shift()
      }
    }
    if (data.status) {
      task.value.status = data.status
    }
  }
}

const loadTask = async () => {
  try {
    const response = await getTaskDetail(route.params.id)
    task.value = response.data
  } catch (error) {
    ElMessage.error('加载任务详情失败')
    router.push('/tasks')
  }
}

const loadStats = async () => {
  try {
    const response = await getTaskStats(route.params.id)
    taskStats.value = response.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadCrashes = async () => {
  try {
    const response = await getTaskCrashes(route.params.id)
    recentCrashes.value = response.data.crashes?.slice(0, 5) || []
  } catch (error) {
    console.error('加载崩溃数据失败:', error)
  }
}

const updateRunTime = () => {
  if (task.value?.started_at) {
    const start = new Date(task.value.started_at)
    const now = new Date()
    const diff = Math.floor((now - start) / 1000)

    const hours = Math.floor(diff / 3600)
    const minutes = Math.floor((diff % 3600) / 60)
    const seconds = diff % 60

    runTime.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }
}

onMounted(async () => {
  await loadTask()
  await loadStats()
  await loadCrashes()

  // 连接 WebSocket
  try {
    await socketClient.connect()
    socketClient.on('task_update', handleTaskUpdate)
    if (task.value.status === 'running') {
      socketClient.subscribeTask(route.params.id)
    }
  } catch (error) {
    console.error('WebSocket 连接失败:', error)
  }

  // 启动计时器
  setInterval(() => {
    updateRunTime()
  }, 1000)
})

onUnmounted(() => {
  socketClient.removeAllListeners('task_update')
})
</script>

<style scoped>
.task-detail-container {
  padding: 24px 0;
}

.page-header {
  background: white;
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-card {
  height: 320px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rate-chart {
  height: 240px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.rate-bars {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 200px;
  width: 100%;
}

.rate-bar {
  flex: 1;
  display: flex;
  align-items: flex-end;
}

.bar-fill {
  width: 100%;
  max-width: 30px;
  min-width: 10px;
  background: linear-gradient(180deg, #409eff 0%, #66b1ff 100%);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

.coverage-display {
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.coverage-circle {
  position: relative;
  width: 150px;
  height: 150px;
}

.coverage-circle svg {
  width: 100%;
  height: 100%;
}

.coverage-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.coverage-labels {
  margin-top: 20px;
}

.coverage-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
  margin: 4px 0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.info-card,
.crashes-card {
  height: 400px;
}

.crashes-list {
  height: 300px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.crash-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  background: #fef0f0;
  margin-bottom: 8px;
}

.crash-icon {
  color: #f56c6c;
  font-size: 20px;
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

:deep(.el-descriptions__label) {
  width: 100px;
}

:deep(.el-descriptions__body .el-descriptions__table .el-descriptions__cell) {
  padding: 12px 16px;
}
</style>
