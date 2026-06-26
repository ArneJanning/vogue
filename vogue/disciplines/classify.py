from importlib.resources import files
import yaml
from vogue.model import Field


class Classifier:
    def __init__(self, rules: list[dict]):
        # each rule: {"match": <lowercase substring>, "field": <Field value>}
        self._rules = [(r["match"].lower(), Field(r["field"])) for r in rules]

    @classmethod
    def default(cls) -> "Classifier":
        text = files("vogue.disciplines").joinpath("defaults.yaml").read_text(encoding="utf-8")
        return cls(yaml.safe_load(text)["rules"])

    def with_overrides(self, overrides: list[dict]) -> "Classifier":
        merged = [{"match": m, "field": f.value} for m, f in self._rules]
        return Classifier(overrides + merged)  # overrides checked first

    def classify(self, discipline_raw: str) -> Field:
        d = (discipline_raw or "").lower()
        if not d:
            return Field.UNKNOWN
        for sub, field in self._rules:
            if sub in d:
                return field
        return Field.UNKNOWN
