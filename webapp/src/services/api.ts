import type {
  KnowledgeSearchResponse,
  PrestudyResponse,
  QuizStartResponse,
  QuizSubmitResponse,
  RagSearchRequest,
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
  init.headers = headers;

  const response = await fetch(url, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function createPrestudyFromText(text: string): Promise<PrestudyResponse> {
  return request("/api/prestudy/from-text/", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function createPrestudyFromPpt(file: File): Promise<PrestudyResponse> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  return request("/api/prestudy/from-ppt/", {
    method: "POST",
    body: formData,
  });
}

export function getPrestudyJob(jobId: string): Promise<PrestudyResponse> {
  return request(`/api/prestudy/${jobId}/`);
}

export function startQuiz(jobId: string): Promise<QuizStartResponse> {
  return request("/api/quiz/start/", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId }),
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
    body: JSON.stringify(payload),
  });
}

export function uploadKnowledge(file: File): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  return request("/api/kb/upload/", {
    method: "POST",
    body: formData,
  });
}
