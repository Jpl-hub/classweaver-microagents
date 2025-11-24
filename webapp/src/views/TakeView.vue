<template>
  <section class="space-y-8">
    <div v-if="!hasSession" class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-3">
      <h1 class="text-2xl font-semibold text-slate-800">尚未找到测验会话</h1>
      <p class="text-sm text-slate-600">
        请返回仪表盘，点击“启动测验”按钮创建新的测验。创建成功后会自动跳转至此页面。
      </p>
      <div class="flex flex-wrap gap-2">
        <button class="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500" @click="router.push('/')">
          返回仪表盘
        </button>
        <button
          v-if="restoreHint"
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
          @click="restoreFromStorage"
        >
          {{ restoreHint }}
        </button>
      </div>
    </div>

    <div v-else class="space-y-8">
      <header class="rounded border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 class="text-2xl font-semibold text-slate-800">测验进行中</h1>
            <p class="text-sm text-slate-500">会话 ID：{{ sessionId }}</p>
            <p v-if="jobId" class="text-sm text-slate-500">关联任务：{{ jobId }}</p>
          </div>
          <div class="text-right">
            <p class="text-4xl font-bold text-slate-800">{{ completionPercent.toFixed(0) }}%</p>
            <p class="text-xs uppercase text-slate-500">已作答</p>
            <p class="text-xs text-slate-500">{{ answeredCount }} / {{ questions.length }}</p>
          </div>
        </div>
      </header>

      <section v-if="sourceAction" class="rounded border border-dashed border-slate-200 bg-white/80 p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.3em] text-slate-500">来自行动卡</p>
        <h2 class="mt-1 text-lg font-semibold text-slate-800">{{ sourceAction.title }}</h2>
        <p class="mt-1 text-sm text-slate-600">{{ sourceAction.summary }}</p>
        <p class="mt-2 text-xs text-slate-400">已由 Tutor 指派，完成本次小测即可回到首页查看结果。</p>
      </section>

      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-800">题目列表</h2>
          <p class="text-sm text-slate-500">{{ unansweredCount }} 道题尚未作答</p>
        </div>
        <div class="space-y-4 max-h-[720px] overflow-y-auto pr-1">
          <QuizCard
            v-for="question in questions"
            :key="question.id"
            v-model="answers[question.id]"
            :question="question"
            :readonly="Boolean(result)"
          />
        </div>
      </section>

      <section class="flex flex-wrap gap-4">
        <button
          class="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
          :disabled="isSubmitting || Boolean(result)"
          @click="handleSubmit"
        >
          {{ isSubmitting ? "提交中..." : "提交答案" }}
        </button>
        <button
          class="rounded border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
          :disabled="isSubmitting"
          @click="resetSelections"
        >
          重置
        </button>
        <p v-if="submitError" class="text-sm text-red-600">{{ submitError }}</p>
      </section>

      <section v-if="result" class="space-y-4">
        <article class="rounded border border-slate-200 bg-white p-6 shadow-sm">
          <header class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 class="text-xl font-semibold text-slate-800">测验结果</h2>
              <p class="text-sm text-slate-500">得分只统计答对题目，诊断卡可用于后续复习。</p>
            </div>
            <div class="text-right">
              <p class="text-4xl font-bold text-emerald-600">{{ result.score }}%</p>
              <p class="text-xs uppercase text-slate-500">得分</p>
            </div>
          </header>
          <div class="mt-4 grid gap-4 md:grid-cols-3">
            <div class="rounded border border-slate-200 p-4 text-sm text-slate-600">
              <p class="text-xs uppercase text-slate-500">优势知识点</p>
              <ul class="mt-2 list-disc pl-4">
                <li v-for="kp in result.review_card.strengths" :key="kp">{{ kp }}</li>
                <li v-if="!result.review_card.strengths.length">暂无优势知识点。</li>
              </ul>
            </div>
            <div class="rounded border border-slate-200 p-4 text-sm text-slate-600">
              <p class="text-xs uppercase text-slate-500">重点提升</p>
              <ul class="mt-2 list-disc pl-4">
                <li v-for="kp in result.review_card.focus" :key="kp">{{ kp }}</li>
                <li v-if="!result.review_card.focus.length">暂无需要重点提升的项目。</li>
              </ul>
            </div>
            <div class="rounded border border-slate-200 p-4 text-sm text-slate-600">
              <p class="text-xs uppercase text-slate-500">总结</p>
              <p class="mt-2">{{ result.review_card.summary }}</p>
            </div>
          </div>
        </article>

        <article class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <header class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-800">题目解析</h3>
            <p class="text-xs text-slate-500">绿色为答对，红色为待加强。</p>
          </header>
          <div class="grid gap-3 md:grid-cols-2">
            <div
              v-for="detail in result.detail"
              :key="detail.id"
              class="rounded-2xl border p-4 shadow-sm"
              :class="detail.correct ? 'border-emerald-100 bg-emerald-50/70' : 'border-rose-100 bg-rose-50/70'"
            >
              <div class="flex items-center justify-between gap-2">
                <p class="text-sm font-semibold text-slate-800">{{ findQuestion(detail.id)?.question || "题目" }}</p>
                <span
                  class="rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em]"
                  :class="detail.correct ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'"
                >
                  {{ detail.correct ? "答对" : "待加强" }}
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-600">
                你的作答：<strong>{{ detail.user_answer || "未作答" }}</strong> · 标准答案：<strong>{{ detail.answer || "无" }}</strong>
              </p>
              <p v-if="detail.explain" class="mt-2 text-sm text-slate-700">{{ detail.explain }}</p>
              <p v-else class="mt-2 text-xs text-slate-500">暂无解析，回顾课堂内容再试一次。</p>
            </div>
          </div>
        </article>

        <section v-if="result.diagnostics" class="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-lg font-semibold text-slate-800">AI 诊断</h3>
          <p class="mt-1 text-sm text-slate-700 leading-relaxed">{{ formatDiagnostics(result.diagnostics) }}</p>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import QuizCard from "../components/QuizCard.vue";
