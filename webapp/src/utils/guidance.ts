import type { QualityEvaluation, QuizSubmitResponse } from "../types";

export function issueLabel(issue?: string | null) {
  const labels: Record<string, string> = {
    retrieval_gap: "检索不足",
    evidence_gap: "证据不足",
    tutoring_gap: "练习承接不足",
    learner_fit_gap: "学习体验不足",
    quiz_gap: "测验覆盖不足",
    multimodal_gap: "需要图示支持",
  };
  return labels[issue || ""] ?? "当前主线";
}

export function issueAwareOverview(primaryIssue: string, fallback: string) {
  const map: Record<string, string> = {
    retrieval_gap: "这节内容里有些证据还不够稳，我们先把关键概念和出处讲清，再继续做题。",
    evidence_gap: "这节内容的核心知识还需要再对准资料证据，我们先稳住概念再往下走。",
    tutoring_gap: "这节课的难点不在知识点本身，而在怎么把它顺滑地学会，我们先用更轻的练习起步。",
    learner_fit_gap: "Lumi 会先降低一点节奏和认知负荷，帮你把主线搭起来，再进入更完整的学习流程。",
    quiz_gap: "这节课更需要尽快做一次校准测验，看看哪些点是真的会了，哪些只是看懂了。",
  };
  return map[primaryIssue] || fallback;
}

export function buildIssueHints(primaryIssue: string, missingEvidence: string[]) {
  const base = missingEvidence.slice(0, 2);
  if (primaryIssue === "retrieval_gap" || primaryIssue === "evidence_gap") {
    return [...base, "先留意概念依据和资料出处", "不急着刷题，先把核心事实讲稳"];
  }
  if (primaryIssue === "tutoring_gap" || primaryIssue === "learner_fit_gap") {
    return ["先用短练习进入状态", "如果觉得节奏快，可以随时让 Lumi 放慢一点"];
  }
  if (primaryIssue === "quiz_gap") {
    return ["先梳理主线知识点", "随后尽快用小测确认掌握度"];
  }
  return base;
}

export function issueAwareCoachIntro(primaryIssue: string) {
  if (primaryIssue === "retrieval_gap" || primaryIssue === "evidence_gap") {
    return "Lumi 会先帮你把证据和关键概念讲稳，再进入练习和测验，避免一开始就学偏。";
  }
  if (primaryIssue === "tutoring_gap" || primaryIssue === "learner_fit_gap") {
    return "Lumi 会先用更轻的引导和练习带你进入状态，再逐步推进知识点和测验。";
  }
  if (primaryIssue === "quiz_gap") {
    return "Lumi 会先帮你梳理知识点，再尽快用小测校准掌握度，避免后面建议失焦。";
  }
  return "Lumi 助教会按时间线一步步带你学习、讲解和测验，过程中可以随时提问或补充需求。";
}

export function buildQuizFollowup(
  result: QuizSubmitResponse | null,
  evaluation?: QualityEvaluation | null,
) {
  const primaryIssue = String(evaluation?.primary_issue || "").trim();
  const focus = result?.review_card?.focus ?? [];

  if (focus.length) {
    return {
      title: `先回到 ${focus[0]} 做一轮复盘`,
      summary: "你已经暴露出明确薄弱点，先回到陪学助教或工作台针对性补一下，再继续推进更省时间。",
      actionLabel: "去陪学助教复盘",
      target: "coach" as const,
    };
  }
  if (primaryIssue === "retrieval_gap" || primaryIssue === "evidence_gap") {
    return {
      title: `先补${issueLabel(primaryIssue)}`,
      summary: "当前分数不是主要问题，先把资料证据和关键概念补稳，再继续刷题会更值。",
      actionLabel: "回工作台补证据",
      target: "home" as const,
    };
  }
  if (primaryIssue === "quiz_gap") {
    return {
      title: "再做一轮短测校准",
      summary: "你已经完成这一轮，接下来适合回到工作台或陪学助教，再生成一轮更有针对性的题。",
      actionLabel: "回工作台继续",
      target: "home" as const,
    };
  }
  return {
    title: "继续推进下一步学习",
    summary: "这一轮结果已经能支撑继续学习，回到工作台查看下一条建议，或者直接进入陪学助教继续。",
    actionLabel: "回工作台",
    target: "home" as const,
  };
}
