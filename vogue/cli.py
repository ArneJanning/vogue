import typer
from vogue.study import Study
from vogue import pipeline

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


if __name__ == "__main__":
    app()
