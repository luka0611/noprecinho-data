# Receipt and flyer data quality — spec v1

_Written 2026-10-23. Status: draft, pre-implementation. Owner decisions of 23 Oct 2026 are marked **(owner)**._
_This fills the gap left by C16: the app no longer has a government feed, so every price we publish must be
defensible on its own. Companion docs: `source-schema.md`, `source-terms.md`._

## 1. Scope and goal

Sources we may use:

| Source | What it is | Trust starting point |
|---|---|---|
| `FLYER` | A store's public weekly flyer (encarte): declared offer with validity dates | High for the validity window; the store published it |
| `RECEIPT` | A user-scanned NFC-e: a real transaction | High that it happened, low that it is representative |
| `PARTNER` | A store's own price list, sent to us | High, but only for that store and date |

Goal: **never publish a price we cannot defend**, and show honestly how well each price is supported.
A low price is not suspicious by itself — it is the product. The question is always "plausible for this exact
product, in this unit, at this store, on this date?".

## 2. Vocabulary

- **Observation** — one price for one product at one store, from one source, at one time.
- **Confirmation** — independent corroboration of an observation (another receipt with a *different* access key, a
  flyer with the same price in its validity window, or a partner list).
- **Hard check** — objective, deterministic; failure rejects the observation and pays no reward.
- **Soft check** — statistical/contextual; failure does not delete the price, it sets `UNCONFIRMED` and sends it to
  the review queue.
- **Status** — `CONFIRMED` | `UNCONFIRMED` | `REJECTED`.

## 3. Data model (replaces the single-row `price` table of plan v2 §9.3)

The plan's `price` table has one row per (product, store) and no source, tier, validity or status. That cannot carry
C16. New shape:

```sql
CREATE TABLE observation (
  id            INTEGER PRIMARY KEY,
  product_id    INTEGER NOT NULL,      -- resolved product (GTIN or generic item)
  store_id      INTEGER NOT NULL,
  source        TEXT    NOT NULL,      -- FLYER | RECEIPT | PARTNER
  tier          INTEGER NOT NULL DEFAULT 0,  -- 0 ANY, 1 CPF, 2 CNPJ
  price_cents   INTEGER NOT NULL,
  unit          TEXT    NOT NULL,      -- UN | KG | L ...
  pack_qty      INTEGER NOT NULL DEFAULT 1,
  seen_at       INTEGER NOT NULL,      -- epoch s of the sale / flyer publication
  valid_until   INTEGER,               -- flyers only
  status        INTEGER NOT NULL,      -- 0 REJECTED, 1 UNCONFIRMED, 2 CONFIRMED
  confidence    INTEGER NOT NULL,      -- 0..100
  confirmations INTEGER NOT NULL DEFAULT 0,
  receipt_hash  TEXT,                  -- sha256(access key), receipts only; never the key
  reject_code   TEXT,                  -- H1..H6 when REJECTED
  created_at    INTEGER NOT NULL
);
CREATE INDEX observation_product ON observation(product_id, status, seen_at);
CREATE INDEX observation_store   ON observation(store_id, status, seen_at);
```

The published `price` (best price per product/store) becomes a view/aggregate over confirmed rows, keeping the
previous shape for the app. Unconfirmed rows are shipped separately or flagged (see §9).

## 4. Hard checks — reject, no reward

| Code | Check | Rule |
|---|---|---|
| H1 | Identity and parse | GTIN valid (check digit) or generic item mapped; size/unit parsed; `price_cents > 0`; unit price within category bounds |
| H2 | Receipt arithmetic | `sum(lines) + discounts == total ± R$ 0,05`; line count sane; CNPJ 14 digits; access-key checksum valid; emission date not in the future, not older than 90 days |
| H3 | Dedupe | `sha256(access key)` unseen; the same line not inserted twice |
| H4 | Allowlist | Only the official SEFAZ-BA NFC-e host may be consulted; never an arbitrary URL taken from a QR code |
| H5 | Privacy | No CPF, buyer name or raw access key in the upload; if the parsed payload contains them, strip on the phone before sending and never store them |
| H6 | Limits | Payload size, items per receipt, and per-install daily caps respected |

A failed hard check is not a punishment: the UI says "não conseguimos ler esta nota" and the user can retry.

## 5. Soft checks — quarantine, never delete

Run in the publish job (Python, pure code, no LLM).

| Code | Signal | Rule (initial, config) |
|---|---|---|
| S1 | Unit price vs regional median | Compare R$/L, R$/kg or R$/un against the product's regional median, last 90 days, min. 10 observations. Flag outside 0.5×–2.0×, or modified z-score `0.6745 × (x − median) / MAD` with `|z| > 3.5` |
| S2 | Store history | Compare with the same product's median at that store (90 days). A 60% drop is plausible as a promo; a drop that persists > 14 days is likely a new regular price |
| S3 | Flyer match | Same product, same store, same price inside the flyer's validity window → upgrade to `CONFIRMED` |
| S4 | Second independent receipt | Another receipt for the same product/store/price with a **different** `receipt_hash`, ≥ 24 h apart or from a different install → `CONFIRMED` |
| S5 | Store pattern | Several outliers at one store on one day = clearance/price-error event. Keep, flag the batch, review together |
| S6 | Persistence | An outlier that persists > 14 days is treated as a real new price (still needs S3/S4 to become `CONFIRMED`) |
| S7 | OCR confidence | Only if a photo/OCR fallback is ever added; low-confidence lines are never credited |
| S8 | Contributor trust | New installs and installs with recent rejects get a lower confidence bonus until they build history |

False positives are expected. **No soft check deletes data**; it changes status and confidence, and the review queue
decides. The reference price is never an online marketplace price (shipping, different seller, different size) — it
is the same store's history, the regional median, the flyer and a second receipt.

