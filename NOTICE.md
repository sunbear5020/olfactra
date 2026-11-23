# NOTICE — OLFACTRA

**OLFACTRA** (The Intelligence of Scent) is an independent open-source project by
**FEI · HEL Lab, Gyeongsang National University**, released under the MIT License.
`Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University`.

**Version 0.2.0** — JSON schema `0.2.0`. This release adds the provenance
registry (section 3-quater), calculated LogP/TPSA descriptors and the
Markdown/Excel methodology reports.

## 1. Clean-room statement

OLFACTRA was built from **public** chemistry, botany and history sources only:

| Layer | Source of truth | What is *not* used |
| --- | --- | --- |
| Molecule library | PubChem records (CID, molecular formula, molecular weight, SMILES) for 43 fragrance materials | no proprietary captive-molecule data, no supplier technical sheets reproduced |
| 3-D structures | RDKit ETKDGv3 embedding + MMFF94s optimisation of the same public SMILES, computed locally | no coordinates copied from a commercial structure database |
| Receptor binding model | published structural principles of class A GPCR 7-TM bundles; Ballesteros–Weinstein residue numbering | no PDB entry re-distributed, no commercial docking score, no proprietary pharmacophore model |
| Odour perception data | **Pyrfume Data** (MIT) extract of Keller & Vosshall 2016, Dravnieks 1985 and Mainland et al. 2015, matched by PubChem CID | no re-typed or estimated values; materials without a measurement are marked as unmeasured |
| Odour description | public odour descriptions and published essential-oil composition literature | no commercial fragrance-oil GC-MS reports, no branded formula cards |
| History (ATLAS) | public-domain ancient texts, museum/herbarium records, open-access papers | no modern translation text reproduced beyond short factual reference |
| Formulation logic | own implementation of dilution arithmetic and note balance | no IFF/IFRA/Givaudan/Firmenich proprietary formula or software |
| Structures (web) | SVG drawn from the public SMILES, generated locally | no vendor images, logos, or screenshots |

No trademark, logo, trade dress, or proprietary formulation of any fragrance
house is used. Plant names, material names and company-neutral chemical names
appear only as factual references; all trademarks remain with their owners.

## 2. Scientific boundary — read this before citing results

> **0.2.0** labels every indicator `measured`, `derived` or `heuristic`; section
> 3-quater describes that registry.

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

## 3-bis. 3-D structure and receptor-binding model — read this before citing a pose

The `MOLECULE` tab shows two different things, and they carry different weight.

**The 3-D structure of each molecule is real geometry.** Every one of the 43
molecules is embedded from its public SMILES with RDKit's ETKDGv3 distance
geometry and relaxed with the MMFF94s force field. Bond lengths, angles and the
conformer are the result of that computation and can be checked against the
SMILES. What it is *not*: a conformational ensemble. A molecule with several
rotatable bonds visits many shapes in solution; the page shows one low-energy
conformer and does not claim it is the bioactive one.

**The receptor–ligand binding view is a schematic teaching model.**

- The four receptors (OR1A1, OR2J3, OR5AN1, OR1G1) are represented by an
  idealised 7-transmembrane α-helix bundle built from the *published layout* of
  class A GPCRs, not from a PDB structure file.
- Their pocket residues are **model residues** named with Ballesteros–Weinstein
  numbers (`Phe6.51`, `Asn7.39`, …), chosen for the chemistry that receptor class
  is reported to respond to. They are not the atomic coordinates or the exact
  sequence positions of any specific receptor.
- Docking is a deterministic rigid-body search of that single conformer inside
  the cavity, scored by the number and type of contacts it can make with the
  model residues. There is no force field, no solvent, no entropy term and no
  scoring function fitted to measured affinities.
- The H-bond / hydrophobic / π lines and the ångström values are distances in
  **this model's coordinates**, between a ligand atom and a residue side-chain
  functional group (or side-chain centroid). They are not measured distances.
- The displayed "모식 적합도(schematic fit)" is a presentation aid for comparing
  poses, not Kd, EC50, ΔG or any other affinity value. Nothing here is a
  prediction that a molecule smells a particular way, and nothing here replaces
  a wet-lab binding assay, an olfactometer study, or a safety assessment.
- Where the public Mainland et al. (2015) screen measured a response for the same
  molecule–receptor pair, the viewer says "문헌 보고 활성" and names the source.
  When it says nothing, no measurement is claimed — not even an absence of
  binding, because many of these pairs were never assayed.

## 3-ter. Pyrfume — the public odour datasets, and their limits

