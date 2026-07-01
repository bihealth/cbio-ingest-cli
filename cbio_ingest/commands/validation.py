import time

import click

from cbio_ingest.api import api_url, make_session
from cbio_ingest.display import print_logs, print_table_validation

_TERMINAL_STATUSES = {"completed", "failed"}


@click.group()
def validation():
    """Manage validations."""
    pass


@validation.command("list")
@click.pass_context
def validation_list(ctx: click.Context):
    """List all validations."""
    response = make_session(ctx).get(api_url(ctx, "/validations/"))
    print_table_validation(response.json())


@validation.command("get")
@click.argument("validation_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def validation_get(ctx: click.Context, validation_id: int, follow: bool):
    """Fetch a single validation by ID."""
    session = make_session(ctx)
    url = api_url(ctx, f"/validations/{validation_id}")
    data = session.get(url).json()
    print_table_validation([data])
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
        print_table_validation([data])


@validation.command("delete")
@click.argument("validation_id", type=int)
@click.pass_context
def validation_delete(ctx: click.Context, validation_id: int):
    """Delete a validation."""
    make_session(ctx).delete(api_url(ctx, f"/validations/{validation_id}"))
    click.echo(f"Validation {validation_id} deleted.")
