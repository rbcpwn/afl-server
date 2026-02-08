<template>
  <div class="tasks-container">
    <el-card class="tasks-card">
      <template #header>
        <div class="card-header">
          <h2>Fuzz 任务列表</h2>
          <el-button type="primary" @click="goToUpload">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="statusFilter" placeholder="筛选状态" style="width: 150px" clearable>
          <el-option label="全部" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>

        <el-select v-model="typeFilter" placeholder="筛选类型" style="width: 150px" clearable>
          <el-option label="全部" value="" />
          <el-option label="白盒测试" value="whitebox" />
          <el-option label="黑盒测试" value="blackbox" />
        </el-select>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索任务名称"
          style="width: 250px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <el-table :data="filteredTasks" stripe style="width: 100%">
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column label="测试类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'whitebox' ? 'primary' : 'success'">
              {{ row.type === 'whitebox' ? '白盒' : '黑盒' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="execCount" label="执行次数" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.execCount) }}
          </template>
        </el-table-column>
        <el-table-column prop="crashCount" label="崩溃数" width="80">
          <template #default="{ row }">
            <span :class="{ 'crash-count': row.crashCount > 0 }">
              {{ row.crashCount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="coverage" label="覆盖率" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.coverage || 0"
              :status="getCoverageStatus(row.coverage)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'paused'"
              type="primary"
              size="small"
              @click="startTask(row)"
            >
              启动
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              @click="pauseTask(row)"
            >
              暂停
            </el-button>
            <el-button
              size="small"
              @click="viewDetails(row)"
            >
              详情
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteTask(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalTasks"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const tasks = ref([])
const statusFilter = ref('')
const typeFilter = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const totalTasks = computed(() => tasks.value.length)

const filteredTasks = computed(() => {
  let result = tasks.value

  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }

  if (typeFilter.value) {
    result = result.filter(t => t.type === typeFilter.value)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(t =>
      t.name.toLowerCase().includes(keyword) ||
      t.id.toString().includes(keyword)
    )
  }

  const start = (currentPage.value - 1) * pageSize.value
  return result.slice(start, start + pageSize.value)
})

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'success',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getCoverageStatus = (coverage) => {
  if (coverage >= 80) return 'success'
  if (coverage >= 50) return 'warning'
  return 'exception'
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

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = () => {
  currentPage.value = 1
}

const handleCurrentChange = () => {
}

const startTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动任务 "${task.name}" 吗？`,
      '确认启动',
      {
        confirmButtonText: '启动',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    task.status = 'running'
    ElMessage.success(`任务 "${task.name}" 已启动`)
  } catch {
  }
}

const pauseTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要暂停任务 "${task.name}" 吗？`,
      '确认暂停',
      {
        confirmButtonText: '暂停',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    task.status = 'paused'
    ElMessage.success(`任务 "${task.name}" 已暂停`)
  } catch {
  }
}

const viewDetails = (task) => {
  router.push(`/tasks/${task.id}`)
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index > -1) {
      tasks.value.splice(index, 1)
    }
    ElMessage.success(`任务 "${task.name}" 已删除`)
  } catch {
  }
}

const goToUpload = () => {
  router.push('/upload')
}

const loadTasks = () => {
  tasks.value = [
    {
      id: 1,
      name: 'test_whitebox_vuln',
      type: 'whitebox',
      status: 'running',
      execCount: 1523456,
      crashCount: 3,
      coverage: 67.5,
      createdAt: '2024-01-15 10:30:00'
    },
    {
      id: 2,
      name: 'test_blackbox_app',
      type: 'blackbox',
      status: 'pending',
      execCount: 0,
      crashCount: 0,
      coverage: 0,
      createdAt: '2024-01-16 14:20:00'
    },
    {
      id: 3,
      name: 'buffer_overflow_test',
      type: 'whitebox',
      status: 'completed',
      execCount: 5678901,
      crashCount: 12,
      coverage: 92.3,
      createdAt: '2024-01-14 09:15:00'
    },
    {
      id: 4,
      name: 'format_string_bug',
      type: 'whitebox',
      status: 'failed',
      execCount: 234567,
      crashCount: 0,
      coverage: 34.2,
      createdAt: '2024-01-17 11:45:00'
    }
  ]

  if (route.query.taskId) {
    const taskId = parseInt(route.query.taskId)
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      ElMessage.success(`已跳转到任务: ${task.name}`)
    }
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.tasks-container {
  max-width: 1400px;
  margin: 0 auto;
}

.tasks-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  color: #303133;
  margin: 0;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.crash-count {
  color: #f56c6c;
  font-weight: bold;
}

.el-pagination {
  margin-top: 24px;
  justify-content: flex-end;
}
</style>
