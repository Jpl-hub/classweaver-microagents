import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "./utils/auth";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("./views/HomeView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/take",
    name: "take",
    component: () => import("./views/TakeView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/coach",
    name: "coach",
    component: () => import("./views/CoachView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/print",
    name: "print",
    component: () => import("./views/PrintView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/knowledge",
    name: "knowledge",
    component: () => import("./views/KnowledgeView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/history",
    name: "history",
    component: () => import("./views/HistoryView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("./views/LoginView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("./views/RegisterView.vue"),
    meta: { requiresAuth: false },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const publicNames = new Set(["login", "register"]);

router.beforeEach(async (to) => {
  if (publicNames.has((to.name as string) || "")) {
    return true;
  }
  const auth = useAuth();
  await auth.loadCurrentUser();
  if (!auth.currentUser.value) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
