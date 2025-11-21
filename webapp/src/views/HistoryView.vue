<template>
  <section class="space-y-6">
    <header class="glass-panel flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-[0.4em] text-slate-500">历史记录</p>
        <h1 class="text-2xl font-semibold text-slate-900">最近的课程任务</h1>
        <p class="text-sm text-slate-500">数据存储于本地浏览器，仅展示最近一次生成的任务。</p>
      </div>
      <router-link class="btn-secondary text-xs" to="/">返回首页</router-link>
    </header>

    <article class="glass-panel space-y-4">
      <p v-if="!snapshot" class="text-sm text-slate-500">暂无历史任务，请返回首页发送一次对话。</p>
      <div v-else class="space-y-3">
        <div class="flex flex-wrap items-center justify-between text-sm text-slate-700">
          <span class="font-semibold">{{ snapshot.title }}</span>
          <span class="status-pill">{{ snapshot.statusText }}</span>
        </div>
        <p class="text-xs text-slate-500">任务 ID：{{ snapshot.id }} · 上次更新：{{ snapshot.updatedAt }}</p>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-600">
          <p>知识点：{{ snapshot.knowledgeCount }} 条 ｜ 测验题目：{{ snapshot.quizCount }} 题</p>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700 space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-semibold text-slate-700">对话内容</span>
            <button class="btn-ghost" type="button" @click="clearHistory">删除记录</button>
          </div>
          <div v-if="conversation.length" class="max-h-[400px] space-y-2 overflow-y-auto pr-1">
            <div
              v-for="msg in conversation"
              :key="msg.id"
              class="message-row"
              :class="msg.role === 'user' ? 'message-row--user' : ''"
            >
              <div class="message-avatar">{{ msg.role === 'user' ? '我' : '助' }}</div>
              <div
                class="message-bubble"
                :class="msg.role === 'user' ? 'message-bubble--user' : msg.kind === 'status' ? 'message-bubble--system' : 'message-bubble--assistant'"
                v-html="formatMessageText(msg.text)"
              />
            </div>
          </div>
          <p v-else class="text-slate-400 text-xs">暂无对话记录。</p>
        </div>
        <div class="flex gap-2">
          <router-link class="btn-primary text-xs" :to="{ name: 'home' }">回到主页</router-link>
          <router-link
            v-if="snapshot.id"
            class="btn-secondary text-xs"
            :to="{ name: 'print', query: { jobId: snapshot.id } }"
          >
            打印讲义
          </router-link>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { PrestudyJobTicket, PrestudyResponse } from "../types";
import { formatRelativeTime } from "../utils/knowledge";

interface ChatMessage {
  id: string;
  role: "user" | "system";
  text: string;
  kind?: string;
  created_at?: number;
}

const STORAGE_KEY = "classweaver:last-prestudy";
const CONVERSATION_STORAGE_KEY = "classweaver:last-conversation";

const snapshot = computed(() => {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const payload = JSON.parse(raw) as { ticket?: PrestudyJobTicket | null; result?: PrestudyResponse | null; updatedAt?: number };
    const job = payload.result;
    if (!job) return null;
    return {
      id: job.id,
      title: job.lesson_plan?.title || "未命名课程",
      statusText: statusText(job.status),
      knowledgeCount: job.final_json?.knowledge_points?.length ?? 0,
      quizCount: (job.final_json?.quiz?.items as unknown[])?.length ?? 0,
      updatedAt: payload.updatedAt ? formatRelativeTime(new Date(payload.updatedAt).toString()) : "刚刚",
    };
  } catch (error) {
    console.warn("读取历史记录失败", error);
    return null;
  }
});

const conversation = computed<ChatMessage[]>(() => {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(CONVERSATION_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ChatMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
});

function clearHistory() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
  location.reload();
}

function formatMessageText(text: string) {
  return text.replace(/\\n/g, "<br>");
}

function statusText(value?: string): string {
  const map: Record<string, string> = {
    queued: "排队中",
    pending: "待处理",
    processing: "进行中",
    completed: "已完成",
    completed_with_fallback: "已完成（兜底）",
    failed: "已失败",
  };
  if (!value) return "未开始";
  return map[value] ?? value;
}
</script>
