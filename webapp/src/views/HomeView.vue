<template>
  <div class="space-y-8">
    <section class="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
      <article class="glass-panel space-y-5">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.45em] text-slate-500">流程总览</p>
            <h1 class="text-3xl font-semibold text-slate-900">ClassWeaver 学习编排</h1>
          </div>
        </header>
          <div class="rounded-2xl border border-emerald-100 bg-emerald-50/80 p-4 text-sm text-emerald-900 shadow-sm">
            <p class="font-semibold text-emerald-900">系统提示</p>
            <p class="text-emerald-700/90">在这里补充知识点、上传资料或直接发文本生成课程/测验，状态会自动同步。</p>
          </div>
        <div class="grid gap-3 md:grid-cols-2">
          <article
            v-for="stage in pipelineStages"
            :key="stage.id"
            class="relative overflow-hidden rounded-2xl border bg-white/90 p-4 shadow-sm transition"
            :class="stagePillClass(stage.state)"
          >
            <div
              v-if="stage.state === 'running'"
              class="pointer-events-none absolute inset-0 bg-gradient-to-br from-emerald-50/80 via-emerald-50/30 to-transparent"
            />
            <div class="flex items-center justify-between text-xs font-semibold tracking-[0.3em] text-slate-500">
              <span>{{ stage.label }}</span>
              <span
                class="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-[0.25em]"
                :class="stageStateClass(stage.state)"
              >
                {{ stageStateLabel(stage.state) }}
              </span>
            </div>
            <p v-if="stage.hint" class="text-[11px] tracking-[0.2em] text-slate-400">{{ stage.hint }}</p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <p class="text-base font-semibold text-slate-900">{{ stage.title }}</p>
              <span v-if="stage.meta" class="text-xs text-slate-400">{{ stage.meta }}</span>
            </div>
            <p class="text-sm text-slate-600">{{ stage.summary }}</p>
          </article>
        </div>
      </article>

      <article class="glass-panel space-y-4">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">任务状态</p>
            <h2 class="text-xl font-semibold text-slate-900">{{ jobTitle }}</h2>
            <p class="text-xs text-slate-500">最近同步：{{ lastUpdatedDisplay }}</p>
          </div>
        </header>
        <p class="text-sm text-slate-500">{{ taskStatusSummary }}</p>
        <div class="space-y-3">
          <article
            v-for="agent in agentProgress"
            :key="agent.id"
            class="rounded-2xl border border-white/80 bg-white/80 p-3 shadow-sm"
          >
            <div class="flex items-center justify-between text-sm font-semibold text-slate-800">
              <span>{{ agent.label }}</span>
              <span
                class="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-[0.2em]"
                :class="stageStateClass(agent.state)"
              >
                {{ stageStateLabel(agent.state) }}
              </span>
            </div>
            <div class="mt-1 flex items-center justify-between text-xs text-slate-500">
              <span>{{ agent.detail }}</span>
              <span class="font-semibold text-slate-700">{{ agent.value }}</span>
            </div>
            <div class="mt-2 h-1.5 rounded-full bg-slate-200">
              <div class="h-full rounded-full bg-slate-900 transition-all" :style="{ width: `${agent.progress}%` }" />
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ agent.note }}</p>
          </article>
        </div>
        <footer class="flex flex-wrap items-center justify-between text-xs text-slate-500">
          <span>上次同步：{{ lastUpdatedDisplay }}</span>
          <span v-if="statusMessage" class="text-emerald-600">{{ statusMessage }}</span>
        </footer>
      </article>
    </section>

    <section class="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
      <article class="glass-panel space-y-5">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">对话工作区</p>
            <h2 class="text-xl font-semibold text-slate-900">与学习助手协作</h2>
            <p class="text-xs text-slate-500">可直接聊课程意图，也可切换知识库或附加文件，生成提纲、测验与行动建议。</p>
          </div>
          <span class="status-pill">{{ jobReady ? '随时可用' : '等待课程任务' }}</span>
        </header>
        <div class="space-y-3 rounded-3xl border border-slate-100 bg-slate-50 p-4">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-semibold text-slate-700">对话记录</span>
            <div class="flex items-center gap-2">
              <button class="btn-ghost" type="button" @click="viewHistory">查看历史记录</button>
              <button class="btn-ghost" type="button" @click="startNewConversation">新建对话</button>
            </div>
          </div>
          <div class="max-h-[360px] min-h-[180px] space-y-4 overflow-y-auto pr-1">
            <div
              v-for="message in conversation"
              :key="message.id"
              class="message-row"
              :class="message.role === 'user' ? 'message-row--user' : ''"
            >
              <div class="message-avatar">{{ message.role === 'user' ? '我' : '助' }}</div>
              <div
                class="message-bubble"
                :class="
                  message.role === 'user'
                    ? 'message-bubble--user'
                    : message.kind === 'status'
                      ? 'message-bubble--system'
                      : 'message-bubble--assistant'
                "
                v-html="formatMessageText(message.text)"
              />
            </div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3 text-xs text-slate-600">
          <label class="btn-secondary !px-3 !py-1 text-xs">
            附加文件
            <input
              class="sr-only"
              type="file"
              accept=".ppt,.pptx,.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
              @change="onChatFileChange"
            />
          </label>
          <span v-if="chatFile" class="text-slate-600">已选择 {{ chatFile.name }}</span>
          <select
            v-model="selectedKnowledgeBase"
            class="rounded-2xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 focus:border-slate-400"
          >
            <option v-for="base in knowledgeBases" :key="base.id" :value="base.id">{{ base.name }}</option>
          </select>
          <span class="text-slate-400">·</span>
          <span class="text-slate-500">默认不挂载知识库，可随时切换</span>
        </div>

        <form class="space-y-3" @submit.prevent="handleChatSubmit">
          <textarea
            v-model="chatInput"
            class="min-h-[200px] w-full resize-none rounded-3xl border border-slate-200 bg-white/90 p-4 text-sm text-slate-800 outline-none focus:border-slate-500"
            :placeholder="chatMode === 'pipeline' ? '告诉我课程提纲、补充信息或希望改进的环节…' : '输入需要在知识库中检索的问题…'"
          />
          <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span class="font-semibold text-slate-600">使用知识库</span>
            <template v-if="activeDocNames.length">
              <span
                v-for="name in activeDocNames"
                :key="name"
                class="inline-flex items-center rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-medium text-slate-600"
              >
                {{ name }}
              </span>
            </template>
            <span v-else class="text-slate-400">未选择（默认无知识库）</span>
          </div>
          <div class="flex flex-wrap items-center justify-end gap-3">
            <button class="btn-secondary" type="button" :disabled="sendingMessage" @click="openKnowledgeView">管理知识库</button>
            <button class="btn-secondary" type="button" :disabled="sendingMessage" @click="clearChatInput">清空</button>
            <button class="btn-primary" type="submit" :disabled="sendingMessage">
              {{ sendingMessage ? '发送中...' : '发送到多智能体' }}
            </button>
          </div>
          <p v-if="chatError" class="text-sm text-rose-600">{{ chatError }}</p>
        </form>

      </article>

      <article class="glass-panel space-y-5" v-if="job">
        <header class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">课程总览</p>
            <h2 class="text-2xl font-semibold text-slate-900">{{ jobTitle }}</h2>
          </div>
          <button class="btn-secondary text-xs" type="button" @click="openPrintable()">打印讲义</button>
        </header>
        <section class="space-y-3">
          <h3 class="text-sm font-semibold text-slate-700">重点知识</h3>
          <ul class="space-y-2 max-h-64 overflow-y-auto pr-1">
            <li
              v-for="point in knowledgeHighlights"
              :key="point.key"
              class="rounded-2xl border border-white/60 bg-white/80 px-4 py-3 text-sm text-slate-700"
            >
              <p class="font-semibold text-slate-900">{{ point.title }}</p>
              <p class="text-xs text-slate-500">{{ point.summary }}</p>
            </li>
            <li v-if="!knowledgeHighlights.length" class="text-xs text-slate-500">等待 Planner 输出知识点…</li>
          </ul>
        </section>
        <section class="space-y-3">
          <h3 class="text-sm font-semibold text-slate-700">测验预览</h3>
          <ul class="space-y-2 max-h-[420px] overflow-y-auto pr-1">
            <li v-for="quiz in quizShowcase" :key="quiz.id" class="rounded-2xl border border-white/60 bg-white/80 px-4 py-3">
              <p class="text-sm font-semibold text-slate-900">{{ quiz.question }}</p>
              <p class="text-xs text-slate-500">难度：{{ difficultyLabel(quiz.difficulty) }}</p>
            </li>
            <li v-if="!quizShowcase.length" class="text-xs text-slate-500">Rewriter 正在准备测验题目…</li>
          </ul>
        </section>
        <section class="space-y-3">
          <h3 class="text-sm font-semibold text-slate-700">知识连接（MCP）</h3>
          <p class="text-xs text-slate-500">将外部数据源通过 MCP 暴露给 ClassWeaver，可在多智能体协作时精准引用。</p>
          <div class="grid gap-2 sm:grid-cols-2">
            <input v-model="mcpProfile.endpoint" class="rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400" type="text" placeholder="MCP 地址 (https://example.com)" />
            <input v-model="mcpProfile.namespace" class="rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400" type="text" placeholder="命名空间 / Provider" />
            <input v-model="mcpProfile.token" class="rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400" type="password" placeholder="API Token (可选)" />
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button class="btn-secondary text-xs" type="button" @click="saveMcpProfile">保存 MCP 配置</button>
            <button class="btn-ghost text-xs" type="button" @click="showMcpModal = true">查看接入指引</button>
          </div>
          <p v-if="mcpStatusMessage" class="text-xs text-emerald-600">{{ mcpStatusMessage }}</p>
        </section>
      </article>
    </section>

    <section v-if="job" class="grid gap-6 xl:grid-cols-2">
      <article class="glass-panel space-y-5">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">行动指南</p>
            <h2 class="text-xl font-semibold text-slate-900">下一步怎么做？</h2>
          </div>
          <button class="btn-secondary text-xs" type="button" :disabled="isLoadingRecommendations" @click="loadRecommendations()">
            {{ isLoadingRecommendations ? '刷新中...' : '刷新推荐' }}
          </button>
        </header>
        <p class="text-sm text-slate-500">先教学，再测验，最后把真实行动写回教学方案。</p>
        <div class="flex flex-col gap-4 lg:flex-row">
          <article class="flex-1 rounded-3xl border border-white/80 bg-white/85 p-4 shadow-sm space-y-3 flex flex-col">
            <header class="flex items-center justify-between text-sm font-semibold text-slate-800">
              <span>教学知识点</span>
              <span class="text-xs text-slate-500">{{ knowledgePointCount ? `${knowledgePointCount} 个重点` : '等待 Planner' }}</span>
            </header>
            <p class="text-sm text-slate-600">结合知识点走一个教学节奏，完成后记得更新教学方案状态。</p>
            <ul class="space-y-2 text-xs text-slate-600 max-h-[420px] overflow-y-auto pr-1 flex-1">
              <li
                v-for="point in knowledgeHighlights.slice(0, 5)"
                :key="point.key"
                class="rounded-2xl border border-white/60 bg-white/90 px-3 py-2"
              >
                <p class="font-semibold text-slate-900">{{ point.title }}</p>
                <p>{{ point.summary }}</p>
              </li>
              <li v-if="!knowledgeHighlights.length" class="text-xs text-slate-400">等待 Planner 输出知识点…</li>
            </ul>
            <div class="mt-auto flex flex-wrap gap-2 pt-1">
              <button class="btn-primary text-xs" type="button" @click="showKnowledgeModal = true">展开全部知识点</button>
              <button class="btn-ghost text-xs" type="button" @click="openPrintable()">打印讲义</button>
            </div>
          </article>
          <article class="flex-1 rounded-3xl border border-white/80 bg-white/85 p-4 shadow-sm space-y-3 flex flex-col">
            <header class="flex items-center justify-between text-sm font-semibold text-slate-800">
              <span>课堂测验</span>
              <span class="text-xs text-slate-500">{{ quizCount ? `${quizCount} 道题` : '准备中' }}</span>
            </header>
            <p class="text-sm text-slate-600">随时发起一次测验，了解掌握情况，再决定要不要复教或巩固。</p>
            <ul class="space-y-2 text-xs text-slate-600 max-h-[420px] overflow-y-auto pr-1 flex-1">
              <li
                v-for="quiz in quizShowcase.slice(0, 5)"
                :key="quiz.id"
                class="rounded-2xl border border-white/60 bg-white/90 px-3 py-2"
              >
                <p class="font-semibold text-slate-900">{{ quiz.question }}</p>
                <p>难度：{{ difficultyLabel(quiz.difficulty) }}</p>
              </li>
              <li v-if="!quizShowcase.length" class="text-xs text-slate-400">Rewriter 正在准备测验题目…</li>
            </ul>
            <div class="mt-auto flex flex-wrap items-center gap-2 pt-1">
              <button class="btn-primary text-xs" type="button" :disabled="isLaunchingQuiz" @click="startQuizSession()">
                {{ isLaunchingQuiz ? '进入中...' : '发起测验' }}
              </button>
              <p v-if="quizError" class="text-xs text-rose-600">{{ quizError }}</p>
            </div>
          </article>
        </div>
        <article class="rounded-3xl border border-white/80 bg-white/85 p-4 shadow-sm space-y-3">
          <header class="flex items-center justify-between text-sm font-semibold text-slate-800">
            <span>添加行动</span>
            <span class="text-xs text-slate-500">{{ topRecommendations.length ? `${topRecommendations.length} 条推荐` : '等待 AI 建议' }}</span>
          </header>
          <p class="text-sm text-slate-600">结合 AI 给出的提醒，把课堂任务写回教学方案或直接触发陪学助教。</p>
          <div v-if="topRecommendations.length" class="space-y-2 text-xs text-slate-600 max-h-[360px] overflow-y-auto pr-1">
            <article
              v-for="action in topRecommendations"
              :key="action.id || action.title"
              class="rounded-2xl border border-white/70 bg-white/90 p-3"
            >
              <p class="font-semibold text-slate-900">{{ action.title }}</p>
              <p>{{ action.summary }}</p>
            </article>
          </div>
          <p v-else class="text-xs text-slate-400">暂无推荐，点击上方“刷新推荐”即可获取新的行动。</p>
          <div class="flex flex-wrap gap-2">
            <button class="btn-secondary text-xs" type="button" @click="openEventModal()">记录教学反馈</button>
            <button class="btn-ghost text-xs" type="button" @click="openCoachMode()">进入陪学助教</button>
          </div>
        </article>
      </article>
      <article class="glass-panel space-y-4">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">教学方案</p>
            <h2 class="text-xl font-semibold text-slate-900">教学方案时间线</h2>
          </div>
          <div class="flex flex-wrap gap-2">
            <button class="btn-secondary text-xs" type="button" @click="openCoachMode()">进入陪学助教</button>
            <button class="btn-ghost text-xs" type="button" @click="openEventModal()">记录教学事件</button>
          </div>
        </header>
        <div v-if="timelineLoading" class="text-sm text-slate-500">时间线加载中...</div>
        <ul v-else class="space-y-3 max-h-[360px] overflow-y-auto pr-1">
          <li
            v-for="event in timelineEvents"
            :key="event.id"
            class="rounded-2xl border border-white/70 bg-white/80 p-4"
          >
            <div class="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-500">
              <span>{{ formatEventType(event.event_type) }}</span>
              <span>{{ formatEventTime(event.occurred_at) }}</span>
            </div>
            <p class="text-base font-semibold text-slate-900">
              {{ event.payload?.title || event.payload?.note || '教学事件' }}
            </p>
            <p class="text-xs text-slate-500">
              {{ event.payload?.summary || '系统自动记录' }}
            </p>
          </li>
          <li v-if="!timelineEvents.length" class="text-xs text-slate-500">暂无事件，执行行动后会自动补齐。</li>
        </ul>
      </article>
    </section>

    <div v-if="showKnowledgeModal" class="action-modal">
      <div class="action-modal__backdrop" @click="showKnowledgeModal = false" />
      <div class="action-modal__panel space-y-3">
        <header>
          <h3 class="text-lg font-semibold text-slate-900">知识点清单</h3>
          <p class="text-sm text-slate-500">当前课程共 {{ knowledgeModalPoints.length }} 个知识点。</p>
        </header>
        <ul class="max-h-[420px] space-y-2 overflow-y-auto">
          <li
            v-for="point in knowledgeModalPoints"
            :key="point.id || point.title"
            class="rounded-2xl border border-slate-100 bg-white/90 px-4 py-3 text-sm text-slate-700"
          >
            <p class="font-semibold text-slate-900">{{ point.title || '未命名知识点' }}</p>
            <p class="text-xs text-slate-500">{{ point.summary || '暂无简介' }}</p>
          </li>
        </ul>
        <div class="flex flex-wrap gap-2">
          <button class="btn-primary text-xs" type="button" @click="showKnowledgeModal = false">关闭</button>
          <button class="btn-secondary text-xs" type="button" @click="openPrintable()">打印讲义</button>
        </div>
      </div>
    </div>

    <div v-if="showMcpModal" class="action-modal">
      <div class="action-modal__backdrop" @click="showMcpModal = false" />
      <div class="action-modal__panel space-y-3">
        <header>
          <h3 class="text-lg font-semibold text-slate-900">MCP 接入指引</h3>
          <p class="text-sm text-slate-500">按照以下步骤，把自有服务通过 Model Context Protocol 接入 ClassWeaver。</p>
        </header>
        <ol class="list-decimal space-y-2 pl-5 text-sm text-slate-600">
          <li>在课堂服务端部署 MCP server，暴露 Endpoint（HTTPS）。</li>
          <li>在上方表单填入 Endpoint / Namespace / Token 并保存。</li>
          <li>在后端配置 `PRESTUDY_MCP_ENABLED=true`（或通过环境变量传入）。</li>
          <li>多智能体在执行时会携带该配置，自动调用 MCP 获取资料。</li>
        </ol>
        <p class="text-xs text-slate-500">更多示例可参考官方文档，也可以把服务定义成 JSON schema 提供给 学习助手。</p>
        <button class="btn-secondary text-xs" type="button" @click="showMcpModal = false">我知道了</button>
      </div>
    </div>

    <div v-if="showEventModal" class="action-modal">
      <div class="action-modal__backdrop" @click="closeEventModal" />
      <form class="action-modal__panel" @submit.prevent="submitEvent">
        <header>
          <h3 class="text-lg font-semibold text-slate-900">记录课堂事件</h3>
          <p class="text-sm text-slate-500">填写详细信息方便追踪行动状态。</p>
        </header>
        <div class="grid gap-3">
          <label class="text-xs text-slate-500">
            事件类型
            <select v-model="eventForm.event_type" class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800">
              <option value="note">Note</option>
              <option value="practice">Practice</option>
              <option value="question">Question</option>
              <option value="timeline">Timeline</option>
            </select>
          </label>
          <label class="text-xs text-slate-500">
            执行人
            <input v-model="eventForm.actor" class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800" type="text" />
          </label>
          <label class="text-xs text-slate-500">
            描述
            <textarea
              v-model="eventForm.summary"
              class="mt-1 h-24 w-full resize-none rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800"
              placeholder="发生了什么？"
            ></textarea>
          </label>
          <label class="text-xs text-slate-500">
            action_id（可选）
            <input v-model="eventForm.action_id" class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800" type="text" />
          </label>
          <label class="text-xs text-slate-500">
            状态
            <select v-model="eventForm.status" class="mt-1 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800">
              <option value="pending">待执行</option>
              <option value="running">进行中</option>
              <option value="completed">已完成</option>
            </select>
          </label>
        </div>
        <div class="flex flex-wrap gap-3">
          <button class="btn-primary text-sm" type="submit" :disabled="eventSaving">{{ eventSaving ? '写入中...' : '写入事件' }}</button>
          <button class="btn-secondary text-sm" type="button" @click="closeEventModal">取消</button>
          <p v-if="eventError" class="text-sm text-rose-600">{{ eventError }}</p>
        </div>
      </form>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  createPrestudyFromPpt,
  createPrestudyFromText,
  getLessonTimeline,
  getPrestudyJob,
  getPrestudyJobStatus,
  listKnowledgeDocuments,
  postLessonEvent,
  searchKnowledge,
  startQuiz,
  triggerRecommendations,
} from "../services/api";
import type { LessonEventEntry, PrestudyJobTicket, PrestudyResponse, RecommendationSuggestion, QuizQuestion } from "../types";
import {
  DEFAULT_KNOWLEDGE_BASE,
  KNOWLEDGE_BASE_SELECTION_KEY,
  KNOWLEDGE_BASE_STORAGE_KEY,
  type KnowledgeBaseItem,
  mapDocumentToKnowledgeBase,
  normalizeKnowledgeBaseList,
  resolveKnowledgeBaseName,
} from "../utils/knowledge";
import {
  type ActionStatusEntry,
  type ActionStatusState,
  clearActionStatuses,
  getActionStatusMap,
  setActionStatus,
} from "../utils/actions";

