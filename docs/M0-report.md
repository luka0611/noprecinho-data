# M0 report — recon, gate and NO-GO

_Written 2026-10-23. Closes Milestone 0 (plan v2 §6). Author: agent session with the owner._
_Companion docs: `source-schema.md`, `source-terms.md`, `flyer-policy.md`, `receipt-quality.md`._

## 1. Verdict

**NO-GO for collecting from Preço da Hora Bahia.**

This is not a rate-limit verdict and not a technical failure: the data owner refused in writing.

- The site's Terms of Use (`/condicoesdeusoetermos`) allow personal, non-commercial use only and forbid copying,
  redistribution and retransmission (clauses 3.1, 3.3, 3.7, 7.1) — recorded in `source-terms.md`.
- The LAI request (protocol 3355579, sent 20 Oct 2026) was answered on **23 Oct 2026**: there is no provision for
  third-party reuse ("destinadas exclusivamente para o usuário final"), **automated access to the site is not
  permitted**, no open database or API is planned, and there are no plans to turn the service into infrastructure for
  automated providers.

Consequence: collection stays stopped **permanently**, unless SEFAZ-BA reverses this position in writing. The app is
built on flyers, user-scanned receipts and partner price lists (C16, now permanent rather than a pause).

## 2. What M0 had to decide (plan §6.2)

| Gate criterion | Result |
|---|---|
| Schema run succeeded | **Passed** — `codigo 80`, full schema mapped (`source-schema.md`) |
| ≤ 1 refusal across probes | **Inconclusive** — one HTTP 202 (empty search) and one double connect timeout; we stopped at the first sign and made no further requests |
| `robots.txt` does not disallow | **Passed** — HTTP 200 soft-404 (no rules) |
| No Terms forbidding automated access | **FAILED** — Terms forbid reuse; LAI confirms automated access is not permitted |
| Which store-sampling method works (C2) | **Not measured** — `store_anchor` got HTTP 202, `cart_probe` got no HTTP response at all |
| Geo check (US runner) | **Passed** — normal answers from GitHub's runners, so no fallback host was needed |

**Overall: NO-GO**, because two independent conditions (Terms and the written LAI answer) forbid the access model.

## 3. What was run

All probes ran in GitHub Actions through `probe.yml` (manual dispatch only), one client per run, ≥ 25 s between
requests, ≤ 10 requests per probe, full stop on any refusal, no retries on 403/429. Total ≈ 30 requests across 6 runs,
against an M0 budget of ~120.

| Probe | Requests (incl. session) | Result |
|---|---|---|
| `robots` | 1 | HTTP 200, 23,487-byte HTML "not found" page (soft-404) → no crawl rules |
| `schema` / `geo` | 3 | Pituba, `termo=arroz`, 2 km: `codigo 80`, 603 lines, 4 pages, 25/page, 15 distinct stores on page 1 |
| `gtin` | 5 | GTIN in `termo` and in the `gtin` field return the same totals |
| `cnpj` | 5 | **0 results** with `cnpj` alone and with `cnpj` + `termo`; the site UI has no store filter either |
| `radius` | 6 | Coca-Cola 2 L: 45 / 430 / 727 lines at 2 / 10 / 30 km; page 1 = 25 lines from 25 distinct stores; ages up to ~55 days despite `horas=72` |
| `sugestao` | 3 | Returns `{gtin, descricao, foto}` — cheap GTIN discovery, had it been usable |
| `store_anchor` | 4 | Seed OK, then the empty-`termo` search returned **HTTP 202** → client stopped; the `termo="a"` variant was never run |
| `cart_probe` | 2 | **Zero HTTP responses**: `GET /robots.txt` connect-timeout (30 s), 60 s wait, one retry, timeout again |

## 4. Timeline of the refusal

- **18:00–18:22 UTC, 20 Oct** — robots, schema, gtin, cnpj, radius and sugestao ran normally (HTTP 200, no CAPTCHA).
- **18:19 UTC** — `store_anchor`: the empty-term search answered **HTTP 202**. Treated as a possible refusal: no retry,
  no more requests that day. Empty searches are now refused in code before sending.
