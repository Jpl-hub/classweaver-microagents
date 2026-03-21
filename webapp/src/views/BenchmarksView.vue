<template>
  <section class="space-y-6">
    <header class="glass-panel flex flex-wrap items-center justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.4em] text-slate-500">实验分析</p>
        <h1 class="text-2xl font-semibold text-slate-900">Benchmark Reports</h1>
        <p class="text-sm text-slate-500">直接查看本地 benchmark 报告，对比 review on/off、检索策略和评测差异。</p>
      </div>
      <button class="btn-secondary text-xs" type="button" :disabled="loading" @click="loadReports">
        {{ loading ? "刷新中..." : "刷新报告" }}
      </button>
    </header>

    <article v-if="suggestedPair" class="glass-panel space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.4em] text-slate-500">推荐对比</p>
          <h2 class="text-lg font-semibold text-slate-900">{{ suggestedPair.baseline.name }} vs {{ suggestedPair.candidate.name }}</h2>
          <p class="text-sm text-slate-500">自动识别到一组最适合展示“反思是否有效”的 review 对比报告。</p>
        </div>
        <button class="btn-primary text-xs" type="button" :disabled="compareLoading" @click="applySuggestedPair">
          使用这组对比
        </button>
      </div>
    </article>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <article class="glass-panel space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">报告列表</h2>
          <span class="text-xs text-slate-500">{{ reports.length }} 份</span>
        </div>
        <p v-if="error" class="text-sm text-rose-600">{{ error }}</p>
        <ul v-if="reports.length" class="space-y-3">
          <li
            v-for="report in reports"
            :key="report.name"
            class="rounded-2xl border border-slate-200 bg-white/80 p-4 transition"
            :class="selectedName === report.name ? 'border-slate-900 shadow-sm' : 'hover:border-slate-300'"
          >
            <button class="w-full text-left" type="button" @click="selectReport(report.name)">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ report.name }}</p>
                  <p class="text-xs text-slate-500">{{ report.meta?.report_type || "unknown" }} · {{ report.config?.base_name || "未标注知识库" }}</p>
                </div>
                <span class="text-xs text-slate-400">{{ formatNumber(report.summary?.cases) }} cases</span>
              </div>
              <div class="mt-2 grid gap-2 sm:grid-cols-2">
                <div class="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  overall: {{ formatNumber(report.summary?.avg_final_overall) }}
                </div>
                <div class="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  delta: {{ signedNumber(report.summary?.avg_score_delta) }}
                </div>
              </div>
            </button>
          </li>
        </ul>
        <p v-else class="text-sm text-slate-500">当前还没有 benchmark 报告。先在后端跑一份 `evaluate_*` 命令。</p>
      </article>

      <div class="space-y-6">
        <article class="glass-panel space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.4em] text-slate-500">报告详情</p>
              <h2 class="text-lg font-semibold text-slate-900">{{ selectedName || "未选择报告" }}</h2>
            </div>
            <div class="flex gap-2">
              <select v-model="baselineName" class="rounded-2xl border border-slate-200 px-3 py-2 text-xs text-slate-800">
                <option value="">选择 baseline</option>
                <option v-for="report in reports" :key="`base-${report.name}`" :value="report.name">{{ report.name }}</option>
              </select>
              <select v-model="candidateName" class="rounded-2xl border border-slate-200 px-3 py-2 text-xs text-slate-800">
                <option value="">选择 candidate</option>
                <option v-for="report in reports" :key="`cand-${report.name}`" :value="report.name">{{ report.name }}</option>
              </select>
              <button class="btn-primary text-xs" type="button" :disabled="compareLoading || !baselineName || !candidateName" @click="runCompare">
                {{ compareLoading ? "对比中..." : "对比报告" }}
              </button>
            </div>
          </div>

          <div v-if="selectedReport" class="grid gap-3 sm:grid-cols-3">
            <article v-for="card in summaryCards" :key="card.label" class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
              <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">{{ card.label }}</p>
              <p class="mt-1 text-2xl font-semibold text-slate-900">{{ card.value }}</p>
              <p class="text-xs text-slate-500">{{ card.hint }}</p>
            </article>
          </div>
          <p v-else class="text-sm text-slate-500">选择左侧报告后，这里会展示 summary 和 config。</p>

          <div v-if="selectedReport" class="grid gap-4 lg:grid-cols-2">
            <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">配置</p>
              <ul class="mt-3 space-y-2 text-sm text-slate-700">
                <li v-for="[key, value] in configEntries" :key="key">{{ key }}: {{ formatValue(value) }}</li>
              </ul>
            </article>
            <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">摘要指标</p>
              <ul class="mt-3 space-y-2 text-sm text-slate-700">
                <li v-for="[key, value] in summaryEntries" :key="key">{{ key }}: {{ formatValue(value) }}</li>
              </ul>
            </article>
          </div>

          <div v-if="issueRateGroups.length" class="grid gap-4 lg:grid-cols-3">
            <article
              v-for="group in issueRateGroups"
              :key="group.label"
              class="rounded-2xl border border-slate-100 bg-slate-50 p-4"
            >
              <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">{{ group.label }}</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in group.items"
                  :key="item.key"
                  class="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600"
                >
                  {{ issueLabel(item.key) }} {{ formatRate(item.value) }}
                </span>
              </div>
            </article>
          </div>
        </article>

        <article v-if="compareResult" class="glass-panel space-y-4">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">对比结果</p>
            <h2 class="text-lg font-semibold text-slate-900">{{ compareResult.baseline }} vs {{ compareResult.candidate }}</h2>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <article
              v-for="metric in compareMetrics"
              :key="metric.name"
              class="rounded-2xl border p-3"
              :class="metric.delta > 0 ? 'border-emerald-200 bg-emerald-50/70' : metric.delta < 0 ? 'border-rose-200 bg-rose-50/70' : 'border-slate-200 bg-slate-50'"
            >
              <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">{{ metric.name }}</p>
              <p class="mt-1 text-sm font-semibold text-slate-900">{{ metric.baseline }} -> {{ metric.candidate }}</p>
              <p class="text-xs" :class="metric.delta > 0 ? 'text-emerald-700' : metric.delta < 0 ? 'text-rose-700' : 'text-slate-500'">
                delta {{ signedNumber(metric.delta) }}
              </p>
            </article>
          </div>
          <div v-if="compareInsights.length" class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-[11px] uppercase tracking-[0.25em] text-slate-400">结论摘要</p>
            <ul class="mt-3 space-y-2 text-sm text-slate-700">
              <li v-for="item in compareInsights" :key="item">{{ item }}</li>
            </ul>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { compareBenchmarkReports, getBenchmarkReport, listBenchmarkReports } from "../services/api";
