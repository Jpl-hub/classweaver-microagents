<template>
  <div class="min-h-screen bg-[#f5f7fb] text-slate-900">
    <div class="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">知识库</p>
          <h1 class="text-3xl font-semibold text-slate-900">我的知识库</h1>
          <p class="mt-2 max-w-2xl text-sm text-slate-600">
            这里汇集了你上传过的讲义、PDF 与 PPT，支持批量上传与快速检索。选择一个资料即可在学习工作台内引用。
          </p>
        </div>
        <RouterLink class="btn-secondary" :to="{ name: 'home' }">
          返回学习工作台
        </RouterLink>
      </header>

      <section class="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <article class="glass-panel flex flex-col gap-4">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-sm text-slate-500">资料库概览</p>
              <h2 class="text-xl font-semibold text-slate-900">
                {{ knowledgeCount > 0 ? `共 ${knowledgeCount} 个知识库` : "暂未上传资料" }}
              </h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button class="btn-secondary" type="button" @click="openKnowledgeUpload" :disabled="!selectedKnowledgeBase">
                上传资料
              </button>
              <button class="btn-ghost text-sm" type="button" :disabled="isLoadingList" @click="syncKnowledgeBasesFromServer">
                {{ isLoadingList ? "刷新中…" : "刷新列表" }}
              </button>
              <button
                class="btn-ghost text-sm text-rose-600"
                type="button"
                :disabled="deletingAll"
                @click="handleClearAll"
              >
                {{ deletingAll ? "清空中..." : "清空全部知识库" }}
              </button>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-sm">
              <input
                v-model="newBaseName"
                class="w-48 rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400"
                type="text"
                placeholder="输入名称创建知识库"
              />
              <button class="btn-secondary" type="button" @click="handleCreateBase">新建知识库</button>
            </div>
            <input
              ref="uploadInputRef"
              class="sr-only absolute -z-10 h-px w-px overflow-hidden"
              type="file"
              accept=".txt,.pdf,.doc,.docx,.ppt,.pptx"
              multiple
              @change="handleKnowledgeUpload"
            >
          </div>
          <p v-if="knowledgeUploadStatus" class="text-xs text-slate-500">
            {{ knowledgeUploadStatus }}
          </p>
          <div class="space-y-3">
            <article
              v-for="base in knowledgeBases"
              :key="base.id"
              class="rounded-2xl border border-white/70 bg-white/80 p-4"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-base font-semibold text-slate-900">{{ base.name }}</p>
                  <p class="text-xs text-slate-500">最近更新：{{ base.updated }} · 容量：{{ base.size }}</p>
                </div>
                <button
                  class="text-xs text-slate-500 underline-offset-4 hover:text-slate-800"
                  type="button"
                  @click="setActiveKnowledgeBase(base.id)"
                >
                  {{ selectedKnowledgeBase === base.id ? "当前使用" : "设为当前" }}
                </button>
              </div>
              <div class="flex flex-wrap gap-2 text-xs text-slate-500">
                <button
                  v-if="base.id !== DEFAULT_KNOWLEDGE_BASE.id"
                  class="text-rose-600 underline underline-offset-4 hover:text-rose-700"
                  type="button"
                  :disabled="deletingDocId === base.id"
                  @click="handleDelete(base.id)"
                >
                  {{ deletingDocId === base.id ? "删除中..." : "删除此知识库" }}
                </button>
                <span v-else class="text-slate-400">默认知识库不可删除</span>
              </div>
            </article>
            <p
              v-if="knowledgeBases.length <= 1"
              class="rounded-2xl border border-dashed border-slate-300/80 bg-white/60 px-4 py-5 text-sm text-slate-600"
            >
              还没有上传任何资料，点击右上角的“上传资料”即可导入 PDF、DOCX、PPT 等文件，供学习工作台随时引用。
            </p>
          </div>
        </article>

        <article class="glass-panel flex flex-col gap-4">
          <div>
            <p class="text-sm text-slate-500">快速检索</p>
            <h3 class="text-xl font-semibold text-slate-900">定位关键片段</h3>
          </div>
          <div class="rounded-2xl border border-white/70 bg-white/70 p-4">
            <label class="text-xs text-slate-500">当前引用</label>
            <select
              v-model="selectedKnowledgeBase"
              class="mt-1 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400"
            >
              <option
                v-for="base in knowledgeBases"
                :key="base.id"
                :value="base.id"
              >
                {{ base.name }}
              </option>
            </select>
          </div>
          <textarea
            v-model="knowledgeSearchQuery"
            class="min-h-[140px] w-full rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400"
            placeholder="输入知识点、题目或想查的段落，系统将仅在当前知识库中检索…"
          />
          <button
            class="btn-primary"
            :disabled="!knowledgeSearchQuery.trim()"
            type="button"
            @click="handleKnowledgeSearch"
          >
            开始检索
          </button>
          <div class="space-y-3">
            <article
              v-for="result in knowledgeSearchResults"
              :key="result.text"
              class="rounded-2xl border border-slate-200/80 bg-white px-4 py-3"
            >
              <p class="text-sm font-medium text-slate-800">
                {{ result.text }}
              </p>
              <p class="mt-1 text-xs text-slate-500">
                来源：{{ renderRefs(result.refs, result.title) }} · 相似度 {{ result.score.toFixed(2) }}
              </p>
            </article>
            <p
              v-if="!knowledgeSearchResults.length"
              class="rounded-2xl border border-dashed border-slate-200/80 bg-white/70 px-4 py-4 text-xs text-slate-500"
            >
              尚未检索，可输入问题或知识点后点击“开始检索”查看命中的片段。
            </p>
          </div>
          <div class="mt-4 rounded-2xl border border-white/70 bg-white/80 p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-slate-500">当前库内文档</p>
                <h4 class="text-base font-semibold text-slate-900">{{ documents.length ? `${documents.length} 份` : "暂无文档" }}</h4>
              </div>
              <span v-if="isLoadingDocs" class="text-xs text-slate-500">加载中…</span>
            </div>
            <ul class="mt-2 space-y-2 max-h-40 overflow-y-auto pr-1">
              <li
                v-for="doc in documents"
                :key="doc.doc_id"
                class="rounded-xl border border-slate-200/70 bg-white px-3 py-2 text-sm text-slate-700"
              >
                <p class="font-semibold text-slate-900">{{ doc.title }}</p>
                <p class="text-xs text-slate-500">更新时间：{{ doc.updated_at }}</p>
              </li>
              <li v-if="!documents.length" class="text-xs text-slate-500">上传资料后会显示在这里。</li>
            </ul>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import {
  clearKnowledgeDocuments,
  deleteKnowledgeBase,
  createKnowledgeBase,
  listKnowledgeBases,
  listKnowledgeDocuments,
  searchKnowledge,
  uploadKnowledge,
} from "../services/api";
import type { KnowledgeSearchResult, RagSearchRequest, KnowledgeDocumentSummary } from "../types";
import type { KnowledgeBaseItem } from "../utils/knowledge";
import {
  DEFAULT_KNOWLEDGE_BASE,
  KNOWLEDGE_BASE_SELECTION_KEY,
  KNOWLEDGE_BASE_STORAGE_KEY,
  mapBaseToItem,
  normalizeKnowledgeBaseList,
  resolveKnowledgeBaseName,
} from "../utils/knowledge";