## 6. Status and confidence

Start at confidence 50. Adjustments:

- +25 flyer match (S3) or second independent receipt (S4); +15 partner list;
- −30 outlier (S1/S2); −20 low contributor trust; −40 arithmetic/parse warning inside tolerance;
- clamp 0..100.

Status rules:

- `REJECTED` — any H1–H6 failure. Not published, not paid.
- `CONFIRMED` — confidence ≥ 75 **or** S3 match **or** S4 second independent receipt.
- `UNCONFIRMED` — everything else that passed the hard checks.

A `CONFIRMED` observation can be demoted if a later independent observation contradicts it and no flyer supports it.

## 7. Rewards — zero-cost, quality-weighted **(owner)**

The app has no revenue at launch. Cash rewards are out (fraud, tax, payment complexity). Rewards are non-monetary
and only paid for **accepted** observations.

Earn "pontos de ajuda" (local, per install):

| Event | Points |
|---|---|
| Accepted receipt (hard checks passed) | 10 |
| Coverage bonus: store with < 5 observations in the last 30 days | +15 |
| Confirmation bonus: this receipt is the second independent one (S4) | +25 |
| Rejected receipt | 0 |

Cap: at most 10 rewarded receipts per install per day; one reward per `receipt_hash` ever (two users photographing
the *same* receipt is one purchase — the second earns nothing, and it does not count as an independent confirmation).

Spend (all local, no server identity):

| Points | Perk |
|---|---|
| 100 | 90-day price chart |
| 300 | Extra price alerts |
| 600 | Early access to new features |
| 1 000 | "Guardião dos preços" badge |

Plus: the "Você já ajudou N pessoas a economizar" counter (from the manifest, global), and an **opt-in**
pseudonymous monthly "Top contribuidores do bairro". No names unless the user chooses one.

Anti-abuse: dedupe by key hash, per-install caps, trust score, and (later) Play Integrity. No cash, no lottery in v1
(promotional draws in Brazil fall under Lei 5.768/71 and need authorization). These points must never unlock anything
we sell through Play Billing, to stay clear of the payments policy.

## 8. Flyer rules — facts only **(owner)**

_Canonical version: [`flyer-policy.md`](flyer-policy.md). Summary:_

We use publicly distributed flyers without asking, but only the facts:

- **Take:** product description, size/unit, price (CPF and CNPJ tier when both are shown), validity dates, store.
- **Never take:** the flyer's photos, artwork, layout, page reproduction, the store's logo, or a wholesale copy of the
  list in the flyer's own order. No images are ever republished.
- Legal basis: prices and product data are facts; Lei 9.610/98 art. 7º, XIII protects the selection/organization of a
  database, and §2º excludes the data or information themselves. Using the store's name to say where the price is =
  nominative use; logos only with authorization.
- **Attribution:** "Preço divulgado pela loja no encarte de DD/MM, válido até DD/MM."
- **Validity:** expired flyer prices are never shown as current.
- **Opt-out:** any store that asks to be removed is removed immediately; we answer within 7 days.
- Permission is still **requested** — for the weekly PDF arriving reliably, for logo/brand use, and for a commercial
  partnership — but it is not a precondition for using the facts.
- A flyer price **is** an offer (it has validity); a receipt price never is.

## 9. App/UI rules

- `CONFIRMED` — normal display, price + age ("vendido há 3 h", real age as always).
- `UNCONFIRMED` — shown with a "não confirmado" / "1 nota" badge. It is **never** the headline cheapest in search or
  the optimizer without the badge; the optimizer applies a tie-break penalty and prefers confirmed prices.
- `REJECTED` — never shown.
- A "esse preço está errado?" report button on every price; reports feed the review queue.
- The optimizer keeps the owner rule: prices older than 12 days stay usable and are counted/subtotalled as uncertain.

## 10. Where each check runs

1. **Phone** — parse the NFC-e, strip CPF/name, compute `receipt_hash`, build the JSON; one user-initiated request to
   the official NFC-e host (never to Preço da Hora).
2. **Intake** — Cloudflare Worker + D1: rate limits, size limits, dedupe by hash, no accounts.
3. **Publish job** — H2–H6 re-validation, S1–S8, status/confidence, build `data.db`, update the review queue.
4. **Review queue** — a private CSV/page with product, store, price, median, z-score, confirmations, date; owner (or a
   helper) marks *promo confirmada / erro / descartar*. Minutes per week at launch volume.

## 11. Metrics (printed in the publish summary)

- Rejection rate (target < 10%), confirmation rate (> 60% after 30 days), outlier rate, top reject codes.
- Median cart coverage at the top-20 stores (C2), now computed over confirmed flyer/receipt data.
- Reward points issued (should be ~0 cost), per-store coverage gained from receipts.

## 12. Open questions

- OCR fallback for printed receipts (v1 = QR only, OCR later; it is the biggest error source).
- Terms of the NFC-e consultation portal (M3 research, as in plan §11.12).
- Play Integrity budget and whether device attestation is worth it at launch.
- Whether `UNCONFIRMED` prices appear in v1 at all, or only after a first confirmation.
- Confidentiality terms for partner full price lists (different from public flyers).

## 13. References

- Plan v2 §8.4 (outliers), §9.3 (schema — superseded by §3 here), §11.12 (receipt scanning), §12 (optimizer),
  C2 (cart coverage), C6 (receipts), C14 (no phone numbers/MEI names), C16 (source pivot).
- Lei 9.610/98 art. 7º, XIII and §2º; CDC arts. 30–37; Lei 9.279/96 (trademarks, unfair competition).
- Not legal advice; the 1-hour lawyer consult before charging businesses still applies.