import type { BenchmarkReportCompareResponse, BenchmarkReportSummary } from "../types";

const reports = ref<BenchmarkReportSummary[]>([]);
const selectedName = ref("");
const selectedReport = ref<Record<string, unknown> | null>(null);
const baselineName = ref("");
const candidateName = ref("");
const compareResult = ref<BenchmarkReportCompareResponse | null>(null);
const loading = ref(false);
const compareLoading = ref(false);
const error = ref("");

const summaryCards = computed(() => {
  const summary = (selectedReport.value?.summary as Record<string, unknown> | undefined) ?? {};
  return [
    { label: "cases", value: formatNumber(summary.cases), hint: "样本数" },
    { label: "final overall", value: formatNumber(summary.avg_final_overall), hint: "最终平均分" },
    { label: "score delta", value: signedNumber(summary.avg_score_delta), hint: "review 平均增益" },
  ];
});

const configEntries = computed(() => Object.entries((selectedReport.value?.config as Record<string, unknown> | undefined) ?? {}));
const summaryEntries = computed(() => Object.entries((selectedReport.value?.summary as Record<string, unknown> | undefined) ?? {}));
const issueRateGroups = computed(() => {
  const summary = (selectedReport.value?.summary as Record<string, unknown> | undefined) ?? {};
  const groups = [
    { label: "问题标签分布", value: summary.issue_tag_rates },
    { label: "主问题分布", value: summary.primary_issue_rates },
    { label: "建议策略分布", value: summary.recommended_strategy_rates },
    { label: "已解决问题", value: summary.resolved_issue_tag_rates },
    { label: "新引入问题", value: summary.introduced_issue_tag_rates },
  ];
  return groups
    .map((group) => ({
      label: group.label,
      items: Object.entries((group.value as Record<string, unknown> | undefined) ?? {})
        .filter(([, value]) => typeof value === "number")
        .map(([key, value]) => ({ key, value: Number(value) })),
    }))
    .filter((group) => group.items.length);
});
const compareMetrics = computed(() =>
  Object.entries(compareResult.value?.diff?.metrics ?? {}).map(([name, metric]) => ({
    name,
    baseline: formatNumber(metric.baseline),
    candidate: formatNumber(metric.candidate),
    delta: Number(metric.delta ?? 0),
  })),
);
const suggestedPair = computed(() => {
  const reviewReports = reports.value.filter((report) => report.meta?.report_type === "review_cycles");
  const baseline = reviewReports.find((report) => report.config?.review_enabled === false);
  const candidate = reviewReports.find((report) => report.config?.review_enabled === true);
  if (!baseline || !candidate) return null;
  return { baseline, candidate };
});
const compareInsights = computed(() => {
  const metrics = compareResult.value?.diff?.metrics ?? {};
  const insights: string[] = [];
  const overallDelta = Number(metrics.avg_final_overall?.delta ?? 0);
  const scoreDelta = Number(metrics.avg_score_delta?.candidate ?? 0);
  const acceptRate = Number(metrics.review_accept_rate?.candidate ?? 0);
  const triggerRate = Number(metrics.review_trigger_rate?.candidate ?? 0);
  const shiftRate = Number(metrics.primary_issue_shift_rate?.candidate ?? 0);

  if (triggerRate > 0) {
    insights.push(`review 已经真正参与执行，触发率 ${triggerRate.toFixed(2)}。`);
  }
  if (overallDelta > 0) {
    insights.push(`开启 review 后最终平均分提升 ${overallDelta.toFixed(2)}。`);
  } else if (overallDelta === 0 && scoreDelta > 0) {
    insights.push(`开启 review 后最终平均分至少守住基线，同时 review 平均增益为 +${scoreDelta.toFixed(2)}。`);
  } else if (overallDelta < 0) {
    insights.push(`开启 review 后最终平均分下降 ${Math.abs(overallDelta).toFixed(2)}，策略仍需继续优化。`);
  }
  if (acceptRate > 0) {
    insights.push(`当前有 ${(acceptRate * 100).toFixed(0)}% 的 review 候选被采纳，说明采纳策略已经开始过滤负增益结果。`);
  }
  if (shiftRate > 0) {
    insights.push(`有 ${(shiftRate * 100).toFixed(0)}% 的样本在 review 后主问题发生了变化，说明系统不只是重写答案，而是真的在推动问题类型迁移。`);
  }
  return insights;
});

