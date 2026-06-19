from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table

_STATUS_STYLE: dict[str, str] = {
    "completed": "green",
    "failed": "red",
    "in_progress": "yellow",
    "initial": "blue",
}

_LEVEL_STYLE: dict[str, str] = {
    "INFO": "cyan",
    "WARNING": "yellow",
    "ERROR": "bold red",
}


def color_status(status: str) -> str:
    style = _STATUS_STYLE.get(status)
    return f"[{style}]{status}[/]" if style else status


def _fmt_dt(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def _print_table(
    rows: list[dict], optional_cols: list[tuple[str, Callable[[dict[str, Any]], str]]]
) -> None:
    if not rows:
        Console().print("[dim]No entries found.[/]")
        return

    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Date")
    table.add_column("Status")

    for header in optional_cols:
        table.add_column(header[0])

    for row in rows:
        cols = [
            str(row.get("id") or "-"),
            row.get("name", "-"),
            _fmt_dt(row.get("date")),
            color_status(row.get("status", "-")),
        ]

        for col in optional_cols:
            cols.append(col[1](row))

        table.add_row(*cols)

    Console().print(table)


def print_table_study(rows: list[dict]) -> None:
    cols = [
        ("In Source Folder", lambda row: str(row.get("in_source_folder", "?")).lower()),
        ("Validation ID", lambda row: str(row.get("validation_id", "-"))),
    ]
    _print_table(rows, optional_cols=cols)


def print_table_panel(rows: list[dict]) -> None:
    cols = [
        ("In Source Folder", lambda row: str(row.get("in_source_folder", "?")).lower()),
    ]
    _print_table(rows, optional_cols=cols)


def print_table_validation(rows: list[dict]) -> None:
    cols = [
        ("Report", lambda row: f"{row.get('name')}.html" if row.get("name") else "-"),
        ("Study ID", lambda row: str(row.get("study_id", "-"))),
    ]
    _print_table(rows, optional_cols=cols)


def print_logs(logs: list[dict], show_header: bool = True) -> None:
    console = Console()
    if not logs:
        console.print("[dim]No logs.[/]")
        return

    table = Table(show_header=show_header, box=None, padding=(0, 1))
    table.add_column("Timestamp", style="dim")
    table.add_column("Level", no_wrap=True)
    table.add_column("Reporter", style="dim")
    table.add_column("Message")

    for entry in logs:
        level = entry.get("level", "-")
        style = _LEVEL_STYLE.get(level.upper(), "")
        table.add_row(
            _fmt_dt(entry.get("timestamp")),
            f"[{style}]{level}[/]" if style else level,
            entry.get("reporter", "-"),
            entry.get("message", "-"),
        )

    console.print(table)
