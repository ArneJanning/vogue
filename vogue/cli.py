import datetime
import typer
from vogue.study import Study
from vogue import pipeline
from vogue.coding import CodingStore, Coding, Label, uncoded
from vogue.coding import SuggestionStore, Suggestion
from vogue.suggest.core import LLMSuggester, BaselineSuggester, openrouter_complete
from vogue.analysis import build_overlay, render_report, cross_correlate
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
LABEL_TO_KEY = {v: k for k, v in KEYMAP.items()}


@app.command()
def code(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
         coder: str = typer.Option("", help="name recorded with each coding"),
         limit: int = typer.Option(None, help="cap records fetched")):
    """Interactively label discipline-filtered records as trope/adjacent/homonym/literal/unsure.

    Idempotent: only records without an existing coding are surfaced. If a suggestions file
    exists (see `vogue suggest`), the machine suggestion is offered as the default.
    """
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term, limit=limit)
    kept = pipeline.funnel_for_records(records, study.keep_fields).kept
    store = CodingStore(study.codings_dir / f"{term}.csv")
    suggestions = SuggestionStore(study.codings_dir / f"{term}.suggestions.csv").load()
    already = store.coded_keys()
    todo = uncoded(kept, already)
    typer.echo(f"{len(todo)} new to code, {len(already)} already coded")
    today = datetime.date.today().isoformat()
    for r in todo:
        sugg = suggestions.get(r.key)
        typer.echo(f"\n{r.year}  [{r.discipline_raw}]  {r.title}\n{r.url}")
        prompt = "label [t]rope [a]djacent [h]omonym [l]iteral [u]nsure [s]kip [q]uit"
        if sugg is not None:
            prompt += f"  (suggested: {sugg.suggested.value})"
        default_key = LABEL_TO_KEY.get(sugg.suggested) if sugg is not None else ""
        ans = typer.prompt(prompt, default=default_key).strip().lower()
        if ans == "q":
            break
        if ans == "s" or ans not in KEYMAP:
            continue
        store.append(Coding(key=r.key, term=term, label=KEYMAP[ans], coder=coder,
                            coded_at=today, suggested=sugg.suggested.value if sugg else ""))
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


@app.command()
def leadlag(study_dir: str, term: str = typer.Option(...),
            lead: str = typer.Option("openalex:raw", help="series expected to lead"),
            lag: str = typer.Option("gepris:coded_trope", help="series expected to lag"),
            method: str = typer.Option("zscore", help="detrend: zscore|diff|peak|none"),
            max_lag: int = typer.Option(8), limit: int = typer.Option(2000)):
    """Estimate how many years `lead` precedes `lag` via detrended cross-correlation."""
    study = Study.load(study_dir)
    overlay = build_overlay(study, term, limit=limit)
    a, b = overlay.series.get(lag), overlay.series.get(lead)
    if not a or not b:
        typer.echo(f"need both series present; available: {sorted(overlay.series)}")
        raise typer.Exit(1)
    res = cross_correlate(a, b, max_lag=max_lag, method=method)
    if res is None:
        typer.echo("insufficient overlapping data for a lead-lag estimate")
        raise typer.Exit(1)
    direction = "leads" if res.best_lag >= 0 else "lags"
    typer.echo(
        f"{term}: '{lead}' {direction} '{lag}' by {abs(res.best_lag)} years "
        f"(r={res.best_corr:.2f}, method={method}, n={res.n_pairs})")


def _make_suggester(model: str):
    if model == "rules":
        return BaselineSuggester()
    return LLMSuggester(openrouter_complete(model))


@app.command()
def suggest(study_dir: str, source: str = typer.Option(...), term: str = typer.Option(...),
            model: str = typer.Option("z-ai/glm-5.2",
                                      help="OpenRouter model slug, or 'rules' for the offline baseline"),
            limit: int = typer.Option(None, help="cap records fetched")):
    """Pre-label uncoded records with an LLM (via OpenRouter) into a side file.

    Suggestions are never authoritative — `code` shows them as defaults for human confirmation.
    Needs OPENROUTER_API_KEY for real models; use --model rules for an offline no-op baseline.
    """
    study = Study.load(study_dir)
    records = pipeline.fetch_term(study, source, term, limit=limit)
    kept = pipeline.funnel_for_records(records, study.keep_fields).kept
    coded = CodingStore(study.codings_dir / f"{term}.csv").coded_keys()
    sstore = SuggestionStore(study.codings_dir / f"{term}.suggestions.csv")
    have = sstore.suggested_keys()
    todo = [r for r in kept if r.key not in coded and r.key not in have]
    suggester = _make_suggester(model)
    today = datetime.date.today().isoformat()
    for r in todo:
        sstore.append(Suggestion(key=r.key, term=term, suggested=suggester.suggest(r, term),
                                 model=model, suggested_at=today))
    typer.echo(f"suggested {len(todo)} records ({len(have)} already had suggestions)")


if __name__ == "__main__":
    app()
