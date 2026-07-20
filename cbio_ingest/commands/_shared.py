"""Shared helpers that bridge the click CLI and the (click-agnostic) `CBioIngestClient`."""

from collections.abc import Iterator
from contextlib import contextmanager

import click

from cbio_ingest.client import CBioIngestClient, CBioIngestError


def get_client(ctx: click.Context) -> CBioIngestClient:
    """Build a `CBioIngestClient` from the CLI's configuration context."""
    cfg = ctx.obj
    return CBioIngestClient(cfg["url"], cfg["token"])


@contextmanager
def translate_errors() -> Iterator[None]:
    """Translate `CBioIngestError`s raised by the client into `click.ClickException`s."""
    try:
        yield
    except CBioIngestError as e:
        raise click.ClickException(str(e)) from e
