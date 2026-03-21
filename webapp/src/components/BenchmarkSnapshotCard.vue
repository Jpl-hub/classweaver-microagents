<template>
  <article class="glass-panel space-y-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.4em] text-slate-500">实验基线</p>
        <h2 class="text-xl font-semibold text-slate-900">最近评测结论</h2>
        <p class="text-sm text-slate-500">把当前任务放回最近一组 review 实验里看，确认反思策略是否真的带来增益。</p>
      </div>
      <router-link class="btn-secondary text-xs" :to="{ name: 'benchmarks' }">进入实验分析</router-link>
    </header>

    <p v-if="loading" class="text-sm text-slate-500">正在读取 benchmark 报告...</p>
    <p v-else-if="error" class="text-sm text-rose-600">{{ error }}</p>
    <p v-else-if="!snapshot" class="text-sm text-slate-500">当前还没有可用的 review 对比报告，先跑 `evaluate_review_cycles` 再回来查看。</p>

    <template v-else>
      <div class="grid gap-3 sm:grid-cols-3">
        <article
          v-for="card in cards"
          :key="card.label"
          class="rounded-2xl border border-slate-100 bg-slate-50 p-3"
        >
          <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">{{ card.label }}</p>
          <p class="mt-1 text-2xl font-semibold text-slate-900">{{ card.value }}</p>
          <p class="text-xs text-slate-500">{{ card.hint }}</p>
        </article>
      </div>

      <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
        <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">实验摘要</p>
        <ul class="mt-3 space-y-2 text-sm text-slate-700">
          <li v-for="item in insights" :key="item">{{ item }}</li>
        </ul>
      </div>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { compareBenchmarkReports, listBenchmarkReports } from "../services/api";
import type { BenchmarkReportCompareResponse, BenchmarkReportSummary } from "../types";

const props = defineProps<{
  currentOverall?: number | null;
  currentVerdict?: string | null;
  currentPrimaryIssue?: string | null;
  currentRecommendedStrategy?: string | null;
}>();

const loading = ref(false);
const error = ref("");
const snapshot = ref<BenchmarkReportCompareResponse | null>(null);
const candidateSummary = ref<Record<string, unknown> | null>(null);

const cards = computed(() => {
  const metrics = snapshot.value?.diff?.metrics ?? {};
  const currentOverall = typeof props.currentOverall === "number" ? props.currentOverall : null;
  return [
    {
      label: "final overall",
      value: formatNumber(metrics.avg_final_overall?.candidate),
      hint: "review on 实验均值",
    },
    {
      label: "score delta",
      value: signedNumber(metrics.avg_score_delta?.candidate),
      hint: "review 平均增益",
    },
    {
      label: "current task",
      value: currentOverall === null ? "-" : formatNumber(currentOverall),
      hint: props.currentVerdict ? `当前判定 ${props.currentVerdict}` : "当前任务总分",
    },
  ];
});

