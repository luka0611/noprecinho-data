"""Milestone 0 probes (plan v2 §6.1). Each probe makes at most ~10 requests through the polite client.

Every probe writes its raw responses to <out>/<probe>/*.json (uploaded as a short-lived artifact, never committed)
and returns Markdown lines for the GitHub step summary.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from .pdh_client import PdhClient, SearchResult

# Pituba circle (Salvador) — the v1 schema probe location.
PITUBA = (-12.9986, -38.4614)

# 5 items of the reference cart (plan v2 §21.6) used by cart_probe.
CART_TERMS = ["arroz 5kg", "feijao carioca 1kg", "oleo soja 900ml", "acucar cristal 1kg", "cafe 250g"]


class Probe:
    def __init__(self, client: PdhClient, out: Path, inputs: dict[str, str]) -> None:
        self.c = client
        self.out = out
        self.inputs = inputs
        self.md: list[str] = []
        out.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, data: Any) -> None:
        (self.out / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def search(self, name: str, **kw: Any) -> SearchResult:
        r = self.c.search(**kw)
        self.save(name, r.raw)
        self.md.append(f"- `{name}`: codigo={r.codigo} totalRegistros={r.total_registros} "
                       f"paginas={r.total_paginas} linhas={len(r.rows)} lojas={len(stores(r))}")
        return r

    def seed(self) -> SearchResult:
        lat, lng = PITUBA
        return self.search("seed_arroz_pituba_2km", termo="arroz", lat=lat, lng=lng, raio_km=2)


# ---------------------------------------------------------------- helpers over result rows

def _est(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("estabelecimento") or {}


def _prod(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("produto") or {}


def stores(r: SearchResult) -> Counter[str]:
    return Counter(str(_est(x).get("cnpj", "?")) for x in r.rows)


def first_gtin(r: SearchResult) -> str | None:
    for x in r.rows:
        g = str(_prod(x).get("gtin") or "")
        if g.isdigit() and 8 <= len(g) <= 14 and set(g) != {"0"}:
            return g
    return None


def store_coords(r: SearchResult, cnpj: str) -> tuple[float, float] | None:
    for x in r.rows:
        e = _est(x)
        if str(e.get("cnpj")) == cnpj and e.get("latitude") and e.get("longitude"):
            return float(e["latitude"]), float(e["longitude"])
    return None


def key_inventory(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Every key seen per object with one example value — feeds docs/source-schema.md."""
    inv: dict[str, dict[str, str]] = {}
    for row in rows:
        for top, val in row.items():
            if isinstance(val, dict):
                for k, v in val.items():
                    inv.setdefault(top, {}).setdefault(k, repr(v)[:60])
            else:
                inv.setdefault("(row)", {}).setdefault(top, repr(val)[:60])
    return inv


# ---------------------------------------------------------------- the probes

def probe_robots(p: Probe) -> None:
    v = p.c.check_robots()
    p.md.append(f"- {v.summary()}")


def probe_schema(p: Probe) -> None:
    """Also serves as the `geo` check: it runs from a GitHub runner (US/Azure IP)."""
    r = p.seed()
    inv = key_inventory(r.rows)
    p.save("key_inventory", inv)
    p.md.append("- envelope keys: " + ", ".join(sorted(r.raw.keys())))
    for obj, keys in inv.items():
        p.md.append(f"- `{obj}` keys ({len(keys)}): " + ", ".join(sorted(keys)))


def probe_gtin(p: Probe) -> None:
    gtin = p.inputs.get("gtin") or first_gtin(p.seed())
    if not gtin:
        p.md.append("- no GTIN found in seed search")
        return
    lat, lng = PITUBA
    a = p.search("gtin_in_termo", termo=gtin, lat=lat, lng=lng, raio_km=10)
    b = p.search("gtin_in_gtin_field", gtin=gtin, lat=lat, lng=lng, raio_km=10)
    p.md.append(f"- GTIN {gtin}: termo→{a.total_registros}, gtin field→{b.total_registros}")


