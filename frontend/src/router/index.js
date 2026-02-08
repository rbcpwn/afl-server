import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue')
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('@/views/Tasks.vue')
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/views/TaskDetail.vue')
  },
  {
    path: '/results',
    name: 'Results',
    component: () => import('@/views/Results.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