const STORAGE_KEY = "classweaver:last-prestudy";
const CONVERSATION_STORAGE_KEY = "classweaver:last-conversation";
const QUIZ_SESSION_STORAGE_KEY = "classweaver:last-quiz-session";
const MAX_CONVERSATION_LENGTH = 60;

interface ChatMessage {
  id: string;
  role: "user" | "system";
  text: string;
  kind?: "status" | "job" | "knowledge";
  created_at: number;
}

const router = useRouter();

const isGenerating = ref(false);
const generationSource = ref<"text" | "ppt" | null>(null);
const generationError = ref("");
const statusMessage = ref("");

const job = ref<PrestudyResponse | null>(null);
const jobTicket = ref<PrestudyJobTicket | null>(null);
const persistedTimestamp = ref<number | null>(null);
const jobRestoreError = ref("");
const announcedJobIds = ref<string[]>([]);
const ANNOUNCE_STORAGE_KEY = "classweaver:announced-jobs";

const recommendations = ref<RecommendationSuggestion[]>([]);
const topRecommendations = computed(() => recommendations.value);
const isLoadingRecommendations = ref(false);
const recommendationError = ref("");

const timelineEvents = ref<LessonEventEntry[]>([]);
const timelineLoading = ref(false);
const timelineError = ref("");
const pollTimer = ref<number | null>(null);

