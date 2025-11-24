<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav class="flex w-full flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div class="flex items-center gap-6">
          <RouterLink to="/" class="text-lg font-semibold text-slate-900">ClassWeaver</RouterLink>
          <div class="flex flex-wrap items-center gap-4 text-sm text-slate-600">
            <RouterLink to="/" class="hover:text-blue-600">&#23398;&#20064;&#24037;&#20316;&#21488;</RouterLink>
            <RouterLink to="/coach" class="hover:text-blue-600">&#25945;&#32451;&#36741;&#23548;</RouterLink>
            <RouterLink to="/take" class="hover:text-blue-600">&#27979;&#39564;&#32451;&#20064;</RouterLink>
            <RouterLink to="/print" class="hover:text-blue-600">&#25171;&#21360;&#28165;&#21333;</RouterLink>
          </div>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <template v-if="currentUser">
            <span class="rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-800">&#29992;&#25143;&#65306;{{ currentUser.username }}</span>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 font-medium text-white transition hover:bg-slate-700 disabled:opacity-60"
              :disabled="authLoading"
              @click="handleLogout"
            >
              &#36864;&#20986;
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="rounded-full border border-slate-200 px-4 py-2 font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
            >
              &#30331;&#24405;
            </RouterLink>
            <RouterLink
              to="/register"
              class="rounded-full bg-slate-900 px-4 py-2 font-medium text-white transition hover:bg-slate-700"
            >
              &#27880;&#20876;
            </RouterLink>
          </template>
        </div>
      </nav>
    </header>
    <main class="w-full px-4 py-6 sm:px-6 lg:px-10">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useAuth } from "./utils/auth";

const { currentUser, authLoading, loadCurrentUser, signOut } = useAuth();

onMounted(() => {
  loadCurrentUser();
});

const handleLogout = async () => {
  await signOut();
};
</script>
