<template>
  <section class="space-y-3 rounded border border-slate-200 bg-white p-4 shadow-sm">
    <header class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-slate-800">模型追踪</h2>
      <span class="text-xs font-medium text-slate-500">{{ items.length }} 步骤</span>
    </header>
    <ul v-if="items.length" class="space-y-2">
      <li
        v-for="(item, index) in items"
        :key="index"
        class="rounded border border-slate-200 bg-slate-50 p-3 text-sm leading-5"
      >
        <div class="font-medium text-slate-800">{{ item.step }} · {{ item.provider }}</div>
        <div class="text-slate-600">
          {{ item.model }} @ {{ item.base_url }} — {{ item.latency_ms }} ms
        </div>
        <div class="text-slate-500">
          input: {{ item.input_chars }} chars · output: {{ item.output_chars }} chars
        </div>
        <div v-if="item.rag?.enabled" class="text-xs text-emerald-600">
          RAG 后端：{{ (item.rag.backend as string) || "未设置" }}
        </div>
        <div v-if="item.fallback" class="text-xs font-semibold text-amber-600">已触发降级</div>
      </li>
    </ul>
    <p v-else class="text-sm text-slate-500">执行预习流程后会显示追踪数据。</p>
  </section>
</template>

<script setup lang="ts">
import type { ModelTraceSegment } from "../types";

defineProps<{ items: ModelTraceSegment[] }>();
</script>
