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

      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-800">题目列表</h2>
          <p class="text-sm text-slate-500">{{ unansweredCount }} 道题尚未作答</p>
        </div>
        <div class="space-y-4">
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

        <article class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-3">
          <h3 class="text-lg font-semibold text-slate-800">题目解析</h3>
          <table class="w-full text-left text-sm">
            <thead>
              <tr class="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th class="py-2">题目</th>
                <th class="py-2">你的作答</th>
                <th class="py-2">标准答案</th>
                <th class="py-2">结果</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="detail in result.detail" :key="detail.id" class="border-b border-slate-100">
                <td class="py-2 pr-4">{{ findQuestion(detail.id)?.question || "题目" }}</td>
                <td class="py-2 pr-4">{{ detail.user_answer || "无" }}</td>
                <td class="py-2 pr-4">{{ detail.answer || "无" }}</td>
                <td class="py-2">
                  <span
                    class="rounded px-2 py-1 text-xs font-semibold"
                    :class="detail.correct ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
                  >
                    {{ detail.correct ? "答对" : "答错" }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </article>

        <JsonPreview :value="result.diagnostics" />
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import JsonPreview from "../components/JsonPreview.vue";
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

onMounted(() => {
  const statePayload = route.state as Record<string, unknown>;
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
