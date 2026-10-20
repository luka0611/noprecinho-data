# Source response schema (Preço da Hora Bahia) — observed in Milestone 0

Observed 2026-10-20 by the `schema` probe ([run 39470839852](https://github.com/luka0611/noprecinho-data/actions/runs/39470839852)):
`POST /produtos/` with `termo=arroz`, Pituba (-12.9986, -38.4614), `raio=2`, `ordenar=preco.asc`, `horas=72`, page 1,
from a GitHub-hosted runner. Raw JSON is kept only as a 3-day artifact (never committed). Example values below are
from that response; the store phone number is deliberately not reproduced (plan v2 C14).

## Envelope

| key | example | notes |
|---|---|---|
| `codigo` | `80` | 80 = ok (50 = no results; anything else → treat as a block) |
| `totalRegistros` | `603` | total sales lines matched in the window |
| `totalPaginas` | `4` | **capped at 4** even with 603 matches (4 × 25 = 100 lines max per search) |
| `registrosporPagina` / `registrosdaPagina` | `25` / `25` | page size fixed at 25 |
| `pagina` | `1` | |
| `dias` | `72` | window echoes `horas=72` (named "dias" but value is hours) |
| `dataConsulta` | `"2026-10-20 18:00:44-00:00"` | UTC |
| `categorias` | `[{"codigo": 8, "descricao": "ARROZ"}, …]` | the source's own categories present in the result |
| `centro` | object (3 keys) | search centre echo |
| `intervaloPreco` | object (2 keys) | min/max price of the result set |
| `tempoResposta` | `0.295` | server time in seconds |
| `resultado` | list of `{produto, estabelecimento}` | one item per **receipt line** (not per store) |

## `produto` (19 keys)

| key | example | notes |
|---|---|---|
| `descricao` | `"FLOCOS ARROZ CARAMELIZADOS"` | raw receipt description |
| `gtin` | `null` / `"7891…"` | **often null** — many lines have no barcode |
| `codProduto` | `"6159010800025751970"` | store's internal code, apparently CNPJ (14) + item code |
| `ncm` / `ncmGrupo` | `19041000` / `"OUTROS ALIMENTOS"` | tax class + its group name |
| `unidade` | `"UN"`, `"CX"`, `"PCT9"`, `"UND9"`, `"PT"`, `"PCE"`, `"PC"` | **free-form with suffixes** → normalize (strip digits, map synonyms) |
| `precoUnitario` | `2.0` | unit price (reais, float) |
| `precoBruto` / `precoLiquido` | `2.0` / `2.0` | gross / net of discount |
| `desconto` | `null` or number | 4 of 25 lines had a discount > 0 → v1 "com desconto" chip is feasible |
| `data` | `"2026-10-18 16:25:56-00:00"` | time of sale, UTC |
| `intervalo` | `"há 2 dia(s), 1 hora(s)…"` | human text; ignore (and it arrived mis-decoded — check response charset) |
| `timeSpan` | `5688` | age in minutes (= now − data) |
| `cod_nfce` | `"24026958736"` | receipt number → store only as SHA-1 hash for dedupe (plan §7.5) |
| `tipoNFe` | `65` | 65 = NFC-e (consumer receipt) |
| `foto` | `"https://api.precodahora.ba.gov.br/v1/images/default"` | government image URL — **never hotlink** from app/site |
| `anp`, `farmaciaPopular`, `score` | `null`, `false`, `null` | fuel code / pharmacy programme / search score |

## `estabelecimento` (15 keys)

| key | example | notes |
|---|---|---|
| `cnpj` | `"61590108000257"` | 14 digits |
| `nomeEstabelecimento` | `"VAREJAO DELICATESSEN"` | receipt (legal/trade) name — apply MEI rules (§8.3) |
| `endLogradouro`, `endNumero`, `bairro`, `cep` | `"AVENIDA AMARALINA"`, `"000885"`, `"AMARALINA"`, `"41900020"` | |
| `municipio`, `codMunicipio`, `uf` | `"SALVADOR"`, `2927408`, `"BA"` | IBGE code |
| `latitude`, `longitude` | `-13.0132`, `-38.4698` | present → no geocoding needed |
| `distancia` | `1.8595` | km from the search centre |
| `telefone` | (not reproduced) | **dropped at observation time — never stored or republished (C14)** |
| `tentativa`, `farmaciaPopular` | `2.0`, `false` | unknown meaning / pharmacy flag |

## First consequences for the collector (to confirm with the other probes)

- `ordenar=preco.asc` with a generic term returns cheap *unrelated* lines first ("FLOCOS ARROZ…" for "arroz") —
  GTIN/store-centric searches matter more than text searches.
- Page 1 of 25 lines covered 15 distinct stores within 2 km.
- No refusal, no CAPTCHA from a US GitHub runner → **no fallback host needed** (geo check passed, C1).