const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const selectedKnowledgeBase = ref<string | number>("");
const knowledgeUploadStatus = ref("");
const knowledgeSearchQuery = ref("");
const knowledgeSearchResults = ref<KnowledgeSearchResult[]>([]);
const documents = ref<KnowledgeDocumentSummary[]>([]);
const uploadInputRef = ref<HTMLInputElement>();
const newBaseName = ref("");
const isLoadingList = ref(false);
const isLoadingDocs = ref(false);
const deletingDocId = ref<string | null>(null);
const deletingAll = ref(false);

const currentKnowledgeBase = computed(() =>
  knowledgeBases.value.find((base) => base.id === selectedKnowledgeBase.value),
);
const knowledgeCount = computed(() => knowledgeBases.value.length);

function firstAvailableBaseId(list: KnowledgeBaseItem[]): string | number {
  const candidate = list.find((base) => String(base.id) !== String(DEFAULT_KNOWLEDGE_BASE.id));
  return candidate?.id ?? "";
}

watch(
  [knowledgeBases, selectedKnowledgeBase],
  () => {
    persistKnowledgeBases();
  },
  { deep: true },
);

function restoreKnowledgeBases() {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const storedList = window.sessionStorage.getItem(KNOWLEDGE_BASE_STORAGE_KEY);
    if (storedList) {
      const parsed = JSON.parse(storedList) as KnowledgeBaseItem[];
      if (Array.isArray(parsed) && parsed.length) {
        knowledgeBases.value = normalizeKnowledgeBaseList(parsed);
      }
    }
    const storedSelected = window.sessionStorage.getItem(KNOWLEDGE_BASE_SELECTION_KEY);
    if (storedSelected && knowledgeBases.value.some((base) => String(base.id) === storedSelected)) {
      selectedKnowledgeBase.value = storedSelected;
    } else {
      selectedKnowledgeBase.value = firstAvailableBaseId(knowledgeBases.value);
    }
  } catch {
    window.sessionStorage.removeItem(KNOWLEDGE_BASE_STORAGE_KEY);
    window.sessionStorage.removeItem(KNOWLEDGE_BASE_SELECTION_KEY);
    knowledgeBases.value = [];
    selectedKnowledgeBase.value = "";
  }
}

function persistKnowledgeBases() {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(KNOWLEDGE_BASE_STORAGE_KEY, JSON.stringify(knowledgeBases.value));
  window.sessionStorage.setItem(KNOWLEDGE_BASE_SELECTION_KEY, String(selectedKnowledgeBase.value));
}

