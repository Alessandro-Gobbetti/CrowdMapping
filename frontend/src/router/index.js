import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/CrowdMapping/',
    name: 'map',
    meta: { title: 'Map' },
    component: () => import(/* webpackChunkName: "map" */ '@/views/MapPage.vue')
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
