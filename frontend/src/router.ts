import { createRouter, createWebHistory } from "vue-router"

import AppLayout from "./layouts/AppLayout.vue"

import Login from "./views/LoginView.vue"
import Dashboard from "./views/DashboardView.vue"
import Patients from "./views/PatientsView.vue"
import PatientDetail from "./views/PatientDetailView.vue"
import Owners from "./views/OwnersView.vue"
import Orders from "./views/OrdersView.vue"       
import OrderDetail from "./views/OrderDetailView.vue"
import Settings from "./views/SettingsView.vue"   

const routes = [
  {
    path: "/",
    component: AppLayout,
    children: [
      { path: "", redirect: "/dashboard" },
      { path: "dashboard", component: Dashboard },
      { path: "patients", component: Patients },
            { path: "patients/:id", component: PatientDetail },
      { path: "owners", component: Owners },
      { path: "orders", component: Orders },
            { path: "orders/:id", component: OrderDetail },
      { path: "settings", component: Settings },
      { path: "/login", component: Login },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