async function syncKnowledgeBasesFromServer() {
  isLoadingList.value = true;
  try {
    const resp = await listKnowledgeBases();
    const serverList = (resp.bases ?? []).map(mapBaseToItem);
    const normalized = normalizeKnowledgeBaseList(serverList);
    knowledgeBases.value = normalized;
    const fallback = firstAvailableBaseId(normalized);
    if (!selectedKnowledgeBase.value && fallback) {
      selectedKnowledgeBase.value = fallback;
    } else if (!normalized.some((base) => String(base.id) === String(selectedKnowledgeBase.value))) {
      selectedKnowledgeBase.value = fallback;
    }
    await loadDocuments();
  } catch (error) {
    console.warn("获取知识库列表失败", error);
  } finally {
    isLoadingList.value = false;
  }
}

async function loadDocuments() {
  isLoadingDocs.value = true;
  try {
    const resp = await listKnowledgeDocuments(selectedKnowledgeBase.value);
    documents.value = resp.documents ?? [];
  } catch (error) {
    console.warn("获取文档列表失败", error);
  } finally {
    isLoadingDocs.value = false;
  }
}

async function handleKnowledgeUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = target.files ? Array.from(target.files).filter(Boolean) : [];
  if (!files.length) return;
  if (!selectedKnowledgeBase.value) {
    knowledgeUploadStatus.value = "请先选择或创建一个知识库。";
    target.value = "";
    return;
  }
  knowledgeUploadStatus.value = "上传中…";
  try {
    await uploadKnowledge(files, selectedKnowledgeBase.value);
    knowledgeUploadStatus.value = `上传完成，共 ${files.length} 份资料`;
    await syncKnowledgeBasesFromServer();
    await loadDocuments();
  } catch (error) {
    knowledgeUploadStatus.value = (error as Error).message ?? "上传失败";
  } finally {
    target.value = "";
  }
}

function openKnowledgeUpload() {
  uploadInputRef.value?.click();
}

function setActiveKnowledgeBase(id: string) {
  selectedKnowledgeBase.value = id;
  loadDocuments();
}

async function handleCreateBase() {
  const name = newBaseName.value.trim();
  if (!name) {
    knowledgeUploadStatus.value = "请输入知识库名称后创建。";
    return;
  }
  try {
    const base = await createKnowledgeBase(name);
    knowledgeBases.value = normalizeKnowledgeBaseList([...knowledgeBases.value, mapBaseToItem(base)]);
    selectedKnowledgeBase.value = base.id;
    newBaseName.value = "";
    await loadDocuments();
    knowledgeUploadStatus.value = `已创建知识库「${base.name}」`;
  } catch (error) {
    knowledgeUploadStatus.value = (error as Error).message ?? "创建失败";
  }
}

async function handleDelete(docId: string) {
  deletingDocId.value = docId;
  knowledgeUploadStatus.value = "";
  try {
    await deleteKnowledgeBase(docId);
    await syncKnowledgeBasesFromServer();
  } catch (error) {
    knowledgeUploadStatus.value = (error as Error).message ?? "删除失败";
  } finally {
    deletingDocId.value = null;
  }
}

async function handleClearAll() {
  deletingAll.value = true;
  knowledgeUploadStatus.value = "";
  try {
    await clearKnowledgeDocuments();
    await syncKnowledgeBasesFromServer();
    documents.value = [];
  } catch (error) {
    knowledgeUploadStatus.value = (error as Error).message ?? "清空失败";
  } finally {
    deletingAll.value = false;
  }
}

async function handleKnowledgeSearch() {
  if (!knowledgeSearchQuery.value.trim()) return;
  if (!selectedKnowledgeBase.value) {
    knowledgeUploadStatus.value = "请先选择要检索的知识库。";
    return;
  }
  const payload: RagSearchRequest = {
    query: knowledgeSearchQuery.value.trim(),
    top_k: 5,
    base_id: selectedKnowledgeBase.value !== DEFAULT_KNOWLEDGE_BASE.id ? selectedKnowledgeBase.value : undefined,
  };
  const resp = await searchKnowledge(payload);
  knowledgeSearchResults.value = resp.results;
}

const renderRefs = (
  refs: Array<{ doc_id: string; chunk_id: string }> = [],
  fallbackTitle?: string,
) => {
  if (!refs?.length) {
    return fallbackTitle ?? "知识库片段";
  }
  return refs
    .map((ref, index) => {
      const name = resolveKnowledgeBaseName(ref.doc_id, knowledgeBases.value, fallbackTitle ?? `资料 ${index + 1}`);
      const chunkHint = ref.chunk_id ? ref.chunk_id.split("-").pop() : "";
      return chunkHint ? `${name} · 片段 ${chunkHint}` : name;
    })
    .join(" / ");
};

onMounted(async () => {
  restoreKnowledgeBases();
  await syncKnowledgeBasesFromServer();
  await loadDocuments();
});
</script>
