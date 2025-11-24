import type {
  KnowledgeDocumentListResponse,
  KnowledgeSearchResponse,
  KnowledgeBase,
  LessonTimelinePayload,
  PrestudyJobTicket,
  PrestudyResponse,
  QuizStartResponse,
  QuizSubmitResponse,
  RagSearchRequest,
  RecommendationTaskResponse,
  UserProfile,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

function getCookie(name: string): string | null {
  // Escape regex special chars to safely read cookie by name
  const escaped = name.replace(/([.*+?^${}()|[\]\\])/g, "\\$1");
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function ensureCsrfToken(): Promise<string> {
  // Always read the latest cookie to avoid stale tokens
  let cookieToken = getCookie("csrftoken");
  if (cookieToken) return cookieToken;

  // fetch from backend to set cookie
  const resp = await fetch(`${API_BASE}/api/auth/csrf/`, {
    method: "GET",
    credentials: "include",
  });
  if (resp.ok) {
    try {
      const data = await resp.json();
      cookieToken = data?.csrfToken ?? getCookie("csrftoken");
    } catch {
      cookieToken = getCookie("csrftoken");
    }
  }
  return cookieToken ?? "";
}

const AUTH_STORAGE_KEY = "classweaver:current-user";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const init: RequestInit = { method: "GET", credentials: "include", ...options };

  const headers = new Headers(init.headers ?? {});
  const isFormData = init.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept-Language")) {
    headers.set("Accept-Language", "zh-CN");
  }
  const method = (init.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = await ensureCsrfToken();
    if (token && !headers.has("X-CSRFToken")) {
      headers.set("X-CSRFToken", token);
    }
  }
  init.headers = headers;

  const response = await fetch(url, init);
  const raw = await response.text();
  if (!response.ok) {
    let detail = raw;
    try {
      const parsed = raw ? JSON.parse(raw) : null;
      detail = parsed?.detail ?? parsed?.error ?? raw;
    } catch {
      detail = raw || response.statusText;
    }
    const error = new Error(detail || response.statusText);
    (error as any).status = response.status;
    if (response.status === 401) {
      // 会话失效时清理本地登录态，交由路由守卫跳转
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
      }
    }
    throw error;
  }

  if (response.status === 204 || !raw) {
    return undefined as T;
  }

  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    console.warn("Failed to parse JSON response", error);
    throw new Error(raw);
  }
}

export function createPrestudyFromText(payload: { text: string; base_id?: string | number; locale?: string }): Promise<PrestudyJobTicket> {
  return request("/api/prestudy/from-text/", {
    method: "POST",
    body: JSON.stringify({ locale: "zh-CN", ...payload }),
  });
}

export function createPrestudyFromPpt(file: File, baseId?: string | number, locale = "zh-CN"): Promise<PrestudyJobTicket> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  if (baseId && !`${baseId}`.startsWith("__")) formData.append("base_id", `${baseId}`);
  formData.append("locale", locale);
  return request("/api/prestudy/from-ppt/", {
    method: "POST",
    body: formData,
  });
}

export function getPrestudyJob(jobId: string): Promise<PrestudyResponse> {
  return request(`/api/prestudy/${jobId}/`);
}

export function getPrestudyJobStatus(jobId: string): Promise<PrestudyJobTicket> {
  return request(`/api/jobs/${jobId}/`);
}

export function startQuiz(jobId: string): Promise<QuizStartResponse> {
  return request("/api/quiz/start/", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, locale: "zh-CN" }),
  });
}

export function submitQuiz(sessionId: string, answers: Array<{ id: string; answer: string }>): Promise<QuizSubmitResponse> {
  return request("/api/quiz/submit/", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, answers }),
  });
}

export function searchKnowledge(payload: RagSearchRequest): Promise<KnowledgeSearchResponse> {
  return request("/api/kb/search/", {
    method: "POST",
    body: JSON.stringify({ locale: "zh-CN", ...payload }),
  });
}

export function knowledgeQa(question: string, baseId?: string | number, top_k = 4) {
  return request("/api/kb/qa/", {
    method: "POST",
    body: JSON.stringify({
      question,
      base_id: baseId && !`${baseId}`.startsWith("__") ? `${baseId}` : undefined,
      top_k,
    }),
  });
}

export interface KnowledgeUploadResponse {
  docs_created: number;
  chunks: number;
  backend: string;
  dim: number;
  documents: KnowledgeDocumentListResponse["documents"];
}

export function uploadKnowledge(files: File | File[], baseId?: string | number): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  const batch = Array.isArray(files) ? files : [files];
  batch.forEach((file) => formData.append("file", file, file.name));
  if (baseId && !`${baseId}`.startsWith("__")) {
    formData.append("base_id", `${baseId}`);
  }
  return request("/api/kb/upload/", {
    method: "POST",
    body: formData,
  });
}

export function listKnowledgeDocuments(baseId?: string | number): Promise<KnowledgeDocumentListResponse> {
  const suffix = baseId && !`${baseId}`.startsWith("__") ? `?base_id=${baseId}` : "";
  return request(`/api/kb/documents/${suffix}`);
}

export function deleteKnowledgeDocument(docId: string): Promise<{ deleted: number }> {
  return request(`/api/kb/documents/${encodeURIComponent(docId)}/`, { method: "DELETE" });
}

export function clearKnowledgeDocuments(): Promise<{ deleted: number }> {
  return request("/api/kb/documents/", { method: "DELETE" });
}

export function listKnowledgeBases(): Promise<{ bases: KnowledgeBase[] }> {
  return request("/api/kb/bases/");
}

export function deleteKnowledgeBase(baseId: string | number): Promise<void> {
  return request(`/api/kb/bases/${baseId}/`, { method: "DELETE" });
}

export function createKnowledgeBase(name: string, description?: string): Promise<KnowledgeBase> {
  return request("/api/kb/bases/", {
    method: "POST",
    body: JSON.stringify({ name, description: description ?? "" }),
  });
}

export function getLessonTimeline(planId: number | string): Promise<LessonTimelinePayload> {
  return request(`/api/lesson/${planId}/timeline/`);
}

export function postLessonEvent(
  planId: number | string,
  payload: { event_type: string; actor?: string; detail?: string; [key: string]: unknown },
): Promise<void> {
  return request(`/api/lesson/${planId}/events/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function triggerRecommendations(jobId: string, sessionId?: string): Promise<RecommendationTaskResponse> {
  return request("/api/recommendations/", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, session_id: sessionId, locale: "zh-CN" }),
  });
}

export function registerUser(payload: { username: string; password: string; email?: string }): Promise<UserProfile> {
  return request("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: { username: string; password: string }): Promise<UserProfile> {
  return request("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logoutUser(): Promise<void> {
  return request("/api/auth/logout/", {
    method: "POST",
  });
}

export function fetchCurrentUser(): Promise<UserProfile> {
  return request("/api/auth/me/");
}

export async function primeCsrfToken(): Promise<void> {
  await ensureCsrfToken();
}
