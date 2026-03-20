<template>
  <section class="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
    <header class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.35em] text-slate-500">质量审计</p>
        <h2 class="text-lg font-semibold text-slate-900">评测与反思</h2>
      </div>
      <span class="rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em]" :class="verdictClass">
        {{ verdictLabel }}
      </span>
    </header>

    <p v-if="!evaluation" class="text-sm text-slate-500">当前任务还没有评测结果，生成新任务后会显示 groundedness、citation 和学习体验审计。</p>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-3">
        <article v-for="score in scoreCards" :key="score.key" class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">{{ score.label }}</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ score.value }}</p>
          <p class="text-xs text-slate-500">{{ score.hint }}</p>
        </article>
      </div>

      <div class="grid gap-3 sm:grid-cols-3">
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">硬规则分</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ ruleOverall }}</p>
          <p class="text-xs text-slate-500">由引用覆盖、测验完整度、练习支持度直接计算</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">引用覆盖</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ citationCoverage }}</p>
          <p class="text-xs text-slate-500">知识点 / 题目 / 练习是否真的带证据</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">风险闸门</p>
          <p class="mt-1 text-lg font-semibold text-slate-900">{{ gatesSummary }}</p>
          <p class="text-xs text-slate-500">用于触发补检索、重生成或多模态复核</p>
        </article>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">学习体验</p>
          <div class="mt-3 space-y-3 text-sm text-slate-700">
            <p><span class="font-semibold text-slate-900">丝滑度：</span>{{ learnerExperience.smoothness || "暂无" }}</p>
            <p><span class="font-semibold text-slate-900">认知负荷：</span>{{ learnerExperience.cognitive_load || "暂无" }}</p>
            <p><span class="font-semibold text-slate-900">个性化：</span>{{ learnerExperience.personalization || "暂无" }}</p>
          </div>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">系统反思</p>
          <div class="mt-3 flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-[0.2em]">
            <span class="rounded-full border border-slate-200 bg-white px-2 py-1 text-slate-600">
              {{ reflection?.should_regenerate ? "需要重生成" : "无需重生成" }}
            </span>
            <span class="rounded-full border border-slate-200 bg-white px-2 py-1 text-slate-600">
              {{ reflection?.should_expand_retrieval ? "建议补检索" : "检索足够" }}
            </span>
            <span class="rounded-full border border-slate-200 bg-white px-2 py-1 text-slate-600">
              {{ reflection?.should_add_multimodal_review ? "建议多模态复核" : "无需多模态复核" }}
            </span>
          </div>
          <ul class="mt-3 space-y-2 text-sm text-slate-700">
            <li v-for="item in reflectionList" :key="item" class="rounded-2xl border border-white/80 bg-white/80 px-3 py-2">
              {{ item }}
            </li>
            <li v-if="!reflectionList.length" class="text-slate-400">暂无反思建议。</li>
          </ul>
        </article>
      </div>

      <div class="grid gap-4 lg:grid-cols-3">
        <article class="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
          <p class="text-[11px] uppercase tracking-[0.25em] text-emerald-700">优势</p>
          <ul class="mt-3 space-y-2 text-sm text-emerald-900">
            <li v-for="item in evaluation.strengths || []" :key="item">{{ item }}</li>
            <li v-if="!(evaluation.strengths || []).length" class="text-emerald-700/70">暂无。</li>
          </ul>
        </article>
        <article class="rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
          <p class="text-[11px] uppercase tracking-[0.25em] text-amber-700">风险</p>
          <ul class="mt-3 space-y-2 text-sm text-amber-900">
            <li v-for="item in evaluation.risks || []" :key="item">{{ item }}</li>
            <li v-if="!(evaluation.risks || []).length" class="text-amber-700/70">暂无。</li>
          </ul>
        </article>
        <article class="rounded-2xl border border-rose-100 bg-rose-50/70 p-4">
          <p class="text-[11px] uppercase tracking-[0.25em] text-rose-700">缺失证据</p>
          <ul class="mt-3 space-y-2 text-sm text-rose-900">
            <li v-for="item in evaluation.missing_evidence || []" :key="item">{{ item }}</li>
            <li v-if="!(evaluation.missing_evidence || []).length" class="text-rose-700/70">暂无。</li>
          </ul>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { QualityEvaluation, ReflectionInsights } from "../types";

const props = defineProps<{
  evaluation?: QualityEvaluation | null;
  reflection?: ReflectionInsights | null;
}>();

const learnerExperience = computed(() => props.evaluation?.learner_experience ?? {});
const reflection = computed(() => props.reflection ?? null);

const scoreCards = computed(() => [
  {
    key: "overall",
    label: "综合",
    value: props.evaluation?.scores?.overall ?? 0,
    hint: "总评"
  },
  {
    key: "groundedness",
    label: "Groundedness",
    value: props.evaluation?.scores?.groundedness ?? 0,
    hint: "内容是否真正立足资料"
  },
  {
    key: "learner_fit",
    label: "Learner Fit",
    value: props.evaluation?.scores?.learner_fit ?? 0,
    hint: "是否适合继续学下去"
  },
]);

const verdictLabel = computed(() => {
  const value = String(props.evaluation?.verdict || "").toLowerCase();
  if (value === "pass") return "通过";
  if (value === "review") return "复核";
  if (value === "block") return "拦截";
  return "未知";
});

const verdictClass = computed(() => {
  const value = String(props.evaluation?.verdict || "").toLowerCase();
  if (value === "pass") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (value === "review") return "border-amber-200 bg-amber-50 text-amber-700";
  if (value === "block") return "border-rose-200 bg-rose-50 text-rose-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
});

const ruleOverall = computed(() => props.evaluation?.rule_metrics?.scorecard?.overall ?? 0);

const citationCoverage = computed(() => {
  const ratios = props.evaluation?.rule_metrics?.ratios ?? {};
  const knowledge = Number(ratios.knowledge_ref_ratio ?? 0);
  const quiz = Number(ratios.quiz_ref_ratio ?? 0);
  const practice = Number(ratios.practice_citation_ratio ?? 0);
  return Math.round((knowledge + quiz + practice) / 3);
});

const gatesSummary = computed(() => {
  const gates = props.evaluation?.rule_metrics?.gates ?? {};
  const active = Object.entries(gates)
    .filter(([, enabled]) => Boolean(enabled))
    .map(([key]) => key);
  return active.length ? `${active.length} 个告警` : "全部通过";
});

const reflectionList = computed(() => {
  const items = [...(reflection.value?.diagnosis ?? []), ...(reflection.value?.next_actions ?? [])];
  return items.slice(0, 6);
});
</script>
