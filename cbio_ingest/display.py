from datetime import datetime

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


def print_table(rows: list[dict]) -> None:
    if not rows:
        Console().print("[dim]No entries found.[/]")
        return

    table = Table(show_header=True, box=box.SIMPLE)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Date Created")
    table.add_column("Status")

    for row in rows:
        table.add_row(
            str(row.get("id") or "-"),
            row.get("name", "-"),
            _fmt_dt(row.get("date_ingested")),
            color_status(row.get("status", "-")),
        )

    Console().print(table)


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
