<template>
  <section class="space-y-8">
    <header class="rounded border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-xs uppercase tracking-wide text-blue-600">ClassWeaver 工作台</p>
          <h1 class="text-2xl font-semibold text-slate-800">快速生成预习资料、测验与打印包</h1>
          <p class="text-sm text-slate-500">
            步骤：输入课程内容 → 自动生成知识点与测验 → 立刻开启测验或导出打印。
          </p>
        </div>
        <ol class="grid gap-2 text-sm text-slate-600 md:w-1/2 md:grid-cols-3">
          <li class="rounded border border-slate-200 bg-slate-50 p-3">
            <strong class="block text-xs uppercase text-slate-500">步骤 1</strong>
            粘贴文本或上传 PPTX
          </li>
          <li class="rounded border border-slate-200 bg-slate-50 p-3">
            <strong class="block text-xs uppercase text-slate-500">步骤 2</strong>
            查看生成的知识点与测验
          </li>
          <li class="rounded border border-slate-200 bg-slate-50 p-3">
            <strong class="block text-xs uppercase text-slate-500">步骤 3</strong>
            启动测验或下载打印资料
          </li>
        </ol>
      </div>
    </header>

    <div v-if="restoreError" class="rounded border border-amber-300 bg-amber-50 p-4 text-sm text-amber-700">
      无法恢复上一次任务：{{ restoreError }}。您可以重新生成新的内容。
    </div>

    <div class="grid gap-6 md:grid-cols-2">
      <article class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header>
          <h2 class="text-lg font-semibold text-slate-800">从文本生成</h2>
          <p class="text-sm text-slate-500">粘贴课程资料，系统会生成知识点、术语表和测验题。</p>
        </header>
        <textarea
          v-model="textInput"
          class="h-44 w-full resize-none rounded border border-slate-300 p-3 text-sm focus:border-blue-500 focus:outline-none"
          placeholder="例如：课程目标、重点知识点、小结、练习等"
        ></textarea>
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-500">{{ textInput.length }} 字符</span>
          <button
            class="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
            :disabled="isGenerating || !textInput.trim()"
            @click="handleGenerateFromText"
          >
            {{ isGenerating && generationSource === "text" ? "生成中..." : "生成" }}
          </button>
        </div>
        <p v-if="generationError" class="text-sm text-red-600">{{ generationError }}</p>
      </article>

      <article class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <header>
          <h2 class="text-lg font-semibold text-slate-800">从 PPTX 生成</h2>
          <p class="text-sm text-slate-500">上传 PowerPoint 文件。系统会提取文字并生成对应内容。</p>
        </header>
        <input type="file" accept=".pptx" @change="onPptFileChange" />
        <button
          class="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
          :disabled="isGenerating || !pptFile"
          @click="handleGenerateFromPpt"
        >
          {{ isGenerating && generationSource === "ppt" ? "上传中..." : "生成" }}
        </button>
        <p v-if="pptFile" class="text-xs text-slate-500">已选择文件：{{ pptFile.name }}</p>
        <p v-if="generationError && generationSource === 'ppt'" class="text-sm text-red-600">{{ generationError }}</p>
      </article>
    </div>

    <div v-if="generationSuccess" class="rounded border border-emerald-300 bg-emerald-50 p-4 text-sm text-emerald-700">
      生成完成！查看下方“下一步”提示，直接启动测验或导出打印资料。刷新页面后可通过保存的任务继续使用。
    </div>

    <section v-if="job" class="space-y-6">
      <article class="rounded border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p class="text-xs uppercase text-slate-500">最新生成</p>
            <h2 class="text-xl font-semibold text-slate-800">任务 #{{ job.id }}</h2>
            <p class="text-sm text-slate-500">
              状态：{{ statusLabel }} · 耗时 {{ job.duration_ms }} ms
              <span v-if="lastUpdatedDisplay"> · 上次更新 {{ lastUpdatedDisplay }}</span>
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              class="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
              :disabled="isStartingQuiz"
              @click="handleStartQuiz"
            >
              {{ isStartingQuiz ? "创建测验中..." : "启动测验" }}
            </button>
            <button
              class="rounded border border-blue-500 px-4 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50"
              @click="navigateToPrintable"
            >
              打印资料包
            </button>
            <button
              class="rounded border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
              @click="clearStoredJob"
            >
              清除结果
            </button>
          </div>
        </div>
        <p class="mt-3 text-sm text-slate-500">
          已为您生成知识点、术语表、测验题与打印资料。生成后的任务已自动保存在浏览器，刷新页面仍可继续使用。
        </p>
        <p v-if="quizError" class="mt-2 text-sm text-red-600">{{ quizError }}</p>
      </article>

      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-xs uppercase text-slate-500">任务 ID</p>
          <p class="text-lg font-semibold text-slate-800">{{ job.id }}</p>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-xs uppercase text-slate-500">状态</p>
          <p class="text-lg font-semibold text-slate-800">{{ job.status }}</p>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-xs uppercase text-slate-500">耗时</p>
          <p class="text-lg font-semibold text-slate-800">{{ job.duration_ms }} ms</p>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-xs uppercase text-slate-500">测验题量</p>
          <p class="text-lg font-semibold text-slate-800">{{ quizItems.length }}</p>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <article class="space-y-3 rounded border border-slate-200 bg-white p-4 shadow-sm">
          <header class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-800">知识点</h3>
            <span class="text-xs text-slate-500">{{ knowledgePoints.length }} 个条目</span>
          </header>
          <ul class="space-y-2 max-h-64 overflow-y-auto">
            <li v-for="kp in knowledgePoints" :key="kp.id || kp.title" class="rounded border border-slate-200 p-3">
              <h4 class="text-sm font-semibold text-slate-800">{{ kp.title || kp.id }}</h4>
              <p class="text-sm text-slate-600">{{ kp.summary }}</p>
            </li>
            <li v-if="!knowledgePoints.length" class="text-sm text-slate-500">暂无知识点。</li>
          </ul>
        </article>

        <article class="space-y-3 rounded border border-slate-200 bg-white p-4 shadow-sm">
          <header class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-800">术语表</h3>
            <span class="text-xs text-slate-500">{{ glossaryItems.length }} 个词条</span>
          </header>
          <dl class="space-y-2 max-h-64 overflow-y-auto">
            <div v-for="entry in glossaryItems" :key="entry.term" class="rounded border border-slate-200 p-3">
              <dt class="text-sm font-semibold text-slate-800">{{ entry.term }}</dt>
              <dd class="text-sm text-slate-600">{{ entry.definition }}</dd>
            </div>
            <p v-if="!glossaryItems.length" class="text-sm text-slate-500">暂无术语。</p>
          </dl>
        </article>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <JsonPreview :value="job.planner_json" />
        <JsonPreview :value="job.final_json" />
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <TracePanel :items="job.model_trace" />
        <div class="space-y-3 rounded border border-slate-200 bg-white p-4 shadow-sm">
          <header class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-800">测验预览</h3>
            <span class="text-xs text-slate-500">展示前 {{ Math.min(3, quizItems.length) }} 道题</span>
          </header>
          <div class="space-y-3">
            <QuizCard v-for="item in quizItems.slice(0, 3)" :key="item.id" :question="item" :readonly="true" />
          </div>
          <p class="text-xs text-slate-500">
            小贴士：点击“启动测验”后，系统会分发完整题目集并记录答题结果。
          </p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-6 shadow-sm space-y-6">
      <header class="space-y-2">
        <p class="text-xs uppercase tracking-wide text-emerald-600">可选 · 增强生成效果</p>
        <h2 class="text-lg font-semibold text-slate-800">导入资料并检索知识库</h2>
        <p class="text-sm text-slate-500">
          上传教材/讲义后，系统会自动切片并写入向量索引；后续生成或检索时即可引用这些片段，提升回答准确度。
        </p>
        <ul class="list-disc space-y-1 pl-5 text-xs text-slate-500">
          <li>支持 TXT、PDF、DOCX、PPTX；若 PDF 为扫描件，请先进行 OCR 转换。</li>
          <li>上传完成后可直接在右侧检索验证内容，或在生成任务时自动引用。</li>
        </ul>
      </header>

      <div class="grid gap-6 md:grid-cols-2">
        <div class="space-y-3 rounded border border-emerald-100 bg-emerald-50 p-4">
          <h3 class="text-sm font-semibold text-emerald-800">步骤 1 · 导入资料</h3>
          <p class="text-xs text-emerald-700">
            选择文件后点击上传，我们会在后台完成分段、嵌入与索引写入。
          </p>
          <input type="file" accept=".txt,.pdf,.docx,.pptx" @change="onKbFileChange" />
          <button
            class="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
            :disabled="isUploadingKb || !kbFile"
            @click="handleKbUpload"
          >
            {{ isUploadingKb ? "上传中..." : "上传到知识库" }}
          </button>
          <p v-if="kbStatus" class="text-sm" :class="kbStatus.success ? 'text-emerald-700' : 'text-red-600'">
            {{ kbStatus.message }}
          </p>
          <p v-else class="text-xs text-emerald-700">
            小贴士：成功上传会提示切片数量；若为 0，请检查文件是否包含可复制文字。
          </p>
        </div>

        <div class="space-y-3 rounded border border-slate-200 bg-white p-4">
          <h3 class="text-sm font-semibold text-slate-800">步骤 2 · 检索片段</h3>
          <p class="text-xs text-slate-500">
            通过关键词查找刚导入的知识片段，确认内容是否正确，或直接引用到预习讲义中。
          </p>
          <div class="flex flex-col gap-2 md:flex-row">
            <input
              v-model="knowledgeQuery"
              type="text"
              placeholder="输入检索关键词，例如“二次函数 顶点”"
              class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <div class="flex items-center gap-1">
              <label class="text-xs text-slate-500" for="kb-top-k">返回</label>
              <input
                id="kb-top-k"
                v-model.number="topK"
                type="number"
                min="1"
                max="10"
                class="w-20 rounded border border-slate-300 px-2 py-2 text-sm"
              />
              <span class="text-xs text-slate-500">条</span>
            </div>
            <button
              class="rounded bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              :disabled="isSearching || !knowledgeQuery.trim()"
              @click="handleKnowledgeSearch"
            >
              {{ isSearching ? "检索中..." : "开始检索" }}
            </button>
          </div>
          <p v-if="knowledgeError" class="text-sm text-red-600">{{ knowledgeError }}</p>
          <ul class="max-h-64 space-y-3 overflow-y-auto" v-if="knowledgeResults.length">
            <li
              v-for="item in knowledgeResults"
              :key="item.refs[0]?.chunk_id"
              class="rounded border border-slate-200 p-3 text-sm"
            >
              <div class="flex items-center justify-between text-xs text-slate-500">
                <span>{{ item.title || item.refs[0]?.doc_id }}</span>
                <span>相似度：{{ item.score.toFixed(3) }}</span>
              </div>
              <p class="mt-2 whitespace-pre-line text-slate-700">{{ item.text }}</p>
              <p class="mt-2 text-xs text-slate-500">引用：{{ formatRefs(item) }}</p>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-500">{{ knowledgeEmptyMessage }}</p>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import JsonPreview from "../components/JsonPreview.vue";
