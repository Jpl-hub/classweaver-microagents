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

export interface PrestudyResponse {
  id: string;
  status: string;
  planner_json: Record<string, unknown>;
  final_json: Record<string, unknown>;
  model_trace: ModelTraceSegment[];
  duration_ms: number;
  printable?: PrintablePayload;
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

export interface RagSearchRequest {
  query: string;
  top_k: number;
}
