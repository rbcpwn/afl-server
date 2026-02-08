# AFL Fuzz 平台前端

基于 Vue 3 + Element Plus 开发的 AFL Fuzz 平台前端界面。

## 功能特性

- 白盒测试：上传 C/C++ 源代码进行 AFL 编译插桩测试
- 黑盒测试：上传 ELF 二进制文件进行 QEMU 模式测试
- 种子管理：上传和管理测试种子文件
- 任务管理：查看、启动、暂停、删除 fuzz 任务
- 结果分析：崩溃样本分析、覆盖率报告、漏洞详情

## 技术栈

- Vue 3 (Composition API)
- Vue Router
- Pinia
- Element Plus
- Axios
- Vite

## 本地开发

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 http://localhost:5173 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 目录结构

```
frontend/
├── src/
│   ├── api/          # API 接口
│   ├── router/       # 路由配置
│   ├── stores/       # Pinia 状态管理
│   ├── utils/        # 工具函数
│   ├── views/        # 页面组件
│   ├── App.vue       # 根组件
│   └── main.js       # 入口文件
├── index.html
├── package.json
└── vite.config.js
```

## API 接口说明

### 白盒测试上传
- POST `/api/upload/whitebox`
- 参数：taskName, mainFile, compileArgs, files[]

### 黑盒测试上传
- POST `/api/upload/blackbox`
- 参数：taskName, inputType, dependencies, file

### 种子文件上传
- POST `/api/upload/seeds`
- 参数：taskId, files[]

### 任务管理
- GET `/api/tasks` - 获取任务列表
- POST `/api/tasks/:id/start` - 启动任务
- POST `/api/tasks/:id/pause` - 暂停任务
- DELETE `/api/tasks/:id` - 删除任务

### 结果查询
- GET `/api/results` - 获取结果统计
- GET `/api/results/crashes` - 获取崩溃列表
- GET `/api/results/coverage` - 获取覆盖率数据
