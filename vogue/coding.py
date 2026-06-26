import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from vogue.model import Record


class Label(str, Enum):
    TROPE = "trope"        # the fashionable concept itself
    ADJACENT = "adjacent"  # same fashion-family, not the term (e.g. "maintenance" vs the repair turn)
    HOMONYM = "homonym"    # same string, unrelated technical sense (e.g. conversation-analytic "repair")
    LITERAL = "literal"    # literal activity, not a concept (e.g. archaeological object repair)
    UNSURE = "unsure"


@dataclass
class Coding:
    key: str
    term: str
    label: Label
    suggested: str = ""   # optional machine suggestion (Plan v0.2); blank when human-only
    coder: str = ""
    coded_at: str = ""    # ISO date supplied by the caller
    note: str = ""


FIELDNAMES = ["key", "term", "label", "suggested", "coder", "coded_at", "note"]


class CodingStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict[str, Coding]:
        if not self.path.exists():
            return {}
        out: dict[str, Coding] = {}
        with self.path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                out[row["key"]] = Coding(
                    key=row["key"], term=row["term"], label=Label(row["label"]),
                    suggested=row.get("suggested", ""), coder=row.get("coder", ""),
                    coded_at=row.get("coded_at", ""), note=row.get("note", ""),
                )
        return out

    def append(self, coding: Coding) -> None:
        new = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if new:
                w.writeheader()
            w.writerow({
                "key": coding.key, "term": coding.term, "label": coding.label.value,
                "suggested": coding.suggested, "coder": coding.coder,
                "coded_at": coding.coded_at, "note": coding.note,
            })

    def coded_keys(self) -> set[str]:
        return set(self.load().keys())


def uncoded(records: list[Record], coded_keys: set[str]) -> list[Record]:
    """Records whose key is not yet present in the coding store. Pure; drives idempotent coding."""
    return [r for r in records if r.key not in coded_keys]
