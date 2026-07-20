import click

from cbio_ingest.client import TERMINAL_STATUSES, poll_job
from cbio_ingest.commands._shared import get_client, translate_errors
from cbio_ingest.display import print_logs, print_table_panel


@click.group()
def panel():
    """Manage panels."""
    pass


@panel.command("list")
@click.pass_context
def panel_list(ctx: click.Context):
    """List all available and imported panels."""
    client = get_client(ctx)
    with translate_errors():
        panels = client.list_panels()
    print_table_panel(panels)


@panel.command("get")
@click.argument("panel_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def panel_get(ctx: click.Context, panel_id: int, follow: bool):
    """Fetch a single panel by ID."""
    client = get_client(ctx)
    with translate_errors():
        data = client.get_panel(panel_id)
        print_table_panel([data])
        print_logs(data.get("logs", []))

        if follow and data.get("status") not in TERMINAL_STATUSES:
            seen = len(data.get("logs", []))
            for data in poll_job(data, lambda: client.get_panel(panel_id)):
                new_logs = data.get("logs", [])[seen:]
                if new_logs:
                    print_logs(new_logs, show_header=False)
                seen = len(data.get("logs", []))
            print_table_panel([data])


@panel.command("ingest")
@click.argument("name", type=str)
@click.option("--force", is_flag=True, default=False, help="Force re-ingestion if already exists.")
@click.pass_context
def panel_ingest(ctx: click.Context, name: str, force: bool):
    """Ingest a panel into cBioPortal."""
    client = get_client(ctx)
    with translate_errors():
        data = client.ingest_panel(name, force=force)
    click.echo(
        f"Ingestion job submitted for panel '{data.get('name', name)}' (id: {data.get('id', '?')})."
    )


@panel.command("delete")
@click.argument("panel_id", type=int)
@click.pass_context
def panel_delete(ctx: click.Context, panel_id: int):
    """Delete a panel from cBioPortal."""
    client = get_client(ctx)
    with translate_errors():
        client.delete_panel(panel_id)
    click.echo(f"Panel {panel_id} deleted.")
