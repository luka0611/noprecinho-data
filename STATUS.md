# Status — noprecinho-data

_Updated 2026-10-20._

## Done
- Repo created with README, DATA_NOTICE, DECISIONS, STATUS, LICENSE.
- `collector/`: polite `pdh_client` (spacing, budget, robots C11, stop on any refusal), M0 probes, CLI `noprecinho probe`.
- `probe.yml` (manual only) and `tests.yml` (41 tests, green in CI).

## Next (Milestone 0 — plan v2 §6)
- Run probes in Actions after owner OK: robots → schema (geo) → gtin → cnpj → radius → sugestao → store_anchor → cart_probe,
  spread over 2–3 days (≤ 120 requests total).
- `docs/source-terms.md` (C12), `docs/source-schema.md`, `docs/M0-report.md`.

## Blockers / waiting on owner
- Bot contact page URL + contact e-mail for the User-Agent (plan v2 §4 item 7).
- LAI request (C10) — protocol number.
