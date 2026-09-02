import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import AssessmentView from '../views/AssessmentView.vue'
import LocalContextView from '../views/LocalContextView.vue'
import AreaResultView from '../views/AreaResultView.vue'
import AboutView from '../views/AboutView.vue'

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
    // The About page itself is not built yet, just routed to a
    // placeholder for now so the header link is not dead.
    path: '/about',
    name: 'About',
    component: AboutView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router