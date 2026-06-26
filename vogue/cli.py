import datetime
import typer
from vogue.study import Study
from vogue import pipeline
from vogue.coding import CodingStore, Coding, Label, uncoded

app = typer.Typer(help="Track the Begriffskonjunktur of scholarly concepts.")


@app.callback()
def _main() -> None:
    """vogue CLI."""


@app.command()
def funnel(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...)):
    """Fetch a term from a source and print the raw -> discipline funnel."""
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term)
    f = pipeline.funnel_for_records(records, study.keep_fields)
    typer.echo(f"{term} [{source}]  raw={f.raw}  discipline={f.discipline}")


KEYMAP = {"t": Label.TROPE, "a": Label.ADJACENT, "h": Label.HOMONYM,
          "l": Label.LITERAL, "u": Label.UNSURE}


@app.command()
def code(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
         coder: str = typer.Option("", help="name recorded with each coding")):
    """Interactively label discipline-filtered records as trope/adjacent/homonym/literal/unsure.

    Idempotent: only records without an existing coding are surfaced.
    """
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term)
    kept = pipeline.funnel_for_records(records, study.keep_fields).kept
    store = CodingStore(study.codings_dir / f"{term}.csv")
    already = store.coded_keys()
    todo = uncoded(kept, already)
    typer.echo(f"{len(todo)} new to code, {len(already)} already coded")
    today = datetime.date.today().isoformat()
    for r in todo:
        typer.echo(f"\n{r.year}  [{r.discipline_raw}]  {r.title}\n{r.url}")
        ans = typer.prompt(
            "label [t]rope [a]djacent [h]omonym [l]iteral [u]nsure [s]kip [q]uit"
        ).strip().lower()
        if ans == "q":
            break
        if ans == "s" or ans not in KEYMAP:
            continue
        store.append(Coding(key=r.key, term=term, label=KEYMAP[ans],
                            coder=coder, coded_at=today))
    typer.echo("done")


@app.command()
def tally(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...)):
    """Print the full funnel for a term: raw -> discipline -> coded, broken down by label."""
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term)
    funnel = pipeline.funnel_for_records(records, study.keep_fields)
    store = CodingStore(study.codings_dir / f"{term}.csv")
    counts = pipeline.coded_tally(funnel.kept, store.load())
    parts = [f"{term} [{source}]", f"raw={funnel.raw}", f"discipline={funnel.discipline}",
             f"coded={sum(counts.values())}"]
    parts += [f"{lab.value}={counts.get(lab, 0)}" for lab in Label]
    typer.echo("  ".join(parts))


if __name__ == "__main__":
    app()
