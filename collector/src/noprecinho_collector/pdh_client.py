"""Polite client for precodahora.ba.gov.br — the ONLY module that talks to the source (plan v2 §7.2).

Hard rules (legal line, Código Penal art. 154-A — see plan v2 §16.1):
- single-threaded, one client per run, every request spaced >= delay_s (monotonic clock), hard request budget;
- honest User-Agent with contact URL;
- robots.txt checked once per run (rules in robots.py);
- NO retries on 403/429, no CAPTCHA handling, no proxies, no header/fingerprint games:
  any refusal raises Blocked and the run stops.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from . import robots

BASE = "https://precodahora.ba.gov.br"
SEARCH_PATH = "/produtos/"
SEARCH_URL = f"{BASE}{SEARCH_PATH}"
ROBOTS_URL = f"{BASE}/robots.txt"
CONTACT_URL = "https://github.com/luka0611/noprecinho-data"
USER_AGENT = f"NoPrecinhoBot/0.1 (+{CONTACT_URL})"

CODIGO_OK = 80
CODIGO_EMPTY = 50
NETWORK_RETRY_WAIT_S = 60.0

_CAPTCHA_RE = re.compile(r'id="rc"\s+data-id="[^"]+"')
_CSRF_RE = re.compile(r'id="validate"\s+data-id="([^"]+)"')


class Blocked(Exception):
    """The source refused us (403/429/CAPTCHA/no CSRF/non-JSON/unknown codigo/robots). Stop the run."""


class BudgetExhausted(Exception):
    """The per-run request budget is spent."""


class Clock(Protocol):
    def monotonic(self) -> float: ...
    def sleep(self, seconds: float) -> None: ...


class RealClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


@dataclass
class RequestLog:
    method: str
    path: str
    params: dict[str, Any]
    status: int | None
    ms: int
    total: int | None = None
    note: str = ""


@dataclass
class SearchResult:
    codigo: int
    total_registros: int
    total_paginas: int
    rows: list[dict[str, Any]]
    raw: dict[str, Any] = field(repr=False)

    @property
    def empty(self) -> bool:
        return not self.rows


class PdhClient:
    def __init__(
        self,
        *,
        delay_s: float = 25.0,
        max_requests: int = 25,
        timeout_s: float = 30.0,
        user_agent: str = USER_AGENT,
        transport: httpx.BaseTransport | None = None,
        clock: Clock | None = None,
    ) -> None:
        if delay_s < 20.0:
            raise ValueError("delay_s below 20 s is not allowed (plan v2 §5.3)")
        self.delay_s = delay_s
        self.max_requests = max_requests
        self.user_agent = user_agent
        self.clock = clock or RealClock()
        self.requests_made = 0
        self.log: list[RequestLog] = []
        self.robots_verdict: robots.RobotsVerdict | None = None
        self._last_request_at: float | None = None
        self._csrf: str | None = None
        self._reopened_on_400 = False
        self._http = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Language": "pt-BR,pt;q=0.9"},
            timeout=timeout_s,
            follow_redirects=False,
            transport=transport,
        )

    # ---------------------------------------------------------------- plumbing

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PdhClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _wait_turn(self) -> None:
        if self._last_request_at is not None:
            remaining = self.delay_s - (self.clock.monotonic() - self._last_request_at)
            if remaining > 0:
                self.clock.sleep(remaining)

    def _send(self, method: str, url: str, *, params: dict[str, Any] | None = None, **kw: Any) -> httpx.Response:
        """One request: spacing, budget, at most one retry on network error / 5xx. Never retries 403/429."""
        attempts = 0
        while True:
            if self.requests_made >= self.max_requests:
                raise BudgetExhausted(f"budget of {self.max_requests} requests spent")
            self._wait_turn()
            self.requests_made += 1
            started = self.clock.monotonic()
            path = httpx.URL(url).path
            try:
                resp = self._http.request(method, url, **kw)
            except httpx.TransportError as e:
                self._last_request_at = self.clock.monotonic()
                self.log.append(RequestLog(method, path, params or {}, None, 0, note=type(e).__name__))
                if attempts == 0:
                    attempts += 1
                    self.clock.sleep(NETWORK_RETRY_WAIT_S)
                    continue
                raise
            self._last_request_at = self.clock.monotonic()
            ms = int((self._last_request_at - started) * 1000)
            self.log.append(RequestLog(method, path, params or {}, resp.status_code, ms))
            if resp.status_code in (403, 429):
                raise Blocked(f"http {resp.status_code} on {method} {path}")
            if resp.status_code >= 500 and attempts == 0:
                attempts += 1
                self.clock.sleep(NETWORK_RETRY_WAIT_S)
                continue
            return resp

    # ---------------------------------------------------------------- robots + session

    def check_robots(self) -> robots.RobotsVerdict:
        if self.robots_verdict is None:
            resp = self._send("GET", ROBOTS_URL)
            self.robots_verdict = robots.evaluate(
                resp.status_code, resp.text, resp.headers.get("content-type", ""), self.user_agent, SEARCH_PATH
            )
            self.log[-1].note = self.robots_verdict.summary()
            if not self.robots_verdict.allowed:
                raise Blocked(f"robots: {self.robots_verdict.summary()}")
        return self.robots_verdict

    def open_session(self) -> None:
        self.check_robots()
        resp = self._send("GET", SEARCH_URL)
        if resp.status_code != 200:
            raise Blocked(f"session page http {resp.status_code}")
        html = resp.text
        if _CAPTCHA_RE.search(html):
            raise Blocked("captcha")
        m = _CSRF_RE.search(html)
        if not m:
            raise Blocked("no csrf token on session page")
        self._csrf = m.group(1)

    # ---------------------------------------------------------------- search

    def search(
        self,
        *,
        lat: float,
        lng: float,
        raio_km: int,
        termo: str = "",
        gtin: str = "",
        cnpj: str = "",
        pagina: int = 1,
        ordenar: str = "preco.asc",
        horas: int = 72,
        extra: dict[str, str] | None = None,
    ) -> SearchResult:
        if not isinstance(raio_km, int) or not 1 <= raio_km <= 30:
            raise ValueError("raio_km must be an integer 1..30")
        if self._csrf is None:
            self.open_session()
        form = {
            "termo": termo,
            "gtin": gtin,
            "cnpj": cnpj,
            "horas": str(horas),
            "latitude": f"{lat:.6f}",
            "longitude": f"{lng:.6f}",
            "raio": str(raio_km),
            "pagina": str(pagina),
            "ordenar": ordenar,
            **(extra or {}),
        }
        resp = self._post_search(form)
        if resp.status_code == 400 and not self._reopened_on_400:
            # expired CSRF: re-open the session once per run and retry this request once
            self._reopened_on_400 = True
            self._csrf = None
            self.open_session()
            resp = self._post_search(form)
        if resp.status_code != 200:
            raise Blocked(f"search http {resp.status_code}")
        if "json" not in resp.headers.get("content-type", "").lower():
            raise Blocked(f"search returned non-JSON ({resp.headers.get('content-type', '?')})")
        try:
            data = resp.json()
        except ValueError as e:
            raise Blocked("search returned invalid JSON") from e
        result = parse_search(data)
        self.log[-1].total = result.total_registros
        return result

    def suggest(self, item: str) -> Any:
        """Autocomplete endpoint POST /sugestao/ (M0 checks whether it returns GTINs)."""
        if self._csrf is None:
            self.open_session()
        assert self._csrf is not None
        resp = self._send(
            "POST",
            f"{BASE}/sugestao/",
            params={"item": item},
            data={"item": item},
            headers={"X-CSRFToken": self._csrf, "X-Requested-With": "XMLHttpRequest",
                     "Referer": SEARCH_URL, "Origin": BASE},
        )
        if resp.status_code != 200 or "json" not in resp.headers.get("content-type", "").lower():
            raise Blocked(f"sugestao http {resp.status_code} {resp.headers.get('content-type', '?')}")
        return resp.json()

    def _post_search(self, form: dict[str, str]) -> httpx.Response:
        assert self._csrf is not None
        params = {k: v for k, v in form.items() if v}
        return self._send(
            "POST",
            SEARCH_URL,
            params=params,
            data=form,
            headers={
                "X-CSRFToken": self._csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": SEARCH_URL,
                "Origin": BASE,
            },
        )


def _shape(data: Any) -> str:
    if isinstance(data, dict):
        return "{" + ",".join(f"{k}:{type(v).__name__}" for k, v in list(data.items())[:12]) + "}"
    return type(data).__name__


def parse_search(data: Any) -> SearchResult:
    """Validate the response envelope. codigo 80 = ok, 50 / totalRegistros 0 = empty, anything else = Blocked."""
    if not isinstance(data, dict) or "codigo" not in data:
        raise Blocked(f"unexpected response shape {_shape(data)}")
    try:
        codigo = int(data["codigo"])
    except (TypeError, ValueError) as e:
        raise Blocked(f"non-numeric codigo {data.get('codigo')!r}") from e
    total = int(data.get("totalRegistros") or 0)
    pages = int(data.get("totalPaginas") or 0)
    if codigo == CODIGO_EMPTY or (codigo == CODIGO_OK and total == 0):
        return SearchResult(codigo, 0, 0, [], data)
    if codigo != CODIGO_OK:
        raise Blocked(f"codigo {codigo}: {str(data.get('mensagem') or data.get('msg') or '')[:80]}")
    rows = data.get("resultado")
    if not isinstance(rows, list):
        raise Blocked(f"codigo 80 without resultado list {_shape(data)}")
    return SearchResult(codigo, total, pages, rows, data)
