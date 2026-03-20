from src.agents.rewriter import rewrite_quiz


class _FakeClient:
    def chat(self, **kwargs):
        return """
        {
          "quiz": {
            "items": [
              {
                "id": "q1",
                "question": "问题",
                "options": {"A": "甲", "B": "乙", "C": "丙", "D": "丁"},
                "answer": "A",
                "explain": "解释",
                "difficulty": "easy",
                "kp_ids": ["kp1"],
                "refs": [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}],
                "variants": []
              }
            ]
          }
        }
        """


def test_rewriter_preserves_refs():
    planner_payload = {
        "quiz": {
            "items": [
                {
                    "id": "q1",
                    "question": "原题",
                    "options": {"A": "甲", "B": "乙", "C": "丙", "D": "丁"},
                    "answer": "A",
                    "refs": [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}],
                }
            ]
        }
    }

    payload = rewrite_quiz(client=_FakeClient(), planner_payload=planner_payload)

    assert payload["quiz"]["items"][0]["refs"] == [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}]