const insights = computed(() => {
  const metrics = snapshot.value?.diff?.metrics ?? {};
  const result: string[] = [];
  const overallDelta = numericDelta(metrics.avg_final_overall?.delta);
  const scoreDelta = numericValue(metrics.avg_score_delta?.candidate);
  const acceptRate = numericValue(metrics.review_accept_rate?.candidate);
  const triggerRate = numericValue(metrics.review_trigger_rate?.candidate);
  const currentOverall = typeof props.currentOverall === "number" ? props.currentOverall : null;
  const candidateOverall = numericValue(metrics.avg_final_overall?.candidate);

  if (triggerRate > 0) {
    result.push(`最新 review 实验已经真正执行反思，触发率 ${percent(triggerRate)}。`);
  }
  if (overallDelta > 0) {
    result.push(`开启 review 后最终平均分提升 ${overallDelta.toFixed(2)}。`);
  } else if (overallDelta === 0 && scoreDelta > 0) {
    result.push(`开启 review 后最终平均分守住基线，同时保留了 +${scoreDelta.toFixed(2)} 的平均修正增益。`);
  } else if (overallDelta < 0) {
    result.push(`开启 review 后最终平均分下降 ${Math.abs(overallDelta).toFixed(2)}，当前策略还要继续压缩误触发。`);
  }
  if (acceptRate > 0) {
    result.push(`当前有 ${percent(acceptRate)} 的 review 候选被采纳，说明系统已经在筛掉负增益重跑。`);
  }
  if (currentOverall !== null && Number.isFinite(candidateOverall)) {
    const delta = currentOverall - candidateOverall;
    if (delta >= 0) {
      result.push(`这次任务的总分比最近 review 实验均值高 ${delta.toFixed(2)}。`);
    } else {
      result.push(`这次任务的总分比最近 review 实验均值低 ${Math.abs(delta).toFixed(2)}，适合回看 trace 和证据覆盖。`);
    }
  }
  const primaryIssue = String(props.currentPrimaryIssue || "").trim();
  const issueRates = (candidateSummary.value?.primary_issue_rates as Record<string, unknown> | undefined) ?? {};
  const strategyRates = (candidateSummary.value?.recommended_strategy_rates as Record<string, unknown> | undefined) ?? {};
  if (primaryIssue) {
    const rate = typeof issueRates[primaryIssue] === "number" ? Number(issueRates[primaryIssue]) : null;
    if (rate !== null) {
      result.push(`当前主问题是“${issueLabel(primaryIssue)}”，在最近 review 实验里占比 ${percent(rate)}。`);
    } else {
      result.push(`当前主问题是“${issueLabel(primaryIssue)}”，但最近 benchmark 里还没有足够样本。`);
    }
  }
  const recommendedStrategy = String(props.currentRecommendedStrategy || "").trim();
  if (recommendedStrategy) {
    const rate = typeof strategyRates[recommendedStrategy] === "number" ? Number(strategyRates[recommendedStrategy]) : null;
    if (rate !== null) {
      result.push(`系统建议走“${strategyLabel(recommendedStrategy)}”，这条路径在最近 review 实验里占比 ${percent(rate)}。`);
    }
  }
  return result;
});

onMounted(loadSnapshot);

async function loadSnapshot() {
  loading.value = true;
  error.value = "";
  try {
    const reportList = await listBenchmarkReports();
    const pair = pickSuggestedReviewPair(reportList.reports ?? []);
    if (!pair) {
      snapshot.value = null;
      candidateSummary.value = null;
      return;
    }
    candidateSummary.value = (pair.candidate.summary as Record<string, unknown> | undefined) ?? null;
    snapshot.value = await compareBenchmarkReports(pair.baseline.name, pair.candidate.name);
  } catch (err) {
    error.value = (err as Error).message;
  } finally {
    loading.value = false;
  }
}

function pickSuggestedReviewPair(reports: BenchmarkReportSummary[]) {
  const reviewReports = reports.filter((report) => report.meta?.report_type === "review_cycles");
  const baseline = reviewReports.find((report) => report.config?.review_enabled === false);
  const candidate = reviewReports.find((report) => report.config?.review_enabled === true);
  if (!baseline || !candidate) return null;
  return { baseline, candidate };
}

function formatNumber(value: unknown) {
  if (typeof value === "number") return value.toFixed(Number.isInteger(value) ? 0 : 2);
  return String(value ?? "-");
}

function signedNumber(value: unknown) {
  if (typeof value === "number") return `${value > 0 ? "+" : ""}${value.toFixed(Number.isInteger(value) ? 0 : 2)}`;
  return String(value ?? "-");
}

function numericValue(value: unknown) {
  return typeof value === "number" ? value : Number.NaN;
}

function numericDelta(value: unknown) {
  return typeof value === "number" ? value : 0;
}

function percent(value: number) {
  return `${(value * 100).toFixed(0)}%`;
}

function issueLabel(value: string) {
  const labels: Record<string, string> = {
    retrieval_gap: "检索不足",
    evidence_gap: "证据不足",
    tutoring_gap: "练习承接不足",
    quiz_gap: "测验不足",
    learner_fit_gap: "体验不足",
    multimodal_gap: "多模态复核",
    none: "无明显短板",
  };
  return labels[value] ?? value;
}

function strategyLabel(value: string) {
  const labels: Record<string, string> = {
    full_pipeline: "全链路复核",
    tutor_only: "定向补练习",
    multimodal_review: "多模态复核",
    keep: "保持当前版本",
  };
  return labels[value] ?? value;
}
</script>