import QuizCard from "../components/QuizCard.vue";
import TracePanel from "../components/TracePanel.vue";
import {
  createPrestudyFromPpt,
  createPrestudyFromText,
  getPrestudyJob,
  searchKnowledge,
  startQuiz,
  uploadKnowledge,
} from "../services/api";
import type {
  GlossaryItem,
  KnowledgePoint,
  KnowledgeSearchResult,
  PrintablePayload,
  PrestudyResponse,
  QuizQuestion,
} from "../types";

const STORAGE_KEY = "classweaver:last-prestudy";

interface PersistedJob {
  id: string;
  payload?: PrestudyResponse;
  updatedAt?: number;
}

const router = useRouter();

const textInput = ref("");
const pptFile = ref<File | null>(null);
const kbFile = ref<File | null>(null);
const knowledgeQuery = ref("");
const topK = ref(5);

const job = ref<PrestudyResponse | null>(null);
const isGenerating = ref(false);
const generationSource = ref<"text" | "ppt" | null>(null);
const generationError = ref("");
const generationSuccess = ref(false);

const knowledgeResults = ref<KnowledgeSearchResult[]>([]);
const isSearching = ref(false);
const knowledgeError = ref("");
const hasSearched = ref(false);

const isUploadingKb = ref(false);
const kbStatus = ref<{ success: boolean; message: string } | null>(null);