const knowledgeBases = ref<KnowledgeBaseItem[]>([DEFAULT_KNOWLEDGE_BASE]);
const selectedKnowledgeBase = ref<string>(DEFAULT_KNOWLEDGE_BASE.id);
const knowledgeSyncing = ref(false);
const knowledgeStatus = ref("尚未同步");
const showKnowledgeModal = ref(false);
const showMcpModal = ref(false);
const mcpStatusMessage = ref("");
const MCP_PROFILE_STORAGE_KEY = "classweaver:mcp-profile";
const mcpProfile = reactive({
  endpoint: "",
  namespace: "",
  token: "",
});
const selectedKnowledgeBaseName = computed(() =>
  resolveKnowledgeBaseName(selectedKnowledgeBase.value, knowledgeBases.value, DEFAULT_KNOWLEDGE_BASE.name),
);

const actionStatuses = ref<Record<string, ActionStatusEntry>>({});
const isLaunchingQuiz = ref(false);
const quizError = ref("");

const showEventModal = ref(false);
const eventSaving = ref(false);
const eventError = ref("");
const eventForm = reactive({
  event_type: "note",
  actor: "学习助手",
  summary: "",
  action_id: "",
  status: "running" as ActionStatusState,
});
const chatModes = [
  { id: "pipeline", label: "多智能体" },
  { id: "knowledge", label: "知识检索" },
] as const;
const chatMode = ref<(typeof chatModes)[number]["id"]>("pipeline");
const chatInput = ref("");
const chatFile = ref<File | null>(null);
const conversation = ref<ChatMessage[]>([
  {
    id: "welcome",
    role: "system",
    text: "欢迎使用 ClassWeaver 学习助手，告诉我课程目标、附加资料，或直接向知识库提问。",
    kind: "status",
    created_at: Date.now(),
  },
]);
const sendingMessage = ref(false);
const chatError = ref("");
const jobReady = computed(() => Boolean(job.value && job.value.status !== "failed"));
const jobTitle = computed(() => job.value?.lesson_plan?.title || "未命名课程");
const knowledgePointCount = computed(() => toArray(job.value?.final_json?.knowledge_points).length);
const quizCount = computed(() => {
  const quizBlock = job.value?.final_json?.quiz as Record<string, unknown> | undefined;
  const items = Array.isArray(quizBlock?.items) ? (quizBlock?.items as unknown[]) : [];
  return items.length;
});
const practiceCount = computed(() => {
  const tutorBlock = job.value?.final_json?.tutor as Record<string, unknown> | undefined;
  const practice = Array.isArray(tutorBlock?.practice) ? (tutorBlock?.practice as unknown[]) : [];
  return practice.length;
});
const knowledgeModalPoints = computed(() => toArray(job.value?.final_json?.knowledge_points));

