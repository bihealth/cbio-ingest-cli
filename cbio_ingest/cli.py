from pathlib import Path

import click

from cbio_ingest.api import sanity_check_server
from cbio_ingest.commands.panel import panel
from cbio_ingest.commands.study import study
from cbio_ingest.config import DEFAULT_CONFIG_PATH, load_config


@click.group()
@click.version_option()
@click.option(
    "--config",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_CONFIG_PATH,
    show_default=True,
    help="Path to TOML config file.",
)
@click.option("--url", default=None, envvar="CBIO_URL", help="API base URL.")
@click.option(
    "--token",
    default=None,
    envvar="CBIO_TOKEN",
    help="Bearer token for authentication.",
)
@click.option(
    "--section",
    default="default",
    show_default=True,
    help="Config file section to read from.",
)
@click.pass_context
def cli(ctx: click.Context, config: Path, url: str | None, token: str | None, section: str):
    """cbio-ingest cli main command"""
    ctx.ensure_object(dict)
    cfg = load_config(config).get(section, {})
    url = url or cfg.get("url")
    token = token or cfg.get("token")

    if not url:
        raise click.UsageError(
            "URL is required. Provide --url, set CBIO_URL, or add it to the config file."
        )

    if not token:
        raise click.UsageError(
            "Token is required. Provide --token, set CBIO_TOKEN, or add it to the config file."
        )

    ctx.obj = {"url": url, "token": token}

    sanity_check_server(ctx)


cli.add_command(study)
cli.add_command(panel)
