<template>
  <div class="coach-page">
    <section class="coach-hero glass-panel" v-if="!isLoading && job">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">
          {{ job.lesson_plan ? "课程计划 #" + job.lesson_plan.id : "备课任务" }}
        </p>
        <h1 class="text-2xl font-semibold text-slate-900">陪学助教 · {{ jobTitle }}</h1>
        <p class="mt-2 text-sm text-slate-600">
          Lumi 助教会按时间线一步步带你学习、讲解和测验，过程中可以随时提问或补充需求。
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <button class="btn-secondary text-xs" type="button" @click="navigateHome">返回工作台</button>
        <button class="btn-primary text-xs" type="button" @click="handleSceneAction(defaultQuizAction)">
          直接开始测验
        </button>
      </div>
    </section>

    <section v-if="isLoading" class="coach-empty">
      <p class="text-sm text-slate-500">助教正在加载最新脚本，请稍候...</p>
    </section>

    <section v-else-if="loadError" class="coach-empty">
      <p class="text-sm text-rose-600">{{ loadError }}</p>
      <button class="btn-primary mt-3" type="button" @click="navigateHome">返回工作台</button>
    </section>

    <section v-else-if="!job" class="coach-empty">
      <p class="text-sm text-slate-500">
        暂未找到正在运行的课堂，请先在工作台完成一次内容生成或从历史任务进入陪学模式。
      </p>
      <button class="btn-primary mt-3" type="button" @click="navigateHome">去工作台</button>
    </section>

    <template v-else>
      <section class="coach-stage glass-panel">
        <div
          class="flex h-44 w-[360px] max-w-full flex-col items-center justify-center rounded-3xl shadow-2xl ring-4 ring-white/70 transition text-pink-700"
          :class="avatarMoodClass(activeScene?.mood)"
        >
          <span class="text-6xl drop-shadow-sm">👩🏻‍🎓</span>
          <span class="mt-2 text-base font-semibold">Lumi 老师</span>
        </div>
        <div class="coach-dialog">
          <p class="coach-dialog__label">{{ activeScene?.title }}</p>
          <p class="coach-dialog__text">{{ activeScene?.summary }}</p>
          <ul v-if="activeScene?.hints?.length" class="coach-dialog__list">
            <li v-for="hint in activeScene?.hints" :key="hint">{{ hint }}</li>
          </ul>
          <div class="mt-3 space-y-2">
            <label class="text-xs font-semibold text-slate-500">对当前步骤有疑问或补充？</label>
            <div class="flex flex-wrap gap-2">
              <input
                v-model="coachFeedback"
                class="flex-1 min-w-[220px] rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400"
                type="text"
                placeholder="告诉 Lumi 你想补充的需求或不懂的点"
              />
              <button class="btn-secondary text-xs" type="button" @click="pushCoachFeedback" :disabled="!coachFeedback.trim()">
                提交给助教
              </button>
            </div>
            <ul v-if="userQuestions.length" class="space-y-1 text-xs text-slate-500">
              <li v-for="(q, idx) in userQuestions" :key="`${idx}-${q.slice(0,8)}`">· {{ q }}</li>
            </ul>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button
              v-if="activeScene?.action"
              class="btn-primary"
              type="button"
              :disabled="isLaunchingAction"
              @click="handleSceneAction(activeScene.action)"
            >
              {{ activeScene.action.label }}
            </button>
            <button class="btn-secondary" type="button" @click="navigateHome">返回工作台</button>
          </div>
        </div>
        <div class="coach-controls mt-3 flex w-full flex-col gap-2 items-stretch">
          <div class="flex items-center justify-between gap-3">
            <button class="btn-ghost text-xs" type="button" :disabled="activeIndex === 0" @click="prevScene">上一步</button>
            <div class="flex-1 text-center text-xs text-slate-500">
              {{ activeIndex + 1 }} / {{ scenes.length }} · 完成度 {{ sceneProgress }}
            </div>
          </div>
          <div class="w-full -mx-2 sm:-mx-4">
            <button
              class="w-full rounded-2xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50"
              type="button"
              :disabled="activeIndex >= scenes.length - 1"
              @click="nextScene"
            >
              下一步
            </button>
          </div>
        </div>
      </section>

      <section class="coach-scenes glass-panel">
        <header class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.35em] text-slate-500">陪学脚本</p>
            <h2 class="text-xl font-semibold text-slate-900">场景导航</h2>
          </div>
          <p class="text-xs text-slate-500">场景基于 Planner / Tutor / Timeline 自动生成</p>
        </header>
        <div class="scene-list">
          <article
            v-for="(scene, index) in scenes"
            :key="scene.id"
            class="scene-card"
            :class="sceneCardClass(index)"
            @click="selectScene(index)"
          >
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold uppercase tracking-[0.35em] text-slate-400">{{ sceneLabel(scene) }}</p>
              <span class="text-[11px] font-semibold text-slate-500">{{ index + 1 }} / {{ scenes.length }}</span>
            </div>
            <h3 class="text-base font-semibold text-slate-900">{{ scene.title }}</h3>
            <p class="text-sm text-slate-600">{{ scene.summary }}</p>
            <div v-if="scene.hints?.length" class="mt-2 flex flex-wrap gap-1">
              <span v-for="hint in scene.hints.slice(0, 3)" :key="hint" class="scene-chip">{{ hint }}</span>
            </div>
            <button
              v-if="scene.action"
              class="btn-secondary mt-3 text-xs"
              type="button"
              @click.stop="handleSceneAction(scene.action)"
            >
              {{ scene.action.label }}
            </button>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getLessonTimeline, getPrestudyJob, startQuiz } from "../services/api";
