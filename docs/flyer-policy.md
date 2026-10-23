# Flyer policy (encartes) — v1

_Written 2026-10-23. Owner decisions of 23 Oct 2026. Companion: `receipt-quality.md` (validation, status, rewards)._

## 1. Scope

Public weekly flyers (**encartes**) from supermarkets, atacarejos, mercadinhos and depósitos in Salvador and Lauro de
Freitas. In the database these are observations with `source = FLYER`.

A flyer price **is** an offer: the store published it, with a validity window. That is what lets the app call it
"oferta" (plan v2 C9 — for receipt prices that word stays forbidden).

## 2. The rule in one paragraph

We use **the facts** from a publicly distributed flyer — product, size, price, validity, store — and we never use the
flyer as a work: no photos, no artwork, no layout, no page reproduction, no logo. Using facts does not require prior
permission; we still ask stores for the weekly file, for logo use and for a partnership, because that is better
business and better relations. Any store that asks to be removed is removed immediately.

## 3. What we take, what we never take

| Take | Never take |
|---|---|
| Product description (short, factual), brand if shown | Photos, illustrations, background art |
| Size / unit / pack quantity | The flyer's layout, colours, page as an image |
| Price in cents (CPF and CNPJ tiers when both shown) | The store's logo (unless an authorized partner) |
| Validity start/end dates | Promotional copy, slogans, "só hoje" claims verbatim |
| Store: trade name, CNPJ, address, chain | The flyer's full list in its own order (see §5) |
| Page/reference date, source provenance | Prices without a stated validity (see §8) |

Personal names: if a flyer shows an MEI/individual's name instead of a trade name, apply C14 — trade name only, or
skip the store.

## 4. Legal basis (short, not legal advice)

- Prices, product descriptions, sizes and dates are **facts/data**. Lei 9.610/98 art. 7º, XIII protects a database's
  *selection or organization* as a creative work, and §2º expressly excludes "dados ou informações em si". Brazil has
  no separate database right.
- What remains protected: the flyer's **photos** (art. 7º, VII), artwork and layout. Copying them is infringement —
  so we don't.
- Store **name** used to say where the price is = nominative use. The **logo** is a trademark — only with permission.
- A flyer price binds the store as an offer (CDC art. 30). Republishing it wrongly or after expiry is misleading
  information (CDC art. 37) and can also be unfair competition if it is inaccurate or denigrating.
- Automated collection from a store's site, app or Instagram can breach *their* terms even though the facts are free:
  download publicly posted files by hand or with permission, never scrape.

## 5. How we obtain a flyer

Allowed:

- PDF/link published on the store's own website or sent in a WhatsApp broadcast;
- flyer handed out at the store, or a photo of a public in-store poster (it is advertising material, meant to be read
  and passed on);
- the store sends it to us after our message (`PERMISSION_AND_STORES.txt` in the plan repo).

Not allowed:

- automated scraping of Instagram/Facebook/store apps (platform terms);
- working around any block, login or CAPTCHA;
- reusing another site's copy of the flyer as if it were the source.

**Provenance** is recorded for every flyer: where it came from (URL / WhatsApp / photo), date received, file SHA-256.
The flyer file itself stays out of the public repo (it contains protected artwork): keep it in a private folder
(`secrets/flyers/`) or the private plan repo, never in `noprecinho-data`.

## 6. Extraction workflow

1. **Extract** — vision LLM (Gemini, batched) over the flyer image/PDF; output strict JSON: `items[]` with raw
   description, size/unit, `price_cents`, `tier` (ANY/CPF/CNPJ), `valid_from`, `valid_until`, page/position.
   Cache by file hash so the same flyer is never re-processed.
2. **Normalize** — match to a product: GTIN if printed; otherwise the regex size/unit parser + a catalog match; no
   confident match → `UNCONFIRMED` and a line in the catalog review list.
3. **Validate** — price > 0, validity sane (≤ 30 days, end ≥ start), duplicates removed, unit price within category
   bounds. Failures go to the review queue, not to the app.
4. **Map stores** — "válido em todas as lojas da rede" → all chain stores in the region; store-specific → that CNPJ
   only. Ambiguous → `UNCONFIRMED`.
5. **Publish** — inside the validity window a flyer observation is `CONFIRMED` by definition (the store declared it);
   extraction confidence low or store ambiguous → `UNCONFIRMED`.
