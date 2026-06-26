import os
from typing import Callable, Protocol
import httpx
from vogue.model import Record
from vogue.coding import Label


def build_prompt(record: Record, term: str) -> str:
    abstract = (record.abstract or "")[:500]
    return (
        f'Classify how a research record uses the word "{term}".\n'
        f"Choose exactly one label:\n"
        f'- trope: "{term}" as the fashionable scholarly concept (the "{term} turn")\n'
        f"- adjacent: same intellectual fashion-family but not the term itself\n"
        f"- homonym: the same word in an unrelated technical sense\n"
        f"- literal: a literal activity or object, not a concept\n"
        f"- unsure\n\n"
        f"Record:\n"
        f"  title: {record.title}\n"
        f"  discipline: {record.discipline_raw}\n"
        f"  abstract: {abstract}\n\n"
        f"Answer with one label word only."
    )


def parse_label(text: str) -> Label:
    t = (text or "").strip().lower()
    for lab in Label:           # trope, adjacent, homonym, literal, unsure
        if lab.value in t:
            return lab
    return Label.UNSURE


class Suggester(Protocol):
    def suggest(self, record: Record, term: str) -> Label: ...


class BaselineSuggester:
    """No-LLM fallback: always 'unsure'. Useful offline / without an API key."""

    def suggest(self, record: Record, term: str) -> Label:
        return Label.UNSURE


class LLMSuggester:
    def __init__(self, complete: Callable[[str], str],
                 prompt_builder: Callable[[Record, str], str] = build_prompt):
        self.complete = complete
        self.prompt_builder = prompt_builder

    def suggest(self, record: Record, term: str) -> Label:
        return parse_label(self.complete(self.prompt_builder(record, term)))


def openrouter_complete(model: str, api_key: str | None = None,
                        base_url: str = "https://openrouter.ai/api/v1",
                        client: httpx.Client | None = None) -> Callable[[str], str]:
    """A `complete` callable backed by OpenRouter's OpenAI-compatible chat endpoint."""
    key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Export it, or use --model rules "
            "for the offline baseline.")
    cl = client or httpx.Client(timeout=30)

    def complete(prompt: str) -> str:
        r = cl.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "temperature": 0, "max_tokens": 16,
                  "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    return complete
