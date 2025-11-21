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
    path: "/coach",
    name: "coach",
    component: () => import("./views/CoachView.vue"),
  },
  {
    path: "/print",
    name: "print",
    component: () => import("./views/PrintView.vue"),
  },
  {
    path: "/knowledge",
    name: "knowledge",
    component: () => import("./views/KnowledgeView.vue"),
  },
  {
    path: "/history",
    name: "history",
    component: () => import("./views/HistoryView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
