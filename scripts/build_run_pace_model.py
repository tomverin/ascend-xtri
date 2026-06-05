#!/usr/bin/env python3
"""Build a run pace model from ridden XTri run GPX files.

Combines moving speed (from timestamps) with grade buckets and OSM surface
classes to produce reference speeds for trail marathon pacing.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_gpx_osm_surface import (  # noqa: E402
    GRADE_BUCKETS,
    build_way_segments,
    classify,
    combine_points,
    compute_local_grades,
    load_or_fetch_osm,
    matched_segments,
    parse_gpx,
    resample,
    smooth_elevation,
)
from analyze_ride_speed import TPoint, centered_grade, parse_gpx_timed, smooth_ele  # noqa: E402

SURFACE_GROUPS = {
    "road": "route",
    "track": "piste",
    "trail": "sentier",
    "other": "autre",
}

HIGHWAY_TO_GROUP = {
    "motorway": "road",
    "trunk": "road",
    "primary": "road",
    "secondary": "road",
    "tertiary": "road",
    "unclassified": "road",
    "residential": "road",
    "service": "road",
    "living_street": "road",
    "track": "track",
    "path": "trail",
    "footway": "trail",
    "bridleway": "trail",
    "steps": "trail",
    "cycleway": "trail",
}


def surface_group(tags: dict | None, surface_class: str) -> str:
    if not tags:
        if surface_class in {"paved", "unknown_likely_paved"}:
            return "road"
        if surface_class in {"unpaved", "suspect_unpaved"}:
            return "trail"
        return "other"
    highway = tags.get("highway", "")
    if highway in HIGHWAY_TO_GROUP:
        return HIGHWAY_TO_GROUP[highway]
    if surface_class in {"paved", "unknown_likely_paved"}:
        return "road"
    if surface_class in {"unpaved", "suspect_unpaved"}:
        return "trail"
    return "other"


@dataclass
class RunFile:
    path: Path
    label: str


DEFAULT_RUNS = [
    RunFile(
        Path("archive/past-races/Alpsman_Run_Top_finisher_32e.gpx"),
        "Alpsman 2023 run (32e top finisher)",
    ),
    RunFile(
        Path("archive/past-races/Bearman_Run__5e_scratch.gpx"),
        "Bearman 2023 run (5e scratch)",
    ),
    RunFile(
        Path("archive/past-races/Icon_xtri_2025_run_38e_scratch.gpx"),
        "Icon 2025 run (38e scratch)",
    ),
    RunFile(
        Path("archive/past-races/Icon_xtri_Run__tough_to_the_end.gpx"),
        "Icon run (tough to the end)",
    ),
    RunFile(
        Path(
            "archive/past-races/Celtman_Run__des_hauts,_des_bas,_de_la_pluie_mais_top_finisher_21_250_et_4e_vétéran.gpx"
        ),
        "Celtman run (21e / 4e vétéran)",
    ),
]


def grade_label(grade: float) -> str:
    for lbl, lo, hi in GRADE_BUCKETS:
        if lo <= grade < hi:
            return lbl
    return GRADE_BUCKETS[-1][0]


def analyze_run(
    root: Path,
    run: RunFile,
    cache_dir: Path,
    match_threshold_m: float = 120.0,
    grade_span_m: float = 100.0,
    max_dt_s: float = 25.0,
    min_speed_kmh: float = 2.5,
) -> dict:
    path = run.path if run.path.is_absolute() else root / run.path
    pts = parse_gpx_timed(path)
    if len(pts) < 20:
        raise SystemExit(f"Not enough timed points in {path}")
    pts = smooth_ele(pts, 1)

    points = combine_points([path])
    samples = smooth_elevation(resample(points, 40.0), 1)
    grades = compute_local_grades(samples, span_m=grade_span_m)

    cache_file = cache_dir / f"{path.stem}_osm.json"
    osm = load_or_fetch_osm(points, cache_file, 180, chunk_km=12.0)
    lat0 = sum(p.lat for p in points) / len(points)
    ways = build_way_segments(osm, lat0)
    rows = matched_segments(samples, ways, match_threshold_m)

    # Map sample index by distance for OSM class lookup
    sample_classes: list[tuple[float, str, dict]] = []
    for row in rows:
        mid_km = (row["start_km"] + row["end_km"]) / 2
        tags = row.get("tags") or {}
        sample_classes.append((mid_km, row["class"], tags))

    def lookup_class(dist_km: float) -> tuple[str, dict]:
        best = sample_classes[0] if sample_classes else (0.0, "unknown", {})
        for km, cls, tags in sample_classes:
            if km <= dist_km:
                best = (km, cls, tags)
            else:
                break
        return best[1], best[2]

    bucket_dist = defaultdict(float)
    bucket_time = defaultdict(float)
    combo_dist = defaultdict(float)
    combo_time = defaultdict(float)
    group_dist = defaultdict(float)
    group_time = defaultdict(float)

    total_dist_m = 0.0
    total_move_s = 0.0
    total_elapsed_s = pts[-1].t - pts[0].t
    gain_m = 0.0
    loss_m = 0.0

    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = b.dist_m - a.dist_m
        dt = b.t - a.t
        if d <= 0 or dt <= 0:
            continue
        de = b.ele - a.ele
        if de > 0:
            gain_m += de
        else:
            loss_m -= de
        spd = d / dt * 3.6
        if dt > max_dt_s or spd < min_speed_kmh:
            continue
        total_dist_m += d
        total_move_s += dt
        grade = centered_grade(pts, i, grade_span_m)
        glbl = grade_label(grade)
        mid_km = (a.dist_m + b.dist_m) / 2000.0
        surf_cls, tags = lookup_class(mid_km)
        grp = surface_group(tags, surf_cls)
        bucket_dist[glbl] += d / 1000.0
        bucket_time[glbl] += dt
        combo_dist[(glbl, grp)] += d / 1000.0
        combo_time[(glbl, grp)] += dt
        group_dist[grp] += d / 1000.0
        group_time[grp] += dt

    def pack(dist_map, time_map) -> dict:
        out = {}
        for key, dkm in dist_map.items():
            th = time_map[key] / 3600.0
            out[str(key)] = {
                "dist_km": dkm,
                "move_h": th,
                "kmh": dkm / th if th > 0 else 0.0,
                "min_per_km": 60.0 / (dkm / th) if dkm > 0 and th > 0 else 0.0,
            }
        return out

    climbs = []
    from analyze_gpx_osm_surface import detect_climbs, detect_descents  # noqa: E402

    for c in detect_climbs(samples, grades, min_km=0.8, min_gain=60.0, start_grade=3.0, extend_grade=1.5):
        climbs.append(c)
    descents = detect_descents(
        samples, grades, min_km=0.5, min_loss=40.0, start_grade=-3.0, extend_grade=-1.5
    )

    return {
        "label": run.label,
        "gpx": str(path.relative_to(root) if path.is_relative_to(root) else path),
        "distance_km": pts[-1].dist_m / 1000.0,
        "gain_m": gain_m,
        "loss_m": loss_m,
        "elapsed_h": total_elapsed_s / 3600.0,
        "moving_h": total_move_s / 3600.0,
        "overall_moving_kmh": (total_dist_m / 1000.0) / (total_move_s / 3600.0) if total_move_s else 0.0,
        "grade_buckets": pack(bucket_dist, bucket_time),
        "surface_groups": pack(group_dist, group_time),
        "grade_surface": pack(combo_dist, combo_time),
        "climbs": climbs,
        "descents": descents,
    }


def aggregate_model(runs: list[dict]) -> dict:
    """Distance-weighted aggregate across races."""
    grade_agg_dist = defaultdict(float)
    grade_agg_time = defaultdict(float)
    combo_agg_dist = defaultdict(float)
    combo_agg_time = defaultdict(float)
    group_agg_dist = defaultdict(float)
    group_agg_time = defaultdict(float)

    for run in runs:
        for glbl, vals in run["grade_buckets"].items():
            grade_agg_dist[glbl] += vals["dist_km"]
            grade_agg_time[glbl] += vals["move_h"]
        for grp, vals in run["surface_groups"].items():
            group_agg_dist[grp] += vals["dist_km"]
            group_agg_time[grp] += vals["move_h"]
        for key, vals in run["grade_surface"].items():
            combo_agg_dist[key] += vals["dist_km"]
            combo_agg_time[key] += vals["move_h"]

    def agg_pack(dist_map, time_map) -> dict:
        out = {}
        for key, dkm in dist_map.items():
            th = time_map[key]
            out[key] = {
                "dist_km": dkm,
                "kmh": dkm / th if th > 0 else 0.0,
                "min_per_km": 60.0 / (dkm / th) if dkm > 0 and th > 0 else 0.0,
                "n_races_sample_km": dkm,
            }
        return out

    return {
        "grade_buckets": agg_pack(grade_agg_dist, grade_agg_time),
        "surface_groups": agg_pack(group_agg_dist, group_agg_time),
        "grade_surface": agg_pack(combo_agg_dist, combo_agg_time),
    }


def estimate_route_to_km(terrain: dict, model: dict, end_km: float) -> dict:
    """Grade summary for distance 0..end_km from resampled rows."""
    grade_dist = defaultdict(float)
    group_dist = defaultdict(float)
    for row in terrain.get("rows", []):
        if row["end_km"] <= 0:
            continue
        start = max(0.0, row["start_km"])
        end = min(end_km, row["end_km"])
        if end <= start:
            continue
        frac = (end - start) / max(row["dist_km"], 1e-6)
        dkm = row["dist_km"] * frac
        glbl = grade_label(row.get("grade_pct", 0.0))
        grade_dist[glbl] += dkm
        tags = row.get("tags") or {}
        grp = surface_group(tags, row.get("class", "unknown"))
        group_dist[grp] += dkm
    partial = {
        "grade_summary": {k: {"dist_km": v} for k, v in grade_dist.items()},
        "rows": [r for r in terrain.get("rows", []) if r["start_km"] < end_km],
    }
    est = estimate_route(partial, model)
    est["end_km"] = end_km
    est["surface_share"] = {
        k: v / max(end_km, 1e-6) for k, v in group_dist.items()
    }
    return est


def estimate_route(terrain: dict, model: dict) -> dict:
    """Apply model to a planned route grade_summary + rows for surface mix."""
    speeds_grade = {k: v["kmh"] for k, v in model["grade_buckets"].items()}
    speeds_combo = {}
    for key, vals in model["grade_surface"].items():
        speeds_combo[key] = vals["kmh"]

    # Build surface share from rows
    group_dist = defaultdict(float)
    for row in terrain.get("rows", []):
        tags = row.get("tags") or {}
        grp = surface_group(tags, row.get("class", "unknown"))
        group_dist[grp] += row["dist_km"]
    total = sum(group_dist.values()) or 1.0
    group_share = {k: v / total for k, v in group_dist.items()}

    total_h = 0.0
    rows = []
    for glbl, _, _ in GRADE_BUCKETS:
        dist = terrain.get("grade_summary", {}).get(glbl, {}).get("dist_km", 0.0)
        if dist <= 0:
            continue
        # Blend grade speed with dominant surface on route for that grade (fallback grade only)
        spd = speeds_grade.get(glbl, 0.0)
        # Prefer combo keys if enough sample (weighted by route surface share)
        combo_spd = 0.0
        combo_w = 0.0
        for grp, share in group_share.items():
            key = str((glbl, grp))
            # keys stored as str(tuple) in json - need to match
            for k, v in speeds_combo.items():
                if glbl in k and grp in k:
                    combo_spd += v * share
                    combo_w += share
                    break
        if combo_w > 0 and combo_spd > 0:
            spd = combo_spd
        hours = dist / spd if spd > 0 else 0.0
        total_h += hours
        rows.append({"grade": glbl, "dist_km": dist, "kmh": spd, "hours": hours})

    return {"total_h": total_h, "rows": rows, "surface_share": group_share}


def render_markdown(
    runs: list[dict],
    model: dict,
    ascend_est: dict | None,
    ascend_km33: dict | None = None,
) -> str:
    lines = [
        "# Modèle de pacing run XTri (références historiques)",
        "",
        "Sources : Icon / Alpsman / Bearman / Celtman — vitesses **en mouvement**",
        "(stops exclus), recoupées pente + type de chemin OSM.",
        "",
        "## Courses analysées",
        "",
        "| Course | Distance | D+ | D- | Roulage | Moy. km/h |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in runs:
        lines.append(
            f"| {r['label']} | {r['distance_km']:.1f} km | +{r['gain_m']:.0f} m | "
            f"-{r['loss_m']:.0f} m | {r['moving_h']:.2f} h | {r['overall_moving_kmh']:.1f} |"
        )
    lines.extend(["", "## Vitesses par pente (agrégat pondéré)", ""])
    lines.append("| Pente | Distance cumulée | km/h | min/km |")
    lines.append("|---|---:|---:|---:|")
    for glbl, _, _ in GRADE_BUCKETS:
        v = model["grade_buckets"].get(glbl)
        if not v or v["dist_km"] <= 0:
            continue
        lines.append(
            f"| {glbl} | {v['dist_km']:.1f} km | {v['kmh']:.1f} | {v['min_per_km']:.0f} |"
        )
    lines.extend(["", "## Vitesses par type de chemin", ""])
    lines.append("| Terrain | Distance cumulée | km/h | min/km |")
    lines.append("|---|---:|---:|---:|")
    surface_labels = {"road": "route", "track": "piste", "trail": "sentier", "other": "autre"}
    for key, label in surface_labels.items():
        v = model["surface_groups"].get(key)
        if not v or v["dist_km"] <= 0:
            continue
        lines.append(
            f"| {label} | {v['dist_km']:.1f} km | {v['kmh']:.1f} | {v['min_per_km']:.0f} |"
        )
    lines.extend(["", "## Matrice pente × terrain (km/h)", ""])
    lines.append("| Pente | Route | Piste | Sentier |")
    lines.append("|---|---:|---:|---:|")
    for glbl, _, _ in GRADE_BUCKETS:
        cells = []
        for grp in ["road", "track", "trail"]:
            val = model["grade_surface"].get(f"({glbl!r}, {grp!r})") or model["grade_surface"].get(
                str((glbl, grp))
            )
            if val is None:
                for k, v in model["grade_surface"].items():
                    if glbl in k and grp in k:
                        val = v
                        break
            cells.append(f"{val['kmh']:.1f}" if val and val.get("dist_km", 0) >= 0.3 else "—")
        if any(c != "—" for c in cells):
            lines.append(f"| {glbl} | {cells[0]} | {cells[1]} | {cells[2]} |")

    lines.extend(["", "## Bosses majeures par course", ""])
    for r in runs:
        lines.append(f"### {r['label']}")
        lines.append("")
        if r["climbs"]:
            lines.append("| Km | Long. | D+ | Pente |")
            lines.append("|---:|---:|---:|---:|")
            for c in r["climbs"][:12]:
                lines.append(
                    f"| {c['start_km']:.0f}-{c['end_km']:.0f} | {c['length_km']:.1f} km | "
                    f"+{c['gain_m']:.0f} m | {c['avg_grade_pct']:.1f} % |"
                )
        lines.append("")

    if ascend_est:
        lines.extend([
            "## Application Ascend run (GPX v2)",
            "",
            f"**Temps roulage estimé (42 km) : {ascend_est['total_h']:.2f} h** ({ascend_est['total_h']*60:.0f} min)",
            "",
            "| Pente | Distance | km/h modèle | Temps |",
            "|---|---:|---:|---:|",
        ])
        for row in ascend_est["rows"]:
            lines.append(
                f"| {row['grade']} | {row['dist_km']:.1f} km | {row['kmh']:.1f} | {row['hours']*60:.0f} min |"
            )
        lines.append("")

    if ascend_km33:
        lines.extend([
            "### Barrière km 33 @ 18h15",
            "",
            f"**Run km 0–33 estimé : {ascend_km33['total_h']*60:.0f} min** ({ascend_km33['total_h']:.2f} h)",
            "",
            "| Scénario T2 | Passage km 33 | Marge / 18h15 |",
            "|---|---|---|",
        ])
        barrier = 18 + 15 / 60
        t2_trans = 10 / 60
        for label, bike_end_clock in [
            ("12h17 (table xtri)", 12 + 17 / 60),
            ("12h25 (vélo @ 230 W)", 12 + 25 / 60),
            ("12h45 (+ stops vélo)", 12 + 45 / 60),
            ("13h00 (vélo lent)", 13.0),
        ]:
            km33_clock = bike_end_clock + t2_trans + ascend_km33["total_h"]
            h = int(km33_clock)
            m = int(round((km33_clock - h) * 60)) % 60
            margin_min = (barrier - km33_clock) * 60
            status = "✅" if margin_min >= 0 else "❌"
            lines.append(
                f"| {label} | {h:02d}h{m:02d} | {status} {margin_min:+.0f} min |"
            )
        lines.extend([
            "",
            "Comparaison table xtri médiane : km 0–33 ≈ **5h05** · modèle Tom ≈ "
            f"**{ascend_km33['total_h']*60:.0f} min**.",
            "",
        ])

    lines.extend([
        "## Règles d'usage",
        "",
        "- Modèle = **tes** vitesses race, pas la table médiane xtri.",
        "- En montée raide sentier (≥ 6 %), viser **~4–5 km/h** (12–15 min/km).",
        "- Plat route : **~9–11 km/h**.",
        "- Descente : ne pas surestimer — genou / technique.",
        "",
        "Régénérer :",
        "```sh",
        ".venv/bin/python scripts/race/build_run_pace_model.py",
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--ascend-terrain", type=Path, default=None)
    args = ap.parse_args()
    root = args.root
    out_md = args.out_md or root / "AscendXtri/run_pace_model.md"
    out_json = args.out_json or root / "AscendXtri/run_pace_model.json"
    ascend_terrain = args.ascend_terrain or root / "AscendXtri/terrain_analysis.json"
    cache_dir = root / "archive/past-races/.cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for run in DEFAULT_RUNS:
        print(f"Analyzing {run.label}...", file=sys.stderr)
        results.append(analyze_run(root, run, cache_dir))

    model = aggregate_model(results)
    ascend_est = None
    ascend_km33 = None
    if ascend_terrain.exists():
        terrain = json.loads(ascend_terrain.read_text())
        ascend_est = estimate_route(terrain, model)
        ascend_km33 = estimate_route_to_km(terrain, model, 33.0)

    payload = {
        "runs": results,
        "aggregate_model": model,
        "ascend_estimate": ascend_est,
        "ascend_km33_estimate": ascend_km33,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(
        render_markdown(results, model, ascend_est, ascend_km33), encoding="utf-8"
    )
    print(f"Wrote {out_md}", file=sys.stderr)
    print(f"Wrote {out_json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
