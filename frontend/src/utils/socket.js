import { io } from 'socket.io-client'
import { ElMessage } from 'element-plus'

// 全局事件总线，用于组件间通信
const eventBus = {
  listeners: {},
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  },
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data))
    }
  },
  off(event, callback) {
    if (!this.listeners[event]) return
    const index = this.listeners[event].indexOf(callback)
    if (index > -1) {
      this.listeners[event].splice(index, 1)
    }
  }
}

// 简单的 Socket.IO 客户端
class SimpleSocketClient {
  constructor() {
    this.socket = null
    this.connected = false
  }

  // 连接到服务器
  connect(url = '') {
    return new Promise((resolve, reject) => {
      if (this.connected && this.socket) {
        resolve(this.socket)
        return
      }

      try {
        // 确定连接地址
        const socketUrl = url || window.location.origin

        // 创建 Socket.IO 实例
        this.socket = io(socketUrl, {
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionDelay: 3000,
          timeout: 10000
        })

        // 连接成功
        this.socket.on('connect', () => {
          this.connected = true
          console.log('[Socket] 已连接')
          ElMessage.success('已连接到服务器')
          eventBus.emit('socket:connected')
          resolve(this.socket)
        })

        // 连接错误
        this.socket.on('connect_error', (error) => {
          console.error('[Socket] 连接错误:', error)
          ElMessage.error('连接失败: ' + (error.message || '网络错误'))
          eventBus.emit('socket:disconnected')
          reject(error)
        })

        // 断开连接
        this.socket.on('disconnect', (reason) => {
          this.connected = false
          console.log('[Socket] 已断开:', reason)
          eventBus.emit('socket:disconnected')
        })

        // 服务器错误
        this.socket.on('error', (error) => {
          console.error('[Socket] 服务器错误:', error)
          if (error.message) {
            ElMessage.error('服务器错误: ' + error.message)
          }
        })

        // 接收任务更新
        this.socket.on('task_update', (data) => {
          console.log('[Socket] 任务更新:', data)
          eventBus.emit('task:update', data)
        })

        // 接收仪表盘更新
        this.socket.on('dashboard_update', (data) => {
          console.log('[Socket] 仪表盘更新:', data)
          eventBus.emit('dashboard:update', data)
        })

        // 心跳响应
        this.socket.on('pong', (data) => {
          console.log('[Socket] 心跳响应:', data)
        })
      } catch (error) {
        console.error('[Socket] 连接异常:', error)
        ElMessage.error('连接失败: ' + (error.message || '请检查网络'))
        reject(error)
      }
    })
  }

  // 断开连接
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
      console.log('[Socket] 已断开')
      eventBus.emit('socket:disconnected')
    }
  }

  // 发送事件
  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('[Socket] 未连接，无法发送事件:', event)
      eventBus.emit('socket:disconnected')
      ElMessage.warning('请先连接服务器')
    }
  }

  // 订阅任务更新
  onTaskUpdate(callback) {
    eventBus.on('task:update', callback)
  }

  // 取消订阅任务更新
  offTaskUpdate(callback) {
    eventBus.off('task:update', callback)
  }

  // 订阅仪表盘更新
  onDashboardUpdate(callback) {
    eventBus.on('dashboard:update', callback)
  }

  // 取消订阅仪表盘更新
  offDashboardUpdate(callback) {
    eventBus.off('dashboard:update', callback)
  }

  // 连接状态
  onConnect(callback) {
    eventBus.on('socket:connected', callback)
  }

  // 断开连接状态
  onDisconnect(callback) {
    eventBus.on('socket:disconnected', callback)
  }

  // 心跳检测
  ping() {
    if (this.socket && this.connected) {
      this.socket.emit('ping')
    }
  }

  // 检查连接状态
  isConnected() {
    return this.connected
  }
}

// 创建全局实例
const socketClient = new SimpleSocketClient()

export default socketClient
