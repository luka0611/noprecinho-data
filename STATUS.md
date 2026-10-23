# Status — noprecinho-data

_Updated 2026-10-23._

## Phase

Milestone 0 closed: **NO-GO** for Preço da Hora (LAI 3355579 answered 23 Oct — no reuse, no automated access).
Building the C16 data path: flyers (facts only) + user receipts + partner lists.

## Done

- Repo skeleton (README, DATA_NOTICE, DECISIONS, STATUS, MIT license), public per C13.
- `collector/`: polite `pdh_client` (spacing, budget, robots, stop on any refusal), M0 probes, CLI `noprecinho probe`;
  **43 tests** pass locally and in CI (`tests.yml`); `probe.yml` is manual-only.
- M0 probes ran 20 Oct (≈30 requests, 0 normal-path refusals): robots soft-404, schema/geo OK from US runners,
  gtin = termo, cnpj 0 results, radius 45/430/727 lines, sugestao returns GTINs; `store_anchor` got HTTP 202 and
  `cart_probe` got connect timeouts (no HTTP responses) → stopped, no retries.
- Terms of Use found → collection paused; LAI answered 23 Oct → M0 closed.
- Docs: `docs/M0-report.md`, `docs/source-schema.md`, `docs/source-terms.md`, `docs/flyer-policy.md`,
  `docs/receipt-quality.md`.

## Now / next

- `data.db` schema v1: observation rows with `source`, `tier`, `valid_until`, `status`, `confidence` (supersedes plan
  v2 §9.3's single-row `price`).
- Builder skeleton + normalizer (GTIN check digit, size/unit regex) + plausibility module (`receipt-quality.md` §4–§6).
- Receipt intake contract (phone → Worker/D1 → publish job) and the first flyer end-to-end (extraction → `data.db` →
  app).
- Then the publish pipeline (`manifest.json` + `data.db.gz`) and the site.

## Blocked / waiting on owner

- **A first store flyer** — outreach per `E:\FeiraCerta\PERMISSION_AND_STORES.txt`; nothing real can be built without it.
- Gemini API key (OWNER_TODO 4) for flyer extraction; Telegram bot (5) for alerts; Cloudflare account (6) for
  intake/publish.
- Screenshot of the in-app Terms (official app → Menu Principal → "Sobre o app").

## Hard stop

- No requests to `precodahora.ba.gov.br`, ever. The collector stays unused; no collection workflow exists.
