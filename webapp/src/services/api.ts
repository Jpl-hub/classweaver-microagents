import type {
  KnowledgeDocumentListResponse,
  KnowledgeSearchResponse,
  LessonTimelinePayload,
  PrestudyJobTicket,
  PrestudyResponse,
  QuizStartResponse,
  QuizSubmitResponse,
  RagSearchRequest,
  RecommendationTaskResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const init: RequestInit = { method: "GET", ...options };

  const headers = new Headers(init.headers ?? {});
  const isFormData = init.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept-Language")) {
    headers.set("Accept-Language", "zh-CN");
  }
  init.headers = headers;

  const response = await fetch(url, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const raw = await response.text();
  if (!raw) {
    return undefined as T;
  }

  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    console.warn("Failed to parse JSON response", error);
    throw new Error(raw);
  }
}

export function createPrestudyFromText(payload: { text: string; doc_ids?: string[]; locale?: string }): Promise<PrestudyJobTicket> {
  return request("/api/prestudy/from-text/", {
    method: "POST",
    body: JSON.stringify({ locale: "zh-CN", ...payload }),
  });
}

export function createPrestudyFromPpt(file: File, docIds?: string[], locale = "zh-CN"): Promise<PrestudyJobTicket> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  if (docIds?.length) {
    formData.append("doc_ids", JSON.stringify(docIds));
  }
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

export interface KnowledgeUploadResponse {
  docs_created: number;
  chunks: number;
  backend: string;
  dim: number;
  documents: KnowledgeDocumentListResponse["documents"];
}

export function uploadKnowledge(files: File | File[]): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  const batch = Array.isArray(files) ? files : [files];
  batch.forEach((file) => formData.append("file", file, file.name));
  return request("/api/kb/upload/", {
    method: "POST",
    body: formData,
  });
}

export function listKnowledgeDocuments(): Promise<KnowledgeDocumentListResponse> {
  return request("/api/kb/documents/");
}

export function deleteKnowledgeDocument(docId: string): Promise<{ deleted: number }> {
  return request(`/api/kb/documents/${encodeURIComponent(docId)}/`, { method: "DELETE" });
}

export function clearKnowledgeDocuments(): Promise<{ deleted: number }> {
  return request("/api/kb/documents/", { method: "DELETE" });
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
