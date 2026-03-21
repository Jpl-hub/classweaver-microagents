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

      <div class="grid gap-3 sm:grid-cols-4">
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">知识点证据</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ evidenceCoverage.knowledge }}</p>
          <p class="text-xs text-slate-500">带引用知识点 / 总知识点</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">题目证据</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ evidenceCoverage.quiz }}</p>
          <p class="text-xs text-slate-500">带引用题目 / 总题目</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">练习证据</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ evidenceCoverage.practice }}</p>
          <p class="text-xs text-slate-500">带 citation 练习 / 总练习</p>
        </article>
        <article class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">检索填充</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ evidenceCoverage.retrieval }}</p>
          <p class="text-xs text-slate-500">最终命中 / search_k</p>
        </article>
      </div>

      <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">可信结论</p>
        <ul class="mt-3 space-y-2 text-sm text-slate-700">
          <li v-for="item in trustNarrative" :key="item" class="rounded-2xl border border-white/80 bg-white/80 px-3 py-2">
            {{ item }}
          </li>
        </ul>
      </article>

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

      <article v-if="reviewSummary?.executed_rounds" class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">Review Cycle</p>
            <h3 class="text-base font-semibold text-slate-900">反思驱动修正</h3>
          </div>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600">
            {{ reviewSummary.executed_rounds }} 轮
          </span>
        </div>
        <div class="mt-3 grid gap-3 sm:grid-cols-3">
          <article class="rounded-2xl border border-white/80 bg-white/80 p-3">
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400">初始分数</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ reviewSummary.initial_overall_score ?? 0 }}</p>
          </article>
          <article class="rounded-2xl border border-white/80 bg-white/80 p-3">
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400">最终分数</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ reviewSummary.final_overall_score ?? 0 }}</p>
          </article>
          <article class="rounded-2xl border border-white/80 bg-white/80 p-3">
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400">多模态复核</p>
            <p class="mt-1 text-sm font-semibold text-slate-900">{{ reviewSummary.pending_multimodal_review ? "待接入" : "当前未触发" }}</p>
          </article>
        </div>
        <div class="mt-3 grid gap-3 sm:grid-cols-2">
          <article class="rounded-2xl border border-white/80 bg-white/80 p-3">
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400">采纳轮次</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ acceptedReviewCount }}</p>
            <p class="text-xs text-slate-500">真正进入最终结果的 review 修正</p>
          </article>
          <article class="rounded-2xl border border-white/80 bg-white/80 p-3">
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400">拒绝轮次</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ rejectedReviewCount }}</p>
            <p class="text-xs text-slate-500">被策略拒绝的负增益或低收益重跑</p>
          </article>
        </div>
        <ul class="mt-3 space-y-2 text-sm text-slate-700">
          <li v-for="cycle in reviewSummary.cycles || []" :key="cycle.round" class="rounded-2xl border border-white/80 bg-white/80 px-3 py-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-semibold text-slate-900">第 {{ cycle.round }} 轮：{{ strategyLabel(cycle.strategy) }}</span>
              <span
                class="rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.2em]"
                :class="cycle.accepted ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
              >
                {{ cycle.accepted ? "已采纳" : "已拒绝" }}
              </span>
            </div>
            <div class="mt-1">
              top_k {{ cycle.top_k }}，分数 {{ cycle.initial_overall_score ?? 0 }} -> {{ cycle.revised_overall_score ?? 0 }}
            </div>
            <span v-if="typeof cycle.score_delta === 'number'">（{{ cycle.score_delta >= 0 ? "+" : "" }}{{ cycle.score_delta }}）</span>
            <div v-if="cycle.query_text" class="mt-1 text-xs text-slate-500">
              query: {{ cycle.query_text }}
            </div>
            <div v-if="cycle.query_rewrite?.rationale" class="mt-1 text-xs text-slate-500">
              rewrite: {{ cycle.query_rewrite.rationale }}
            </div>
            <div v-if="cycle.decision_reason" class="mt-1 text-xs text-slate-500">
              决策原因：{{ cycle.decision_reason }}
            </div>
          </li>
        </ul>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { QualityEvaluation, ReflectionInsights, ReviewSummary } from "../types";

const props = defineProps<{
  evaluation?: QualityEvaluation | null;
  reflection?: ReflectionInsights | null;
  reviewSummary?: ReviewSummary | null;
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
const llmOverall = computed(() => props.evaluation?.scores?.overall ?? 0);

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

const reviewSummary = computed(() => props.reviewSummary ?? null);
const acceptedReviewCount = computed(() => (reviewSummary.value?.cycles ?? []).filter((cycle) => cycle.accepted).length);
const rejectedReviewCount = computed(() => (reviewSummary.value?.cycles ?? []).filter((cycle) => cycle.accepted === false).length);

const evidenceCoverage = computed(() => {
  const counts = props.evaluation?.rule_metrics?.counts ?? {};
  const retrieval = props.evaluation?.rule_metrics?.retrieval ?? {};
  return {
    knowledge: `${counts.knowledge_points_with_refs ?? 0}/${counts.knowledge_points ?? 0}`,
    quiz: `${counts.quiz_items_with_refs ?? 0}/${counts.quiz_items ?? 0}`,
    practice: `${counts.practice_items_with_citations ?? 0}/${counts.practice_items ?? 0}`,
    retrieval: `${retrieval.final_hits ?? 0}/${retrieval.search_k ?? 0}`,
  };
});

const trustNarrative = computed(() => {
  const items: string[] = [];
  const gates = props.evaluation?.rule_metrics?.gates ?? {};
  const overallGap = llmOverall.value - ruleOverall.value;

  if (Math.abs(overallGap) >= 15) {
    items.push(`LLM 总评分与硬规则分相差 ${Math.abs(overallGap)}，这次结果需要优先看证据覆盖而不是只看总分。`);
  } else {
    items.push(`LLM 总评分与硬规则分差值 ${Math.abs(overallGap)}，当前主观判断与证据审计没有明显背离。`);
  }
  if (gates.needs_more_references) {
    items.push("当前知识点或题目引用覆盖不足，结论还不够稳。");
  } else {
    items.push("知识点和题目引用覆盖基本过线，核心内容具备可追溯证据。");
  }
  if (gates.needs_more_retrieval) {
    items.push("检索候选填充偏低，后续更值得先做补检索而不是盲目重写答案。");
  }
  if (gates.needs_more_practice) {
    items.push("练习支持还不够，学习体验风险主要在承接和巩固，而不是知识点本身。");
  }
  if (acceptedReviewCount.value > 0 || rejectedReviewCount.value > 0) {
    items.push(`当前 review 共采纳 ${acceptedReviewCount.value} 轮，拒绝 ${rejectedReviewCount.value} 轮，说明系统已经开始过滤低收益修正。`);
  }
  return items;
});

function strategyLabel(value?: string) {
  if (value === "tutor_only") return "定向补练习";
  if (value === "full_pipeline") return "全链路复核";
  return value || "复核";
}
</script>
