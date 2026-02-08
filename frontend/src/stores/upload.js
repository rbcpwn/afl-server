import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUploadStore = defineStore('upload', () => {
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const uploadMessage = ref('')
  const uploadHistory = ref([])

  const setUploading = (value) => {
    uploading.value = value
  }

  const setProgress = (value) => {
    uploadProgress.value = value
  }

  const setMessage = (message) => {
    uploadMessage.value = message
  }

  const addHistory = (record) => {
    uploadHistory.value.unshift({
      ...record,
      timestamp: new Date().toISOString()
    })
  }

  const clearHistory = () => {
    uploadHistory.value = []
  }

  const reset = () => {
    uploading.value = false
    uploadProgress.value = 0
    uploadMessage.value = ''
  }

  return {
    uploading,
    uploadProgress,
    uploadMessage,
    uploadHistory,
    setUploading,
    setProgress,
    setMessage,
    addHistory,
    clearHistory,
    reset
  }
})