import type {
  KnowledgePoint,
  LessonTimelinePayload,
  LessonEventEntry,
  PrestudyResponse,
  PrintablePracticeItem,
  QuizQuestion,
} from "../types";

const STORAGE_KEY = "classweaver:last-prestudy";
const QUIZ_SESSION_STORAGE_KEY = "classweaver:last-quiz-session";

type SceneMood = "focus" | "idea" | "warm" | "quiz";
type SceneType = "intro" | "concept" | "timeline" | "practice" | "quiz" | "wrap";

interface SceneAction {
  label: string;
  type: "quiz" | "print" | "home";
}

interface CoachScene {
  id: string;
  title: string;
  summary: string;
  hints?: string[];
  mood: SceneMood;
  type: SceneType;
  action?: SceneAction;
}

interface PersistedJobPayload {
  ticket: { id: string } | null;
  result: PrestudyResponse | null;
}

const router = useRouter();
const route = useRoute();

const job = ref<PrestudyResponse | null>(null);
const timeline = ref<LessonTimelinePayload | null>(null);
const scenes = ref<CoachScene[]>([]);
const activeIndex = ref(0);
const isLoading = ref(true);
const isLaunchingAction = ref(false);
const loadError = ref("");
const userQuestions = ref<string[]>([]);
const coachFeedback = ref("");

const jobTitle = computed(() => job.value?.lesson_plan?.title || "今日课堂");
const activeScene = computed(() => scenes.value[activeIndex.value] ?? null);
const sceneProgress = computed(() => {
  if (!scenes.value.length) {
    return "0%";
  }
  return `${(((activeIndex.value + 1) / scenes.value.length) * 100).toFixed(0)}%`;
});
const defaultQuizAction: SceneAction = {
  label: "开启测验",
  type: "quiz",
};

function avatarMoodClass(mood?: SceneMood): string {
  switch (mood) {
    case "idea":
      return "bg-gradient-to-br from-amber-100 via-pink-50 to-white";
    case "warm":
      return "bg-gradient-to-br from-rose-300 via-white to-amber-100";
    case "quiz":
      return "bg-gradient-to-br from-sky-200 via-white to-emerald-200";
    default:
      return "bg-gradient-to-br from-pink-100 via-white to-slate-100";
  }
}

