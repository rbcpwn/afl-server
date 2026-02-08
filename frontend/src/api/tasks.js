import request from '@/utils/request'

export const getTasks = () => {
  return request({
    url: '/tasks',
    method: 'get'
  })
}

export const getDashboardStats = () => {
  return request({
    url: '/results/dashboard',
    method: 'get'
  })
}

export const getAllCrashes = (taskId) => {
  return request({
    url: '/results/crashes',
    method: 'get',
    params: { taskId }
  })
}

export const getCoverage = (taskId) => {
  return request({
    url: '/results/coverage',
    method: 'get',
    params: { taskId }
  })
}

export const exportReport = (taskId) => {
  return request({
    url: '/results/export',
    method: 'get',
    params: { taskId },
    responseType: 'blob'
  })
}

export const downloadCrash = (crashId) => {
  return request({
    url: `/results/crashes/${crashId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

export const getTaskStats = (taskId) => {
  return request({
    url: `/tasks/${taskId}/stats`,
    method: 'get'
  })
}

export const getTaskCrashes = (taskId) => {
  return request({
    url: `/tasks/${taskId}/crashes`,
    method: 'get'
  })
}

export const getTaskCorpus = (taskId) => {
  return request({
    url: `/tasks/${taskId}/corpus`,
    method: 'get'
  })
}

export const getTaskDetail = (taskId) => {
  return request({
    url: `/tasks/${taskId}`,
    method: 'get'
  })
}

export const startTask = (taskId, fuzzerCount = 1) => {
  return request({
    url: `/tasks/${taskId}/start`,
    method: 'post',
    data: { fuzzer_count: fuzzerCount }
  })
}

export const pauseTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}/pause`,
    method: 'post'
  })
}

export const resumeTask = (taskId) => {
  return request({
    url: `/tasks/${taskId}/resume`,
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