`olfactra_core/datasets/pyrfume_olfactra.json` is a **subset of Pyrfume Data**
(https://github.com/pyrfume/pyrfume-data, MIT License), regenerated with
`tools/build_pyrfume_bundle.py`. The bundle records every source file's SHA-256
so the snapshot can be verified. Three datasets are used:

| Key | Reference | What it contributes |
| --- | --- | --- |
| `keller_2016` | Keller A, Vosshall LB (2016). *Olfactory perception of chemically diverse molecules.* BMC Neuroscience 17:55. doi:[10.1186/s12868-016-0287-2](https://doi.org/10.1186/s12868-016-0287-2) | pleasantness, intensity and familiarity (0–100) of single odorants, plus 20 semantic descriptor ratings |
| `dravnieks_1985` | Dravnieks A (1985). *Atlas of Odor Character Profiles.* ASTM DS61. doi:[10.1520/DS61-EB](https://doi.org/10.1520/DS61-EB) | 146-descriptor odour character profiles |
| `mainland_2015` | Mainland JD, Li YR, Zhou T, Liu WLL, Matsunami H (2015). *Human olfactory receptor responses to odorants.* Scientific Data 2:150002. doi:[10.1038/sdata.2015.2](https://doi.org/10.1038/sdata.2015.2) | which human olfactory receptors a molecule activated in a cell-based screen |

Pyrfume itself is described in Hamel et al. (2024), *Pyrfume: a window to the
collective intelligence of smell*, Scientific Data,
doi:[10.1038/s41597-024-04051-z](https://doi.org/10.1038/s41597-024-04051-z).

**Coverage, stated plainly.** Of the 43 molecules in this library, **23 have at
least one measured value** in the bundle — 18 in Keller 2016, 14 in Dravnieks
1985 and 8 in Mainland 2015 (a molecule can appear in more than one). The other
20 (most of the sesquiterpenes, muscone, cis-jasmone, hinokitiol, …) are **not**
in these datasets; the page marks them `미측정` and this project does not
interpolate a value for them. Their odour descriptions rest on general
essential-oil and chemistry literature, which is a weaker kind of evidence and
is labelled as such.

**How the numbers are used.** Measured pleasantness enters `OLFACTRA ID` only as
a small documented prior (weight 1.2 out of roughly 14 total FIT points), shown
as one reason line and as a per-material evidence table, and only when at least
15 % of an accord's mass carries a measured value. It never decides the ranking
by itself, because **a blend is not the sum of its parts**: masking, synergy and
adaptation make mixtures smell different from every component. An accord whose
materials average 70/100 can smell worse, better, or simply different.

## 3-quater. Provenance registry (0.2.0) — measured, derived, heuristic

Every number OLFACTRA shows is registered in `olfactra_core/provenance.py` with
three things a reader needs before quoting it:

| Evidence class | Meaning | Examples |
| --- | --- | --- |
| **measured** | published in a dataset or public record, checkable at the DOI | PubChem identity; Keller 2016 pleasantness/intensity/familiarity; Dravnieks 1985 descriptors; Mainland 2015 receptor responses |
| **derived** | computed from public inputs by a stated, reproducible method | dilution arithmetic (mL · g · % w/w); RDKit ETKDGv3 + MMFF94s conformers; Crippen LogP; Ertl TPSA; the hedonic prior |
| **heuristic** | a curated or rule-based ranking aid with no measured target | odour-family weights; blend harmony; note assignment; volatility index; the safety working ceiling; the schematic docking fit |

The registry carries each indicator's formula, inputs, references and **boundary**
in one place, and it is the single source for the METHOD tab, the Markdown report
appendix, the Excel `Methodology` sheet and `GET /api/provenance`. A heuristic
labelled as a heuristic cannot be mistaken for a measurement, and an unmeasured
molecule is never filled with an estimate.

### Calculated LogP and TPSA

`olfactra_core/datasets/descriptors_rdkit.json` is rebuilt from the public SMILES
of each PubChem CID by `tools/build_descriptors.py`:

- **LogP** — RDKit `Descriptors.MolLogP`, the Crippen (1988) atomic-contribution
  method with Wildman–Crippen (1999) corrections.
- **TPSA** — RDKit `rdMolDescriptors.CalcTPSA`, the Ertl, Rohde & Selzer (2000)
  fragment method.

Both are **estimates from a contribution model, not measurements**: no
experimental partition coefficient, no vapour pressure. They describe the
molecular character of a formula and let two formulas be compared; they do not
predict how fast a blend evaporates or how it will smell. The committed file
records the RDKit version and the method names so the values can be reproduced
(`python tools/build_descriptors.py --check`).

### Volatility is a heuristic, and vapour pressure is not used

The volatility index on the MOLECULE map is `base(note) × clamp(170 / MW, 0.55, 1.20)`.
No vapour-pressure dataset is bundled with this project, so **no vapour pressure
or LogP term is used to estimate volatility**; the index only orders materials
along the note axis. Vapour pressure is reported here as a limitation, not as a
number.

## 4. Attribution and citation

If you use OLFACTRA in research, teaching or a product, please cite:

> FEI · HEL Lab (2026). *OLFACTRA: The Intelligence of Scent (Core 0.2.0)*.
> Gyeongsang National University. https://github.com/sunbear5020/olfactra (MIT)

The bundled odour-perception data must be cited through its own sources as well
(Keller & Vosshall 2016; Dravnieks 1985; Mainland et al. 2015; Pyrfume / Hamel
et al. 2024 — full references in section 3-ter).

## 5. Data corrections

Chemical data errors are treated as bugs. If a formula, molecular weight, CAS
number or SMILES is wrong, open an issue with the PubChem CID or a primary
reference and it will be corrected in the library and in the published web
workbench.
