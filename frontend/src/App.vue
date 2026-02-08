<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1 class="title">AFL Fuzz 平台</h1>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            router
            class="nav-menu"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/dashboard">
              <el-icon><DataLine /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="/upload">
              <el-icon><UploadFilled /></el-icon>
              <span>上传测试文件</span>
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>Fuzz 任务</span>
            </el-menu-item>
            <el-menu-item index="/results">
              <el-icon><Document /></el-icon>
              <span>结果分析</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, UploadFilled, List, DataLine, Document } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
</script>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
}

.title {
  font-size: 20px;
  color: #409eff;
  margin: 0;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  margin-left: 60px;
  border-bottom: none;
}

.el-main {
  padding: 24px;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
