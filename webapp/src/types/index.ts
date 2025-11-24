export interface QuizQuestion {
  id: string;
  question: string;
  options: Record<string, string>;
  difficulty: "easy" | "medium" | "hard";
  selected_variant?: string;
  kp_ids?: string[];
}

export interface ModelTraceSegment {
  orchestrator: string;
  step: string;
  provider: string;
  model: string;
  base_url: string;
  latency_ms: number;
  input_chars: number;
  output_chars: number;
  rag?: Record<string, unknown>;
  fallback?: boolean;
}

export interface KnowledgePoint {
  id?: string;
  title?: string;
  summary?: string;
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface PrintablePracticeItem {
  prompt: string;
  answer?: string;
  reasoning?: string;
}

export interface PrintablePayload {
  title: string;
  knowledge_points: KnowledgePoint[];
  glossary: GlossaryItem[];
  quiz: Array<QuizQuestion & { answer?: string; explain?: string }>;
  practice: PrintablePracticeItem[];
}

export interface LessonPlanSummary {
  id: number;
  title: string;
  structure: Record<string, unknown>;
  notes?: string;
}

export interface PrestudyResponse {
  id: string;
  status: string;
  planner_json: Record<string, unknown>;
  final_json: Record<string, unknown>;
  model_trace: ModelTraceSegment[];
  duration_ms: number;
  printable?: PrintablePayload;
  lesson_plan?: LessonPlanSummary;
}

export interface PrestudyJobTicket {
  id: string;
  status: string;
  detail?: string;
  estimated_wait_sec?: number;
}

export interface QuizStartResponse {
  session_id: string;
  questions: QuizQuestion[];
}

export interface QuizSubmitResponse {
  score: number;
  detail: Array<{
    id: string;
    correct: boolean;
    answer: string;
    user_answer: string;
    explain?: string;
    difficulty?: string;
  }>;
  diagnostics: Record<string, unknown>;
  review_card: {
    strengths: string[];
    focus: string[];
    summary: string;
  };
  extra_questions?: QuizQuestion[];
}

export interface KnowledgeSearchResult {
  text: string;
  score: number;
  refs: Array<{ doc_id: string; chunk_id: string }>;
  title?: string;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeSearchResponse {
  results: KnowledgeSearchResult[];
}

export interface KnowledgeDocumentSummary {
  doc_id: string;
  title: string;
  updated_at: string;
  base_id?: number;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocumentSummary[];
}

export interface RagSearchRequest {
  query: string;
  top_k: number;
  base_id?: string | number;
}

export interface KnowledgeQaResponse {
  answer: string;
  contexts: KnowledgeSearchResult[];
}

export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
}

export interface LessonEventEntry {
  id: number;
  event_type: string;
  actor?: string;
  payload?: Record<string, unknown>;
  occurred_at: string;
}

export interface LessonTimelinePayload {
  plan: LessonPlanSummary;
  events: LessonEventEntry[];
}

export type RecommendationAgent = "planner" | "rewriter" | "tutor" | "coach";
export type RecommendationStage = "focus" | "practice" | "classroom" | "resource" | "planning";
export type RecommendationTarget = "review" | "quiz" | "timeline" | "resource";

export interface RecommendationSuggestion {
  id?: string;
  agent?: RecommendationAgent;
  stage?: RecommendationStage;
  target?: RecommendationTarget;
  type: string;
  title: string;
  summary: string;
  action: string;
  kp_ids?: string[];
  doc_ids?: string[];
}

export interface RecommendationPayload {
  generated_at: string;
  job_id: string | number;
  session_id?: string;
  suggestions: RecommendationSuggestion[];
}

export interface RecommendationTaskResponse {
  id: string;
  status: string;
  output: RecommendationPayload;
}

export interface UserProfile {
  id: number;
  username: string;
  email?: string;
}
