from __future__ import annotations

import json

import httpx
import pytest
from conftest import OK_JSON, json_response

from noprecinho_collector import cli
from noprecinho_collector.probes import PROBES, Probe, first_gtin, key_inventory, stores


def rows_with_coords():
    data = json.loads(json.dumps(OK_JSON))
    for i, row in enumerate(data["resultado"]):
        row["estabelecimento"].update({"latitude": -12.99 - i / 100, "longitude": -38.46})
    return data


def test_schema_probe_writes_inventory(make_client, source, tmp_path):
    source.search_responses.append(json_response(OK_JSON))
    with make_client(max_requests=10) as c:
        p = Probe(c, tmp_path, {})
        PROBES["schema"](p)
    inv = json.loads((tmp_path / "key_inventory.json").read_text(encoding="utf-8"))
    assert {"produto", "estabelecimento"} <= inv.keys()
    assert any("produto" in line for line in p.md)


def test_cart_probe_stays_within_six_searches(make_client, source, tmp_path):
    source.search_responses += [json_response(rows_with_coords())] * 7
    with make_client(max_requests=10) as c:
        p = Probe(c, tmp_path, {})
        PROBES["cart_probe"](p)
        searches = sum(1 for r in c.log if r.method == "POST")
    assert searches == 1 + 2 * 2  # seed + 2 stores in fixture x 2 items
    assert c.requests_made <= 10


def test_every_probe_fits_budget_of_ten(make_client, source, tmp_path):
    for name, fn in PROBES.items():
        source.search_responses[:] = [json_response(rows_with_coords())] * 12
        source.calls.clear()
        if name == "sugestao":
            continue  # separate endpoint, covered below
        with make_client(max_requests=10) as c:
            fn(Probe(c, tmp_path / name, {}))
            assert c.requests_made <= 10, name


def test_sugestao_probe(clock, tmp_path):
    from noprecinho_collector.pdh_client import PdhClient

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/robots.txt":
            return httpx.Response(404)
        if req.url.path == "/produtos/":
            return httpx.Response(200, text='<i id="validate" data-id="t"></i>', headers={"content-type": "text/html"})
        return json_response(["ARROZ TIO JOAO 5KG", "ARROZ CAMIL 1KG"])

    with PdhClient(transport=httpx.MockTransport(handler), clock=clock) as c:
        p = Probe(c, tmp_path, {})
        PROBES["sugestao"](p)
    assert (tmp_path / "sugestao_arroz.json").exists()


def test_helpers():
    from noprecinho_collector.pdh_client import parse_search

    r = parse_search(OK_JSON)
    assert first_gtin(r) == "7891234567895"
    assert len(stores(r)) == 2
    assert "precoUnitario" in key_inventory(r.rows)["produto"]


def test_kill_switch_makes_no_requests(monkeypatch, tmp_path):
    monkeypatch.setenv("COLLECT_ENABLED", "false")

    def boom(*a, **k):
        raise AssertionError("client must not be created")

    monkeypatch.setattr(cli, "PdhClient", boom)
    assert cli.main(["probe", "schema", "--out", str(tmp_path)]) == 0


def test_cli_reports_block(monkeypatch, tmp_path, make_client, source):
    source.session = lambda r: httpx.Response(429)
    out_file = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
    monkeypatch.setattr(cli, "PdhClient", lambda **kw: make_client(**kw))
    assert cli.main(["probe", "schema", "--out", str(tmp_path)]) == 2
    assert "blocked=true" in out_file.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", sorted(PROBES))
def test_cli_accepts_all_probe_names(name):
    with pytest.raises(SystemExit) as e:
        cli.main(["probe", name, "--help"])
    assert e.value.code == 0
