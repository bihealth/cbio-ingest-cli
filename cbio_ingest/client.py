"""HTTP client for the cBioPortal Ingest API.

This module has no dependency on `click` (or any other CLI framework) so
that it can eventually be extracted into a standalone client library and
reused outside of this CLI.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from typing import Any

import requests

TERMINAL_STATUSES = {"completed", "failed"}


class CBioIngestError(Exception):
    """Base class for all errors raised by `CBioIngestClient`."""


class ConnectionFailedError(CBioIngestError):
    """Raised when the API server cannot be reached."""


class RequestTimeoutError(CBioIngestError):
    """Raised when a request to the API times out."""


class ApiError(CBioIngestError):
    """Raised when the API responds with an HTTP error status."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class NotACBioIngestApiError(CBioIngestError):
    """Raised when the configured server doesn't look like the cBioPortal Ingest API."""


class CBioIngestClient:
    """Client for the cBioPortal Ingest API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"
        self._session.headers["Accept"] = "application/json"

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, *, check_on_404: bool = True, **kwargs: Any) -> Any:
        try:
            response = self._session.request(method, self._url(path), **kwargs)
        except requests.ConnectionError:
            raise ConnectionFailedError(
                "Could not connect to the API. Is the server running?"
            ) from None
        except requests.Timeout:
            raise RequestTimeoutError("Request timed out.") from None

        if not response.ok:
            # A 404 could mean either "resource not found" or "wrong server
            # entirely". Sanity-check the server to produce a clearer error.
            if response.status_code == 404 and check_on_404:
                try:
                    self.check_server()
                except CBioIngestError as e:
                    raise ApiError(404, str(e)) from None
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(response.status_code, detail)

        return response.json() if response.content else None

    def check_server(self) -> None:
        """Verify that the configured server is a cBioPortal Ingest API instance."""
        fail_msg = "Connected to a server but it does not seem to be the cbio-ingest API."
        try:
            data = self._request("GET", "/", check_on_404=False)
        except requests.exceptions.JSONDecodeError:
            raise NotACBioIngestApiError(fail_msg) from None
        if not isinstance(data, dict) or data.get("title") != "cBioPortal Ingest API":
            raise NotACBioIngestApiError(fail_msg)

    # Studies

    def list_studies(self) -> list[dict]:
        return self._request("GET", "/studies/")

    def get_study(self, study_id: int) -> dict:
        return self._request("GET", f"/studies/{study_id}")

    def ingest_study(self, name: str, force: bool = False) -> dict:
        return self._request(
            "POST", "/studies/", json={"name": name}, params={"force": str(force).lower()}
        )

    def delete_study(self, study_id: int) -> None:
        self._request("DELETE", f"/studies/{study_id}")

    def validate_study(self, name: str, force: bool = False) -> dict:
        return self._request(
            "POST", "/validations/", json={"name": name}, params={"force": str(force).lower()}
        )

    # Panels

    def list_panels(self) -> list[dict]:
        return self._request("GET", "/panels/")

    def get_panel(self, panel_id: int) -> dict:
        return self._request("GET", f"/panels/{panel_id}")

    def ingest_panel(self, name: str, force: bool = False) -> dict:
        return self._request(
            "POST", "/panels/", json={"name": name}, params={"force": str(force).lower()}
        )

    def delete_panel(self, panel_id: int) -> None:
        self._request("DELETE", f"/panels/{panel_id}")

    # Validations

    def list_validations(self) -> list[dict]:
        return self._request("GET", "/validations/")

    def get_validation(self, validation_id: int) -> dict:
        return self._request("GET", f"/validations/{validation_id}")

    def delete_validation(self, validation_id: int) -> None:
        self._request("DELETE", f"/validations/{validation_id}")


def poll_job(
    initial: dict,
    fetch: Callable[[], dict],
    *,
    interval: float = 2.0,
    sleep: Callable[[float], None] | None = None,
) -> Iterator[dict]:
    """Yield successive states of a job until it reaches a terminal status.

    `initial` is the already-fetched current state, used only to decide
    whether polling is needed; it is not re-yielded by this generator.
    """
    sleep = sleep or time.sleep
    data = initial
    while data.get("status") not in TERMINAL_STATUSES:
        sleep(interval)
        data = fetch()
        yield data