const attachedDocIds = computed(() => {
  const ids = new Set<string>();
  if (selectedKnowledgeBase.value && selectedKnowledgeBase.value !== DEFAULT_KNOWLEDGE_BASE.id) {
    ids.add(selectedKnowledgeBase.value);
  }
  return Array.from(ids);
});

const activeDocNames = computed(() => attachedDocIds.value.map((id) => docChipLabel(id)).filter(Boolean));
const lastUpdatedDisplay = computed(() => {
  if (!persistedTimestamp.value) return "刚刚";
  return formatRelativeTime(persistedTimestamp.value);
});

const jobStatusLabel = computed(() => {
  if (job.value) return statusText(job.value.status);
  if (jobTicket.value) return statusText(jobTicket.value.status);
  return "未开始";
});

const pipelineStages = computed(() => buildPipelineStages());
const pipelineProgress = computed(() => {
  const stages = pipelineStages.value;
  if (!stages.length) return 0;
  const weight: Record<StageState, number> = { completed: 1, running: 0.6, pending: 0.2 };
  const total = stages.reduce((sum, stage) => sum + (weight[stage.state] ?? 0), 0);
  return Math.round((total / stages.length) * 100);
});
const pipelineSummary = computed(() => {
  if (!job.value && !jobTicket.value) {
    return "未挂载知识库，直接输入课程意图或选择上方知识库即可开始编排。";
  }
  if (job.value?.status === "failed") {
    return "任务失败，请调整输入后重试。";
  }
  if (job.value?.status && ["completed", "completed_with_fallback"].includes(job.value.status)) {
    return "课程已生成，可查看课程总览或执行行动指南。";
  }
  if (jobTicket.value && !job.value) {
    return "学习助手已接单，正在排队或执行。";
  }
  return "多智能体协作进行中…";
});



