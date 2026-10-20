# Status — noprecinho-data

_Updated 2026-10-20._

## Done
- Repo created with README, DATA_NOTICE, DECISIONS, STATUS, LICENSE.
- `collector/`: polite `pdh_client` (spacing, budget, robots C11, stop on any refusal), M0 probes, CLI `noprecinho probe`.
- `probe.yml` (manual only) and `tests.yml` (41 tests, green in CI).

## M0 probe results so far (2026-10-20, all from GitHub Actions, 0 refusals)
| probe | result |
|---|---|
| robots | soft-404 (no robots.txt) → allowed |
| schema / geo | OK from US runner → no fallback host; schema in `docs/source-schema.md` |
| cnpj | **0 results** (cnpj alone and cnpj+termo); site UI has no store filter → CNPJ store sampling doesn't work |
| gtin | GTIN in `termo` = GTIN in `gtin` field (same totals) |
| radius (Coca-Cola 2L) | 2/10/30 km → 45/430/727 lines; page 1 = 25 lines from **25 distinct stores**; ages up to ~55 days despite horas=72 |
| store_anchor | empty termo → **HTTP 202** → client stopped (no retry); 'a' variant not run. Empty searches now refused in code. |
| sugestao | returns `{gtin, descricao, foto}` list → cheap GTIN discovery for the `discovery` job |
| terms | footer references terms of use, but both PDFs are dead links → owner: continue + ask in LAI (`docs/source-terms.md`) |

## Next (Milestone 0 — plan v2 §6)
- cart_probe run 39476483954 (2026-10-20 18:38 UTC): **connect timeout on the first request (robots.txt), twice** → no HTTP
  response at all. Site down, or runner IP dropped (possible silent block after the 202). No more probes today; no re-run
  from other IPs. Next: owner checks the site in a browser; if up, ONE cart_probe after ≥ 1 day.
- Proposed (awaiting go-ahead): double connect timeout → Blocked("unreachable") → exit 2 + Telegram alert.
- Store-centric idea (owner): search at the store's own coordinates, raio=1, keep lines whose `cnpj` matches — cart_probe measures this.
- Write `docs/M0-report.md`: GO/SLOW-GO/NO-GO, chosen strategy. Likely direction: **GTIN-centric refresh** (one line per
  store per GTIN search) instead of CNPJ sampling; store_anchor decides whether a store-centric method exists (C2).

## Blockers / waiting on owner
- LAI request (C10) — steps in `E:\FeiraCerta\LAI_REQUEST_STEPS.txt`; protocol number.
- Manual check of terms in the official app / Play page (OWNER_TODO 8b).
