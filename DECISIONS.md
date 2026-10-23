# Decisions — noprecinho-data

Append-only. Newest at the bottom. Format: date — decision — why.

- 2026-10-20 — App name **No Precinho**; repo `noprecinho-data` is **public** — free Actions minutes are needed
  (~6,000 min/month of collection); the data is public government data anyway (plan v2 C13).
- 2026-10-20 — Everything unattended runs in GitHub Actions (fallback: small cloud VM), never on the owner's PC (C1).
- 2026-10-20 — Never work around a block (CAPTCHA/403/429/IP ban): stop, alert, reduce, ask. Legal line (CP art. 154-A).
- 2026-10-20 — Code license MIT (plan v1 §6.1 default; owner may change).
- 2026-10-20 — Normalization LLM: provider-agnostic OpenAI-compatible client; Gemini now, OpenRouter later (C1).
- 2026-10-20 — Owner alerts via Telegram.
- 2026-10-20 — Python package `noprecinho_collector`, CLI `noprecinho`.
- 2026-10-20 — M0 geo check passed: the source answers GitHub-hosted (US) runners normally → collector stays in
  GitHub Actions; no fallback host.
- 2026-10-20 — `estabelecimento.telefone` exists in the payload; it is dropped at observation time (C14).
- 2026-10-20 — Bot contact = repo URL only (owner: no e-mail for now).
- 2026-10-20 — Source terms of use exist by reference (footer) but both PDFs are dead links. Owner chose: continue M0
  at minimal volume and request the terms text via LAI (question 5). Details: docs/source-terms.md.
- 2026-10-20 — `cnpj` form field returns 0 results (with and without termo) and the site UI has no store filter →
  CNPJ store sampling does not work as v1 assumed. `gtin` field and GTIN-in-`termo` both work (same totals).
- 2026-10-20 — GTIN searches return each store's latest sale even if weeks old (seen up to ~55 days with horas=72).
  Owner: always show the **real age** of each price ("vendido há 12 dias"); > 72 h = grey + "antigo" (plan v2 §10.3–10.4).
  Ranking/optimizer keep the v2 staleness rules (72 h preferred, ≤ 7 days with penalty).
- 2026-10-20 — Empty-termo search answered HTTP 202; the client stopped (treated as possible refusal). Empty searches are
  now refused before sending. No more requests that day (cautious default); cart_probe first next session.
- 2026-10-20 — Store identity comes from `estabelecimento.cnpj` in every line (even though the site UI doesn't show it).
  Store-centric collection = search at the store's coordinates with raio=1 and filter by cnpj (owner idea; cart_probe tests it).
- 2026-10-20 — **C16:** Preço da Hora Terms of Use (personal, non-commercial; no copying/redistribution) → all collection paused until SEFAZ-BA authorizes in writing. Collector code kept, unused. See docs/source-terms.md.
- 2026-10-23 — **M0 closed NO-GO.** LAI 3355579 answered: no third-party reuse, automated access not permitted, no
  API/dataset planned. No further requests to the source; collector stays unused (MIT, documented); no appeal. Why:
  the data owner refused in writing and plan §0.2/§16.1 treat a refusal as final (CP art. 154-A risk).
- 2026-10-23 — **Flyer facts are used without prior permission** — product, size, price (CPF/CNPJ), validity, store —
  but never images, artwork, layout or logo; permission is still requested for the weekly file, brand use and
  partnerships; opt-out honored within 7 days. Why: art. 7º, XIII + §2º of Lei 9.610/98 excludes data themselves;
  the remaining risk is expression and relationship, not the price. See docs/flyer-policy.md.
- 2026-10-23 — **Receipts: QR-first, rewarded on accepted data only.** Rewards are zero-cost points/badges/early
  access (no cash, no lottery); outliers are quarantined as UNCONFIRMED and confirmed by a second independent
  receipt or a flyer match, never deleted. Why: data quality and anti-abuse; see docs/receipt-quality.md.
- 2026-10-23 — **`data.db` will be observation-based** (source/tier/valid_until/status/confidence), replacing the
  single-row `price` table of plan v2 §9.3. Why: with three sources a product/store can have several concurrent
  prices, and the app must know how well each is supported.
