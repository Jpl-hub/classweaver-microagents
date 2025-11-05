import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("./views/HomeView.vue"),
  },
  {
    path: "/take",
    name: "take",
    component: () => import("./views/TakeView.vue"),
  },
  {
    path: "/print",
    name: "print",
    component: () => import("./views/PrintView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
