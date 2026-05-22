from unittest.mock import patch

import responses as rsps
from click.testing import CliRunner

from cbio_ingest.cli import cli

BASE = "http://testserver"

STUDY = {
    "id": 1,
    "name": "test_study",
    "status": "completed",
    "date_ingested": "2026-05-18T12:00:00+00:00",
    "logs": [
        {
            "timestamp": "2026-05-18T12:38:51.092748+00:00",
            "level": "INFO",
            "reporter": "worker",
            "message": "Ingestion completed.",
        }
    ],
}


@rsps.activate
def test_studies_list(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/studies/", json=[STUDY])
    result = runner.invoke(cli, cli_args + ["study", "list"])
    assert result.exit_code == 0
    assert "test_study" in result.output


@rsps.activate
def test_studies_get(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/studies/1", json=STUDY)
    result = runner.invoke(cli, cli_args + ["study", "get", "1"])
    assert result.exit_code == 0
    assert "test_study" in result.output
    assert "Ingestion completed." in result.output


@rsps.activate
def test_studies_ingest(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.POST, f"{BASE}/studies/", json=STUDY, status=201)
    result = runner.invoke(cli, cli_args + ["study", "ingest", "test_study"])
    assert result.exit_code == 0
    assert "Ingestion job submitted" in result.output
    assert "test_study" in result.output


@rsps.activate
def test_studies_delete(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.DELETE, f"{BASE}/studies/1", json={})
    result = runner.invoke(cli, cli_args + ["study", "delete", "1"])
    assert result.exit_code == 0
    assert "deleted" in result.output


@rsps.activate
def test_studies_list_empty(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/studies/", json=[])
    result = runner.invoke(cli, cli_args + ["study", "list"])
    assert result.exit_code == 0


@rsps.activate
def test_studies_get_http_error(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/studies/99", json={"detail": "Not found"}, status=404)
    result = runner.invoke(cli, cli_args + ["study", "get", "99"])
    assert result.exit_code != 0
    assert "404" in result.output


@rsps.activate
def test_studies_get_follow_already_terminal(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/studies/1", json=STUDY)
    result = runner.invoke(cli, cli_args + ["study", "get", "1", "--follow"])
    assert result.exit_code == 0
    assert "test_study" in result.output
    assert len(rsps.calls) == 1


@rsps.activate
def test_studies_get_follow_polls_until_complete(runner: CliRunner, cli_args: list[str]) -> None:
    in_progress = {**STUDY, "status": "in_progress", "logs": []}
    rsps.add(rsps.GET, f"{BASE}/studies/1", json=in_progress)
    rsps.add(rsps.GET, f"{BASE}/studies/1", json=STUDY)
    with patch("cbio_ingest.commands.study.time.sleep"):
        result = runner.invoke(cli, cli_args + ["study", "get", "1", "--follow"])
    assert result.exit_code == 0
    assert "Ingestion completed." in result.output
    assert len(rsps.calls) == 2
