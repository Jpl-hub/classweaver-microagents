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
  cycle?: string;
  provider: string;
  model: string;
  base_url: string;
  latency_ms: number;
  input_chars: number;
  output_chars: number;
  rag?: RetrievalDiagnostics & Record<string, unknown>;
}

export interface RetrievalDiagnostics {
  enabled?: boolean;
  backend?: string;
  hybrid_enabled?: boolean;
  rerank_enabled?: boolean;
  query_length?: number;
  total_entries?: number;
  search_k?: number;
  vector_hits?: number;
  lexical_hits?: number;
  final_hits?: number;
  source_counts?: Record<string, number>;
}

export interface EvaluationScores {
  groundedness: number;
  citation_coverage: number;
  quiz_quality: number;
  tutoring_value: number;
  learner_fit: number;
  overall: number;
}

export interface EvaluationRuleMetrics {
  counts?: Record<string, number>;
  ratios?: Record<string, number>;
  retrieval?: Record<string, unknown>;
  scorecard?: Partial<EvaluationScores>;
  gates?: Record<string, boolean>;
}

export interface LearnerExperienceInsights {
  smoothness?: string;
  cognitive_load?: string;
  personalization?: string;
}

export interface ReflectionInsights {
  diagnosis?: string[];
  next_actions?: string[];
  should_regenerate?: boolean;
  should_expand_retrieval?: boolean;
  should_add_multimodal_review?: boolean;
}

export interface ReviewCycleSummary {
  round: number;
  top_k: number;
  trigger?: Record<string, boolean>;
  initial_overall_score?: number;
  revised_overall_score?: number;
  score_delta?: number;
  retrieval_diagnostics?: RetrievalDiagnostics;
  evaluation?: QualityEvaluation;
  reflection?: ReflectionInsights;
}

export interface ReviewSummary {
  executed_rounds?: number;
  cycles?: ReviewCycleSummary[];
  initial_overall_score?: number;
  final_overall_score?: number;
  pending_multimodal_review?: boolean;
}

export interface QualityEvaluation {
  verdict?: "pass" | "review" | "block" | string;
  scores?: Partial<EvaluationScores>;
  rule_metrics?: EvaluationRuleMetrics;
  strengths?: string[];
  risks?: string[];
  missing_evidence?: string[];
  learner_experience?: LearnerExperienceInsights;
}

export interface KnowledgePoint {
  id?: string;
  title?: string;
  summary?: string;
  refs?: CitationItem[];
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface PrintablePracticeItem {
  prompt: string;
  answer?: string;
  reasoning?: string;
  citations?: CitationItem[];
}

export interface CitationItem {
  doc_id?: string;
  chunk_id?: string;
  title?: string;
  text?: string;
  score?: number;
  label?: string;
}

export interface PrintablePayload {
  title: string;
  knowledge_points: KnowledgePoint[];
  glossary: GlossaryItem[];
  quiz: Array<QuizQuestion & { answer?: string; explain?: string }>;
  practice: PrintablePracticeItem[];
  sources?: CitationItem[];
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
  retrieval_diagnostics?: RetrievalDiagnostics;
  evaluation?: QualityEvaluation;
  reflection?: ReflectionInsights;
  review_summary?: ReviewSummary;
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
  citations?: CitationItem[];
  retrieval_diagnostics?: RetrievalDiagnostics;
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
