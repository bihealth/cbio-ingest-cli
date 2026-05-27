import click
import pytest
import requests
import responses as rsps

from cbio_ingest.api import ApiSession, sanity_check_server


@pytest.fixture
def session() -> ApiSession:
    return ApiSession()


@rsps.activate
def test_successful_request(session: ApiSession) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/", json=[], status=200)
    response = session.get("http://testserver/studies/")
    assert response.status_code == 200


@rsps.activate
def test_http_error_uses_api_detail(session: ApiSession) -> None:
    rsps.add(
        rsps.GET,
        "http://testserver/studies/99",
        json={"detail": "Not found"},
        status=404,
    )
    with pytest.raises(click.ClickException, match="HTTP 404: Not found"):
        session.get("http://testserver/studies/99")


@rsps.activate
def test_http_error_falls_back_to_text(session: ApiSession) -> None:
    rsps.add(rsps.GET, "http://testserver/studies/99", body=b"Internal error", status=500)
    with pytest.raises(click.ClickException, match="HTTP 500"):
        session.get("http://testserver/studies/99")


@rsps.activate
def test_connection_error_raises_click_exception(session: ApiSession) -> None:
    rsps.add(rsps.GET, "http://testserver/", body=requests.ConnectionError())
    with pytest.raises(click.ClickException, match="Could not connect"):
        session.get("http://testserver/")


@rsps.activate
def test_timeout_raises_click_exception(session: ApiSession) -> None:
    rsps.add(rsps.GET, "http://testserver/", body=requests.Timeout())
    with pytest.raises(click.ClickException, match="timed out"):
        session.get("http://testserver/")


def make_fake_ctx(url="http://testserver", token="t"):
    ctx = click.Context(click.Command("dummy"))
    ctx.obj = {"url": url, "token": token}
    return ctx


@rsps.activate
def test_sanity_check_server_valid(monkeypatch):
    ctx = make_fake_ctx()
    rsps.add(rsps.GET, "http://testserver/", json={"title": "cBioPortal Ingest API"}, status=200)
    # Should not raise
    sanity_check_server(ctx)


@rsps.activate
def test_sanity_check_server_invalid_title(monkeypatch):
    ctx = make_fake_ctx()
    rsps.add(rsps.GET, "http://testserver/", json={"title": "Not cBioPortal"}, status=200)
    with pytest.raises(click.ClickException, match="does not seem to be the cbio-ingest API"):
        sanity_check_server(ctx)


@rsps.activate
def test_sanity_check_server_malformed_json(monkeypatch):
    ctx = make_fake_ctx()
    rsps.add(rsps.GET, "http://testserver/", body="not json", status=200)
    with pytest.raises(click.ClickException, match="does not seem to be the cbio-ingest API"):
        sanity_check_server(ctx)
