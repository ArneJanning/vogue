import datetime
import typer
from vogue.study import Study
from vogue import pipeline
from vogue.coding import CodingStore, Coding, Label, uncoded
from vogue.analysis import build_overlay, render_report
from vogue.plotting import plot_overlay

app = typer.Typer(help="Track the Begriffskonjunktur of scholarly concepts.")


@app.callback()
def _main() -> None:
    """vogue CLI."""


@app.command()
def funnel(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
           limit: int = typer.Option(None, help="cap records fetched (useful for huge OpenAlex result sets)")):
    """Fetch a term from a source and print the raw -> discipline funnel."""
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term, limit=limit)
    f = pipeline.funnel_for_records(records, study.keep_fields)
    typer.echo(f"{term} [{source}]  raw={f.raw}  discipline={f.discipline}")


KEYMAP = {"t": Label.TROPE, "a": Label.ADJACENT, "h": Label.HOMONYM,
          "l": Label.LITERAL, "u": Label.UNSURE}


@app.command()
def code(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
         coder: str = typer.Option("", help="name recorded with each coding"),
         limit: int = typer.Option(None, help="cap records fetched (useful for huge OpenAlex result sets)")):
    """Interactively label discipline-filtered records as trope/adjacent/homonym/literal/unsure.

    Idempotent: only records without an existing coding are surfaced.
    """
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term, limit=limit)
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
def tally(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
          limit: int = typer.Option(None, help="cap records fetched (useful for huge OpenAlex result sets)")):
    """Print the full funnel for a term: raw -> discipline -> coded, broken down by label."""
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term, limit=limit)
    funnel = pipeline.funnel_for_records(records, study.keep_fields)
    store = CodingStore(study.codings_dir / f"{term}.csv")
    counts = pipeline.coded_tally(funnel.kept, store.load())
    parts = [f"{term} [{source}]", f"raw={funnel.raw}", f"discipline={funnel.discipline}",
             f"coded={sum(counts.values())}"]
    parts += [f"{lab.value}={counts.get(lab, 0)}" for lab in Label]
    typer.echo("  ".join(parts))


@app.command()
def report(study_dir: str, term: str = typer.Option(...),
           limit: int = typer.Option(2000, help="cap per-source fetch for the coded subset")):
    """Build the overlay (raw + coded curves) and write out/<term>-report.md + figure."""
    study = Study.load(study_dir)
    overlay = build_overlay(study, term, limit=limit)
    study.out_dir.mkdir(parents=True, exist_ok=True)
    fig = study.out_dir / f"{term}-overlay.png"
    plot_overlay(overlay, fig)
    md = study.out_dir / f"{term}-report.md"
    md.write_text(render_report(overlay, fig.name), encoding="utf-8")
    typer.echo(f"wrote {md} and {fig}")


if __name__ == "__main__":
    app()