const isStartingQuiz = ref(false);
const quizError = ref("");

const isRestoring = ref(true);
const restoreError = ref("");
const persistedTimestamp = ref<number | null>(null);

onMounted(async () => {
  if (typeof window === "undefined") {
    isRestoring.value = false;
    return;
  }
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    isRestoring.value = false;
    return;
  }
  try {
    const stored = JSON.parse(raw) as PersistedJob;
    if (stored.payload) {
      job.value = stored.payload;
      persistedTimestamp.value = stored.updatedAt ?? Date.now();
    }
    if (stored.id) {
      const fresh = await getPrestudyJob(stored.id);
      job.value = fresh;
      generationSuccess.value = false;
      persistedTimestamp.value = Date.now();
      persistJob(fresh);
    }
  } catch (error) {
    restoreError.value = (error as Error).message;
    window.localStorage.removeItem(STORAGE_KEY);
  } finally {
    isRestoring.value = false;
  }
});

function persistJob(payload: PrestudyResponse | null) {
  if (typeof window === "undefined") {
    return;
  }
  if (!payload) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  const bundle: PersistedJob = {
    id: payload.id,
    payload,
    updatedAt: Date.now(),
  };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(bundle));
}

function clearStoredJob() {
  job.value = null;
  generationSuccess.value = false;
  persistedTimestamp.value = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

function asArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

const knowledgePoints = computed<KnowledgePoint[]>(() => {
  const finalData = (job.value?.final_json ?? {}) as Record<string, unknown>;
  const plannerData = (job.value?.planner_json ?? {}) as Record<string, unknown>;
  return asArray<KnowledgePoint>(finalData.knowledge_points ?? plannerData.knowledge_points);
});

const glossaryItems = computed<GlossaryItem[]>(() => {
  const finalData = (job.value?.final_json ?? {}) as Record<string, unknown>;
  const plannerData = (job.value?.planner_json ?? {}) as Record<string, unknown>;
  return asArray<GlossaryItem>(finalData.glossary ?? plannerData.glossary);
});

const quizItems = computed<QuizQuestion[]>(() => {
  const quizBlock = ((job.value?.final_json ?? {}) as Record<string, unknown>).quiz as
    | { items?: unknown[] }
    | undefined;
  return asArray<QuizQuestion>(quizBlock?.items);
});

const printablePayload = computed<PrintablePayload | null>(() => {
  if (!job.value) {
    return null;
  }
  if (job.value.printable) {
    return job.value.printable;
  }
  const tutorBlock = ((job.value.final_json ?? {}) as Record<string, unknown>).tutor as
    | { practice?: unknown[] }
    | undefined;
  return {
    title: "ClassWeaver 打印资料包",
    knowledge_points: knowledgePoints.value,
    glossary: glossaryItems.value,
    quiz: quizItems.value,
    practice: asArray(tutorBlock?.practice),
  };
});

const knowledgeEmptyMessage = computed(() => {
  if (!hasSearched.value) {
    return "上传资料后可在此检索片段，快速确认内容是否正确。";
  }
  if (!knowledgeQuery.value.trim()) {
    return "请输入检索关键词，然后点击“开始检索”。";
  }
  return "未找到匹配的片段，可尝试更换关键词或导入更多资料。";
});

const statusLabel = computed(() => {
  if (!job.value) {
    return "无";
  }
  switch (job.value.status) {
    case "completed":
      return "已完成";
    case "processing":
      return "生成中";
    case "failed":
      return "失败";
    default:
      return job.value.status;
  }
});

const lastUpdatedDisplay = computed(() => {
  if (!persistedTimestamp.value) {
    return "";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(persistedTimestamp.value);
});

function resetGenerationState() {
  isGenerating.value = false;
  generationSource.value = null;
}

async function handleGenerateFromText() {
  if (!textInput.value.trim()) {
    generationError.value = "请先填写课程文本。";
    return;
  }
  isGenerating.value = true;
  generationSource.value = "text";
  generationError.value = "";
  try {
    const response = await createPrestudyFromText(textInput.value.trim());
    job.value = response;
    generationSuccess.value = true;
    persistedTimestamp.value = Date.now();
    persistJob(response);
  } catch (error) {
    generationError.value = (error as Error).message;
  } finally {
    resetGenerationState();
  }
}

function onPptFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  pptFile.value = target.files?.[0] ?? null;
}

async function handleGenerateFromPpt() {
  if (!pptFile.value) {
    generationError.value = "请选择 PPTX 文件。";
    return;
  }
  isGenerating.value = true;
  generationSource.value = "ppt";
  generationError.value = "";
  try {
    const response = await createPrestudyFromPpt(pptFile.value);
    job.value = response;
    generationSuccess.value = true;
    persistedTimestamp.value = Date.now();
    persistJob(response);
  } catch (error) {
    generationError.value = (error as Error).message;
  } finally {
    resetGenerationState();
  }
}

async function handleKnowledgeSearch() {
  if (!knowledgeQuery.value.trim()) {
    knowledgeError.value = "请输入检索关键词。";
    return;
  }
  isSearching.value = true;
  hasSearched.value = true;
  knowledgeError.value = "";
  try {
    const response = await searchKnowledge({ query: knowledgeQuery.value.trim(), top_k: topK.value });
    knowledgeResults.value = response.results ?? [];
  } catch (error) {
    knowledgeError.value = (error as Error).message;
    knowledgeResults.value = [];
  } finally {
    isSearching.value = false;
  }
}

function onKbFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  kbFile.value = target.files?.[0] ?? null;
}

