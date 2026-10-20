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
