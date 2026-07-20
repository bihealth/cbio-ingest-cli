import click

from cbio_ingest.client import TERMINAL_STATUSES, poll_job
from cbio_ingest.commands._shared import get_client, translate_errors
from cbio_ingest.display import print_logs, print_table_study


@click.group()
def study():
    """Manage studies."""
    pass


@study.command("list")
@click.pass_context
def study_list(ctx: click.Context):
    """List all available and imported studies."""
    client = get_client(ctx)
    with translate_errors():
        studies = client.list_studies()
    print_table_study(studies)


@study.command("get")
@click.argument("study_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def study_get(ctx: click.Context, study_id: int, follow: bool):
    """Fetch a single study by ID."""
    client = get_client(ctx)
    with translate_errors():
        data = client.get_study(study_id)
        print_table_study([data])
        print_logs(data.get("logs", []))

        if follow and data.get("status") not in TERMINAL_STATUSES:
            seen = len(data.get("logs", []))
            for data in poll_job(data, lambda: client.get_study(study_id)):
                new_logs = data.get("logs", [])[seen:]
                if new_logs:
                    print_logs(new_logs, show_header=False)
                seen = len(data.get("logs", []))
            print_table_study([data])


@study.command("ingest")
@click.argument("name", type=str)
@click.option("--force", is_flag=True, default=False, help="Force re-ingestion if already exists.")
@click.pass_context
def study_ingest(ctx: click.Context, name: str, force: bool):
    """Ingest a study into cBioPortal."""
    client = get_client(ctx)
    with translate_errors():
        data = client.ingest_study(name, force=force)
    click.echo(
        f"Ingestion job submitted for study '{data.get('name', name)}' (id: {data.get('id', '?')})."
    )


@study.command("validate")
@click.argument("name", type=str)
@click.option("--force", is_flag=True, default=False, help="Force re-validation if already exists.")
@click.pass_context
def validate_study(ctx: click.Context, name: str, force: bool):
    """Ingest a validation into cBioPortal."""
    client = get_client(ctx)
    with translate_errors():
        data = client.validate_study(name, force=force)
    click.echo(
        f"Validation job submitted for study '{data.get('name', name)}' "
        f"(id: {data.get('id', '?')})."
    )


@study.command("delete")
@click.argument("study_id", type=int)
@click.pass_context
def study_delete(ctx: click.Context, study_id: int):
    """Delete a study from cBioPortal."""
    client = get_client(ctx)
    with translate_errors():
        client.delete_study(study_id)
    click.echo(f"Study {study_id} deleted.")