const pipelineStatusLabel = computed(() => {
  if (job.value?.status && ["completed", "completed_with_fallback"].includes(job.value.status)) {
    return "已完成";
  }
  if (jobTicket.value) {
    return "进行中";
  }
  return "未开始";
});


const agentProgress = computed(() => {
  const plannerState: StageState = job.value ? "completed" : jobTicket.value ? "running" : "pending";
  const rewriterState: StageState = job.value
    ? quizCount.value
      ? "completed"
      : "running"
    : jobTicket.value
      ? "pending"
      : "pending";
  const tutorState: StageState = job.value
    ? practiceCount.value
      ? "completed"
      : "running"
    : jobTicket.value
      ? "pending"
      : "pending";
  return [
    {
      id: "planner",
      label: "规划器",
      value: `${knowledgePointCount.value} 个知识点`,
      detail: "知识整理 + 目标拆解",
      note: job.value ? "路径已展开，可按节点教学" : "等待输入课程信息",
      progress: job.value ? 100 : jobTicket.value ? 40 : 10,
      state: plannerState,
    },
    {
      id: "rewriter",
      label: "测验工坊",
      value: `${quizCount.value} 题`,
      detail: "题目与解析持续产出",
      note: job.value ? "题库已就绪，可随时测验" : "提交任务后会自动生成题目",
      progress: job.value ? Math.min(100, Math.max(30, quizCount.value * 10)) : jobTicket.value ? 50 : 10,
      state: rewriterState,
    },
    {
      id: "tutor",
      label: "辅导助手",
      value: `${practiceCount.value} 条练习`,
      detail: "练习提示与推荐",
      note: job.value ? "行动建议已回传到行动指南" : "等待多智能体协同输出",
      progress: job.value ? Math.min(100, Math.max(40, practiceCount.value * 15)) : jobTicket.value ? 30 : 10,
      state: tutorState,
    },
  ];
});

const taskStatusSummary = computed(() => {
  if (statusMessage.value) return statusMessage.value;
  if (jobRestoreError.value) return `恢复任务时出现问题：${jobRestoreError.value}`;
  if (job.value?.status === "failed") return "任务失败，请重新发送或稍后再试。";
  if (jobTicket.value) {
    const pendingAgents = agentProgress.value.filter((agent) => agent.state !== "completed").length;
    return pendingAgents
      ? `多智能体执行中，还有 ${pendingAgents} 个环节等待完成。`
      : "多智能体执行中，即将同步课程数据。";
  }
  return `准备就绪，围绕「${selectedKnowledgeBaseName.value}」开始和学习助手对话即可生成新任务。`;
});



const knowledgeHighlights = computed(() =>
  toArray(job.value?.final_json?.knowledge_points).slice(0, 4).map((kp, index) => ({
    key: kp.id || index,
    title: kp.title || `知识点 ${index + 1}`,
    summary: kp.summary || "等待补充内容…",
  })),
);

const quizShowcase = computed(() => {
  const quizBlock = job.value?.final_json?.quiz as { items?: QuizQuestion[] } | undefined;
  const items = Array.isArray(quizBlock?.items) ? (quizBlock?.items as QuizQuestion[]) : [];
  return items.slice(0, 5);
});
watch(
  () => job.value?.id,
  (jobId) => {
    if (!jobId) {
      actionStatuses.value = {};
      return;
    }
    actionStatuses.value = getActionStatusMap(jobId);
  },
);

watch(
  [knowledgeBases, selectedKnowledgeBase],
  () => {
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(KNOWLEDGE_BASE_STORAGE_KEY, JSON.stringify(knowledgeBases.value));
    window.sessionStorage.setItem(KNOWLEDGE_BASE_SELECTION_KEY, selectedKnowledgeBase.value);
  },
  { deep: true },
);

onMounted(() => {
  restoreConversation();
  restoreAnnouncedJobs();
  restoreKnowledgeState();
  syncKnowledgeBases();
  hydrateFromStorage();
  loadMcpProfile();
  persistConversation();
});

onUnmounted(() => {
  stopPolling();
});
function formatRelativeTime(value?: number | string | null): string {
  if (!value) return "刚刚";
  const date = typeof value === "number" ? new Date(value) : new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  const diff = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return "刚刚";
  if (diff < hour) return `${Math.round(diff / minute)} 分钟前`;
  if (diff < day) return `${Math.round(diff / hour)} 小时前`;
  return `${Math.round(diff / day)} 天前`;
}

function toArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function statusText(value?: string): string {
  const map: Record<string, string> = {
    queued: "已排队",
    pending: "已创建",
    processing: "执行中",
    completed: "完成",
    completed_with_fallback: "完成（降级）",
    failed: "失败",
  };
  if (!value) return "未开始";
  return map[value] ?? value;
}

function docChipLabel(docId: string): string {
  return resolveKnowledgeBaseName(docId, knowledgeBases.value, `Doc ${docId.slice(0, 4)}`);
}

function stagePillClass(state: StageState) {
  if (state === "running") return "border-emerald-200 bg-emerald-50/80 shadow-emerald-100/70";
  if (state === "completed") return "border-emerald-200 bg-emerald-50/60";
  return "border-slate-100 bg-white/90";
}

function stageStateLabel(state: StageState) {
  const map: Record<StageState, string> = {
    pending: "未开始",
    running: "进行中",
    completed: "已完成",
  };
  return map[state];
}