6. **Expire** — after `valid_until` the price is never shown as current; it stays in history.

## 7. CPF / CNPJ tiers

Atacarejo flyers often carry two prices. Record `tier`:

- buyer with CNPJ may pay the CNPJ price; a CPF buyer never does (already in the app model);
- a single price → `ANY`;
- "preço de atacado mediante quantidade mínima" → keep the price and flag the quantity condition; the app shows
  "pode exigir quantidade mínima".

## 8. Validity

- Use the dates printed on the flyer. End of validity = 23:59 local time (America/Bahia) of the last day.
- No validity stated → do **not** invent one: mark `UNCONFIRMED`, expire after 7 days, and ask the store.
- A flyer that covers a month or a holiday period keeps those dates; no extrapolation.
- Expired flyer price + no receipt → not shown as current.

## 9. Attribution and display

Every flyer price shows:

> Preço divulgado pela loja no encarte de DD/MM/AAAA, válido até DD/MM/AAAA.

- "Oferta da loja" is allowed **only** for flyer/partner prices with a validity window — never for receipt prices.
- No store logo unless the store authorized it; default is the store name plus the chain colour dot.
- A flyer price never changes ranking because of a sponsorship (plan §15.4, tested).

## 10. Store relations

- We still send the message asking for the weekly flyer, permission to use the logo, and a partnership. Keep the
  evidence of every **yes** and every **no** in `secrets/store_permissions/` (never uploaded, never in the public
  repo).
- A "yes" is about supply and brand use, not about the legality of the facts — say so plainly if a store asks.
- **Opt-out:** if a store asks to be removed, remove its flyer data within 7 days, confirm in writing, and stop using
  its flyers. Receipt data for that store follows the same takedown request.
- Never imply endorsement or partnership that was not agreed.

## 11. Quality control

- Spot-check ~10 items per flyer after extraction (price, size, tier, validity).
- Duplicate flyers (same store, same validity, same content) dedupe by store + validity + file hash.
- Conflict with receipts: during validity the flyer wins (it is the declared offer); after validity the newer
  receipt wins. Two receipts contradicting a flyer inside its window → flag for review, keep the flyer visible with
  its validity.
- A flyer price that is an extreme outlier vs. the product's median is still published **with its validity**, but
  flagged in the review queue — the store may be running a loss leader.

## 12. Errors and corrections

- A wrong price is **our** error: fix within 24 h, and if it was widespread add a line to `manifest.notice`.
- Stores and users can report via the `/bot` page or the in-app "preço errado" button; answer within 7 days.
- Never blame the store for our extraction mistake.

## 13. Checklist before a flyer goes live

- [ ] provenance recorded (source, date, file hash), file kept out of the public repo
- [ ] validity parsed and sane; no invented dates
- [ ] CPF/CNPJ tiers correct
- [ ] store mapping correct (chain-wide vs. single store)
- [ ] ~10 items spot-checked against the flyer
- [ ] no image, artwork or logo used
- [ ] attribution text set
- [ ] conflicts/outliers sent to the review queue

## 14. FAQ

**Do we need the store's permission to use flyer prices?** No, for the facts. Yes for images, artwork, the logo and
any "partner" presentation. We ask anyway, for the file feed and the relationship.

**Can we say "oferta"?** Only for flyer/partner prices inside their validity. Never for receipt prices.

**Can we copy the flyer's text?** Use short factual descriptions ("Sabão em pó 1 kg"), not the promotional copy.

**What if the store says no?** Remove its flyer data and stop using its flyers; receipt data for that store is removed
too if asked. No argument, no workaround.

**What if the flyer is only on Instagram?** Ask the store to send the PDF, or download it by hand. Do not scrape.

**What about a photo we took in the store?** Same rules: facts only, no image republished.

## 15. References

- Plan v2 C9 (no "oferta" for receipts), C14 (MEI/phone), C16 (source pivot), §8.3 (stores), §8.4 (outliers),
  §21.4 (copy deck).
- `receipt-quality.md` §8 (summary), §4–§6 (validation and status).
- Lei 9.610/98 art. 7º, XIII e §2º; CDC arts. 30–37; Lei 9.279/96.
- Not legal advice; the 1-hour lawyer consult before charging businesses still applies.
