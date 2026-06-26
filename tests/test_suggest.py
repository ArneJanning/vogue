import httpx
from vogue.model import Record, Field
from vogue.coding import Label
from vogue.suggest.core import (parse_label, build_prompt, LLMSuggester,
                                BaselineSuggester, openrouter_complete)


def _rec():
    return Record(source="gepris", id="1", title="Cultures of Repair", year=2021,
                  discipline_raw="Ethnologie", field=Field.HUMANITIES,
                  work_type="GRK", url="u", abstract="repair as cultural practice")


def test_parse_label():
    assert parse_label("trope") is Label.TROPE
    assert parse_label("I think this is a homonym.") is Label.HOMONYM
    assert parse_label("literal object repair") is Label.LITERAL
    assert parse_label("") is Label.UNSURE
    assert parse_label("banana") is Label.UNSURE


def test_build_prompt_mentions_term_and_record():
    p = build_prompt(_rec(), "repair")
    assert "repair" in p and "Cultures of Repair" in p and "Ethnologie" in p


def test_llm_suggester_uses_complete():
    seen = {}
    def fake_complete(prompt):
        seen["prompt"] = prompt
        return "trope\n"
    s = LLMSuggester(fake_complete)
    assert s.suggest(_rec(), "repair") is Label.TROPE
    assert "repair" in seen["prompt"]


def test_baseline_suggester_is_unsure():
    assert BaselineSuggester().suggest(_rec(), "repair") is Label.UNSURE


def test_openrouter_complete_posts_and_reads_choice():
    captured = {}
    def handler(request):
        captured["auth"] = request.headers.get("authorization")
        import json
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "homonym"}}]})
    client = httpx.Client(transport=httpx.MockTransport(handler))
    complete = openrouter_complete("google/gemini-2.0-flash-001", api_key="sk-x", client=client)
    assert complete("hello?") == "homonym"
    assert captured["auth"] == "Bearer sk-x"
    assert captured["body"]["model"] == "google/gemini-2.0-flash-001"
    assert captured["body"]["messages"][0]["content"] == "hello?"
