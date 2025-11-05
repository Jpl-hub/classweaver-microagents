<template>
  <div class="min-h-screen bg-slate-50">
    <header class="bg-white shadow">
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <RouterLink to="/" class="text-lg font-semibold text-slate-900">ClassWeaver</RouterLink>
        <div class="flex items-center gap-4 text-sm text-slate-600">
          <RouterLink to="/" class="hover:text-blue-600">工作台</RouterLink>
          <RouterLink to="/take" class="hover:text-blue-600">开始测验</RouterLink>
          <RouterLink to="/print" class="hover:text-blue-600">打印资料</RouterLink>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-6xl px-6 py-10">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>
