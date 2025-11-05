<template>
  <section class="space-y-6">
    <div v-if="loading" class="rounded border border-slate-200 bg-white p-6 shadow-sm text-sm text-slate-500">
      正在载入打印资料，请稍候…
    </div>

    <div v-else-if="!printable" class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-3">
      <h1 class="text-2xl font-semibold text-slate-800">暂无可打印资料</h1>
      <p class="text-sm text-slate-600">
        请返回仪表盘生成新的任务，或点击下方按钮尝试重新获取最近一次的打印数据。
      </p>
      <div class="flex flex-wrap gap-2">
        <button class="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500" @click="router.push('/')">
          返回仪表盘
        </button>
        <button
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
          @click="restoreFromStorage"
          :disabled="restoring"
        >
          {{ restoring ? "恢复中..." : "恢复最近打印数据" }}
        </button>
        <button
          v-if="jobId"
          class="rounded border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
          @click="fetchPrintable"
        >
          重新请求任务 {{ jobId }}
        </button>
      </div>
      <p v-if="errorMessage" class="text-sm text-red-600">{{ errorMessage }}</p>
    </div>

    <div v-else class="space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-semibold text-slate-800">{{ printable.title }}</h1>
          <p class="text-sm text-slate-500">
            汇总知识点、术语、测验与课后练习。打印后即可线下发放或归档。
          </p>
          <p v-if="jobId" class="text-xs text-slate-500">关联任务：{{ jobId }}</p>
        </div>
        <button class="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500" @click="handlePrint">
          打印
        </button>
      </header>

      <section class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-slate-800">知识点</h2>
          <span class="text-sm text-slate-500">{{ printable.knowledge_points.length }} 条</span>
        </header>
        <ul class="grid gap-3 md:grid-cols-2">
          <li
            v-for="kp in printable.knowledge_points"
            :key="kp.id || kp.title"
            class="rounded border border-slate-200 bg-slate-50 p-4"
          >
            <h3 class="text-lg font-semibold text-slate-800">{{ kp.title || kp.id }}</h3>
            <p class="text-sm text-slate-600">{{ kp.summary }}</p>
          </li>
          <li v-if="!printable.knowledge_points.length" class="text-sm text-slate-500">
            暂无知识点。
          </li>
        </ul>
      </section>

      <section class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-slate-800">术语表</h2>
          <span class="text-sm text-slate-500">{{ printable.glossary.length }} 个词条</span>
        </header>
        <dl class="grid gap-3 md:grid-cols-2">
          <div v-for="item in printable.glossary" :key="item.term" class="rounded border border-slate-200 bg-slate-50 p-4">
            <dt class="text-sm font-semibold text-slate-800">{{ item.term }}</dt>
            <dd class="text-sm text-slate-600">{{ item.definition }}</dd>
          </div>
          <p v-if="!printable.glossary.length" class="text-sm text-slate-500">暂无术语。</p>
        </dl>
      </section>

      <section class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-slate-800">测验</h2>
          <span class="text-sm text-slate-500">{{ printable.quiz.length }} 道题</span>
        </header>
        <ol class="space-y-4">
          <li v-for="(question, index) in printable.quiz" :key="question.id || index" class="rounded border border-slate-200 bg-slate-50 p-4">
            <header class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-slate-800">第 {{ index + 1 }} 题：{{ question.question }}</h3>
              <span class="text-xs font-semibold uppercase text-slate-500">{{ difficultyLabel(question.difficulty) }}</span>
            </header>
            <ul class="mt-3 space-y-1 text-sm text-slate-700">
              <li v-for="(label, key) in question.options" :key="key">{{ key }}. {{ label }}</li>
            </ul>
            <p v-if="question.answer" class="mt-3 text-sm font-semibold text-emerald-600">
              答案：{{ question.answer }}
              <span v-if="question.explain" class="ml-2 font-normal text-slate-600">{{ question.explain }}</span>
            </p>
          </li>
        </ol>
      </section>

      <section class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-slate-800">课后练习</h2>
          <span class="text-sm text-slate-500">{{ printable.practice.length }} 个练习</span>
        </header>
        <ol class="space-y-4">
          <li v-for="(practice, index) in printable.practice" :key="index" class="rounded border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-800">{{ index + 1 }}. {{ practice.prompt }}</p>
            <p v-if="practice.answer" class="mt-2 text-sm text-slate-600">参考答案：{{ practice.answer }}</p>
            <p v-if="practice.reasoning" class="text-sm italic text-slate-500">{{ practice.reasoning }}</p>
          </li>
          <li v-if="!printable.practice.length" class="text-sm text-slate-500">暂无额外练习。</li>
        </ol>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getPrestudyJob } from "../services/api";