watch(
  [job, timeline],
  () => {
    scenes.value = buildCoachScenes(job.value, timeline.value);
    if (activeIndex.value >= scenes.value.length) {
      activeIndex.value = 0;
    }
  },
  { deep: true },
);

onMounted(async () => {
  await hydrateJob();
  if (job.value?.lesson_plan?.id) {
    await fetchTimeline(job.value.lesson_plan.id);
  }
  isLoading.value = false;
});

async function hydrateJob() {
  try {
    const queryJobId = typeof route.query.jobId === "string" ? route.query.jobId : null;
    if (queryJobId) {
      job.value = await getPrestudyJob(queryJobId);
      return;
    }
    const stored = restoreStoredJob();
    if (stored?.result) {
      job.value = stored.result;
      return;
    }
    if (stored?.ticket?.id) {
      job.value = await getPrestudyJob(stored.ticket.id);
    }
  } catch (error) {
    loadError.value = (error as Error).message;
  }
}

function restoreStoredJob(): PersistedJobPayload | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as PersistedJobPayload;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

async function fetchTimeline(planId: number | string) {
  try {
    timeline.value = await getLessonTimeline(planId);
  } catch (error) {
    console.warn("Failed to load timeline", error);
  }
}

function buildCoachScenes(payload: PrestudyResponse | null, timelinePayload: LessonTimelinePayload | null): CoachScene[] {
  if (!payload) {
    return [];
  }
  const finalData = (payload.final_json ?? {}) as Record<string, unknown>;
  const plannerData = (payload.planner_json ?? {}) as Record<string, unknown>;
  const knowledgePoints = asArray<KnowledgePoint>(finalData.knowledge_points ?? plannerData.knowledge_points);
  const practiceItems = asArray<PrintablePracticeItem>((finalData.tutor as Record<string, unknown>)?.practice);
  const quizBlock = finalData.quiz as Record<string, unknown> | undefined;
  const timelineEvents = sortTimeline(timelinePayload?.events ?? []);
  const scenes: CoachScene[] = [];

  const overview =
    (typeof finalData.overview === "string" && finalData.overview.trim()) ||
    (typeof plannerData.summary === "string" && plannerData.summary.trim()) ||
    "我们即将一起复盘本节课的核心知识点，并通过练习巩固。";

  scenes.push({
    id: "intro",
    title: "热身开场",
    summary: overview,
    mood: "warm",
    type: "intro",
  });

  timelineEvents.forEach((event, idx) => {
    scenes.push({
      id: `timeline-${event.id}`,
      title: formatEventTitle(event),
      summary: event.payload?.summary || event.payload?.note || "按这个步骤学习或讲解，如有疑问随时提问。",
      hints: [event.payload?.question, event.payload?.status, event.payload?.note].filter(Boolean).map(String).slice(0, 3),
      mood: idx % 2 === 0 ? "focus" : "idea",
      type: "timeline",
    });
  });

  knowledgePoints.forEach((kp, index) => {
    scenes.push({
      id: `kp-${kp.id ?? index}`,
      title: kp.title || `知识要点 ${index + 1}`,
      summary: kp.summary || "聚焦重点知识，留意概念之间的联系。",
      hints: kp.summary ? kp.summary.split(/；|。/).filter(Boolean).slice(0, 3) : undefined,
      mood: (timelineEvents.length + index) % 2 === 0 ? "focus" : "idea",
      type: "concept",
    });
  });

  practiceItems.forEach((item, index) => {
    scenes.push({
      id: `practice-${index}`,
      title: item.prompt || `练习 ${index + 1}`,
      summary: item.answer
        ? `尝试自己回答，再核对 AI 助教提供的解析：${item.answer}`
        : "思考一下如果你是老师，会如何回答？",
      hints: item.reasoning ? [item.reasoning] : undefined,
      mood: "idea",
      type: "practice",
    });
  });

  if (quizBlock) {
    scenes.push({
      id: "quiz",
      title: "测验准备",
      summary: "准备好了吗？Lumi 会根据刚才的知识点生成自测题，检验掌握度。",
      mood: "quiz",
      type: "quiz",
      action: { label: "开启测验", type: "quiz" },
    });
  }

  scenes.push({
    id: "wrap",
    title: "总结与打印",
    summary: "如果需要纸质版资料或课堂讲义，现在就去打印吧。",
    mood: "warm",
    type: "wrap",
    action: { label: "获取打印资料", type: "print" },
  });

  return scenes;
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatEventTitle(event: LessonEventEntry): string {
  if (event.payload?.title) {
    return event.payload.title as string;
  }
  const map: Record<string, string> = {
    question: "提问/疑惑",
    practice: "练习安排",
    issue: "学习困惑",
    note: "学习备注",
    timeline: "学习步骤",
  };
  return map[event.event_type] ?? event.event_type;
}

function sceneCardClass(index: number) {
  if (index === activeIndex.value) {
    return "scene-card--active";
  }
  if (index < activeIndex.value) {
    return "scene-card--completed";
  }
  return "";
}

function sceneLabel(scene: CoachScene): string {
  const map: Record<SceneType, string> = {
    intro: "热身",
    concept: "知识点",
    timeline: "学习步骤",
    practice: "练习",
    quiz: "测验",
    wrap: "收尾",
  };
  return map[scene.type] ?? "场景";
}

function selectScene(index: number) {
  activeIndex.value = index;
}

function nextScene() {
  if (activeIndex.value < scenes.value.length - 1) {
    activeIndex.value += 1;
  }
}

function prevScene() {
  if (activeIndex.value > 0) {
    activeIndex.value -= 1;
  }
}

async function handleSceneAction(action?: SceneAction) {
  if (!action) {
    return;
  }
  if (action.type === "home") {
    navigateHome();
    return;
  }
  if (!job.value) {
    return;
  }
  if (action.type === "print") {
    router.push({
      name: "print",
      query: { jobId: job.value.id },
      state: { printable: job.value.printable },
    });
    return;
  }
  if (action.type === "quiz") {
    isLaunchingAction.value = true;
    try {
      const session = await startQuiz(job.value.id);
      if (!session?.session_id) {
        throw new Error("未获取到测验会话，请稍后重试。");
      }
      persistQuizSession(session.session_id, job.value.id, session.questions);
      router.push({
        name: "take",
        query: { sessionId: session.session_id, jobId: job.value.id },
        state: {
          sessionId: session.session_id,
          jobId: job.value.id,
          questions: session.questions,
        },
      });
    } catch (error) {
      loadError.value = (error as Error).message;
    } finally {
      isLaunchingAction.value = false;
    }
  }
}

function navigateHome() {
  router.push({ name: "home" });
}

function persistQuizSession(sessionId: string, jobId: string, questions: QuizQuestion[]) {
  if (typeof window === "undefined") return;
  const payload = { sessionId, jobId, questions, savedAt: Date.now() };
  window.sessionStorage.setItem(QUIZ_SESSION_STORAGE_KEY, JSON.stringify(payload));
}

function sortTimeline(events: LessonEventEntry[]): LessonEventEntry[] {
  return [...events].sort((a, b) => {
    const at = new Date(a.occurred_at || 0).getTime();
    const bt = new Date(b.occurred_at || 0).getTime();
    return at - bt;
  });
}

function pushCoachFeedback() {
  const text = coachFeedback.value.trim();
  if (!text) return;
  userQuestions.value = [...userQuestions.value, text];
  coachFeedback.value = "";
}
</script>
