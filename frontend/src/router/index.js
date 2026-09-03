import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import AssessmentView from '../views/AssessmentView.vue'
import LocalContextView from '../views/LocalContextView.vue'
import AreaResultView from '../views/AreaResultView.vue'
import PlantingIdeasView from '../views/PlantingIdeasView.vue'

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
  },
  {
    path: '/area/:postcode',
    name: 'AreaResult',
    component: AreaResultView
  },
  {
    path: '/planting',
    name: 'PlantingIdeas',
    component: PlantingIdeasView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
