import time

import click

from cbio_ingest.api import api_url, make_session
from cbio_ingest.display import print_logs, print_table

_TERMINAL_STATUSES = {"completed", "failed"}


@click.group()
def study():
    """Manage studies."""
    pass


@study.command("list")
@click.pass_context
def study_list(ctx: click.Context):
    """List all available and imported studies."""
    response = make_session(ctx).get(api_url(ctx, "/studies/"), params={"all": ""})
    print_table(response.json())


@study.command("get")
@click.argument("study_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def study_get(ctx: click.Context, study_id: int, follow: bool):
    """Fetch a single study by ID."""
    session = make_session(ctx)
    url = api_url(ctx, f"/studies/{study_id}")
    data = session.get(url).json()
    print_table([data])
    print_logs(data.get("logs", []))

    if follow and data.get("status") not in _TERMINAL_STATUSES:
        seen = len(data.get("logs", []))
        while data.get("status") not in _TERMINAL_STATUSES:
            time.sleep(2)
            data = session.get(url).json()
            new_logs = data.get("logs", [])[seen:]
            if new_logs:
                print_logs(new_logs, show_header=False)
            seen = len(data.get("logs", []))
        print_table([data])


@study.command("ingest")
@click.argument("name", type=str)
@click.option("--force", is_flag=True, default=False, help="Force re-ingestion if already exists.")
@click.option(
    "--keep-logs", is_flag=True, default=False, help="Retain logs after ingestion completes."
)
@click.pass_context
def study_ingest(ctx: click.Context, name: str, force: bool, keep_logs: bool):
    """Ingest a study into cBioPortal."""
    response = make_session(ctx).post(
        api_url(ctx, "/studies/"),
        json={"name": name},
        params={
            "force": str(force).lower(),
            "keep_logs": str(keep_logs).lower(),
        },
    )
    data = response.json()
    click.echo(
        f"Ingestion job submitted for study '{data.get('name', name)}' (id: {data.get('id', '?')})."
    )


@study.command("delete")
@click.argument("study_id", type=int)
@click.pass_context
def study_delete(ctx: click.Context, study_id: int):
    """Delete a study from cBioPortal."""
    make_session(ctx).delete(api_url(ctx, f"/studies/{study_id}"))
    click.echo(f"Study {study_id} deleted.")
