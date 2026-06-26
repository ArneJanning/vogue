from vogue.model import Record
from vogue.disciplines.classify import Classifier


def reconstruct_abstract(inverted: dict | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text in order."""
    if not inverted:
        return None
    pos: dict[int, str] = {}
    for word, idxs in inverted.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos)) or None


def parse_work(work: dict, classifier: Classifier | None = None) -> Record:
    clf = classifier or Classifier.default()
    wid = work["id"].rsplit("/", 1)[-1]
    topic = work.get("primary_topic") or {}
    disc = ((topic.get("field") or {}).get("display_name")) or ""
    return Record(
        source="openalex",
        id=wid,
        title=work.get("display_name") or "",
        year=work.get("publication_year"),
        discipline_raw=disc,
        field=clf.classify(disc),
        work_type=work.get("type") or "",
        url=work["id"],
        abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
        raw=work,
    )
