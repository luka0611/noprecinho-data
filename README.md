# noprecinho-data

Data pipeline for **No Precinho**, an independent price-comparison app for supermarkets and atacarejos in Salvador and
Lauro de Freitas (Bahia, Brazil).

- `collector/` — polite collector for public receipt-based prices (Python, uv)
- `normalizer/`, `builder/`, `site/`, `catalog/` — added in later milestones

**Status:** Milestone 0 (recon). See `STATUS.md` and `DECISIONS.md`.

## How we collect

One honest bot user agent with contact details, at most one request every 20–25 seconds, small per-run caps, and a full
stop on any refusal (403/429/CAPTCHA). We never work around a block. See `DATA_NOTICE.md`.

Aplicativo independente, sem vínculo com o Governo da Bahia ou a SEFAZ-BA.

## License

Code: MIT (see `LICENSE`). Data: see `DATA_NOTICE.md`.