def probe_cnpj(p: Probe) -> None:
    seed = p.seed()
    cnpj = p.inputs.get("cnpj") or (stores(seed).most_common(1)[0][0] if seed.rows else "")
    coords = store_coords(seed, cnpj) or PITUBA
    if not cnpj:
        p.md.append("- no CNPJ found")
        return
    a = p.search("cnpj_only_newest", cnpj=cnpj, lat=coords[0], lng=coords[1], raio_km=1, ordenar="data.desc")
    b = p.search("cnpj_plus_termo", cnpj=cnpj, termo="arroz", lat=coords[0], lng=coords[1], raio_km=1)
    for name, r in (("cnpj only", a), ("cnpj+termo", b)):
        s = stores(r)
        share = (s.get(cnpj, 0) / len(r.rows)) if r.rows else 0
        p.md.append(f"- {name}: {len(r.rows)} rows, {share:.0%} from CNPJ {cnpj[:8]}…, distinct stores {len(s)}")


def probe_radius(p: Probe) -> None:
    gtin = p.inputs.get("gtin") or first_gtin(p.seed())
    if not gtin:
        p.md.append("- no GTIN found in seed search")
        return
    lat, lng = PITUBA
    for km in (2, 10, 30):
        r = p.search(f"radius_{km}km", termo=gtin, lat=lat, lng=lng, raio_km=km)
        p.md.append(f"  - raio {km} km: total {r.total_registros}, distinct stores on page 1: {len(stores(r))}")


def probe_sugestao(p: Probe) -> None:
    resp = p.c.suggest("arroz")
    p.save("sugestao_arroz", resp)
    text = json.dumps(resp, ensure_ascii=False)
    p.md.append(f"- /sugestao/ returned {type(resp).__name__}, {len(text)} chars; first 200: `{text[:200]}`")


def probe_store_anchor(p: Probe) -> None:
    """Empty/minimal termo + store coordinates, radius 1, newest first: does it approximate store sampling?"""
    seed = p.seed()
    top = stores(seed).most_common(1)
    if not top:
        p.md.append("- no store in seed search")
        return
    cnpj = top[0][0]
    lat, lng = store_coords(seed, cnpj) or PITUBA
    for name, termo in (("anchor_empty_termo", ""), ("anchor_termo_a", "a")):
        r = p.search(name, termo=termo, lat=lat, lng=lng, raio_km=1, ordenar="data.desc")
        s = stores(r)
        share = (s.get(cnpj, 0) / len(r.rows)) if r.rows else 0
        p.md.append(f"  - termo={termo!r}: {len(r.rows)} rows, {share:.0%} from the anchor store, {len(s)} stores")


def probe_cart(p: Probe) -> None:
    """Reference-cart items at the 3 busiest stores' coordinates (radius 1), 2 items per store = 6 searches (C2).
    How often does the right store show up for an item?"""
    seed = p.seed()
    picks = [c for c, _ in stores(seed).most_common(3)]
    hits = tries = 0
    for i, cnpj in enumerate(picks):
        lat, lng = store_coords(seed, cnpj) or PITUBA
        for term in (CART_TERMS[(2 * i) % len(CART_TERMS)], CART_TERMS[(2 * i + 1) % len(CART_TERMS)]):
            r = p.search(f"cart_{cnpj[:8]}_{term.split()[0]}", termo=term, lat=lat, lng=lng, raio_km=1)
            tries += 1
            hits += int(cnpj in stores(r))
    p.md.append(f"- cart probe: right store present in {hits}/{tries} searches")


PROBES: dict[str, Callable[[Probe], None]] = {
    "robots": probe_robots,
    "schema": probe_schema,
    "gtin": probe_gtin,
    "cnpj": probe_cnpj,
    "radius": probe_radius,
    "sugestao": probe_sugestao,
    "store_anchor": probe_store_anchor,
    "cart_probe": probe_cart,
}

