import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const loading = ref(false)

  const setTasks = (data) => {
    tasks.value = data
  }

  const setCurrentTask = (task) => {
    currentTask.value = task
  }

  const addTask = (task) => {
    tasks.value.unshift(task)
  }

  const updateTask = (taskId, updates) => {
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index > -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates }
    }
  }

  const removeTask = (taskId) => {
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index > -1) {
      tasks.value.splice(index, 1)
    }
  }

  const setLoading = (value) => {
    loading.value = value
  }

  return {
    tasks,
    currentTask,
    loading,
    setTasks,
    setCurrentTask,
    addTask,
    updateTask,
    removeTask,
    setLoading
  }
})