import type { PrintablePayload, PrestudyResponse } from "../types";

interface StoredPrintable {
  jobId?: string;
  printable: PrintablePayload;
  savedAt?: number;
}

const STORAGE_KEY = "classweaver:last-printable";

const router = useRouter();
const route = useRoute();

const printable = ref<PrintablePayload | null>(null);
const loading = ref(true);
const restoring = ref(false);
const errorMessage = ref("");

const jobId = computed(() => (typeof route.query.jobId === "string" ? route.query.jobId : undefined));

function loadFromStorage(): StoredPrintable | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StoredPrintable;
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function saveToStorage(payload: StoredPrintable) {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...payload, savedAt: Date.now() }));
}

async function fetchPrintable() {
  if (!jobId.value) {
    return;
  }
  loading.value = true;
  errorMessage.value = "";
  try {
    const response: PrestudyResponse = await getPrestudyJob(jobId.value);
    printable.value = response.printable ?? buildPrintableFromFinal(response);
    if (printable.value) {
      saveToStorage({ jobId: jobId.value, printable: printable.value });
    }
  } catch (error) {
    errorMessage.value = (error as Error).message;
    printable.value = null;
  } finally {
    loading.value = false;
  }
}

function toArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function buildPrintableFromFinal(payload: PrestudyResponse): PrintablePayload | null {
  const finalJson = (payload.final_json ?? {}) as Record<string, unknown>;
  const tutorBlock = finalJson.tutor as Record<string, unknown> | undefined;
  const quizBlock = finalJson.quiz as Record<string, unknown> | undefined;
  if (!quizBlock || !Array.isArray(quizBlock.items)) {
    return null;
  }
  return {
    title: "ClassWeaver 打印资料包",
    knowledge_points: toArray<PrintablePayload["knowledge_points"][number]>(finalJson.knowledge_points),
    glossary: toArray<PrintablePayload["glossary"][number]>(finalJson.glossary),
    quiz: toArray<PrintablePayload["quiz"][number]>(quizBlock.items),
    practice: toArray<PrintablePayload["practice"][number]>(tutorBlock?.practice),
  };
}

function restoreFromStorage() {
  restoring.value = true;
  try {
    const stored = loadFromStorage();
    if (stored) {
      if (!jobId.value || !stored.jobId || stored.jobId === jobId.value) {
        printable.value = stored.printable;
      }
    }
  } finally {
    restoring.value = false;
    loading.value = false;
  }
}

onMounted(() => {
  const statePrintable = (route.state as Record<string, unknown>)?.printable as PrintablePayload | undefined;
  if (statePrintable) {
    printable.value = statePrintable;
    saveToStorage({ jobId: jobId.value, printable: statePrintable });
    loading.value = false;
    return;
  }

  const stored = loadFromStorage();
  if (stored && (!jobId.value || !stored.jobId || stored.jobId === jobId.value)) {
    printable.value = stored.printable;
    loading.value = false;
    if (jobId.value && stored.jobId !== jobId.value) {
      saveToStorage({ jobId: jobId.value, printable: stored.printable });
    }
    return;
  }

  if (jobId.value) {
    fetchPrintable();
    return;
  }

  loading.value = false;
});

function difficultyLabel(level?: string) {
  const labels: Record<string, string> = {
    easy: "简单",
    medium: "中等",
    hard: "困难",
  };
  return level ? labels[level] ?? level : "未知";
}

function handlePrint() {
  window.print();
}
</script>
