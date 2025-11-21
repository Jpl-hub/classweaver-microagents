<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav class="flex w-full items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <RouterLink to="/" class="text-lg font-semibold text-slate-900">ClassWeaver</RouterLink>
        <div class="flex items-center gap-4 text-sm text-slate-600">
          <RouterLink to="/" class="hover:text-blue-600">学习工作台</RouterLink>
          <RouterLink to="/coach" class="hover:text-blue-600">课堂教练</RouterLink>
          <RouterLink to="/take" class="hover:text-blue-600">进入测验</RouterLink>
          <RouterLink to="/print" class="hover:text-blue-600">打印讲义</RouterLink>
        </div>
      </nav>
    </header>
    <main class="w-full px-4 py-6 sm:px-6 lg:px-10">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>