function stageStateClass(state: StageState) {
  if (state === "running") return "border-blue-200 bg-blue-50 text-blue-700";
  if (state === "completed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-100 text-slate-500";
}

function clearChatInput() {
  chatInput.value = "";
  chatFile.value = null;
  chatError.value = "";
}

function startNewConversation() {
  conversation.value = [
    {
      id: `welcome-${Date.now()}`,
      role: "system",
      text: "已开启新对话，请告诉我课程目标或要使用的资料。",
      kind: "status",
      created_at: Date.now(),
    },
  ];
  persistConversation();
}

function viewHistory() {
  router.push({ name: "history" });
}

function onChatFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  chatFile.value = target.files?.[0] ?? null;
}
async function handleChatSubmit() {
  if (!chatInput.value.trim() && !chatFile.value) {
    chatError.value = "请输入内容或上传文件";
    return;
  }
  chatError.value = "";
  sendingMessage.value = true;
  try {
    if (chatMode.value === "knowledge") {
      await handleKnowledgeQuery(chatInput.value.trim());
      chatInput.value = "";
    } else if (chatFile.value) {
      await handleGenerateFromPpt(chatFile.value);
      chatFile.value = null;
      chatInput.value = "";
    } else {
      await handleGenerateFromText(chatInput.value.trim());
      chatInput.value = "";
    }
  } finally {
    sendingMessage.value = false;
  }
}

async function handleKnowledgeQuery(query: string) {
  if (!query.trim()) {
    chatError.value = "请输入关键词以追问知识库";
    return;
  }
  appendMessage("user", query);
  try {
    const payload = { query: query.trim(), top_k: 4, doc_ids: attachedDocIds.value };
    const resp = await searchKnowledge(payload);
    if (!resp.results.length) {
      appendMessage("system", "知识库中没有找到相关内容。", "knowledge");
      return;
    }
    const rendered = resp.results
      .map((item, index) => {
        const ref = item.refs?.[0];
        const doc = ref?.doc_id ? resolveKnowledgeBaseName(ref.doc_id, knowledgeBases.value) : "未知文档";
        return `<strong>${index + 1}. ${doc}</strong> · ${item.text}`;
      })
      .join("<br>");
    appendMessage("system", rendered, "knowledge");
  } catch (error) {
    chatError.value = (error as Error).message;
  }
}

async function handleGenerateFromText(content: string) {
  appendMessage("user", content);
  isGenerating.value = true;
  generationSource.value = "text";
  generationError.value = "";
  statusMessage.value = "";
  try {
  const payload: { text: string; doc_ids?: string[]; locale?: string } = { text: content, locale: "zh-CN" };
    if (attachedDocIds.value.length) payload.doc_ids = attachedDocIds.value;
    const ticket = await createPrestudyFromText(payload);
    jobTicket.value = ticket;
    job.value = null;
    persistJobSnapshot(null);
    statusMessage.value = ticket.detail ?? "任务已排队";
    appendMessage("system", ticket.detail ?? "已提交给 Planner，等待结果。", "status");
    beginPolling(ticket.id);
  } catch (error) {
    generationError.value = (error as Error).message;
    chatError.value = generationError.value;
  } finally {
    isGenerating.value = false;
    generationSource.value = null;
  }
}

async function handleGenerateFromPpt(file: File) {
  appendMessage("user", `已上传文件：${file.name}`);
  isGenerating.value = true;
  generationSource.value = "ppt";
  generationError.value = "";
  statusMessage.value = "";
  try {
    const ticket = await createPrestudyFromPpt(file, attachedDocIds.value.length ? attachedDocIds.value : undefined, "zh-CN");
    jobTicket.value = ticket;
    job.value = null;
    persistJobSnapshot(null);
    statusMessage.value = ticket.detail ?? "PPT 上传成功，等待处理";
    appendMessage("system", ticket.detail ?? "已完成 PPT 解析，正在生成。", "status");
    beginPolling(ticket.id);
  } catch (error) {
    generationError.value = (error as Error).message;
    chatError.value = generationError.value;
  } finally {
    isGenerating.value = false;
    generationSource.value = null;
  }
}

function appendMessage(role: ChatMessage["role"], text: string, kind?: ChatMessage["kind"]) {
  conversation.value = [
    ...conversation.value,
    {
      id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      role,
      text,
      kind,
      created_at: Date.now(),
    },
  ].slice(-MAX_CONVERSATION_LENGTH);
  persistConversation();
}

function persistConversation() {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(conversation.value));
}