async function loadReports() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await listBenchmarkReports();
    reports.value = payload.reports ?? [];
    if (!selectedName.value && reports.value.length) {
      await selectReport(reports.value[0].name);
    }
    if (suggestedPair.value && !compareResult.value) {
      baselineName.value = suggestedPair.value.baseline.name;
      candidateName.value = suggestedPair.value.candidate.name;
      await runCompare();
    }
  } catch (err) {
    error.value = (err as Error).message;
  } finally {
    loading.value = false;
  }
}

async function selectReport(name: string) {
  selectedName.value = name;
  const payload = await getBenchmarkReport(name);
  selectedReport.value = payload.report ?? null;
}

async function runCompare() {
  if (!baselineName.value || !candidateName.value) return;
  compareLoading.value = true;
  try {
    compareResult.value = await compareBenchmarkReports(baselineName.value, candidateName.value);
  } finally {
    compareLoading.value = false;
  }
}

async function applySuggestedPair() {
  if (!suggestedPair.value) return;
  baselineName.value = suggestedPair.value.baseline.name;
  candidateName.value = suggestedPair.value.candidate.name;
  await runCompare();
}

function formatNumber(value: unknown) {
  if (typeof value === "number") return value.toFixed(Number.isInteger(value) ? 0 : 4);
  return String(value ?? "-");
}

function signedNumber(value: unknown) {
  if (typeof value === "number") return `${value > 0 ? "+" : ""}${value.toFixed(Number.isInteger(value) ? 0 : 4)}`;
  return String(value ?? "-");
}

function formatValue(value: unknown) {
  if (typeof value === "number") return formatNumber(value);
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value ?? "-");
}

function formatRate(value: number) {
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
    full_pipeline: "全链路复核",
    tutor_only: "定向补练习",
    multimodal_review: "多模态复核",
    keep: "保持版本",
    none: "无明显短板",
  };
  return labels[value] ?? value;
}

onMounted(loadReports);
</script>
