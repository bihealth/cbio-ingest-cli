from __future__ import annotations

from typing import TYPE_CHECKING, MutableMapping

import click
import requests

if TYPE_CHECKING:
    from requests import Response
    from requests.sessions import (
        _Auth,
        _Cert,
        _Data,
        _Files,
        _HeadersUpdateMapping,
        _HooksInput,
        _Params,
        _Timeout,
        _Verify,
    )


class ApiSession(requests.Session):
    def request(  # type: ignore[override]
        self,
        method: bytes | str,
        url: bytes | str,
        params: _Params | None = None,
        data: _Data | None = None,
        headers: _HeadersUpdateMapping | None = None,
        cookies: requests.cookies.RequestsCookieJar | None = None,
        files: _Files | None = None,
        auth: _Auth | None = None,
        timeout: _Timeout | None = None,
        allow_redirects: bool = True,
        proxies: MutableMapping[str, str] | None = None,
        hooks: _HooksInput | None = None,
        stream: bool | None = None,
        verify: _Verify | None = None,
        cert: _Cert | None = None,
        json: object | None = None,
    ) -> Response:
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
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise click.ClickException(f"HTTP {response.status_code}: {detail}")
        return response


def make_session(ctx: click.Context) -> ApiSession:
    cfg = ctx.obj
    session = ApiSession()
    session.headers["Authorization"] = f"Bearer {cfg['token']}"
    session.headers["Accept"] = "application/json"
    return session


def api_url(ctx: click.Context, path: str) -> str:
    return ctx.obj["url"].rstrip("/") + path
