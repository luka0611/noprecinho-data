from __future__ import annotations

import httpx
import pytest
from conftest import CAPTCHA_HTML, OK_JSON, SOFT404_HTML, json_response

from noprecinho_collector.pdh_client import USER_AGENT, Blocked, BudgetExhausted, PdhClient, parse_search

PITUBA = {"lat": -12.9986, "lng": -38.4614, "raio_km": 2}


def test_ok_search_and_session_flow(make_client, source):
    source.search_responses.append(json_response(OK_JSON))
    with make_client() as c:
        r = c.search(termo="arroz", **PITUBA)
    assert r.total_registros == 2 and len(r.rows) == 2
    assert [(m, p) for m, p, _ in source.calls] == [("GET", "/robots.txt"), ("GET", "/produtos/"), ("POST", "/produtos/")]


def test_requests_are_spaced_by_delay(make_client, source):
    source.search_responses += [json_response(OK_JSON), json_response(OK_JSON)]
    with make_client(delay_s=25) as c:
        c.search(termo="arroz", **PITUBA)
        c.search(termo="feijao", **PITUBA)
    times = [t for _, _, t in source.calls]
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert all(g >= 25 for g in gaps), gaps


def test_delay_below_20s_is_refused():
    with pytest.raises(ValueError):
        PdhClient(delay_s=5)


def test_headers_are_honest(make_client, source):
    seen = {}

    def session(req: httpx.Request) -> httpx.Response:
        seen.update(req.headers)
        return httpx.Response(200, text='<div id="validate" data-id="t"></div>', headers={"content-type": "text/html"})

    source.session = session
    with make_client() as c:
        c.open_session()
    assert seen["user-agent"] == USER_AGENT
    assert "NoPrecinhoBot" in USER_AGENT and "+https://" in USER_AGENT


def test_search_sends_csrf_and_ajax_headers(make_client, source):
    source.search_responses.append(json_response(OK_JSON))
    with make_client() as c:
        c.search(termo="arroz", **PITUBA)
    post = source.requests[-1]
    assert post.headers["x-csrftoken"] == "tok123"
    assert post.headers["x-requested-with"] == "XMLHttpRequest"
    assert post.headers["referer"] == "https://precodahora.ba.gov.br/produtos/"
    assert b"raio=2" in post.content and b"termo=arroz" in post.content


@pytest.mark.parametrize("status", [403, 429])
def test_refusal_raises_blocked_without_retry(make_client, source, status):
    source.search_responses.append(httpx.Response(status))
    with make_client() as c, pytest.raises(Blocked):
        c.search(termo="arroz", **PITUBA)
    posts = [1 for m, p, _ in source.calls if m == "POST"]
    assert len(posts) == 1  # no retry


def test_refusal_on_session_page(make_client, source):
    source.session = lambda r: httpx.Response(429)
    with make_client() as c, pytest.raises(Blocked):
        c.open_session()


def test_captcha_stops(make_client, source):
    source.session = lambda r: httpx.Response(200, text=CAPTCHA_HTML, headers={"content-type": "text/html"})
    with make_client() as c, pytest.raises(Blocked, match="captcha"):
        c.open_session()


def test_missing_csrf_stops(make_client, source):
    source.session = lambda r: httpx.Response(200, text="<html></html>", headers={"content-type": "text/html"})
    with make_client() as c, pytest.raises(Blocked, match="csrf"):
        c.open_session()


def test_non_json_search_stops(make_client, source):
    source.search_responses.append(httpx.Response(200, text="<html>erro</html>", headers={"content-type": "text/html"}))
    with make_client() as c, pytest.raises(Blocked, match="non-JSON"):
        c.search(termo="arroz", **PITUBA)


def test_empty_result_codigo_50(make_client, source):
    source.search_responses.append(json_response({"codigo": 50, "mensagem": "Nenhum resultado encontrado!"}))
    with make_client() as c:
        r = c.search(termo="xyz", **PITUBA)
    assert r.empty


def test_unknown_codigo_is_blocked():
    with pytest.raises(Blocked, match="codigo 99"):
        parse_search({"codigo": 99, "mensagem": "Tente mais tarde"})


def test_budget_is_enforced(make_client, source):
    source.search_responses += [json_response(OK_JSON)] * 5
    with make_client(max_requests=3) as c:  # robots + session + 1 search
        c.search(termo="a", **PITUBA)
        with pytest.raises(BudgetExhausted):
            c.search(termo="b", **PITUBA)


def test_one_retry_on_5xx_then_ok(make_client, source, clock):
    source.search_responses += [httpx.Response(503), json_response(OK_JSON)]
    with make_client() as c:
        r = c.search(termo="arroz", **PITUBA)
    assert r.total_registros == 2
    assert 60.0 in clock.sleeps


def test_400_reopens_session_once(make_client, source):
    source.search_responses += [httpx.Response(400), json_response(OK_JSON)]
    with make_client() as c:
        c.search(termo="arroz", **PITUBA)
    gets = [p for m, p, _ in source.calls if m == "GET" and p == "/produtos/"]
    assert len(gets) == 2


def test_second_400_is_blocked(make_client, source):
    source.search_responses += [httpx.Response(400), httpx.Response(400)]
    with make_client() as c, pytest.raises(Blocked):
        c.search(termo="arroz", **PITUBA)


@pytest.mark.parametrize("bad", [0, 31, 2.5])
def test_radius_must_be_integer_km(make_client, bad):
    with make_client() as c, pytest.raises(ValueError):
        c.search(termo="a", lat=-13.0, lng=-38.5, raio_km=bad)


def test_robots_soft404_allows(make_client, source):
    source.robots = lambda r: httpx.Response(200, text=SOFT404_HTML, headers={"content-type": "text/html"})
    with make_client() as c:
        v = c.check_robots()
    assert v.allowed and v.kind == "soft404"


@pytest.mark.parametrize("status", [401, 403])
def test_robots_forbidden_is_nogo(make_client, source, status):
    source.robots = lambda r: httpx.Response(status)
    with make_client() as c, pytest.raises(Blocked, match="robots"):
        c.check_robots()


def test_robots_disallow_produtos_is_nogo(make_client, source):
    source.robots = lambda r: httpx.Response(200, text="User-agent: *\nDisallow: /produtos/\n",
                                             headers={"content-type": "text/plain"})
    with make_client() as c, pytest.raises(Blocked, match="robots"):
        c.check_robots()


def test_robots_disallow_for_our_bot_is_nogo(make_client, source):
    source.robots = lambda r: httpx.Response(200, text="User-agent: NoPrecinhoBot\nDisallow: /\n",
                                             headers={"content-type": "text/plain"})
    with make_client() as c, pytest.raises(Blocked, match="robots"):
        c.check_robots()


def test_robots_other_rules_allow(make_client, source):
    source.robots = lambda r: httpx.Response(200, text="User-agent: *\nDisallow: /admin/\n",
                                             headers={"content-type": "text/plain"})
    with make_client() as c:
        assert c.check_robots().allowed
