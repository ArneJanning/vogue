from pathlib import Path
import yaml
from pydantic import BaseModel, Field as PField
from vogue.model import Field
from vogue.disciplines.classify import Classifier


class Term(BaseModel):
    name: str
    notes: str | None = None
    queries: dict[str, str] = PField(default_factory=dict)  # per-source query overrides


class Study(BaseModel):
    root: Path
    name: str
    sources: list[str]
    keep_fields: list[Field] = PField(default_factory=lambda: [Field.HUMANITIES])
    terms: list[Term] = PField(default_factory=list)
    discipline_overrides: list[dict] = PField(default_factory=list)

    @classmethod
    def load(cls, root: str | Path) -> "Study":
        root = Path(root)
        sy = yaml.safe_load((root / "study.yaml").read_text(encoding="utf-8"))
        ty = yaml.safe_load((root / "terms.yaml").read_text(encoding="utf-8"))
        dy = {}
        dpath = root / "disciplines.yaml"
        if dpath.exists():
            dy = yaml.safe_load(dpath.read_text(encoding="utf-8")) or {}
        return cls(
            root=root, name=sy["name"], sources=sy["sources"],
            keep_fields=[Field(f) for f in sy.get("keep_fields", ["humanities"])],
            terms=[Term(**t) for t in ty.get("terms", [])],
            discipline_overrides=dy.get("overrides", []),
        )

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def codings_dir(self) -> Path:
        return self.root / "codings"

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    def classifier(self) -> Classifier:
        c = Classifier.default()
        return c.with_overrides(self.discipline_overrides) if self.discipline_overrides else c
