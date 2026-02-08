<template>
  <div class="results-container">
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <h2>测试结果分析</h2>
          <el-button type="primary" @click="exportResults">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>

      <div class="stats-grid">
        <el-statistic title="总任务数" :value="totalTasks" />
        <el-statistic title="发现漏洞" :value="totalCrashes" />
        <el-statistic title="总执行次数" :value="totalExecutions" :precision="0" />
        <el-statistic title="平均覆盖率" :value="avgCoverage" suffix="%" :precision="1" />
      </div>

      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="崩溃样本" name="crashes">
          <el-table :data="crashes" stripe style="width: 100%">
            <el-table-column prop="id" label="样本ID" width="80" />
            <el-table-column prop="taskName" label="所属任务" width="180" />
            <el-table-column prop="crashType" label="崩溃类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getCrashTypeColor(row.crashType)">
                  {{ row.crashType }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="signal" label="信号" width="80" />
            <el-table-column prop="reproducible" label="可重现" width="100">
              <template #default="{ row }">
                <el-tag :type="row.reproducible ? 'success' : 'danger'">
                  {{ row.reproducible ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100">
              <template #default="{ row }">
                <el-rate
                  v-model="row.severity"
                  disabled
                  :colors="['#f56c6c', '#e6a23c', '#67c23a']"
                  show-score
                />
              </template>
            </el-table-column>
            <el-table-column prop="foundAt" label="发现时间" width="160" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewCrash(row)">查看</el-button>
                <el-button size="small" type="primary" @click="downloadCrash(row)">
                  下载
                </el-button>
                <el-button size="small" type="danger" @click="reproduceCrash(row)">
                  复现
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="覆盖率报告" name="coverage">
          <div class="coverage-content">
            <div class="coverage-chart">
              <h3>覆盖率趋势</h3>
              <div class="mock-chart">
                <div class="chart-bars">
                  <div v-for="(value, index) in coverageData" :key="index" class="bar">
                    <div
                      class="bar-fill"
                      :style="{ height: value + '%' }"
                      :title="`时间点 ${index + 1}: ${value}%`"
                    ></div>
                    <span class="bar-label">{{ value }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <el-divider />

            <h3>各任务覆盖率详情</h3>
            <el-table :data="taskCoverage" stripe style="width: 100%">
              <el-table-column prop="taskName" label="任务名称" width="200" />
              <el-table-column prop="edgeCoverage" label="边覆盖率" width="120">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.edgeCoverage"
                    :status="getCoverageStatus(row.edgeCoverage)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="pathCoverage" label="路径覆盖率" width="120">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.pathCoverage"
                    :status="getCoverageStatus(row.pathCoverage)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="uniqueCrashes" label="唯一崩溃" width="100" />
              <el-table-column prop="totalExecs" label="总执行次数">
                <template #default="{ row }">
                  {{ formatNumber(row.totalExecs) }}
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="运行时长" width="100" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="漏洞详情" name="vulnerabilities">
          <el-collapse accordion>
            <el-collapse-item
              v-for="vuln in vulnerabilities"
              :key="vuln.id"
              :title="`${vuln.id}. ${vuln.title}`"
              :name="vuln.id"
            >
              <div class="vuln-detail">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="漏洞类型">
                    <el-tag :type="getVulnTypeColor(vuln.type)">{{ vuln.type }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="严重程度">
                    <el-tag :type="getSeverityColor(vuln.severity)">
                      {{ vuln.severity }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="影响文件" span="2">
                    {{ vuln.affectedFile }}
                  </el-descriptions-item>
                  <el-descriptions-item label="漏洞描述" span="2">
                    {{ vuln.description }}
                  </el-descriptions-item>
                  <el-descriptions-item label="触发样本" span="2">
                    <el-button size="small" @click="downloadSample(vuln)">
                      {{ vuln.sampleName }}
                    </el-button>
                  </el-descriptions-item>
                </el-descriptions>

                <div v-if="vuln.stackTrace" class="stack-trace">
                  <h4>调用栈</h4>
                  <pre><code>{{ vuln.stackTrace }}</code></pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const activeTab = ref('crashes')

const totalTasks = ref(4)
const totalCrashes = ref(15)
const totalExecutions = ref(7447024)
const avgCoverage = ref(64.8)

const crashes = ref([
  {
    id: 'C001',
    taskId: 1,
    taskName: 'test_whitebox_vuln',
    crashType: 'Heap Overflow',
    signal: 'SIGSEGV',
    reproducible: true,
    severity: 5,
    foundAt: '2024-01-15 14:32:15'
  },
  {
    id: 'C002',
    taskId: 1,
    taskName: 'test_whitebox_vuln',
    crashType: 'Stack Overflow',
    signal: 'SIGSEGV',
    reproducible: true,
    severity: 4,
    foundAt: '2024-01-15 15:45:22'
  },
  {
    id: 'C003',
    taskId: 1,
    taskName: 'test_whitebox_vuln',
    crashType: 'Use After Free',
    signal: 'SIGABRT',
    reproducible: true,
    severity: 5,
    foundAt: '2024-01-15 16:23:08'
  },
  {
    id: 'C004',
    taskId: 3,
    taskName: 'buffer_overflow_test',
    crashType: 'Buffer Overflow',
    signal: 'SIGSEGV',
    reproducible: true,
    severity: 4,
    foundAt: '2024-01-14 10:12:33'
  },
  {
    id: 'C005',
    taskId: 3,
    taskName: 'buffer_overflow_test',
    crashType: 'Double Free',
    signal: 'SIGABRT',
    reproducible: false,
    severity: 3,
    foundAt: '2024-01-14 12:34:56'
  }
])

const coverageData = ref([10, 25, 38, 52, 65, 72, 78, 85, 88, 92])

const taskCoverage = ref([
  {
    taskName: 'test_whitebox_vuln',
    edgeCoverage: 67.5,
    pathCoverage: 45.2,
    uniqueCrashes: 3,
    totalExecs: 1523456,
    duration: '2h 15m'
  },
  {
    taskName: 'test_blackbox_app',
    edgeCoverage: 12.3,
    pathCoverage: 8.5,
    uniqueCrashes: 0,
    totalExecs: 0,
    duration: '0m'
  },
  {
    taskName: 'buffer_overflow_test',
    edgeCoverage: 92.3,
    pathCoverage: 78.9,
    uniqueCrashes: 12,
    totalExecs: 5678901,
    duration: '5h 30m'
  },
  {
    taskName: 'format_string_bug',
    edgeCoverage: 34.2,
    pathCoverage: 22.1,
    uniqueCrashes: 0,
    totalExecs: 234567,
    duration: '45m'
  }
])

const vulnerabilities = ref([
  {
    id: 'VULN-001',
    title: 'heap_buffer_overflow',
    type: 'Heap Overflow',
    severity: 'Critical',
    affectedFile: 'src/buffer.c:127',
    description: '在处理用户输入时未进行边界检查，导致堆缓冲区溢出。攻击者可通过构造特制输入触发该漏洞，可能导致代码执行。',
    sampleName: 'crash_C001.bin',
    stackTrace: `#0  0x00007f8e4b1a3b5a in memcpy (dst=0x55a1e2a5b2a0, src=0x7fff8c4e5c10, n=1024)
    at ../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:243
#1  0x000055a1e2a3b78c in process_input (input=0x7fff8c4e5c10 "AAAAAA...") at src/buffer.c:127
#2  0x000055a1e2a3c234 in handle_request (fd=3) at src/server.c:89
#3  0x000055a1e2a3d112 in main (argc=1, argv=0x7fff8c4e68f8) at src/main.c:156`
  },
  {
    id: 'VULN-002',
    title: 'stack_overflow_vuln',
    type: 'Stack Overflow',
    severity: 'High',
    affectedFile: 'src/parser.c:89',
    description: '递归调用没有正确设置终止条件，导致栈溢出。',
    sampleName: 'crash_C002.bin',
    stackTrace: `#0  0x000055a1e2a4b123 in parse_recursive (depth=1024) at src/parser.c:89
#1  0x000055a1e2a4b123 in parse_recursive (depth=1023) at src/parser.c:89
...
#1023 0x000055a1e2a4b123 in parse_recursive (depth=1) at src/parser.c:89
#1024 0x000055a1e2a4c456 in main (argc=1, argv=0x7fff8c4e68f8) at src/main.c:156`
  },
  {
    id: 'VULN-003',
    title: 'use_after_free',
    type: 'Use After Free',
    severity: 'Critical',
    affectedFile: 'src/memory.c:203',
    description: '释放内存后仍尝试访问该内存指针，导致UAF漏洞。',
    sampleName: 'crash_C003.bin',
    stackTrace: `#0  0x000055a1e2a5d789 in access_freed_ptr (ptr=0x55a1e2b5a010) at src/memory.c:203
#1  0x000055a1e2a5e123 in process_object (obj=0x55a1e2b5a008) at src/object.c:67
#2  0x000055a1e2a5f456 in main (argc=1, argv=0x7fff8c4e68f8) at src/main.c:156`
  }
])

const getCrashTypeColor = (type) => {
  const colors = {
    'Heap Overflow': 'danger',
    'Stack Overflow': 'danger',
    'Use After Free': 'danger',
    'Buffer Overflow': 'warning',
    'Double Free': 'warning',
    'Format String': 'info'
  }
  return colors[type] || 'info'
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

const getVulnTypeColor = (type) => {
  const colors = {
    'Heap Overflow': 'danger',
    'Stack Overflow': 'danger',
    'Use After Free': 'danger',
    'Buffer Overflow': 'warning',
    'Double Free': 'warning',
    'Format String': 'info',
    'Integer Overflow': 'warning'
  }
  return colors[type] || 'info'
}

const getSeverityColor = (severity) => {
  const colors = {
    'Critical': 'danger',
    'High': 'danger',
    'Medium': 'warning',
    'Low': 'success'
  }
  return colors[severity] || 'info'
}

const viewCrash = (crash) => {
  ElMessage.info(`查看崩溃样本: ${crash.id}`)
}

const downloadCrash = (crash) => {
  ElMessage.success(`正在下载崩溃样本: ${crash.id}`)
}

const reproduceCrash = (crash) => {
  ElMessage.info(`准备复现崩溃: ${crash.id}`)
}

const downloadSample = (vuln) => {
  ElMessage.success(`正在下载样本: ${vuln.sampleName}`)
}

const exportResults = () => {
  ElMessage.success('正在生成报告...')
}
</script>

<style scoped>
.results-container {
  max-width: 1400px;
  margin: 0 auto;
}

.results-card {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.coverage-content {
  padding: 24px 0;
}

.coverage-chart {
  margin-bottom: 24px;
}

.coverage-chart h3 {
  color: #303133;
  margin-bottom: 16px;
}

.mock-chart {
  background: #f5f7fa;
  padding: 32px;
  border-radius: 8px;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  height: 200px;
}

.bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-fill {
  width: 100%;
  max-width: 40px;
  min-width: 20px;
  background: linear-gradient(180deg, #409eff 0%, #67c23a 100%);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

.bar-fill:hover {
  background: linear-gradient(180deg, #66b1ff 0%, #85ce61 100%);
}

.bar-label {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.vuln-detail {
  padding: 16px 0;
}

.vuln-detail .el-descriptions {
  margin-bottom: 24px;
}

.stack-trace {
  margin-top: 24px;
}

.stack-trace h4 {
  color: #303133;
  margin-bottom: 12px;
}

.stack-trace pre {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
}

.stack-trace code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #303133;
}

:deep(.el-tabs__content) {
  padding: 24px;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
}
</style>
