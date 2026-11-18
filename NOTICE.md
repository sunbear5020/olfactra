# NOTICE — OLFACTRA

**OLFACTRA** (The Intelligence of Scent) is an independent open-source project by
**FEI · HEL Lab, Gyeongsang National University**, released under the MIT License.
`Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University`.

## 1. Clean-room statement

OLFACTRA was built from **public** chemistry, botany and history sources only:

| Layer | Source of truth | What is *not* used |
| --- | --- | --- |
| Molecule library | PubChem records (CID, molecular formula, molecular weight, SMILES) for 43 fragrance materials | no proprietary captive-molecule data, no supplier technical sheets reproduced |
| Odour description | public odour descriptions and published essential-oil composition literature | no commercial fragrance-oil GC-MS reports, no branded formula cards |
| History (ATLAS) | public-domain ancient texts, museum/herbarium records, open-access papers | no modern translation text reproduced beyond short factual reference |
| Formulation logic | own implementation of dilution arithmetic and note balance | no IFF/IFRA/Givaudan/Firmenich proprietary formula or software |
| Structures (web) | SVG drawn from the public SMILES, generated locally | no vendor images, logos, or screenshots |

No trademark, logo, trade dress, or proprietary formulation of any fragrance
house is used. Plant names, material names and company-neutral chemical names
appear only as factual references; all trademarks remain with their owners.

## 2. Scientific boundary — read this before citing results

- OLFACTRA **proposes candidate combinations** from public molecule and odour
  data. It does **not** predict how a blend will smell, how it will perform on
  skin, or how it will behave in a specific base.
- Output is meant to **support**, not replace, sensory evaluation, GC-MS analysis,
  stability testing, and a real safety assessment.
- Odour-family weights, note placement and harmony scores are **heuristic
  parameters**, documented as such. They are not measured constants and are not
  fitted to a sensory panel. Treat scores as ranking aids.
- Historical dates are approximate first attestations, not invention dates.
  Where a claim rests on later tradition rather than a primary record, the ATLAS
  text says so.

## 3. Safety boundary

`working_cap_pct` values are **conservative internal working ceilings** for
hobby and research blending, assembled from general public cosmetic/fragrance
guidance (EU declarable-allergen list, published sensitizer and irritant notes,
common perfumery practice). They are:

- **not** IFRA Standards certificates,
- **not** a regulatory opinion for any jurisdiction,
- **not** a substitute for a cosmetics safety assessment (CPSR) or for product
  notification before sale.

Ambient formats (reed diffuser, room spray) are judged against the same ceiling
multiplied by an explicit exposure-route factor, because skin sensitisation
limits are written for skin contact. Ventilation, infants and pets warnings are
never relaxed by that factor.

## 4. Attribution and citation

If you use OLFACTRA in research, teaching or a product, please cite:

> FEI · HEL Lab (2026). *OLFACTRA: The Intelligence of Scent (Core 0.1.0)*.
> Gyeongsang National University. https://github.com/sunbear5020/olfactra (MIT)

## 5. Data corrections

Chemical data errors are treated as bugs. If a formula, molecular weight, CAS
number or SMILES is wrong, open an issue with the PubChem CID or a primary
reference and it will be corrected in the library and in the published web
workbench.
