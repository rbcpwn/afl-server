import io from 'socket.io-client'
import { ElMessage } from 'element-plus'

class SocketClient {
  constructor() {
    this.socket = null
    this.connected = false
    this.listeners = {}
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
  }

  connect(url = 'http://localhost:5000', options = {}) {
    return new Promise((resolve, reject) => {
      if (this.socket && this.connected) {
        resolve(this.socket)
        return
      }

      const defaultOptions = {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: this.reconnectDelay,
        reconnectionAttempts: this.maxReconnectAttempts
      }

      this.socket = io(url, { ...defaultOptions, ...options })

      this.socket.on('connect', () => {
        console.log('WebSocket 已连接')
        this.connected = true
        this.reconnectAttempts = 0
        this.emit('client-ready', { timestamp: Date.now() })
        resolve(this.socket)
      })

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket 已断开:', reason)
        this.connected = false
        this.reconnectAttempts++

        if (reason === 'io server disconnect') {
          this.socket.connect()
        }
      })

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket 连接错误:', error)
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          ElMessage.error('无法连接到服务器，请检查网络连接')
          reject(error)
        }
      })

      this.socket.on('connected', (data) => {
        console.log('服务器确认连接:', data)
      })

      this.socket.on('error', (error) => {
        console.error('WebSocket 错误:', error)
        ElMessage.error(error.message || '发生错误')
      })

      this.setupDefaultListeners()
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.connected = false
      this.socket = null
    }
  }

  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket 未连接，无法发送事件:', event)
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)

    if (this.socket) {
      this.socket.on(event, callback)
    }
  }

  off(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback)
      if (index > -1) {
        this.listeners[event].splice(index, 1)
      }
    }

    if (this.socket) {
      this.socket.off(event, callback)
    }
  }

  removeAllListeners(event) {
    if (event) {
      if (this.listeners[event]) {
        this.listeners[event].forEach(callback => {
          if (this.socket) {
            this.socket.off(event, callback)
          }
        })
        delete this.listeners[event]
      }
    } else {
      if (this.socket) {
        this.socket.removeAllListeners()
      }
      this.listeners = {}
    }
  }

  setupDefaultListeners() {
    this.on('task_update', (data) => {
      console.log('任务更新:', data)
    })

    this.on('dashboard_update', (data) => {
      console.log('仪表盘更新:', data)
    })

    this.on('pong', (data) => {
      console.log('心跳响应:', data)
    })
  }

  subscribeTask(taskId) {
    this.emit('subscribe_task', { task_id: taskId })
  }

  unsubscribeTask(taskId) {
    this.emit('unsubscribe_task', { task_id: taskId })
  }

  subscribeDashboard() {
    this.emit('subscribe_dashboard')
  }

  ping() {
    this.emit('ping')
    return new Promise((resolve) => {
      const onPong = (data) => {
        this.off('pong', onPong)
        resolve(data)
      }
      this.on('pong', onPong)
      setTimeout(() => {
        this.off('pong', onPong)
        resolve(null)
      }, 5000)
    })
  }

  isConnected() {
    return this.connected
  }
}

const socketClient = new SocketClient()

export default socketClient
