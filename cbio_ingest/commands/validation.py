import click

from cbio_ingest.client import TERMINAL_STATUSES, poll_job
from cbio_ingest.commands._shared import get_client, translate_errors
from cbio_ingest.display import print_logs, print_table_validation


@click.group()
def validation():
    """Manage validations."""
    pass


@validation.command("list")
@click.pass_context
def validation_list(ctx: click.Context):
    """List all validations."""
    client = get_client(ctx)
    with translate_errors():
        validations = client.list_validations()
    print_table_validation(validations)


@validation.command("get")
@click.argument("validation_id", type=int)
@click.option("--follow", is_flag=True, help="Poll and stream logs until the job finishes.")
@click.pass_context
def validation_get(ctx: click.Context, validation_id: int, follow: bool):
    """Fetch a single validation by ID."""
    client = get_client(ctx)
    with translate_errors():
        data = client.get_validation(validation_id)
        print_table_validation([data])
        print_logs(data.get("logs", []))

        if follow and data.get("status") not in TERMINAL_STATUSES:
            seen = len(data.get("logs", []))
            for data in poll_job(data, lambda: client.get_validation(validation_id)):
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
    client = get_client(ctx)
    with translate_errors():
        client.delete_validation(validation_id)
    click.echo(f"Validation {validation_id} deleted.")
