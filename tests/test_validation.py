from unittest.mock import patch

import responses as rsps
from click.testing import CliRunner

from cbio_ingest.cli import cli

BASE = "http://testserver"

VALIDATION_LOG = {
    "timestamp": "2026-05-18T12:38:51.092748+00:00",
    "level": "INFO",
    "reporter": "worker",
    "message": "Validation completed.",
}

VALIDATION = {
    "id": 1,
    "name": "study_tcga",
    "date": "2026-05-18T12:00:00+00:00",
    "status": "completed",
    "study_id": "study_tcga",
    "logs": [VALIDATION_LOG],
}


@rsps.activate
def test_validations_list(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/validations/", json=[VALIDATION])

    result = runner.invoke(cli, cli_args + ["validation", "list"])

    assert result.exit_code == 0
    assert "study_tcga" in result.output
    assert "study_tcga.html" in result.output
    assert rsps.calls[0].request.headers["Authorization"] == "Bearer test-token"


@rsps.activate
def test_validations_list_empty(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/validations/", json=[])

    result = runner.invoke(cli, cli_args + ["validation", "list"])

    assert result.exit_code == 0
    assert "No entries found." in result.output


@rsps.activate
def test_validations_get(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=VALIDATION)

    result = runner.invoke(cli, cli_args + ["validation", "get", "1"])

    assert result.exit_code == 0
    assert "study_tcga" in result.output
    assert "study_tcga.html" in result.output
    assert "Validation completed." in result.output


@rsps.activate
def test_validations_get_without_logs(runner: CliRunner, cli_args: list[str]) -> None:
    validation = {key: value for key, value in VALIDATION.items() if key != "logs"}
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=validation)

    result = runner.invoke(cli, cli_args + ["validation", "get", "1"])

    assert result.exit_code == 0
    assert "study_tcga" in result.output
    assert "No logs." in result.output


@rsps.activate
def test_validations_get_http_error(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/validations/99", json={"detail": "Not found"}, status=404)
    rsps.add(rsps.GET, f"{BASE}/", json={"title": "cBioPortal Ingest API"})

    result = runner.invoke(cli, cli_args + ["validation", "get", "99"])

    assert result.exit_code != 0
    assert "HTTP 404: Not found" in result.output


def test_validations_get_rejects_non_integer_id(runner: CliRunner, cli_args: list[str]) -> None:
    result = runner.invoke(cli, cli_args + ["validation", "get", "not-an-id"])

    assert result.exit_code != 0
    assert "Invalid value for 'VALIDATION_ID'" in result.output


@rsps.activate
def test_validations_get_follow_already_completed(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=VALIDATION)

    with patch("cbio_ingest.commands.validation.time.sleep") as sleep:
        result = runner.invoke(cli, cli_args + ["validation", "get", "1", "--follow"])

    assert result.exit_code == 0
    assert "Validation completed." in result.output
    assert len(rsps.calls) == 1
    sleep.assert_not_called()


@rsps.activate
def test_validations_get_follow_already_failed(runner: CliRunner, cli_args: list[str]) -> None:
    failed = {**VALIDATION, "status": "failed"}
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=failed)

    with patch("cbio_ingest.commands.validation.time.sleep") as sleep:
        result = runner.invoke(cli, cli_args + ["validation", "get", "1", "--follow"])

    assert result.exit_code == 0
    assert "failed" in result.output
    assert len(rsps.calls) == 1
    sleep.assert_not_called()


@rsps.activate
def test_validations_get_follow_polls_until_complete_and_streams_new_logs(
    runner: CliRunner, cli_args: list[str]
) -> None:
    queued_log = {
        **VALIDATION_LOG,
        "level": "WARNING",
        "message": "Validation queued.",
    }
    checked_log = {
        **VALIDATION_LOG,
        "message": "Checked clinical data.",
    }
    in_progress = {
        **VALIDATION,
        "status": "in_progress",
        "logs": [queued_log],
    }
    still_running = {
        **VALIDATION,
        "status": "in_progress",
        "logs": [queued_log, checked_log],
    }
    completed = {
        **VALIDATION,
        "logs": [queued_log, checked_log, VALIDATION_LOG],
    }
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=in_progress)
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=still_running)
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=completed)

    with patch("cbio_ingest.commands.validation.time.sleep") as sleep:
        result = runner.invoke(cli, cli_args + ["validation", "get", "1", "--follow"])

    assert result.exit_code == 0
    assert result.output.count("Validation queued.") == 1
    assert "Checked clinical data." in result.output
    assert "Validation completed." in result.output
    assert len(rsps.calls) == 3
    assert sleep.call_count == 2


@rsps.activate
def test_validations_get_follow_stops_on_failure(runner: CliRunner, cli_args: list[str]) -> None:
    in_progress = {**VALIDATION, "status": "in_progress", "logs": []}
    failed = {
        **VALIDATION,
        "status": "failed",
        "logs": [
            {
                **VALIDATION_LOG,
                "level": "ERROR",
                "message": "Validation failed.",
            }
        ],
    }
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=in_progress)
    rsps.add(rsps.GET, f"{BASE}/validations/1", json=failed)

    with patch("cbio_ingest.commands.validation.time.sleep") as sleep:
        result = runner.invoke(cli, cli_args + ["validation", "get", "1", "--follow"])

    assert result.exit_code == 0
    assert "Validation failed." in result.output
    assert "failed" in result.output
    assert len(rsps.calls) == 2
    sleep.assert_called_once_with(2)


@rsps.activate
def test_validations_delete(runner: CliRunner, cli_args: list[str]) -> None:
    rsps.add(rsps.DELETE, f"{BASE}/validations/1", json={})

    result = runner.invoke(cli, cli_args + ["validation", "delete", "1"])

    assert result.exit_code == 0
    assert "Validation 1 deleted." in result.output
    assert rsps.calls[0].request.method == "DELETE"