async function handleKbUpload() {
  if (!kbFile.value) {
    kbStatus.value = { success: false, message: "请选择要上传的文件。" };
    return;
  }
  isUploadingKb.value = true;
  kbStatus.value = null;
  try {
    const response = await uploadKnowledge(kbFile.value);
    const chunkCountRaw = response?.chunks;
    const chunkCount = typeof chunkCountRaw === "number" ? chunkCountRaw : Number(chunkCountRaw ?? 0);
    if (Number.isFinite(chunkCount) && chunkCount > 0) {
      kbStatus.value = {
        success: true,
        message: `上传成功，切片数量：${chunkCount}`,
      };
      kbFile.value = null;
      knowledgeResults.value = [];
      hasSearched.value = false;
      knowledgeQuery.value = "";
    } else if (chunkCount === 0) {
      kbStatus.value = {
        success: false,
        message: "上传完成，但未提取到可用文本。请确认文档包含可复制文字，或先进行 OCR。",
      };
    } else {
      kbStatus.value = {
        success: true,
        message: "上传成功，切片数量未知。",
      };
      kbFile.value = null;
      knowledgeResults.value = [];
      hasSearched.value = false;
      knowledgeQuery.value = "";
    }
  } catch (error) {
    kbStatus.value = { success: false, message: (error as Error).message };
  } finally {
    isUploadingKb.value = false;
  }
}

