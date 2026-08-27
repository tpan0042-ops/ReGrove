import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import AssessmentView from '../views/AssessmentView.vue'
import LocalContextView from '../views/LocalContextView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/assessment',
    name: 'Assessment',
    component: AssessmentView
  },
  {
    path: '/explore',
    name: 'Explore',
    component: LocalContextView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router