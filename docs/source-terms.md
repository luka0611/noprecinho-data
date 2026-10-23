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

## Terms FOUND (2026-10-20, by the owner)

`https://precodahora.ba.gov.br/condicoesdeusoetermos` (HTML page; the footer PDFs are still dead). Key clauses
(paraphrased):

| Clause | What it says |
|---|---|
| 3.1 | Use license is non-exclusive, limited, **personal and non-commercial only**. |
| 3.3 | No right to copy or reproduce any part of the services. |
| 3.7 | No distributing / modifying / selling / retransmitting any part of the services for any business, commercial **or public** purpose; no copying, selling, distributing or transferring content. |
| 4.7 a(iii) | Forbids *disguising the origin* of public information transmitted to third parties (implies passing it on with the source named is contemplated). |
| 4.9 c | No excessive load on the infrastructure. |
| 6.1 | Content claimed as protected by copyright. |
| 7.1 | No reproducing / copying / selling / exploiting any portion for commercial ends, nor using it to promote a company. |
| 8.6 | Forum: Comarca de Salvador. |

## Current conclusion (2026-10-20, replaces the earlier one)

The terms, as written, **forbid our model** (automated copying + public redistribution in an app, with or without
ads/donations). Plan rule (v2 §16.1, this file): terms forbid it → **stop scraping**. Status: **NO-GO for collecting
from Preço da Hora without written permission from SEFAZ-BA.** No more probes. No price data was stored in git (probe
artifacts expired after 3 days).

Counter-arguments (for negotiating, NOT for ignoring the terms): prices are facts; Lei 9.610/98 art. 7 §2 says database
protection does not cover the data themselves; LAI (Lei 12.527/2011) art. 8 §3 III asks transparency sites to allow
automated access in open formats; clause 4.7 a(iii) itself contemplates passing public info on with attribution. A
lawyer must confirm before relying on any of this.

Paths that stay open: written authorization / data agreement / API from SEFAZ-BA (ask with attribution + polite-rate
proposal); LAI request for the dataset; user-scanned receipts (C6); store flyers and store partnerships (B2B).

## LAI answer (2026-10-23) — final

Protocol **3355579** (sent 20 Oct 2026) was answered on 23 Oct 2026, ahead of the ~9 Nov deadline. Summary of the
official reply (quoted short; owner's name omitted, full text kept by the owner):

| Question | Answer |
|---|---|
| Third-party reuse, including commercial? | "Não há previsão de reutilização por terceiros das informações divulgadas no site e no app. Elas são destinadas exclusivamente para o usuário final." |
| Automated access at low frequency? | **"Não é permitido o acesso automatizado ao site."** |
| Open database / official API? | "Não está prevista." |
| Partnership contact? | Contacts go to SEFAZ, but "não há planos para converter o Preço da Hora Bahia em uma infraestrutura para provimento de outros serviços automatizados." |
| Terms of Use text? | Available in the app, Menu Principal → "Sobre o app"; they acknowledged the broken website links and requested the fix. |

Consequence: the NO-GO is confirmed **in writing** and without a rate limit to negotiate. No more requests to the
source, no appeal (the questions were answered; an appeal does not grant a reuse license). See `M0-report.md`.
The in-app Terms should still be screenshotted by the owner for the record.
