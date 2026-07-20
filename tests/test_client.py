import pytest
import requests
import responses as rsps

from cbio_ingest.client import (
    ApiError,
    CBioIngestClient,
    ConnectionFailedError,
    NotACBioIngestApiError,
    RequestTimeoutError,
)


@pytest.fixture
def client() -> CBioIngestClient:
    return CBioIngestClient("http://testserver", "test-token")


@rsps.activate
def test_successful_request(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/", json=[], status=200)
    assert client.list_studies() == []
    assert rsps.calls[0].request.headers["Authorization"] == "Bearer test-token"


@rsps.activate
def test_http_error_uses_api_detail(client: CBioIngestClient) -> None:
    rsps.add(
        rsps.GET,
        "http://testserver/studies/99",
        json={"detail": "Not found"},
        status=404,
    )
    rsps.add(rsps.GET, "http://testserver/", json={"title": "cBioPortal Ingest API"}, status=200)
    with pytest.raises(ApiError, match="HTTP 404: Not found"):
        client.get_study(99)


@rsps.activate
def test_http_error_falls_back_to_text(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/99", body=b"Internal error", status=500)
    with pytest.raises(ApiError, match="HTTP 500") as exc_info:
        client.get_study(99)
    assert exc_info.value.status_code == 500


@rsps.activate
def test_connection_error_raises(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/", body=requests.ConnectionError())
    with pytest.raises(ConnectionFailedError, match="Could not connect"):
        client.list_studies()


@rsps.activate
def test_timeout_raises(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/", body=requests.Timeout())
    with pytest.raises(RequestTimeoutError, match="timed out"):
        client.list_studies()


@rsps.activate
def test_check_server_valid(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/", json={"title": "cBioPortal Ingest API"}, status=200)
    client.check_server()  # Should not raise


@rsps.activate
def test_check_server_invalid_title(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/", json={"title": "Not cBioPortal"}, status=200)
    with pytest.raises(NotACBioIngestApiError, match="does not seem to be the cbio-ingest API"):
        client.check_server()


@rsps.activate
def test_check_server_malformed_json(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/", body="not json", status=200)
    with pytest.raises(NotACBioIngestApiError, match="does not seem to be the cbio-ingest API"):
        client.check_server()


@rsps.activate
def test_404_reports_wrong_server_when_sanity_check_fails(client: CBioIngestClient) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/99", json={"detail": "Not found"}, status=404)
    rsps.add(rsps.GET, "http://testserver/", json={"title": "Not cBioPortal"}, status=200)
    with pytest.raises(ApiError, match="does not seem to be the cbio-ingest API"):
        client.get_study(99)
