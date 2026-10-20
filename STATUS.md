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
| sugestao | returns `{gtin, descricao, foto}` list → cheap GTIN discovery for the `discovery` job |
| terms | footer references terms of use, but both PDFs are dead links → owner: continue + ask in LAI (`docs/source-terms.md`) |

## Next (Milestone 0 — plan v2 §6)
- Run `store_anchor` and `cart_probe` (≈ 15 requests, ≥ 5 min apart).
- Write `docs/M0-report.md`: GO/SLOW-GO/NO-GO, chosen strategy. Likely direction: **GTIN-centric refresh** (one line per
  store per GTIN search) instead of CNPJ sampling; store_anchor decides whether a store-centric method exists (C2).

## Blockers / waiting on owner
- LAI request (C10) — steps in `E:\FeiraCerta\LAI_REQUEST_STEPS.txt`; protocol number.
- Manual check of terms in the official app / Play page (OWNER_TODO 8b).
