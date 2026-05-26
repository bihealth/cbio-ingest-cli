import time

import click

from cbio_ingest.api import api_url, make_session
from cbio_ingest.display import print_logs, print_table

_TERMINAL_STATUSES = {"completed", "failed"}


@click.group()
def panel():
    """Manage panels."""
    pass


@panel.command("list")
@click.pass_context
def panel_list(ctx: click.Context):
    """List all available and imported panels."""
    response = make_session(ctx).get(api_url(ctx, "/panels/"), params={"all": ""})
    print_table(response.json())


@panel.command("get")
@click.argument("panel_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def panel_get(ctx: click.Context, panel_id: int, follow: bool):
    """Fetch a single panel by ID."""
    session = make_session(ctx)
    url = api_url(ctx, f"/panels/{panel_id}")
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


@panel.command("ingest")
@click.argument("name", type=str)
@click.option("--force", is_flag=True, default=False, help="Force re-ingestion if already exists.")
@click.option(
    "--keep-logs", is_flag=True, default=False, help="Retain logs after ingestion completes."
)
@click.pass_context
def panel_ingest(ctx: click.Context, name: str, force: bool, keep_logs: bool):
    """Ingest a panel into cBioPortal."""
    response = make_session(ctx).post(
        api_url(ctx, "/panels/"),
        json={"name": name},
        params={
            "force": str(force).lower(),
            "keep_logs": str(keep_logs).lower(),
        },
    )
    data = response.json()
    click.echo(
        f"Ingestion job submitted for panel '{data.get('name', name)}' (id: {data.get('id', '?')})."
    )


@panel.command("delete")
@click.argument("panel_id", type=int)
@click.pass_context
def panel_delete(ctx: click.Context, panel_id: int):
    """Delete a panel from cBioPortal."""
    make_session(ctx).delete(api_url(ctx, f"/panels/{panel_id}"))
    click.echo(f"Panel {panel_id} deleted.")