function restoreConversation() {
  if (typeof window === "undefined") return;
  try {
    const raw = window.localStorage.getItem(CONVERSATION_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as ChatMessage[];
    if (Array.isArray(parsed) && parsed.length) {
      conversation.value = parsed.slice(-MAX_CONVERSATION_LENGTH);
    }
  } catch {
    window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
  }
}

function persistAnnouncedJobs() {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(ANNOUNCE_STORAGE_KEY, JSON.stringify(announcedJobIds.value));
}

function restoreAnnouncedJobs() {
  if (typeof window === "undefined") return;
  try {
    const raw = window.sessionStorage.getItem(ANNOUNCE_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as string[];
    if (Array.isArray(parsed)) {
      announcedJobIds.value = parsed;
    }
  } catch {
    window.sessionStorage.removeItem(ANNOUNCE_STORAGE_KEY);
  }
}
function persistJobSnapshot(result: PrestudyResponse | null) {
  if (typeof window === "undefined") return;
  const payload = { ticket: jobTicket.value, result, updatedAt: Date.now() };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  persistedTimestamp.value = payload.updatedAt;
}

function hydrateFromStorage() {
  if (typeof window === "undefined") return;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const payload = JSON.parse(raw) as { ticket?: PrestudyJobTicket | null; result?: PrestudyResponse | null; updatedAt?: number };
    if (payload.ticket) jobTicket.value = payload.ticket;
    if (payload.result) {
      job.value = payload.result;
      persistedTimestamp.value = payload.updatedAt ?? null;
      afterJobLoaded(payload.result);
    } else if (payload.ticket?.id) {
      beginPolling(payload.ticket.id);
    }
  } catch (error) {
    jobRestoreError.value = (error as Error).message;
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

function afterJobLoaded(detail: PrestudyResponse) {
  actionStatuses.value = getActionStatusMap(detail.id);
  if (!announcedJobIds.value.includes(detail.id)) {
    appendMessage("system", "课程已生成，可查看课程总览或执行行动指南。", "job");
    announcedJobIds.value = [...announcedJobIds.value, detail.id];
    persistAnnouncedJobs();
  }
  if (detail.lesson_plan?.id) {
    refreshTimeline(detail.lesson_plan.id);
  }
  loadRecommendations(detail.id);
}

async function refreshJobManually() {
  if (!jobTicket.value?.id) return;
  await refreshJobStatus(jobTicket.value.id, true);
}

function beginPolling(jobId: string) {
  stopPolling();
  pollTimer.value = window.setInterval(() => refreshJobStatus(jobId), 4000);
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
}

async function refreshJobStatus(jobId: string, forceDetail = false) {
  try {
    const ticket = await getPrestudyJobStatus(jobId);
    jobTicket.value = ticket;
    persistJobSnapshot(job.value ?? null);
    if (forceDetail || ["completed", "completed_with_fallback", "failed"].includes(ticket.status)) {
      stopPolling();
      await loadJobDetail(jobId);
    }
  } catch (error) {
    statusMessage.value = (error as Error).message;
  }
}

async function loadJobDetail(jobId: string) {
  try {
    const detail = await getPrestudyJob(jobId);
    job.value = detail;
    jobTicket.value = { id: detail.id, status: detail.status };
    persistJobSnapshot(detail);
    afterJobLoaded(detail);
  } catch (error) {
    statusMessage.value = (error as Error).message;
  }
}
async function startQuizSession(action?: RecommendationSuggestion) {
  if (!job.value) return;
  isLaunchingQuiz.value = true;
  quizError.value = "";
  try {
    const session = await startQuiz(job.value.id);
    if (!session?.session_id) {
      throw new Error("未获取到测验会话，请稍后重试。");
    }
    if (action?.id) {
      applyActionStatus(action.id, "running", "测验已启动");
    }
    persistQuizSession(session.session_id, job.value.id, session.questions);
    await router.push({
      name: "take",
      query: { sessionId: session.session_id, jobId: job.value.id },
      state: {
        sessionId: session.session_id,
        jobId: job.value.id,
        questions: session.questions,
        sourceAction: action,
      },
    });
  } catch (error) {
    quizError.value = (error as Error).message;
  } finally {
    isLaunchingQuiz.value = false;
  }
}

function persistQuizSession(sessionId: string, jobId: string, questions: QuizQuestion[]) {
  if (typeof window === "undefined") return;
  const payload = { sessionId, jobId, questions, savedAt: Date.now() };
  window.sessionStorage.setItem(QUIZ_SESSION_STORAGE_KEY, JSON.stringify(payload));
}

function openPrintable(action?: RecommendationSuggestion) {
  if (!job.value) return;
  if (action?.id) applyActionStatus(action.id, "completed", "打印资料已打开");
  router.push({
    name: "print",
    query: { jobId: job.value.id },
    state: { printable: job.value.printable },
  });
}

function openCoachMode() {
  if (!job.value) return;
  router.push({ name: "coach", query: { jobId: job.value.id } });
}

function openKnowledgeView() {
  router.push({ name: "knowledge" });
}

function clearJob() {
  const currentId = job.value?.id;
  job.value = null;
  jobTicket.value = null;
  statusMessage.value = "";
  persistedTimestamp.value = null;
  stopPolling();
  clearActionStatuses(currentId ?? null);
  announcedJobIds.value = [];
  persistAnnouncedJobs();
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

async function loadRecommendations(jobId?: string) {
  const id = jobId ?? job.value?.id;
  if (!id) return;
  isLoadingRecommendations.value = true;
  recommendationError.value = "";
  try {
    const task = await triggerRecommendations(id);
    recommendations.value = task.output?.suggestions ?? [];
  } catch (error) {
    recommendationError.value = (error as Error).message;
    recommendations.value = [];
  } finally {
    isLoadingRecommendations.value = false;
  }
}

async function refreshTimeline(planId?: number | string) {
  const targetPlan = planId ?? job.value?.lesson_plan?.id;
  if (!targetPlan) return;
  timelineLoading.value = true;
  timelineError.value = "";
  try {
    const payload = await getLessonTimeline(targetPlan);
    timelineEvents.value = payload.events ?? [];
  } catch (error) {
    timelineError.value = (error as Error).message;
  } finally {
    timelineLoading.value = false;
  }
}

function openEventModal(action?: RecommendationSuggestion) {
  if (action) {
    eventForm.action_id = action.id ?? "";
    eventForm.summary = action.summary ?? "";
    eventForm.status = actionStatusOf(action.id);
  } else {
    eventForm.action_id = "";
    eventForm.summary = "";
    eventForm.status = "running";
  }
  eventForm.actor = "学习助手";
  showEventModal.value = true;
  eventError.value = "";
}

function closeEventModal() {
  showEventModal.value = false;
}

async function submitEvent() {
  if (!job.value?.lesson_plan?.id) {
    eventError.value = "缺少 lesson_plan id";
    return;
  }
  eventSaving.value = true;
  eventError.value = "";
  try {
    await postLessonEvent(job.value.lesson_plan.id, {
      event_type: eventForm.event_type,
      actor: eventForm.actor || "学习助手",
      payload: {
        summary: eventForm.summary,
        action_id: eventForm.action_id || undefined,
        status: eventForm.status,
      },
    });
    await refreshTimeline(job.value.lesson_plan.id);
    if (eventForm.action_id) {
      applyActionStatus(eventForm.action_id, eventForm.status, eventForm.summary);
    }
    showEventModal.value = false;
  } catch (error) {
    eventError.value = (error as Error).message;
  } finally {
    eventSaving.value = false;
  }
}
function actionStatusOf(actionId?: string | null): ActionStatusState {
  if (!actionId || !job.value) return "pending";
  return actionStatuses.value[actionId]?.status ?? "pending";
}

function actionStatusLabel(state: ActionStatusState): string {
  const map: Record<ActionStatusState, string> = {
    pending: "待执行",
    running: "进行中",
    completed: "已记录",
  };
  return map[state];
}

function actionStatusClass(state: ActionStatusState): string {
  if (state === "running") return "bg-blue-100 text-blue-700";
  if (state === "completed") return "bg-emerald-100 text-emerald-700";
  return "bg-slate-100 text-slate-500";
}

function applyActionStatus(actionId: string, state: ActionStatusState, note?: string) {
  if (!job.value) return;
  const entry = setActionStatus(job.value.id, actionId, state, note);
  if (entry) {
    actionStatuses.value = { ...actionStatuses.value, [actionId]: entry };
  }
}

function markActionRunning(action: RecommendationSuggestion) {
  if (!action.id) return;
  applyActionStatus(action.id, "running", action.summary);
}

function markActionCompleted(action: RecommendationSuggestion) {
  if (!action.id) return;
  applyActionStatus(action.id, "completed", action.summary);
}

function stageLabel(stage?: string | null): string {
  const map: Record<string, string> = {
    focus: "聚焦",
    practice: "练习",
    classroom: "课堂",
    resource: "拓展",
    planning: "规划",
  };
  if (!stage) return "阶段";
  return map[stage] ?? stage;
}

function agentLabel(agent?: string | null): string {
  if (!agent) return "学习助手";
  const map: Record<string, string> = {
    planner: "Planner",
    rewriter: "Rewriter",
    tutor: "Tutor",
    coach: "Coach",
  };
  return map[agent] ?? agent;
}

function formatEventType(eventType: string): string {
  const map: Record<string, string> = {
    note: "系统备注",
    practice: "练习",
    question: "问答",
    timeline: "节点",
  };
  return map[eventType] ?? eventType;
}

function formatEventTime(value: string): string {
  try {
    const date = new Date(value);
    return new Intl.DateTimeFormat("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return value;
  }
}

function difficultyLabel(level?: string) {
  const labels: Record<string, string> = {
    easy: "简单",
    medium: "中等",
    hard: "困难",
  };
  return level ? labels[level] ?? level : "未知";
}

type StageState = "pending" | "running" | "completed";

function buildPipelineStages() {
  const statuses: Array<{ id: string; label: string; title: string; summary: string; state: StageState; hint?: string; meta?: string }> = [];
  const attachmentCount = attachedDocIds.value.length;
  const knowledgeState: StageState = knowledgeSyncing.value ? "running" : attachmentCount > 0 ? "completed" : "pending";
  statuses.push({
    id: "knowledge",
    label: "资料准备",
    title: selectedKnowledgeBaseName.value,
    summary:
      attachmentCount > 0
        ? `已关联 ${attachmentCount} 份资料，将用于个性化生成。`
        : "使用默认课堂摘要，可随时上传或切换知识库。",
    state: knowledgeState,
    hint: knowledgeSyncing.value ? "同步中" : "",
    meta: knowledgeStatus.value || "刚同步",
  });

  const plannerState: StageState = job.value ? "completed" : jobTicket.value ? "running" : "pending";
  statuses.push({
    id: "planner",
    label: "课程架构",
    title: plannerState === "completed" ? "课程框架已生成" : "等待输入",
    summary:
      plannerState === "completed"
        ? `${knowledgePointCount.value} 个知识点准备完毕。`
        : "发送课程提纲后 Planner 会先拆解知识点。",
    state: plannerState,
    meta: knowledgePointCount.value ? `${knowledgePointCount.value} 个节点` : "",
  });

  const rewriterState: StageState = job.value
    ? quizCount.value
      ? "completed"
      : "running"
    : jobTicket.value
      ? "pending"
      : "pending";
  statuses.push({
    id: "rewriter",
    label: "测验生成",
    title: quizCount.value ? `${quizCount.value} 道测验` : "等待题目",
    summary: quizCount.value ? "可直接发起测验或发送给学生练习。" : "Rewriter 会持续补充题目和解析。",
    state: rewriterState,
    meta: quizCount.value ? `${quizCount.value} 题` : "",
  });

  const tutorState: StageState = job.value
    ? practiceCount.value
      ? "completed"
      : "running"
    : jobTicket.value
      ? "pending"
      : "pending";
  statuses.push({
    id: "tutor",
    label: "课堂互动",
    title: practiceCount.value ? `${practiceCount.value} 条行动建议` : "等待互动提示",
    summary: practiceCount.value ? "练习与 Follow-up 已同步至行动指南。" : "完成课程后会自动生成课堂互动建议。",
    state: tutorState,
    meta: practiceCount.value ? `${practiceCount.value} 条` : "",
  });

  return statuses;
}

function formatMessageText(text: string) {
  return text.replace(/\n/g, "<br>");
}

function restoreKnowledgeState() {
  if (typeof window === "undefined") return;
  try {
    const storedList = window.sessionStorage.getItem(KNOWLEDGE_BASE_STORAGE_KEY);
    if (storedList) {
      const parsed = JSON.parse(storedList) as KnowledgeBaseItem[];
      if (Array.isArray(parsed) && parsed.length) {
        knowledgeBases.value = normalizeKnowledgeBaseList(parsed);
      }
    }
    const storedSelected = window.sessionStorage.getItem(KNOWLEDGE_BASE_SELECTION_KEY);
    if (storedSelected && knowledgeBases.value.some((base) => base.id === storedSelected)) {
      selectedKnowledgeBase.value = storedSelected;
    }
  } catch {
    window.sessionStorage.removeItem(KNOWLEDGE_BASE_STORAGE_KEY);
    window.sessionStorage.removeItem(KNOWLEDGE_BASE_SELECTION_KEY);
    knowledgeBases.value = [DEFAULT_KNOWLEDGE_BASE];
    selectedKnowledgeBase.value = DEFAULT_KNOWLEDGE_BASE.id;
  }
}

async function syncKnowledgeBases() {
  knowledgeSyncing.value = true;
  try {
    const resp = await listKnowledgeDocuments();
    const docs = (resp.documents ?? []).map(mapDocumentToKnowledgeBase);
    const normalized = normalizeKnowledgeBaseList(docs);
    knowledgeBases.value = normalized.length ? normalized : [DEFAULT_KNOWLEDGE_BASE];
    if (!knowledgeBases.value.some((base) => base.id === selectedKnowledgeBase.value)) {
      selectedKnowledgeBase.value = knowledgeBases.value[0]?.id ?? DEFAULT_KNOWLEDGE_BASE.id;
    }
    knowledgeStatus.value = `已同步 ${Math.max(knowledgeBases.value.length - 1, 0)} 个文档`;
  } catch (error) {
    knowledgeStatus.value = (error as Error).message;
  } finally {
    knowledgeSyncing.value = false;
  }
}

function loadMcpProfile() {
  if (typeof window === "undefined") return;
  try {
    const stored = window.localStorage.getItem(MCP_PROFILE_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as typeof mcpProfile;
      mcpProfile.endpoint = parsed.endpoint ?? "";
      mcpProfile.namespace = parsed.namespace ?? "";
      mcpProfile.token = parsed.token ?? "";
    }
  } catch {
    mcpProfile.endpoint = "";
    mcpProfile.namespace = "";
    mcpProfile.token = "";
  }
}

function saveMcpProfile() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(MCP_PROFILE_STORAGE_KEY, JSON.stringify(mcpProfile));
    mcpStatusMessage.value = "MCP 配置已保存";
  } catch (error) {
    mcpStatusMessage.value = (error as Error).message;
    return;
  }
  window.setTimeout(() => {
    mcpStatusMessage.value = "";
  }, 2000);
  showMcpModal.value = false;
}

</script>
