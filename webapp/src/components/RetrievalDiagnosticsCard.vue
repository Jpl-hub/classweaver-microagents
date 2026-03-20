<template>
  <section class="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
    <header class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.35em] text-slate-500">检索分析</p>
        <h2 class="text-lg font-semibold text-slate-900">RAG 诊断</h2>
      </div>
      <span class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700">
        {{ diagnostics?.backend || "No RAG" }}
      </span>
    </header>

    <p v-if="!diagnostics?.enabled" class="text-sm text-slate-500">当前任务未启用知识库检索，提交带知识库的任务后会显示诊断信息。</p>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-2">
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">最终命中</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ diagnostics.final_hits ?? 0 }}</p>
          <p class="text-xs text-slate-500">最终保留片段数</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">语料规模</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ diagnostics.total_entries ?? 0 }}</p>
          <p class="text-xs text-slate-500">当前知识库切片数</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">候选池</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ diagnostics.search_k ?? 0 }}</p>
          <p class="text-xs text-slate-500">进入融合/重排的候选量</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">查询长度</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ diagnostics.query_length ?? 0 }}</p>
          <p class="text-xs text-slate-500">本次查询字符数</p>
        </article>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4 space-y-3">
        <div class="flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-[0.2em]">
          <span class="rounded-full border px-2 py-1" :class="diagnostics.hybrid_enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'">
            {{ diagnostics.hybrid_enabled ? "Hybrid On" : "Hybrid Off" }}
          </span>
          <span class="rounded-full border px-2 py-1" :class="diagnostics.rerank_enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'">
            {{ diagnostics.rerank_enabled ? "Rerank On" : "Rerank Off" }}
          </span>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Dense 向量召回</span>
            <span>{{ diagnostics.vector_hits ?? 0 }}</span>
          </div>
          <div class="h-2 rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-sky-500" :style="{ width: `${ratio(diagnostics.vector_hits ?? 0)}%` }" />
          </div>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Lexical 召回</span>
            <span>{{ diagnostics.lexical_hits ?? 0 }}</span>
          </div>
          <div class="h-2 rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-amber-500" :style="{ width: `${ratio(diagnostics.lexical_hits ?? 0)}%` }" />
          </div>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>最终保留</span>
            <span>{{ diagnostics.final_hits ?? 0 }}</span>
          </div>
          <div class="h-2 rounded-full bg-slate-200">
            <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${ratio(diagnostics.final_hits ?? 0)}%` }" />
          </div>
        </div>
      </div>

      <div v-if="diagnostics.source_counts" class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">融合来源</p>
        <div class="mt-2 flex items-center gap-4 text-sm text-slate-700">
          <span>vector {{ diagnostics.source_counts.vector ?? 0 }}</span>
          <span>lexical {{ diagnostics.source_counts.lexical ?? 0 }}</span>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RetrievalDiagnostics } from "../types";

const props = defineProps<{ diagnostics?: RetrievalDiagnostics | null }>();

const maxHits = computed(() =>
  Math.max(1, props.diagnostics?.vector_hits ?? 0, props.diagnostics?.lexical_hits ?? 0, props.diagnostics?.final_hits ?? 0),
);

function ratio(value: number) {
  return Math.min(100, Math.round((value / maxHits.value) * 100));
}
</script>