- **18:38 UTC** — `cart_probe`: the very first request (`GET /robots.txt`) timed out twice, no HTTP response at all.
  Read as a possible silent block: no re-run from another IP, host or the owner's PC (hard rule). The client now maps
  "unreachable after one retry" to `Blocked("unreachable …")` → exit 2 + owner alert.
- **20 Oct (later)** — owner found `/condicoesdeusoetermos`; all collection paused (C16).
- **23 Oct** — LAI answered: reuse not authorized, automated access not permitted.

## 5. What we learned about the source (kept as documentation only)

Enough is known to describe the service, but nothing will be collected from it:

- Session page carries a CSRF token in `id="validate" data-id`; a CAPTCHA signal would be `id="rc" data-id` → stop.
- Search: `POST /produtos/` (form-urlencoded) with `termo`, `gtin`, `cnpj`, `horas` (12–72), `latitude`, `longitude`,
  `raio` (1–30 km), `pagina`, `ordenar`.
- Fixed page size of 25 and a hard cap of 4 pages (100 lines) per search.
- Envelope: `codigo` 80 = ok, 50 = empty; `totalRegistros`, `totalPaginas`, `resultado[{produto, estabelecimento}]`.
- 19 `produto` keys and 15 `estabelecimento` keys; `gtin` often null; `unidade` is free-form (`PCT9`, `UND9`, …);
  `precoBruto`/`precoLiquido`/`desconto` exist; `data` is UTC; `telefone` is dropped at observation time (C14);
  the `foto` URL points at a government host and is never hotlinked.
- The `cnpj` filter returns nothing, so CNPJ-based store sampling does not work. `store_anchor` (minimal term +
  store coordinates + `raio=1`) was the intended alternative and was never confirmed.
- GTIN searches return each store's latest sale even when it is weeks old (~55 days seen) despite `horas=72` — the
  owner rule "always show the real age" came from this.

## 6. Why NO-GO and not SLOW-GO

SLOW-GO (plan §6.2) is for rate limiting: reduce the rate and continue. Here the prohibition is explicit, in writing,
and covers the access model itself. Plan §0.2 / §16.1 also make "never work around a block" a legal rule
(Código Penal art. 154-A), not only an ethical one. Continuing after a formal LAI answer would be bad faith and would
end any future relationship with SEFAZ-BA.

No appeal is planned: all five questions were answered; an administrative appeal contests incomplete answers, it does
not create a reuse license.

## 7. What M0 did not measure

- **C2 — cart coverage and store sampling.** `store_anchor` and `cart_probe` never returned data, so it is still
  unknown whether a store-centric method exists. If SEFAZ ever authorizes access in writing, this is the first thing
  to measure, with a new, minimal M0 addendum (one request at a time, same polite client).
- Real refusal thresholds (429 behaviour) — deliberately not explored.
- Nothing here changes the flyer/receipt plan, which does not depend on this source.

## 8. Data handling

- Raw probe JSON lived only as 3-day Actions artifacts; they expired and were never committed.
- No observations were stored anywhere, in any branch.
- `source-schema.md` keeps key names and example values, including one real store's trade name, CNPJ, address and
  coordinates. These are public business facts, not personal data — but trimming them to generic values is a sensible
  hygiene step (open item, not a legal requirement).

## 9. Decision record

- M0 is **closed as NO-GO**.
- `collector/` stays in the repository as unused, documented code (MIT). It is not scheduled and has no workflow that
  calls the source. Keeping it costs nothing and it is useful if the position ever changes.
- No GitHub secrets or variables are needed for collection (none are set).
- Data strategy from here: **flyers** (facts only; permission requested for file, logo, partnership), **user receipts**
  (QR-first, rewarded), **partner lists** — see `flyer-policy.md` and `receipt-quality.md`.
- No request may be made to `precodahora.ba.gov.br` again.

## 10. Open items

- Owner: screenshot the in-app Terms (official app → Menu Principal → "Sobre o app") for the record.
- Owner: store outreach (3–5 stores) — the fastest way to real data.
- Agent: `data.db` schema v1 (observation rows with source/tier/valid_until/status) and the first flyer end-to-end.
