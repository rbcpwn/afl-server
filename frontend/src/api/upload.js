import request from '@/utils/request'

export const uploadWhiteboxFiles = (formData) => {
  return request({
    url: '/upload/whitebox',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const uploadBlackboxFile = (formData) => {
  return request({
    url: '/upload/blackbox',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const uploadSeedFiles = (formData) => {
  return request({
    url: '/upload/seeds',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getTasks = () => {
  return request({
    url: '/tasks',
    method: 'get'
  })
}

export const getTaskDetail = (taskId) => {
  return request({
    url: `/tasks/${taskId}`,
    method: 'get'
  })
}

export const startTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}/start`,
    method: 'post'
  })
}

export const pauseTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}/pause`,
    method: 'post'
  })
}

export const stopTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}/stop`,
    method: 'post'
  })
}

export const deleteTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}`,
    method: 'delete'
  })
}

export const getResults = () => {
  return request({
    url: '/results',
    method: 'get'
  })
}

export const getCrashes = (taskId) => {
  return request({
    url: `/results/crashes`,
    method: 'get',
    params: { taskId }
  })
}

export const getCoverage = (taskId) => {
  return request({
    url: `/results/coverage`,
    method: 'get',
    params: { taskId }
  })
}

export const downloadCrashSample = (crashId) => {
  return request({
    url: `/results/crashes/${crashId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

export const exportReport = (taskId) => {
  return request({
    url: `/results/export`,
    method: 'get',
    params: { taskId },
    responseType: 'blob'
  })
}
