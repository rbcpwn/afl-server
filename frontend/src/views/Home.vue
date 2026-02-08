<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <h2>欢迎使用 AFL Fuzz 平台</h2>
      <p class="description">
        基于AFL的二进制漏洞挖掘平台，支持白盒和黑盒两种测试方式
      </p>
    </el-card>

    <div class="feature-grid">
      <el-card class="feature-card" shadow="hover">
        <div class="feature-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <h3>白盒测试</h3>
        <p>上传C/C++源代码，通过AFL编译插桩进行测试</p>
      </el-card>

      <el-card class="feature-card" shadow="hover">
        <div class="feature-icon">
          <el-icon :size="48"><Files /></el-icon>
        </div>
        <h3>黑盒测试</h3>
        <p>上传编译好的ELF二进制文件，使用QEMU模式测试</p>
      </el-card>

      <el-card class="feature-card" shadow="hover">
        <div class="feature-icon">
          <el-icon :size="48"><TrendCharts /></el-icon>
        </div>
        <h3>结果分析</h3>
        <p>自动分析崩溃样本，生成详细的漏洞报告</p>
      </el-card>

      <el-card class="feature-card" shadow="hover">
        <div class="feature-icon">
          <el-icon :size="48"><Monitor /></el-icon>
        </div>
        <h3>实时监控</h3>
        <p>实时监控Fuzz任务状态，查看执行进度和覆盖率</p>
      </el-card>
    </div>

    <el-card class="quick-start-card">
      <h3>快速开始</h3>
      <el-steps :active="1" finish-status="success">
        <el-step title="上传测试文件" description="选择白盒或黑盒测试方式" />
        <el-step title="配置Fuzz参数" description="设置目标程序和测试参数" />
        <el-step title="开始Fuzz测试" description="启动AFL进行漏洞挖掘" />
        <el-step title="查看测试结果" description="分析崩溃样本和覆盖率报告" />
      </el-steps>
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="goToUpload">
          立即开始
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
        <el-button size="large" @click="goToDashboard">
          查看仪表盘
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Document, Files, TrendCharts, Monitor, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

const goToUpload = () => {
  router.push('/upload')
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  text-align: center;
  margin-bottom: 32px;
}

.welcome-card h2 {
  color: #303133;
  margin-bottom: 12px;
}

.description {
  color: #606266;
  font-size: 16px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.feature-card {
  text-align: center;
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  color: #409eff;
  margin-bottom: 16px;
}

.feature-card h3 {
  color: #303133;
  margin-bottom: 12px;
}

.feature-card p {
  color: #909399;
  line-height: 1.6;
}

.quick-start-card {
  margin-bottom: 24px;
}

.quick-start-card h3 {
  color: #303133;
  margin-bottom: 24px;
}

.action-buttons {
  margin-top: 32px;
  text-align: center;
}
</style>