import { submitQuiz } from "../services/api";
import type { QuizQuestion, QuizSubmitResponse } from "../types";

const SESSION_STORAGE_KEY = "classweaver:last-quiz-session";

interface StoredQuizSession {
  jobId?: string;
  sessionId: string;
  questions: QuizQuestion[];
  savedAt?: number;
}

const router = useRouter();
const route = useRoute();

const sessionId = ref<string>("");
const jobId = ref<string | undefined>(undefined);
const questions = ref<QuizQuestion[]>([]);
const answers = reactive<Record<string, string>>({});
const sourceAction = ref<{ id?: string; title?: string; summary?: string } | null>(null);

const isSubmitting = ref(false);
const submitError = ref("");
const result = ref<QuizSubmitResponse | null>(null);
const restoreHint = ref<string | null>(null);

const hasSession = computed(() => Boolean(sessionId.value && questions.value.length));
const answeredCount = computed(() => Object.values(answers).filter((value) => value).length);
const unansweredCount = computed(() => Math.max(questions.value.length - answeredCount.value, 0));
const completionPercent = computed(() =>
  questions.value.length ? (answeredCount.value / questions.value.length) * 100 : 0,
);

function setQuestions(list: QuizQuestion[]) {
  questions.value = list;
  Object.keys(answers).forEach((key) => {
    delete answers[key];
  });
  list.forEach((question) => {
    answers[question.id] = answers[question.id] ?? "";
  });
}

function hydrateFrom(payload: Partial<StoredQuizSession> | null | undefined): boolean {
  if (!payload || !payload.sessionId) {
    return false;
  }
  sessionId.value = payload.sessionId;
  jobId.value = payload.jobId;
  if (Array.isArray(payload.questions) && payload.questions.length) {
    setQuestions(payload.questions);
  }
  persistSession();
  return true;
}

function loadStoredSession(): StoredQuizSession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StoredQuizSession;
  } catch {
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

function persistSession() {
  if (typeof window === "undefined" || !sessionId.value) {
    return;
  }
  const data: StoredQuizSession = {
    sessionId: sessionId.value,
    jobId: jobId.value,
    questions: questions.value,
    savedAt: Date.now(),
  };
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(data));
}

function restoreFromStorage() {
  hydrateFrom(loadStoredSession());
  restoreHint.value = null;
}

function formatDiagnostics(value?: Record<string, unknown>): string {
  if (!value || Object.keys(value).length === 0) {
    return "暂无额外建议，继续保持。";
  }
  const summary = typeof value.summary === "string" ? value.summary : null;
  if (summary) {
    return summary;
  }
  try {
    const total = (value.raw as Record<string, unknown>)?.total ?? "";
    const correct = (value.raw as Record<string, unknown>)?.correct ?? "";
    return `共 ${total} 题，答对 ${correct} 题。针对薄弱知识点重点复盘。`;
  } catch {
    return "请根据测验结果调整复盘节奏。";
  }
}

onMounted(() => {
  const statePayload = route.state as Record<string, unknown>;
  sourceAction.value = (statePayload?.sourceAction as { id?: string; title?: string; summary?: string }) ?? null;
  const initial = {
    sessionId: statePayload?.sessionId as string | undefined,
    jobId: statePayload?.jobId as string | undefined,
    questions: (statePayload?.questions as QuizQuestion[]) ?? [],
  };
  let hydrated = hydrateFrom(initial);

  if (!hydrated) {
    const querySession = typeof route.query.sessionId === "string" ? route.query.sessionId : undefined;
    const stored = loadStoredSession();
    if (stored && (!querySession || stored.sessionId === querySession)) {
      hydrated = hydrateFrom(stored);
    } else if (stored && querySession && stored.sessionId !== querySession) {
      restoreHint.value = "发现历史测验，点击恢复";
    }
    if (!hydrated && querySession) {
      sessionId.value = querySession;
      jobId.value = typeof route.query.jobId === "string" ? route.query.jobId : undefined;
    }
  }
});

function resetSelections() {
  Object.keys(answers).forEach((key) => {
    answers[key] = "";
  });
  submitError.value = "";
  result.value = null;
  persistSession();
}

function findQuestion(id: string): QuizQuestion | undefined {
  return questions.value.find((question) => question.id === id);
}

async function handleSubmit() {
  if (!sessionId.value) {
    submitError.value = "缺少会话编号，请返回仪表盘重新启动测验。";
    return;
  }
  const payload = questions.value.map((question) => ({
    id: question.id,
    answer: answers[question.id] ?? "",
  }));
  if (payload.some((entry) => !entry.answer)) {
    submitError.value = "提交前请先完成所有题目。";
    return;
  }

  isSubmitting.value = true;
  submitError.value = "";
  try {
    const response = await submitQuiz(sessionId.value, payload);
    result.value = response;
    persistSession();
  } catch (error) {
    submitError.value = (error as Error).message;
  } finally {
    isSubmitting.value = false;
  }
}
</script>