async function handleStartQuiz() {
  if (!job.value) {
    return;
  }
  isStartingQuiz.value = true;
  quizError.value = "";
  try {
    const session = await startQuiz(job.value.id);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(
        "classweaver:last-quiz-session",
        JSON.stringify({
          jobId: job.value.id,
          sessionId: session.session_id,
          questions: session.questions,
          savedAt: Date.now(),
        }),
      );
    }
    router.push({
      name: "take",
      query: { jobId: job.value.id, sessionId: session.session_id },
      state: {
        sessionId: session.session_id,
        questions: session.questions,
        jobId: job.value.id,
      },
    });
  } catch (error) {
    quizError.value = (error as Error).message;
  } finally {
    isStartingQuiz.value = false;
  }
}

function navigateToPrintable() {
  if (!job.value) {
    return;
  }
  if (typeof window !== "undefined" && printablePayload.value) {
    window.sessionStorage.setItem(
      "classweaver:last-printable",
      JSON.stringify({
        jobId: job.value.id,
        printable: printablePayload.value,
        savedAt: Date.now(),
      }),
    );
  }
  router.push({
    name: "print",
    query: { jobId: job.value.id },
    state: { printable: printablePayload.value },
  });
}

function formatRefs(item: KnowledgeSearchResult): string {
  return (item.refs ?? [])
    .map((ref) => `${ref.doc_id}#${ref.chunk_id}`)
    .join("、") || "无";
}
</script>
