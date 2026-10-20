# Source Terms of Use — search log (plan v2 C12)

Goal: find any Terms of Use / privacy policy of Preço da Hora Bahia (site or official app) and check whether they
forbid automated access or data reuse. If they do → NO-GO for scraping (plan v2 §16.1).

## Checked so far (2026-10-20)

| Where | Result |
|---|---|
| Portaria SEFAZ-BA nº 42/2020 | No rule on reuse, redistribution, commercial use, API or automated access (review §2). Art. 5: prices are not offers. |
| `https://precodahora.ba.gov.br/robots.txt` | No robots.txt (HTTP 200 soft-404 HTML page, 23,487 bytes) → no crawl rules (probe run 39470762298). |
| Web search: "Preço da Hora" + "termos de uso" / "política de privacidade" | No Terms of Use found. |
| App Store listing ([id1503335648](https://apps.apple.com/br/app/id1503335648)) | Developer PRODEB. Privacy policy link: `https://precodahora.ba.gov.br/termos/politicadeprivacidade.pdf` → **HTTP 404** (20 Oct 2026). No app-specific terms link. Privacy label: may collect location and identifiers, not linked to identity. |
| Google Play listing (`br.gov.ba.precodahora`) | Not readable by our fetch tool; to be checked by the owner in a browser/phone. |
| Site footer (`/produtos/` page, read once 20 Oct 2026) | Says: "A utilização deste site está sujeita à aceitação dos termos de uso e termos de privacidade." Links: "termos de uso" → `/termos/termosecondicoes.pdf` (**real HTTP 404**); "termos de privacidade" → `/termos/politicadeprivacidade.pdf` (**HTTP 404**). Relative variant `/produtos/termos/…` → soft-404 page. Also "® Todos os direitos reservados aos realizadores". |
| Site search UI | Filters shown: price range and location only. **No establishment/CNPJ filter** in the UI. |

## Still to check (owner, by hand — no automated requests)

- Official app → settings / "Sobre" / registration screens: any "Termos de uso"?
- Site footer of `https://precodahora.ba.gov.br/` in a normal browser.
- Google Play listing → "Política de privacidade" link.

## Current conclusion

Terms of use **exist by reference** (footer) but **cannot be read**: both PDFs are dead links. Nothing readable forbids
automated access or reuse. Owner decision (20 Oct 2026): continue M0 at minimal volume (honest bot, ≥ 25 s spacing,
stop on any refusal) and ask SEFAZ-BA for the terms text in the LAI request (question 5). If the terms, once obtained,
forbid automated access → stop scraping and move to LAI/partnership + receipt scanning (C6).
"® Todos os direitos reservados" concerns the site itself; prices are facts and not protected (plan v2 §16.1).
