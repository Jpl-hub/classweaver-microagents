from src.agents.utils import parse_agent_json


def test_parse_agent_json_trims_markdown_fences():
    payload = """```json
    {
      "foo": "bar"
    }
    ```"""
    result = parse_agent_json(payload)
    assert result == {"foo": "bar"}
