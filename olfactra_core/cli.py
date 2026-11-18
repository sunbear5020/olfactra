"""Command line entry point: ``python -m olfactra_core <command>``.

Examples
--------
    python -m olfactra_core atlas --category forest
    python -m olfactra_core molecule limonene
    python -m olfactra_core recommend --mood sleep --space bedroom --style floral
    python -m olfactra_core formulate --product edp --volume 50 --load 20 \
        --accord "linalool=40,geraniol=25,phenylethyl alcohol=25,cedrol=10" --out recipe.xlsx
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__, atlas, exporter, molecule, recommender, studio
from .molecule import NOTE_LABELS_KO


def _parse_accord(text: str) -> dict[str, float]:
    """'linalool=40,geraniol=25' -> {'linalool': 40.0, 'geraniol': 25.0}"""
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
            raise SystemExit(f"bad accord entry {chunk!r} (use molecule=percent)")
        accord[molecule.get(key.strip()).id] = float(value)
    if not accord:
        raise SystemExit("accord is empty")
    return accord


def cmd_atlas(args: argparse.Namespace) -> None:
    entries = atlas.search(args.query) if args.query else atlas.all_entries()
    if args.category:
        entries = [e for e in entries if e.category == args.category]
    if args.json:
        print(json.dumps([e.as_dict() for e in entries], ensure_ascii=False, indent=2))
        return
    for e in atlas.timeline():
        if e not in entries:
            continue
        print(f"[{e.category_label}] {e.name_ko} · {e.name_en} — {e.era_label}")
        print(f"    {e.region} · {e.material_part}")
        print(f"    향 분자: {', '.join(molecule.get(m).name_ko for m in e.molecules)}")
        print(f"    {e.use_ko}")
        print()


def cmd_molecule(args: argparse.Namespace) -> None:
    if args.similar:
        target = molecule.get(args.similar)
        for m, score in molecule.similar(target.id, top_k=args.top):
            print(f"{score:0.3f}  {m.name_ko:16s} {m.name:24s} {m.formula:10s} {NOTE_LABELS_KO[m.note]}")
        return
    if args.query:
        hits = molecule.find(args.query)
    else:
        hits = list(molecule.all_molecules())
    if args.json:
        print(json.dumps([m.as_dict() for m in hits], ensure_ascii=False, indent=2))
        return
    for m in hits:
        fams = ", ".join(f"{f}:{w:.2f}" for f, w in m.dominant_families(3))
        print(f"{m.name_ko} ({m.name})")
        print(f"    {m.formula} · MW {m.molecular_weight} · CAS {m.cas} · {m.functional_group}")
        print(f"    {NOTE_LABELS_KO[m.note]} 노트 · {fams}")
        print(f"    {m.descriptor_ko} / {m.descriptor_en}")
        print(f"    대표 원료: {', '.join(m.natural_sources)}")
        print(f"    실무 상한 {m.working_cap_pct:g}% — {m.cap_basis}")
        print()


def cmd_recommend(args: argparse.Namespace) -> None:
    picks = recommender.recommend(
        mood=args.mood, season=args.season, space=args.space, style=args.style, limit=args.limit
    )
    if args.json:
        print(json.dumps([p.as_dict() for p in picks], ensure_ascii=False, indent=2))
        return
    for i, pick in enumerate(picks, start=1):
        a = pick.accord
        print(f"{i}. {a.name_ko} ({a.name_en}) — {pick.score:.0f}점 · 조화 {pick.harmony:.2f}")
        print(f"   {a.tagline}")
        for reason in pick.reasons:
            print(f"   · {reason}")
        print("   배합:")
        for mid, share in a.materials.items():
            m = molecule.get(mid)
            print(f"     {share:5.1f}%  {m.name_ko:16s} [{NOTE_LABELS_KO[m.note]}] {m.descriptor_ko}")
        print(f"   제형 힌트: {studio.get_product_type(pick.product_hint).name_ko}")
        for w in pick.warnings:
            print(f"   ! {w}")
        print()


def cmd_formulate(args: argparse.Namespace) -> None:
    accord = _parse_accord(args.accord) if args.accord else None
    if accord is None:
        picks = recommender.recommend(
            mood=args.mood, season=args.season, space=args.space, style=args.style, limit=1
        )
        accord = picks[0].accord.materials
        print(f"# 조건에 맞는 아코드 '{picks[0].accord.name_ko}'로 계산합니다")
    formula = studio.formulate(args.product, args.volume, args.load, accord)
    if args.json:
        print(json.dumps(formula.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"{formula.product_type.name_ko} {formula.volume_ml:g} mL · 부향률 {formula.load_pct:g}% "
              f"(완성품 {formula.finished_load_pct_ww:.2f}% w/w) · 총 {formula.total_mass_g:.2f} g")
        print(f"{'원료':16s} {'비중':>6s} {'mL':>7s} {'g':>7s} {'완성품%':>9s} {'상한%':>6s}  판정")
        for r in formula.rows:
            print(f"{r.name_ko:16s} {r.share_pct:6.1f} {r.volume_ml:7.3f} {r.mass_g:7.3f} "
                  f"{r.finished_pct_ww:9.3f} {r.cap_pct:6.1f}  {r.status}")
        print("캐리어:")
        for c in formula.carrier_rows:
            print(f"  {c['name']:24s} {c['volume_ml']:7.3f} mL  {c['mass_g']:7.3f} g")
        for w in formula.warnings:
            print(f"! {w}")
    if args.out:
        path = exporter.write_recipe(formula, args.out)
        print(f"저장: {path}")


def cmd_demo(args: argparse.Namespace) -> None:
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    picks = recommender.recommend(mood="calm", season="autumn", space="study", style="green", limit=2)
    for i, pick in enumerate(picks, start=1):
        formula = studio.formulate(pick.product_hint, 100, None, pick.accord.materials)
        for suffix in (".csv", ".json", ".xlsx"):
            exporter.write_recipe(formula, outdir / f"olfactra_demo_{i}_{pick.accord.id}{suffix}")
        print(f"{pick.accord.name_ko}: {formula.status} · {len(formula.warnings)} warnings")
    (outdir / "molecules.csv").write_text(exporter.molecule_table_csv(), encoding="utf-8-sig")
    (outdir / "atlas.csv").write_text(exporter.atlas_table_csv(), encoding="utf-8-sig")
    print(f"demo files written to {outdir}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="olfactra", description="OLFACTRA Core — The Intelligence of Scent")
    p.add_argument("--version", action="version", version=f"olfactra {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("atlas", help="역사·원료 아카이브")
    a.add_argument("query", nargs="?", default=None)
    a.add_argument("--category", default=None, choices=sorted(atlas.CATEGORIES))
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_atlas)

    m = sub.add_parser("molecule", help="분자 라이브러리")
    m.add_argument("query", nargs="?", default=None)
    m.add_argument("--similar", default=None, help="이 분자와 향조가 비슷한 분자 찾기")
    m.add_argument("--top", type=int, default=5)
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=cmd_molecule)

    r = sub.add_parser("recommend", help="기분·계절·공간·스타일 기반 아코드 추천")
    r.add_argument("--mood", choices=sorted(recommender.MOODS))
    r.add_argument("--season", choices=sorted(recommender.SEASONS))
    r.add_argument("--space", choices=sorted(recommender.SPACES))
    r.add_argument("--style", choices=sorted(recommender.STYLES))
    r.add_argument("--limit", type=int, default=3)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_recommend)

    f = sub.add_parser("formulate", help="배합 계산 + 안전 판정")
    f.add_argument("--product", default="edp", help=", ".join(studio.PRODUCT_TYPES))
    f.add_argument("--volume", type=float, default=50.0)
    f.add_argument("--load", type=float, default=None)
    f.add_argument("--accord", default=None, help="'linalool=40,geraniol=30,cedrol=30'")
    f.add_argument("--mood", choices=sorted(recommender.MOODS))
    f.add_argument("--season", choices=sorted(recommender.SEASONS))
    f.add_argument("--space", choices=sorted(recommender.SPACES))
    f.add_argument("--style", choices=sorted(recommender.STYLES))
    f.add_argument("--out", default=None, help="recipe.csv | recipe.json | recipe.xlsx")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_formulate)

    d = sub.add_parser("demo", help="예시 레시피 파일 생성")
    d.add_argument("--out", default="olfactra-demo")
    d.set_defaults(func=cmd_demo)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
