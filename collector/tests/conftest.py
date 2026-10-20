"""Shared fakes: a fake clock and a scripted fake source (hand-made responses shaped like the real site)."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

SESSION_HTML = '<html><body><div id="validate" data-id="tok123"></div></body></html>'
CAPTCHA_HTML = '<html><div id="validate" data-id="tok123"></div><div id="rc" data-id="sitekey"></div></html>'
SOFT404_HTML = "<!DOCTYPE html><html><title>Página não encontrada</title></html>"

OK_JSON = {
    "codigo": 80,
    "totalRegistros": 2,
    "totalPaginas": 1,
    "resultado": [
        {"produto": {"descricao": "ARROZ T1 5KG", "gtin": "7891234567895", "precoUnitario": 24.9},
         "estabelecimento": {"cnpj": "00000000000191", "nomeEstabelecimento": "MERCADO TESTE"}},
        {"produto": {"descricao": "ARROZ T1 5KG", "gtin": "7891234567895", "precoUnitario": 25.5},
         "estabelecimento": {"cnpj": "00000000000272", "nomeEstabelecimento": "ATACADO TESTE"}},
    ],
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeSource:
    """Routes requests to handlers; records (method, path, time) of every request."""

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.calls: list[tuple[str, str, float]] = []
        self.requests: list[httpx.Request] = []
        self.robots: Callable[[httpx.Request], httpx.Response] = lambda r: httpx.Response(404, text="not found")
        self.session: Callable[[httpx.Request], httpx.Response] = lambda r: httpx.Response(
            200, text=SESSION_HTML, headers={"content-type": "text/html"})
        self.search_responses: list[httpx.Response] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, request.url.path, self.clock.now))
        self.requests.append(request)
        if request.url.path == "/robots.txt":
            return self.robots(request)
        if request.method == "GET" and request.url.path == "/produtos/":
            return self.session(request)
        if request.method == "POST" and request.url.path == "/produtos/":
            return self.search_responses.pop(0)
        return httpx.Response(404)


def json_response(data: object, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=json.dumps(data), headers={"content-type": "application/json"})


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def source(clock: FakeClock) -> FakeSource:
    return FakeSource(clock)


@pytest.fixture
def make_client(clock: FakeClock, source: FakeSource):
    from noprecinho_collector.pdh_client import PdhClient

    def _make(**kw):
        return PdhClient(transport=httpx.MockTransport(source.handler), clock=clock, **kw)

    return _make
