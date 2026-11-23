"""OLFACTRA COMPARE — two formulas side by side, property profiles included.

What is compared
----------------
1. **Note pyramid** — the share of the concentrate in top / middle / base, so two
   structures can be read against each other (and not just as percentages).
2. **Molecular property profile** — mass-weighted mean molecular weight, mean
   calculated LogP and mean TPSA of the materials, plus the spread (min–max).
   These are *derived* descriptors (Crippen LogP, Ertl TPSA), not measurements:
   they describe the molecular character of the blend, not how it smells.
3. **Safety headroom** — the largest ``finished_pct_ww / cap`` ratio in each
   formula, shown as the fraction of the ceiling still free, plus the materials
   that are over or near their ceiling.

Everything here is arithmetic over :mod:`olfactra_core.studio` results, so the
same numbers appear in the CLI, the API, the Markdown report and the web
workbench.  Nothing in this module predicts an odour; see
:mod:`olfactra_core.provenance` for the boundary of each indicator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from . import __version__, molecule as mol_lib
from . import provenance, studio


def _weighted(rows: Iterable[studio.MaterialRow], getter) -> float:
    """Mass-weighted mean of a per-material value over the concentrate."""
    num = 0.0
    den = 0.0
    for row in rows:
        m = mol_lib.get(row.id)
        w = row.mass_g
        num += getter(m) * w
        den += w
    return num / den if den else 0.0


def property_profile(formula: studio.Formula) -> dict[str, Any]:
    """Molecular-property profile of one formula (mass-weighted over the concentrate)."""
    rows = formula.rows
    mws = [mol_lib.get(r.id).molecular_weight for r in rows]
    logps = [mol_lib.get(r.id).logp for r in rows]
    tpsas = [mol_lib.get(r.id).tpsa for r in rows]
    max_ratio = max((r.cap_ratio for r in rows), default=0.0)
    return {
        "materials": len(rows),
        "mean_mw": round(_weighted(rows, lambda m: m.molecular_weight), 2),
        "min_mw": round(min(mws), 2) if mws else 0.0,
        "max_mw": round(max(mws), 2) if mws else 0.0,
        "mean_logp": round(_weighted(rows, lambda m: m.logp), 2),
        "min_logp": round(min(logps), 2) if logps else 0.0,
        "max_logp": round(max(logps), 2) if logps else 0.0,
        "mean_tpsa": round(_weighted(rows, lambda m: m.tpsa), 2),
        "max_tpsa": round(max(tpsas), 2) if tpsas else 0.0,
        "solid_share_pct": round(sum(r.share_pct for r in rows if r.is_solid), 2),
        "note_share_pct": {n: round(v * 100.0, 2) for n, v in formula.note_balance.items()},
        "fragrance_mass_g": round(formula.fragrance_mass_g, 3),
        "total_mass_g": round(formula.total_mass_g, 3),
        "finished_load_pct_ww": round(formula.finished_load_pct_ww, 3),
        "max_cap_ratio": round(max_ratio, 3),
        "headroom_pct": round(max(0.0, (1.0 - max_ratio)) * 100.0, 1),
        "status": formula.status,
        "over": [r.name_ko for r in rows if r.status == "over"],
        "caution": [r.name_ko for r in rows if r.status == "caution"],
        "allergens": list(formula.allergens),
    }


@dataclass
class Comparison:
    """Two formulas and the differences that matter between them."""

    a: studio.Formula
    b: studio.Formula
    label_a: str = "A"
    label_b: str = "B"

    # -- derived views ---------------------------------------------------
    def profile(self, side: str) -> dict[str, Any]:
        return property_profile(self.a if side == "a" else self.b)

    def deltas(self) -> dict[str, float]:
        pa, pb = self.profile("a"), self.profile("b")
        keys = ("mean_mw", "mean_logp", "mean_tpsa", "finished_load_pct_ww",
                "fragrance_mass_g", "headroom_pct", "max_cap_ratio")
        out = {k: round(pb[k] - pa[k], 2) for k in keys}
        for note in mol_lib.NOTES:
            out[f"note_{note}_pp"] = round(
                pb["note_share_pct"][note] - pa["note_share_pct"][note], 2
            )
        return out

    def summary_ko(self) -> list[str]:
        """Plain-language differences, ordered by how much they matter."""
        pa, pb = self.profile("a"), self.profile("b")
        d = self.deltas()
        lines: list[str] = []
        if pa["status"] != pb["status"]:
            lines.append(
                f"안전 판정이 다릅니다 — {self.label_a} '{_status_ko(pa['status'])}', "
                f"{self.label_b} '{_status_ko(pb['status'])}'."
            )
        if abs(d["headroom_pct"]) >= 5:
            tighter = self.label_b if d["headroom_pct"] < 0 else self.label_a
            lines.append(
                f"상한 여유분은 {self.label_b}가 {pb['headroom_pct']:.1f}%, {self.label_a}가 "
                f"{pa['headroom_pct']:.1f}% — {tighter} 쪽이 상한에 더 가깝습니다 "
                f"({abs(d['headroom_pct']):.1f}%p 차이)."
            )
        dominant = max(mol_lib.NOTES, key=lambda n: abs(d[f"note_{n}_pp"]))
        if abs(d[f"note_{dominant}_pp"]) >= 3:
            lines.append(
                f"{mol_lib.NOTE_LABELS_KO[dominant]} 노트가 {d[f'note_{dominant}_pp']:+.1f}%p "
                f"({self.label_a} {pa['note_share_pct'][dominant]:.0f}% → "
                f"{self.label_b} {pb['note_share_pct'][dominant]:.0f}%)."
            )
        if abs(d["mean_mw"]) >= 5:
            lines.append(
                f"평균 분자량은 {pa['mean_mw']:.1f} → {pb['mean_mw']:.1f} g/mol "
                f"({d['mean_mw']:+.1f}) — {'무거운' if d['mean_mw'] > 0 else '가벼운'} 쪽으로 이동."
            )
        if abs(d["mean_logp"]) >= 0.2:
            lines.append(
                f"평균 계산 LogP {pa['mean_logp']:.2f} → {pb['mean_logp']:.2f} "
                f"({d['mean_logp']:+.2f}) — {'더 소수성' if d['mean_logp'] > 0 else '더 극성'}인 조성."
            )
        if abs(d["mean_tpsa"]) >= 1.0:
            lines.append(
                f"평균 TPSA {pa['mean_tpsa']:.1f} → {pb['mean_tpsa']:.1f} Å² "
                f"({d['mean_tpsa']:+.1f})."
            )
        new_allergens = sorted(set(pb["allergens"]) - set(pa["allergens"]))
        gone_allergens = sorted(set(pa["allergens"]) - set(pb["allergens"]))
        if new_allergens or gone_allergens:
            bits = []
            if new_allergens:
                bits.append(f"{self.label_b}에 새로 표시 대상: {', '.join(new_allergens)}")
            if gone_allergens:
                bits.append(f"{self.label_a}에만 있던 표시 대상: {', '.join(gone_allergens)}")
            lines.append("알레르겐 표시 — " + "; ".join(bits) + ".")
        if not lines:
            lines.append("두 배합의 노트 구조·물성·안전 여유분이 거의 같습니다.")
        return lines

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.2.0",
            "labels": {"a": self.label_a, "b": self.label_b},
            "a": {
                "label": self.label_a,
                "product_type": self.a.product_type.id,
                "product_type_ko": self.a.product_type.name_ko,
                "volume_ml": self.a.volume_ml,
                "load_pct": self.a.load_pct,
                "status": self.a.status,
                "profile": property_profile(self.a),
                "materials": [r.as_dict() for r in self.a.rows],
            },
            "b": {
                "label": self.label_b,
                "product_type": self.b.product_type.id,
                "product_type_ko": self.b.product_type.name_ko,
                "volume_ml": self.b.volume_ml,
                "load_pct": self.b.load_pct,
                "status": self.b.status,
                "profile": property_profile(self.b),
                "materials": [r.as_dict() for r in self.b.rows],
            },
            "deltas": self.deltas(),
            "summary": self.summary_ko(),
            "boundaries": {
                **provenance.BOUNDARIES,
                "compare": (
                    "물성 평균은 향 농축액의 질량 가중 평균입니다. LogP·TPSA는 구조에서 계산한 "
                    "추정치이고, 노트 비중과 안전 여유분은 각 지표의 경계를 그대로 물려받습니다."
                ),
            },
        }


def _status_ko(status: str) -> str:
    return {"ok": "적합", "caution": "주의", "over": "상한 초과"}.get(status, status)


def compare_formulas(
    formula_a: studio.Formula,
    formula_b: studio.Formula,
    label_a: str = "A",
    label_b: str = "B",
) -> Comparison:
    """Compare two built formulas (note pyramid, property profile, safety headroom)."""
    if not isinstance(formula_a, studio.Formula) or not isinstance(formula_b, studio.Formula):
        raise TypeError("compare_formulas expects two studio.Formula objects")
    return Comparison(a=formula_a, b=formula_b, label_a=label_a, label_b=label_b)


def compare_accords(
    accord_a: str,
    accord_b: str,
    product_a: str | None = None,
    product_b: str | None = None,
    volume_a: float = 50.0,
    volume_b: float = 50.0,
    load_a: float | None = None,
    load_b: float | None = None,
) -> Comparison:
    """Convenience wrapper: compare two preset accords by id."""
    from . import recommender

    a = recommender.get_accord(accord_a)
    b = recommender.get_accord(accord_b)
    fa = studio.formulate(product_a or a.product_hint, volume_a, load_a, a.materials)
    fb = studio.formulate(product_b or b.product_hint, volume_b, load_b, b.materials)
    return Comparison(a=fa, b=fb, label_a=a.name_ko, label_b=b.name_ko)


def parse_accord_text(text: str) -> dict[str, float]:
    """'linalool=40,cedrol=60' → {'linalool': 40.0, 'cedrol': 60.0} (CLI helper)."""
    accord: dict[str, float] = {}
    for chunk in text.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            key, value = chunk.split("=", 1)
        elif ":" in chunk:
            key, value = chunk.split(":", 1)
        else:
            raise ValueError(f"bad accord entry {chunk!r} (use molecule=percent)")
        accord[mol_lib.get(key.strip()).id] = float(value)
    if not accord:
        raise ValueError("accord is empty")
    return accord


def resolve_side(
    spec: str,
    product_type: str | None = None,
    volume_ml: float = 50.0,
    load_pct: float | None = None,
) -> tuple[studio.Formula, str]:
    """Turn a CLI/API spec into a formula.

    ``spec`` is either a preset accord id (``forest-breath``) or an inline accord
    (``linalool=40,cedrol=60``).  Presets keep their own product hint unless one
    is given explicitly.
    """
    from . import recommender

    key = (spec or "").strip()
    try:
        accord = recommender.get_accord(key)
    except KeyError:
        materials = parse_accord_text(key)
        formula = studio.formulate(product_type or "edp", volume_ml, load_pct, materials)
        return formula, product_type or formula.product_type.name_ko
    formula = studio.formulate(
        product_type or accord.product_hint, volume_ml, load_pct, accord.materials
    )
    return formula, accord.name_ko


def markdown(comparison: Comparison) -> str:
    """Markdown comparison report (also used by the CLI --out *.md)."""
    pa, pb = comparison.profile("a"), comparison.profile("b")
    d = comparison.deltas()
    ha = comparison.a
    hb = comparison.b

    def row(label: str, a: Any, b: Any, delta: str = "", evidence: str = "") -> str:
        if evidence:
            return f"| {label} | {a} | {b} | {delta} | {evidence} |"
        return f"| {label} | {a} | {b} | {delta} |"

    def fmt(v: float, digits: int = 1) -> str:
        return f"{v:.{digits}f}"

    lines = [
        "# OLFACTRA — 배합 비교 보고서",
        "",
        f"- 버전: **{__version__}** · schema 0.2.0 · MIT",
        f"- A: **{comparison.label_a}** — {ha.product_type.name_ko} {ha.volume_ml:g} mL, "
        f"부향률 {ha.load_pct:g}%",
        f"- B: **{comparison.label_b}** — {hb.product_type.name_ko} {hb.volume_ml:g} mL, "
        f"부향률 {hb.load_pct:g}%",
        "",
        "## 1. 요약",
        "",
    ]
    lines += [f"- {line}" for line in comparison.summary_ko()]
    lines += [
        "",
        "## 2. 노트 피라미드",
        "",
        "| 노트 | A (%) | B (%) | 차이 (%p) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for note in mol_lib.NOTES:
        lines.append(
            row(mol_lib.NOTE_LABELS_KO[note], fmt(pa["note_share_pct"][note]),
                fmt(pb["note_share_pct"][note]), f"{d[f'note_{note}_pp']:+.1f}")
        )
    lines += [
        "",
        "## 3. 물성 프로파일 (질량 가중 평균)",
        "",
        "| 지표 | A | B | 차이 | 근거 등급 |",
        "| --- | ---: | ---: | ---: | --- |",
        row("원료 수", pa["materials"], pb["materials"], ""),
        row("평균 분자량 (g/mol)", fmt(pa["mean_mw"], 2), fmt(pb["mean_mw"], 2),
            f"{d['mean_mw']:+.2f}", "측정(PubChem)"),
        row("LogP 평균", fmt(pa["mean_logp"], 2), fmt(pb["mean_logp"], 2),
            f"{d['mean_logp']:+.2f}", "유도(Crippen)"),
        row("LogP 범위", f"{pa['min_logp']:.2f}–{pa['max_logp']:.2f}",
            f"{pb['min_logp']:.2f}–{pb['max_logp']:.2f}", "", "유도(Crippen)"),
        row("TPSA 평균 (Å²)", fmt(pa["mean_tpsa"], 1), fmt(pb["mean_tpsa"], 1),
            f"{d['mean_tpsa']:+.1f}", "유도(Ertl)"),
        row("고체 원료 비중 (%)", fmt(pa["solid_share_pct"], 1), fmt(pb["solid_share_pct"], 1), ""),
        row("완성품 부향률 (% w/w)", fmt(pa["finished_load_pct_ww"], 2),
            fmt(pb["finished_load_pct_ww"], 2), f"{d['finished_load_pct_ww']:+.2f}", "유도(계량)"),
        "",
        "## 4. 안전 여유분",
        "",
        "| 항목 | A | B | 차이 |",
        "| --- | ---: | ---: | ---: |",
        row("판정", _status_ko(pa["status"]), _status_ko(pb["status"]), ""),
        row("최대 상한 사용률", f"{pa['max_cap_ratio'] * 100:.0f}%",
            f"{pb['max_cap_ratio'] * 100:.0f}%", f"{d['max_cap_ratio'] * 100:+.0f}%p"),
        row("남은 여유분", f"{pa['headroom_pct']:.1f}%", f"{pb['headroom_pct']:.1f}%",
            f"{d['headroom_pct']:+.1f}%p"),
        row("초과 원료", ", ".join(pa["over"]) or "—", ", ".join(pb["over"]) or "—", ""),
        row("주의 원료", ", ".join(pa["caution"]) or "—", ", ".join(pb["caution"]) or "—", ""),
        row("표시 대상 알레르겐", ", ".join(pa["allergens"]) or "—",
            ", ".join(pb["allergens"]) or "—", ""),
        "",
        "## 5. 방법론·출처·경계",
        "",
        "이 보고서의 수치는 다음 지표들로 만들어졌습니다. 근거 등급이 '휴리스틱'인 값은 "
        "측정값이 아니라 순위·비교를 돕는 규칙입니다.",
        "",
        provenance.markdown_table([
            "pubchem_record", "logp_crippen", "tpsa_ertl", "dilution_arithmetic",
            "safety_gate", "note_pyramid", "blend_harmony", "volatility_index",
        ]),
        "",
        f"> **과학적 경계** — {provenance.BOUNDARIES['science']}",
        "",
        f"> **안전 경계** — {provenance.BOUNDARIES['safety']}",
        "",
        "### 참고문헌",
        "",
        provenance.markdown_references(),
        "",
        "---",
        "",
        "경상국립대학교 환경산림과학부 산림환경자원학과 **FEI · HEL 인간환경연구실** · "
        "`Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University` · MIT License",
    ]
    return "\n".join(lines).rstrip() + "\n"
