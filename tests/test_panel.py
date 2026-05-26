from unittest.mock import patch

import responses as rsps
from click.testing import CliRunner

from cbio_ingest.cli import cli

BASE = "http://testserver"

PANEL = {
    "id": 1,
    "name": "test_panel",
    "status": "completed",
    "date_ingested": "2026-05-18T12:00:00+00:00",
    "logs": [
        {
            "timestamp": "2026-05-18T12:38:51.092748+00:00",
            "level": "INFO",
            "reporter": "worker",
            "message": "Panel ingestion completed.",
        }
    ],
}


@rsps.activate
def test_panels_list(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/panels/", json=[PANEL])
    result = runner.invoke(cli, cli_args + ["panel", "list"])
    assert result.exit_code == 0
    assert "test_panel" in result.output


@rsps.activate
def test_panels_get(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/panels/1", json=PANEL)
    result = runner.invoke(cli, cli_args + ["panel", "get", "1"])
    assert result.exit_code == 0
    assert "test_panel" in result.output
    assert "Panel ingestion completed." in result.output


@rsps.activate
def test_panels_ingest(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.POST, f"{BASE}/panels/", json=PANEL, status=201)
    result = runner.invoke(cli, cli_args + ["panel", "ingest", "test_panel"])
    assert result.exit_code == 0
    assert "Ingestion job submitted" in result.output
    assert "test_panel" in result.output


@rsps.activate
def test_panels_ingest_force_and_keep_logs(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(
        rsps.POST,
        f"{BASE}/panels/",
        json=PANEL,
        status=201,
        match=[rsps.matchers.query_param_matcher({"force": "true", "keep_logs": "true"})],
    )
    result = runner.invoke(
        cli, cli_args + ["panel", "ingest", "test_panel", "--force", "--keep-logs"]
    )
    assert result.exit_code == 0
    assert "Ingestion job submitted" in result.output
    assert "test_panel" in result.output


@rsps.activate
def test_panels_delete(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.DELETE, f"{BASE}/panels/1", json={})
    result = runner.invoke(cli, cli_args + ["panel", "delete", "1"])
    assert result.exit_code == 0
    assert "deleted" in result.output


@rsps.activate
def test_panels_list_empty(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/panels/", json=[])
    result = runner.invoke(cli, cli_args + ["panel", "list"])
    assert result.exit_code == 0


@rsps.activate
def test_panels_get_http_error(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/panels/99", json={"detail": "Not found"}, status=404)
    result = runner.invoke(cli, cli_args + ["panel", "get", "99"])
    assert result.exit_code != 0
    assert "404" in result.output


@rsps.activate
def test_panels_get_follow_already_terminal(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/panels/1", json=PANEL)
    result = runner.invoke(cli, cli_args + ["panel", "get", "1", "--follow"])
    assert result.exit_code == 0
    assert "test_panel" in result.output
    assert len(rsps.calls) == 1


@rsps.activate
def test_panels_get_follow_polls_until_complete(runner: CliRunner, cli_args: list[str]) -> None:
    in_progress = {**PANEL, "status": "in_progress", "logs": []}
    rsps.add(rsps.GET, f"{BASE}/panels/1", json=in_progress)
    rsps.add(rsps.GET, f"{BASE}/panels/1", json=PANEL)
    with patch("cbio_ingest.commands.panel.time.sleep"):
        result = runner.invoke(cli, cli_args + ["panel", "get", "1", "--follow"])
    assert result.exit_code == 0
    assert "Panel ingestion completed." in result.output
    assert len(rsps.calls) == 2
