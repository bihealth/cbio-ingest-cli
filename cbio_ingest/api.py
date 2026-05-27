from typing import Any

import click
import requests


class ApiSession(requests.Session):
    _ctx: Any

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        cookies: Any = None,
        files: Any = None,
        auth: Any = None,
        timeout: float | tuple[float, float] | None = None,
        allow_redirects: bool = True,
        proxies: dict[str, str] | None = None,
        hooks: Any = None,
        stream: bool | None = None,
        verify: bool | str | None = None,
        cert: Any = None,
        json: Any = None,
    ) -> requests.Response:
        try:
            response = super().request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )
        except requests.ConnectionError:
            raise click.ClickException(
                "Could not connect to the API. Is the server running?"
            ) from None
        except requests.Timeout:
            raise click.ClickException("Request timed out.") from None
        if not response.ok:
            # Only check root if 404, to verify if this is the cbio-ingest API
            if response.status_code == 404 and hasattr(self, "_ctx"):
                from cbio_ingest.api import sanity_check_server

                try:
                    sanity_check_server(self._ctx)
                except click.ClickException as e:
                    raise click.ClickException(f"HTTP 404: {e}")
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise click.ClickException(f"HTTP {response.status_code}: {detail}")
        return response


def make_session(ctx: click.Context) -> ApiSession:
    cfg = ctx.obj
    session = ApiSession()
    session._ctx = ctx  # Attach context for error handling
    session.headers["Authorization"] = f"Bearer {cfg['token']}"
    session.headers["Accept"] = "application/json"
    return session


def api_url(ctx: click.Context, path: str) -> str:
    return ctx.obj["url"].rstrip("/") + path


def sanity_check_server(ctx: click.Context) -> None:
    response = make_session(ctx).get(api_url(ctx, "/"), params={"all": ""})
    fail_msg = "Connected to a server but it does not seem to be the cbio-ingest API."
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        raise click.ClickException(fail_msg)
    if data.get("title") != "cBioPortal Ingest API":
        raise click.ClickException(fail_msg)
