from src.agents.evaluator import build_quality_report


class _FakeClient:
    def chat(self, **kwargs):
        return """
        {
          "scores": {
            "groundedness": 84,
            "citation_coverage": 80,
            "quiz_quality": 78,
            "tutoring_value": 76,
            "learner_fit": 81,
            "overall": 80
          },
          "verdict": "review",
          "strengths": ["知识点和题目都绑定了引用"],
          "risks": ["练习题数量偏少"],
          "missing_evidence": ["实验现象缺少图片或图示"],
          "learner_experience": {
            "smoothness": "节奏基本顺滑，但练习承接偏短。",
            "cognitive_load": "一次性知识点较集中，需要阶段性停顿。",
            "personalization": "已有 followup，但缺少按错因分流。"
          },
          "reflection": {
            "diagnosis": ["当前 grounding 够用，但 tutor 练习层偏薄。"],
            "next_actions": ["增加基于错题的二次练习。"],
            "should_regenerate": false,
            "should_expand_retrieval": false,
            "should_add_multimodal_review": true
          }
        }
        """


def test_build_quality_report_combines_rule_metrics_and_llm_judgement():
    payload = build_quality_report(
        client=_FakeClient(),
        text="请生成一节牛顿三定律预习课",
        planner_payload={
            "title": "牛顿三定律",
            "summary": "summary",
            "knowledge_points": [
                {"title": "惯性", "summary": "summary", "refs": [{"doc_id": "doc-1", "chunk_id": "c1"}]},
            ],
        },
        final_payload={
            "knowledge_points": [
                {"title": "惯性", "summary": "summary", "refs": [{"doc_id": "doc-1", "chunk_id": "c1"}]},
            ],
            "quiz": {
                "items": [
                    {
                        "question": "第一定律是什么？",
                        "answer": "A",
                        "difficulty": "easy",
                        "refs": [{"doc_id": "doc-1", "chunk_id": "c1"}],
                        "variants": [{"question": "变体", "options": {"A": "1", "B": "2", "C": "3", "D": "4"}}],
                    }
                ]
            },
        },
        tutor_payload={
            "summary": {"key_takeaways": ["惯性", "受力"], "recap": "recap", "encouragement": "enc"},
            "practice": [{"prompt": "解释惯性", "citations": [{"doc_id": "doc-1", "chunk_id": "c1"}]}],
            "followups": ["再举一个生活例子"],
        },
        rag_chunks=[{"text": "牛顿第一定律", "refs": [{"doc_id": "doc-1", "chunk_id": "c1"}]}],
        rag_diagnostics={"enabled": True, "search_k": 4, "final_hits": 2, "vector_hits": 3, "lexical_hits": 2},
    )

    assert payload["evaluation"]["verdict"] == "review"
    assert payload["evaluation"]["scores"]["overall"] == 80
    assert payload["evaluation"]["rule_metrics"]["counts"]["quiz_items"] == 1
    assert payload["evaluation"]["rule_metrics"]["gates"]["needs_more_practice"] is False
    assert payload["reflection"]["should_add_multimodal_review"] is True
