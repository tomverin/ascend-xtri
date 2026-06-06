#!/usr/bin/env python3
"""Build a self-contained Ascend XTri race dashboard (GitHub Pages).

Embeds bike + run GPX, terrain analysis, run pace model, bike power pacing,
and markdown docs into a single index.html (Leaflet + elevation profile + docs).
"""

from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASCEND = ROOT / "AscendXtri"
RUN_GPX = ASCEND / "Ascend_run_official_2026-06.gpx"
ASSIST_KM = 25.0
BIKE_GPX = ASCEND / "Ascend_xtri_bike.gpx"
RUN_TERRAIN = ASCEND / "terrain_analysis.json"
BIKE_TERRAIN = ASCEND / "bike_terrain_analysis.json"
PACE_MODEL = ASCEND / "run_pace_model.json"
BIKE_SPEED = ASCEND / "ref_speed_bearman_2023_230w.json"
OUT_HTML = ASCEND / "site" / "index.html"

RACE_START = datetime(2026, 7, 25, 3, 0)
SWIM_H = 1 + 8 / 60
T1_H = 10 / 60
T2_H = 10 / 60
BARRIER_CLOCK = 18 + 15 / 60

NS = "{http://www.topografix.com/GPX/1/1}"

DOCS = [
    ("assistance.md", "Assistance support", "Km 0–25 véhicule · km 25+ crew à pied, parking La Mongie, horaires."),
    ("README.md", "Index parcours", "Vue d'ensemble vélo + CAP, scripts, chiffres clés."),
    ("run_course_analysis.md", "Analyse CAP", "4 actes, bosses, descentes genou, barrière km 33."),
    ("run_pace_model.md", "Modèle pacing run", "Vitesses race Icon / Alpsman / Bearman / Celtman."),
    ("terrain_analysis.md", "Terrain CAP (auto)", "Profil, bosses, surfaces OSM — mode run."),
    ("bike_pacing_analysis.md", "Pacing vélo", "Estimation @ 230 W (réf. Bearman 2023)."),
    ("bike_terrain_analysis.md", "Terrain vélo (auto)", "Bosses, cols, surfaces — mode bike."),
]

GRADE_BUCKETS = [
    ("<= -6 %", -100.0, -6.0),
    ("-6 to -3 %", -6.0, -3.0),
    ("-3 to -1 %", -3.0, -1.0),
    ("-1 to +1 %", -1.0, 1.0),
    ("+1 to +3 %", 1.0, 3.0),
    ("+3 to +6 %", 3.0, 6.0),
    (">= +6 %", 6.0, 100.0),
]


def haversine_m(la1: float, lo1: float, la2: float, lo2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_track(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    pts: list[dict] = []
    cum = 0.0
    prev = None
    for tp in root.iter(f"{NS}trkpt"):
        lat = float(tp.attrib["lat"])
        lon = float(tp.attrib["lon"])
        ele_el = tp.find(f"{NS}ele")
        ele = float(ele_el.text) if ele_el is not None and ele_el.text else 0.0
        if prev is not None:
            cum += haversine_m(prev[0], prev[1], lat, lon)
        pts.append({"lat": lat, "lon": lon, "ele": ele, "km": cum / 1000})
        prev = (lat, lon)
    return pts


def downsample(pts: list[dict], target: int = 2500) -> list[dict]:
    if len(pts) <= target:
        return pts
    step = max(1, len(pts) // target)
    out = [pts[i] for i in range(0, len(pts), step)]
    if out[-1] is not pts[-1]:
        out.append(pts[-1])
    return out


def grade_label(grade: float) -> str:
    for lbl, lo, hi in GRADE_BUCKETS:
        if lo <= grade < hi:
            return lbl
    return GRADE_BUCKETS[-1][0]


def centered_grade(pts: list[dict], i: int, span_m: float) -> float:
    half = span_m / 2
    a = i
    while a > 0 and (pts[i]["km"] - pts[a]["km"]) * 1000 < half:
        a -= 1
    b = i
    while b < len(pts) - 1 and (pts[b]["km"] - pts[i]["km"]) * 1000 < half:
        b += 1
    dx = (pts[b]["km"] - pts[a]["km"]) * 1000
    if dx <= 1:
        return 0.0
    return (pts[b]["ele"] - pts[a]["ele"]) / dx * 100


def enrich_track(pts: list[dict], span_m: float) -> list[dict]:
    out = []
    for i, p in enumerate(pts):
        g = centered_grade(pts, i, span_m)
        out.append(
            {
                "lat": round(p["lat"], 6),
                "lon": round(p["lon"], 6),
                "ele": round(p["ele"], 1),
                "km": round(p["km"], 3),
                "grade": round(g, 1),
                "glbl": grade_label(g),
            }
        )
    return out


def add_assist_phase(track: list[dict], km_split: float = ASSIST_KM) -> None:
    for p in track:
        p["assist"] = "vehicle" if p["km"] < km_split else "crew"


def nearest_at_km(track: list[dict], km: float) -> tuple[int, dict]:
    best_i, best_d = 0, 1e9
    for i, p in enumerate(track):
        d = abs(p["km"] - km)
        if d < best_d:
            best_d, best_i = d, i
    return best_i, track[best_i]


def build_assistance_meta(
    run_track: list[dict], run_times: list[float], run_start_h: float
) -> dict:
    markers: list[dict] = []
    for km, kind, title, popup in [
        (0, "start", "Départ run · Payolle", "Assistance véhicule uniquement (pas de crew à pied)"),
        (
            ASSIST_KM,
            "handoff",
            "Km 25 · La Mongie",
            "Parking assistance · laisser le véhicule · crew rejoint Tom à pied",
        ),
        (33, "barrier", "Km 33 · Barrière 18h15", "Col de Sencours / Pic du Midi — top finishers"),
    ]:
        i, p = nearest_at_km(run_track, km)
        t = run_times[i]
        markers.append(
            {
                "km": p["km"],
                "lat": p["lat"],
                "lon": p["lon"],
                "ele": p["ele"],
                "kind": kind,
                "title": title,
                "popup": popup,
                "run_h": round(t, 2),
                "clock": fmt_clock(run_start_h + t),
                "assist": p.get("assist", "crew"),
            }
        )
    p = run_track[-1]
    t = run_times[-1]
    markers.append(
        {
            "km": p["km"],
            "lat": p["lat"],
            "lon": p["lon"],
            "ele": p["ele"],
            "kind": "finish",
            "title": "Arrivée · Col du Tourmalet",
            "popup": "Fin de course · crew à pied obligatoire depuis km 25",
            "run_h": round(t, 2),
            "clock": fmt_clock(run_start_h + t),
            "assist": "crew",
        }
    )
    return {
        "km_split": ASSIST_KM,
        "vehicle_km": ASSIST_KM,
        "crew_km": round(run_track[-1]["km"] - ASSIST_KM, 1),
        "markers": markers,
    }


def render_assist_timeline(markers: list[dict]) -> str:
    rows = []
    for m in markers:
        phase = "🚗 Véhicule" if m.get("assist") == "vehicle" else "🏃 Crew"
        rows.append(
            "<tr>"
            f"<td>{m['title']}</td>"
            f"<td>{m['km']:.1f}</td>"
            f"<td>{phase}</td>"
            f"<td>{m['clock']}</td>"
            f"<td>{m['run_h']*60:.0f} min run</td>"
            "</tr>"
        )
    return "\n".join(rows)


def cum_hours(track: list[dict], speeds: dict[str, float]) -> list[float]:
    times = [0.0]
    for i in range(1, len(track)):
        seg = track[i]["km"] - track[i - 1]["km"]
        spd = speeds.get(track[i]["glbl"], 8.0)
        times.append(times[-1] + (seg / spd if spd > 0 else 0.0))
    return times


def trim_terrain(raw: dict) -> dict:
    keep = (
        "distance_km",
        "gain_m",
        "loss_m",
        "mode",
        "elevation_profile",
        "climbs",
        "descents",
        "bumps",
        "punches",
        "grade_summary",
        "surface_summary",
        "sections",
        "highway_summary",
        "surface_cross_ref",
    )
    out = {k: raw[k] for k in keep if k in raw}
    return out


def barrier_rows(km33_h: float) -> list[dict]:
    rows = []
    for label, bike_end in [
        ("12h17 (table xtri)", 12 + 17 / 60),
        ("12h25 (vélo @ 230 W)", 12 + 25 / 60),
        ("12h45 (+ stops vélo)", 12 + 45 / 60),
        ("13h00 (vélo lent)", 13.0),
    ]:
        pass_clock = bike_end + T2_H + km33_h
        h = int(pass_clock)
        m = int(round((pass_clock - h) * 60)) % 60
        margin = (BARRIER_CLOCK - pass_clock) * 60
        rows.append(
            {
                "label": label,
                "pass": f"{h:02d}h{m:02d}",
                "margin_min": round(margin),
                "ok": margin >= 0,
            }
        )
    return rows


def fmt_clock(hours_from_start: float) -> str:
    when = RACE_START + timedelta(hours=hours_from_start)
    return when.strftime("%H:%M")


def render_climb_rows(climbs: list[dict], limit: int = 20) -> str:
    rows = []
    for c in climbs[:limit]:
        rows.append(
            "<tr>"
            f"<td>{c['start_km']:.1f}–{c['end_km']:.1f}</td>"
            f"<td>{c['length_km']:.1f} km</td>"
            f"<td>+{c['gain_m']:.0f} m</td>"
            f"<td>{c['avg_grade_pct']:.1f} %</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='4'>—</td></tr>"


def render_grade_table(grade_summary: dict, speeds: dict[str, float] | None = None) -> str:
    rows = []
    for lbl, _, _ in GRADE_BUCKETS:
        g = grade_summary.get(lbl)
        if not g or g.get("dist_km", 0) <= 0:
            continue
        dist = g["dist_km"]
        spd = speeds.get(lbl, 0) if speeds else 0
        tmin = dist / spd * 60 if spd > 0 else 0
        spd_cell = f"{spd:.1f}" if spd else "—"
        t_cell = f"{tmin:.0f} min" if spd else "—"
        rows.append(
            f"<tr><td>{lbl}</td><td>{dist:.1f} km</td><td>{spd_cell}</td><td>{t_cell}</td></tr>"
        )
    return "\n".join(rows)


def render_pace_model_table(model: dict) -> str:
    rows = []
    for lbl, _, _ in GRADE_BUCKETS:
        v = model.get("grade_buckets", {}).get(lbl)
        if not v or v.get("dist_km", 0) <= 0:
            continue
        rows.append(
            f"<tr><td>{lbl}</td><td>{v['dist_km']:.1f} km</td>"
            f"<td>{v['kmh']:.1f}</td><td>{v['min_per_km']:.0f}</td></tr>"
        )
    return "\n".join(rows)


def render_runs_table(runs: list[dict]) -> str:
    rows = []
    for r in runs:
        rows.append(
            f"<tr><td>{r['label']}</td><td>{r['distance_km']:.1f} km</td>"
            f"<td>+{r['gain_m']:.0f} m</td><td>{r['moving_h']:.2f} h</td>"
            f"<td>{r['overall_moving_kmh']:.1f}</td></tr>"
        )
    return "\n".join(rows)


def render_barrier_table(rows: list[dict]) -> str:
    out = []
    for r in rows:
        status = "✅" if r["ok"] else "❌"
        sign = "+" if r["margin_min"] >= 0 else ""
        out.append(
            f"<tr><td>{r['label']}</td><td>{r['pass']}</td>"
            f"<td>{status} {sign}{r['margin_min']} min</td></tr>"
        )
    return "\n".join(out)


def render_docs_sidebar(available: list[tuple[str, str, str]]) -> str:
    return "".join(
        f'<a class="doc-link" href="#doc={fname}" data-file="{fname}">'
        f'<div class="title">{title}</div><div class="desc">{desc}</div></a>'
        for fname, title, desc in available
    )


def load_docs() -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    embed: dict[str, str] = {}
    available: list[tuple[str, str, str]] = []
    for fname, title, desc in DOCS:
        path = ASCEND / fname
        if path.exists():
            embed[fname] = path.read_text(encoding="utf-8")
            available.append((fname, title, desc))
    return embed, available


HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Ascend XTri — 25 July 2026</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.0/marked.min.js"></script>
<style>
:root{--bg:#0c1222;--panel:#131a2e;--panel2:#1a2340;--text:#e8edf7;--muted:#8b9cb8;--accent:#6ee7b7;--accent2:#38bdf8;--orange:#fbbf24;--red:#f87171;--green:#4ade80;--border:#2a3654}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text)}
header{padding:16px 24px;background:linear-gradient(135deg,#131a2e,#0f172a);border-bottom:1px solid var(--border)}
header h1{margin:0 0 4px;font-size:22px}
header .meta{color:var(--muted);font-size:13px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}
.stat{background:var(--panel2);padding:8px 14px;border-radius:8px;border:1px solid var(--border)}
.stat .v{font-size:17px;font-weight:600;color:var(--accent)}
.stat .l{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.5px}
nav.tabs{display:flex;gap:4px;padding:0 24px;background:var(--panel);border-bottom:1px solid var(--border);overflow-x:auto}
nav.tabs button{background:none;border:none;color:var(--muted);padding:12px 16px;font-size:14px;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap}
nav.tabs button:hover{color:var(--text)}
nav.tabs button.active{color:var(--accent);border-bottom-color:var(--accent)}
section.tab{display:none;padding:16px 24px}
section.tab.active{display:block}
#map{height:52vh;min-height:340px;border-radius:8px;border:1px solid var(--border)}
.profile-wrap{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px;margin-top:12px;position:relative}
#profile{width:100%;height:300px;display:block}
#tooltip{position:absolute;pointer-events:none;background:rgba(0,0,0,.88);color:#fff;padding:8px 12px;border-radius:6px;font-size:12px;display:none;z-index:5}
.tabs-mini{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.tabs-mini button{background:var(--panel2);border:1px solid var(--border);color:var(--text);padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px}
.tabs-mini button.active{background:var(--accent);border-color:var(--accent);color:#0c1222;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--panel2);color:var(--muted);font-size:11px;text-transform:uppercase;position:sticky;top:0}
tr:hover{background:var(--panel2)}
.scrollable{max-height:65vh;overflow:auto;border:1px solid var(--border);border-radius:8px}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:12px 0}
.kpi{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 16px}
.kpi .l{color:var(--muted);font-size:10px;text-transform:uppercase}
.kpi .v{font-size:20px;font-weight:600;margin-top:4px;color:var(--accent2)}
.kpi .s{color:var(--muted);font-size:11px;margin-top:4px}
.card{background:var(--panel);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:8px;padding:14px 18px;margin-bottom:12px}
.card h3{margin:0 0 8px;font-size:15px}
.card p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.two-col{grid-template-columns:1fr}}
.docs-layout{display:grid;grid-template-columns:260px 1fr;gap:16px;height:calc(100vh - 180px);min-height:500px}
.docs-sidebar{background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow-y:auto;padding:8px}
.doc-link{display:block;padding:10px 12px;border-radius:6px;color:var(--text);text-decoration:none;margin-bottom:4px;border:1px solid transparent;cursor:pointer}
.doc-link:hover,.doc-link.active{background:var(--panel2);border-color:var(--border)}
.doc-link.active{border-color:var(--accent)}
.doc-link .title{font-size:13px;font-weight:600}
.doc-link .desc{color:var(--muted);font-size:11px;margin-top:2px}
.docs-viewer{background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow-y:auto;padding:24px}
.md-content{font-size:14px;line-height:1.6}
.md-content h1{font-size:22px;border-bottom:1px solid var(--border);padding-bottom:8px}
.md-content h2{font-size:17px;margin-top:24px;color:var(--accent2)}
.md-content h3{font-size:15px;margin-top:18px;color:var(--accent)}
.md-content table{font-size:12px}
.md-content code{background:var(--panel2);padding:2px 6px;border-radius:3px;font-size:12px}
.md-content a{color:var(--accent2)}
.slider-wrap{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:14px;margin-top:10px}
.slider-wrap input[type=range]{width:100%;accent-color:var(--accent)}
.pos-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-top:10px;font-size:13px}
.pos-grid .l{color:var(--muted);font-size:10px;text-transform:uppercase}
.pos-grid .v{font-weight:600;margin-top:2px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:4px;vertical-align:middle}
.assist-banner{border-radius:8px;padding:14px 18px;margin-bottom:12px;border-left:4px solid}
.assist-banner.vehicle{background:#132238;border-color:#38bdf8}
.assist-banner.crew{background:#2a1f14;border-color:#f97316}
.assist-banner h3{margin:0 0 6px;font-size:15px}
.assist-banner p{margin:0;color:var(--muted);font-size:13px;line-height:1.5}
.assist-pin{background:#0c1222;border:2px solid #fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px}
@media(max-width:800px){.docs-layout{grid-template-columns:1fr;height:auto}.docs-sidebar{max-height:180px}}
</style>
</head>
<body>
<header>
  <h1>Ascend XTri — 25 juillet 2026</h1>
  <div class="meta">Dashboard parcours · départ 03h00 · assistance véhicule km 0–25 · crew à pied km 25+ · barrière km 33 @ 18h15</div>
  <div class="stats">
    <div class="stat"><div class="v">__BIKE_KM__ km</div><div class="l">Vélo · +__BIKE_GAIN__ m</div></div>
    <div class="stat"><div class="v">__RUN_KM__ km</div><div class="l">CAP · +__RUN_GAIN__ m</div></div>
    <div class="stat"><div class="v">~__BIKE_H__ h</div><div class="l">Vélo @ 230 W</div></div>
    <div class="stat"><div class="v">~__RUN_H__ h</div><div class="l">Run (modèle Tom)</div></div>
    <div class="stat"><div class="v">__T2_CLOCK__</div><div class="l">T2 estimé</div></div>
    <div class="stat"><div class="v">__FINISH_CLOCK__</div><div class="l">Arrivée estimée</div></div>
  </div>
</header>
<nav class="tabs" id="main-tabs">
  <button class="active" data-tab="overview">Vue d'ensemble</button>
  <button data-tab="map">Carte & profil</button>
  <button data-tab="support">Support</button>
  <button data-tab="bike">Vélo</button>
  <button data-tab="run">Course à pied</button>
  <button data-tab="docs">Documents</button>
</nav>

<section class="tab active" id="tab-overview">
  <div class="kpi-grid">
    <div class="kpi"><div class="l">Swim + T1</div><div class="v">~1h18</div><div class="s">Départ run ~04h18 si swim cible</div></div>
    <div class="kpi"><div class="l">Vélo @ 230 W</div><div class="v">~__BIKE_H__ h</div><div class="s">Réf. Bearman 2023 · T2 ~__T2_CLOCK__</div></div>
    <div class="kpi"><div class="l">Run modèle</div><div class="v">~__RUN_H__ h</div><div class="s">5 courses refs · roulage seul</div></div>
    <div class="kpi"><div class="l">Km 0–33 run</div><div class="v">~__KM33_MIN__ min</div><div class="s">Barrière Pic du Midi @ 18h15</div></div>
    <div class="kpi"><div class="l">Rejoindre Tom</div><div class="v">km __ASSIST_KM__</div><div class="s">~__ASSIST_CLOCK__ · parking La Mongie</div></div>
  </div>
  <div class="two-col">
    <div class="card"><h3>🚴 Vélo — 4 actes</h3><p>Lourdes → cols pyrénéens (Balès, Peyragudes, Azet, Aspin…) → T2 Tourmalet. Bosses clés km 80–101, 116–143, 167–179. ~78 % bitume OSM.</p></div>
    <div class="card"><h3>🏃 CAP — 4 actes</h3><p>Payolle → Courade → montée Pic du Midi (km 26–35, +1 400 m) → descente piste Tourmalet. GPX officiel juin 2026 · 38 % pente ≥ 6 %.</p></div>
  </div>
  <div class="two-col" style="margin-top:12px">
    <div class="assist-banner vehicle"><h3>🚗 Km 0 → 25 — assistance véhicule</h3><p>Support en bord de route uniquement — <strong>ne pas courir</strong> avec Tom. Eau, nutrition, vêtements en ponctuel.</p></div>
    <div class="assist-banner crew"><h3>🏃 Km 25 → 42 — crew à pied obligatoire</h3><p>Parking <strong>La Mongie</strong> · laisser le véhicule · navette orga Tourmalet ↔ parking · sac assistance obligatoire.</p></div>
  </div>
  <h3 style="margin-top:20px;color:var(--accent2)">Barrière km 33 @ 18h15</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Scénario fin vélo</th><th>Passage km 33</th><th>Marge / 18h15</th></tr></thead>
    <tbody>__BARRIER_ROWS__</tbody>
  </table></div>
  <p style="color:var(--muted);font-size:13px;margin-top:12px">Hypothèse T2 = 10 min. Le goulot principal reste le <strong>vélo</strong> si rack &gt; ~13h00.</p>
</section>

<section class="tab" id="tab-map">
  <div class="tabs-mini" id="leg-tabs">
    <button class="active" data-leg="run">CAP 42 km</button>
    <button data-leg="bike">Vélo 184 km</button>
  </div>
  <div id="map"></div>
  <div class="legend" id="grade-legend">
    <span><i style="background:#4ade80"></i> plat / léger</span>
    <span><i style="background:#fbbf24"></i> montée modérée</span>
    <span><i style="background:#f87171"></i> montée raide ≥ 6 %</span>
    <span><i style="background:#38bdf8"></i> descente</span>
  </div>
  <div class="legend" id="assist-legend" style="display:none">
    <span><i style="background:#38bdf8"></i> km 0–25 · véhicule</span>
    <span><i style="background:#f97316"></i> km 25+ · crew à pied</span>
    <span>📍 marqueurs : départ · La Mongie · barrière · arrivée</span>
  </div>
  <div class="profile-wrap">
    <canvas id="profile"></canvas>
    <div id="tooltip"></div>
  </div>
  <div class="slider-wrap">
    <input type="range" id="pos-slider" min="0" max="1000" value="0"/>
    <div class="pos-grid" id="pos-info"></div>
  </div>
</section>

<section class="tab" id="tab-support">
  <div class="assist-banner vehicle">
    <h3>🚗 Phase 1 — km 0 à 25 (véhicule seulement)</h3>
    <p>Assistance <strong>ponctuelle en voiture</strong> le long du parcours. Le support ne court pas avec l'athlète. Naviguer sur la carte (onglet Carte) pour voir la zone bleue.</p>
  </div>
  <div class="assist-banner crew">
    <h3>🏃 Phase 2 — km 25 à 42 (crew à pied obligatoire)</h3>
    <p><strong>Parking La Mongie</strong> au km 25 — laisser le véhicule, prendre le sac, rejoindre Tom. Navette orga Tourmalet ↔ parking toute la journée. Zone orange sur la carte.</p>
  </div>
  <h3 style="color:var(--accent2)">Jalons horaires estimés (modèle Tom)</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Point</th><th>Km</th><th>Mode</th><th>Horloge ~</th><th>Temps run</th></tr></thead>
    <tbody>__ASSIST_TIMELINE__</tbody>
  </table></div>
  <p style="color:var(--muted);font-size:13px;margin-top:12px">Hypothèse T2 ~__T2_CLOCK__ · ajuster le jour J selon heure réelle au rack. Utiliser le <strong>slider</strong> sur l'onglet Carte pour voir position + mode assistance à chaque km.</p>
</section>

<section class="tab" id="tab-bike">
  <h3 style="color:var(--accent2)">Estimation @ 230 W (Bearman 2023)</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Pente</th><th>Distance Ascend</th><th>km/h modèle</th><th>Temps</th></tr></thead>
    <tbody>__BIKE_GRADE_ROWS__</tbody>
  </table></div>
  <h3 style="margin-top:20px;color:var(--accent2)">Bosses majeures</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Km</th><th>Long.</th><th>D+</th><th>Pente</th></tr></thead>
    <tbody>__BIKE_CLIMBS__</tbody>
  </table></div>
</section>

<section class="tab" id="tab-run">
  <h3 style="color:var(--accent2)">Modèle pacing — agrégat 5 courses</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Pente</th><th>Distance cumulée refs</th><th>km/h</th><th>min/km</th></tr></thead>
    <tbody>__PACE_MODEL_ROWS__</tbody>
  </table></div>
  <h3 style="margin-top:20px;color:var(--accent2)">Application Ascend (42 km)</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Pente</th><th>Distance</th><th>km/h</th><th>Temps</th></tr></thead>
    <tbody>__RUN_GRADE_ROWS__</tbody>
  </table></div>
  <h3 style="margin-top:20px;color:var(--accent2)">Courses de référence</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Course</th><th>Dist.</th><th>D+</th><th>Roulage</th><th>km/h</th></tr></thead>
    <tbody>__RUNS_ROWS__</tbody>
  </table></div>
  <h3 style="margin-top:20px;color:var(--accent2)">Bosses CAP</h3>
  <div class="scrollable"><table>
    <thead><tr><th>Km</th><th>Long.</th><th>D+</th><th>Pente</th></tr></thead>
    <tbody>__RUN_CLIMBS__</tbody>
  </table></div>
</section>

<section class="tab" id="tab-docs">
  <div class="docs-layout">
    <div class="docs-sidebar" id="docs-sidebar">__DOCS_SIDEBAR__</div>
    <div class="docs-viewer"><div class="md-content" id="md-view">Sélectionnez un document.</div></div>
  </div>
</section>

<script>
const DATA = __DATA_JSON__;
const GRADE_COLORS = {
  "<= -6 %": "#38bdf8",
  "-6 to -3 %": "#60a5fa",
  "-3 to -1 %": "#4ade80",
  "-1 to +1 %": "#4ade80",
  "+1 to +3 %": "#fbbf24",
  "+3 to +6 %": "#fb923c",
  ">= +6 %": "#f87171"
};
const ASSIST_COLORS = { vehicle: "#38bdf8", crew: "#f97316" };
const MARKER_ICON = { start: "🏁", handoff: "🅿️", barrier: "⏱️", finish: "🏔️" };

let leg = "run";
let map, layers = [];
let marker;

function gradeColor(glbl) {
  return GRADE_COLORS[glbl] || "#8b9cb8";
}

function initTabs() {
  document.querySelectorAll("#main-tabs button").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll("#main-tabs button").forEach(b => b.classList.remove("active"));
      document.querySelectorAll("section.tab").forEach(s => s.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "map") setTimeout(() => { map.invalidateSize(); drawProfile(); }, 50);
    };
  });
  document.querySelectorAll("#leg-tabs button").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll("#leg-tabs button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      leg = btn.dataset.leg;
      document.getElementById("pos-slider").value = 0;
      document.getElementById("assist-legend").style.display = leg === "run" ? "flex" : "none";
      renderMap();
      drawProfile();
      updatePos(0);
    };
  });
}

function track() { return leg === "run" ? DATA.run.track : DATA.bike.track; }
function times() { return leg === "run" ? DATA.run.times : DATA.bike.times; }

function renderAssistZones(pts) {
  let i = 0;
  while (i < pts.length) {
    const phase = pts[i].assist;
    if (!phase) { i++; continue; }
    let j = i + 1;
    while (j < pts.length && pts[j].assist === phase) j++;
    const seg = pts.slice(i, Math.min(j + 1, pts.length));
    if (seg.length >= 2) {
      layers.push(L.polyline(seg.map(p => [p.lat, p.lon]), {
        color: ASSIST_COLORS[phase], weight: 12, opacity: 0.28, lineCap: "round"
      }).addTo(map));
    }
    i = j;
  }
  (DATA.assistance?.markers || []).forEach(m => {
    const icon = L.divIcon({
      className: "",
      html: `<div class="assist-pin">${MARKER_ICON[m.kind] || "📍"}</div>`,
      iconSize: [28, 28], iconAnchor: [14, 14]
    });
    const popup = `<strong>${m.title}</strong><br>km ${m.km.toFixed(1)} · ${Math.round(m.ele)} m<br>${m.popup}<br><em>~${m.clock}</em>`;
    layers.push(L.marker([m.lat, m.lon], { icon }).bindPopup(popup).addTo(map));
  });
}

function renderMap() {
  const pts = track();
  if (!map) {
    map = L.map("map", { zoomControl: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 17, attribution: "© OpenStreetMap"
    }).addTo(map);
  }
  layers.forEach(l => map.removeLayer(l));
  layers = [];
  if (marker) { map.removeLayer(marker); marker = null; }
  if (leg === "run") renderAssistZones(pts);
  let chunk = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    if (pts[i].glbl !== pts[i-1].glbl) {
      layers.push(L.polyline(chunk.map(p => [p.lat, p.lon]), { color: gradeColor(chunk[0].glbl), weight: 4, opacity: 0.9 }).addTo(map));
      chunk = [pts[i-1], pts[i]];
    } else chunk.push(pts[i]);
  }
  if (chunk.length) layers.push(L.polyline(chunk.map(p => [p.lat, p.lon]), { color: gradeColor(chunk[0].glbl), weight: 4, opacity: 0.9 }).addTo(map));
  map.fitBounds(L.latLngBounds(pts.map(p => [p.lat, p.lon])), { padding: [24, 24] });
}

function drawProfile() {
  const canvas = document.getElementById("profile");
  const ctx = canvas.getContext("2d");
  const pts = track();
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 300 * dpr;
  canvas.style.width = rect.width + "px";
  canvas.style.height = "300px";
  ctx.scale(dpr, dpr);
  const w = rect.width, h = 300, pad = { l: 48, r: 12, t: 12, b: 28 };
  const maxKm = pts[pts.length-1].km;
  const eles = pts.map(p => p.ele);
  const minE = Math.min(...eles), maxE = Math.max(...eles);
  const x = km => pad.l + (km / maxKm) * (w - pad.l - pad.r);
  const y = ele => pad.t + (1 - (ele - minE) / Math.max(maxE - minE, 1)) * (h - pad.t - pad.b);
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#131a2e";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#2a3654";
  for (let i = 0; i <= 4; i++) {
    const gy = pad.t + i * (h - pad.t - pad.b) / 4;
    ctx.beginPath(); ctx.moveTo(pad.l, gy); ctx.lineTo(w - pad.r, gy); ctx.stroke();
    const ele = maxE - i * (maxE - minE) / 4;
    ctx.fillStyle = "#8b9cb8"; ctx.font = "10px system-ui"; ctx.fillText(Math.round(ele) + " m", 4, gy + 4);
  }
  for (let i = 0; i < pts.length - 1; i++) {
    ctx.strokeStyle = gradeColor(pts[i].glbl);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x(pts[i].km), y(pts[i].ele));
    ctx.lineTo(x(pts[i+1].km), y(pts[i+1].ele));
    ctx.stroke();
  }
  if (leg === "run") {
    const vlines = [
      [DATA.assistance?.km_split || 25, "#38bdf8", "km 25 crew"],
      [33, "#6ee7b7", "km 33 barrière"],
    ];
    vlines.forEach(([km, col, lbl]) => {
      if (km > maxKm) return;
      ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.setLineDash([6, 4]);
      ctx.beginPath(); ctx.moveTo(x(km), pad.t); ctx.lineTo(x(km), h - pad.b); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = col; ctx.font = "11px system-ui";
      ctx.fillText(lbl, x(km) + 4, pad.t + 14);
    });
  }
  canvas._pts = pts; canvas._x = x; canvas._y = y; canvas._pad = pad;
}

function updatePos(idx) {
  const pts = track();
  const i = Math.min(Math.max(0, Math.round(idx / 1000 * (pts.length - 1))), pts.length - 1);
  const p = pts[i];
  const t = times()[i];
  const raceH = leg === "run"
    ? DATA.meta.swim_t1_bike_t2_h + t
    : DATA.meta.swim_t1_h + t;
  const clock = DATA.meta.race_start_h + raceH;
  const hh = Math.floor(clock) % 24, mm = Math.round((clock % 1) * 60);
  let assistHtml = "";
  if (leg === "run" && p.assist) {
    const isVeh = p.assist === "vehicle";
    const lbl = isVeh ? "🚗 Véhicule" : "🏃 Crew à pied";
    const col = ASSIST_COLORS[p.assist];
    assistHtml = `<div><div class="l">Assistance</div><div class="v" style="color:${col}">${lbl}</div></div>`;
  }
  document.getElementById("pos-info").innerHTML =
    `<div><div class="l">Km</div><div class="v">${p.km.toFixed(1)}</div></div>` +
    assistHtml +
    `<div><div class="l">Altitude</div><div class="v">${Math.round(p.ele)} m</div></div>` +
    `<div><div class="l">Pente</div><div class="v">${p.grade.toFixed(1)} %</div></div>` +
    `<div><div class="l">Temps ${leg}</div><div class="v">${Math.floor(t)}h${String(Math.round((t%1)*60)).padStart(2,"0")}</div></div>` +
    `<div><div class="l">Horloge course</div><div class="v">${String(hh).padStart(2,"0")}:${String(mm).padStart(2,"0")}</div></div>`;
  if (!map) return;
  if (!marker) marker = L.circleMarker([p.lat, p.lon], { radius: 8, color: "#fff", fillColor: "#6ee7b7", fillOpacity: 1, weight: 2 }).addTo(map);
  else marker.setLatLng([p.lat, p.lon]);
}

function initSlider() {
  const sl = document.getElementById("pos-slider");
  sl.oninput = () => updatePos(+sl.value);
  const canvas = document.getElementById("profile");
  canvas.onmousemove = e => {
    const pts = canvas._pts; if (!pts) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    let best = 0, bestD = 1e9;
    for (let i = 0; i < pts.length; i++) {
      const d = Math.abs(canvas._x(pts[i].km) - mx);
      if (d < bestD) { bestD = d; best = i; }
    }
    document.getElementById("pos-slider").value = Math.round(best / (pts.length - 1) * 1000);
    updatePos(+document.getElementById("pos-slider").value);
    const p = pts[best];
    const tip = document.getElementById("tooltip");
    tip.style.display = "block";
    tip.style.left = (e.clientX - rect.left + 12) + "px";
    tip.style.top = (e.clientY - rect.top - 8) + "px";
    tip.innerHTML = `km ${p.km.toFixed(1)} · ${Math.round(p.ele)} m · ${p.grade.toFixed(1)} %`;
  };
  canvas.onmouseleave = () => { document.getElementById("tooltip").style.display = "none"; };
}

function initDocs() {
  const view = document.getElementById("md-view");
  function show(file) {
    document.querySelectorAll(".doc-link").forEach(a => a.classList.toggle("active", a.dataset.file === file));
    const md = DATA.docs[file];
    view.innerHTML = md ? marked.parse(md) : "<p>Document introuvable.</p>";
    location.hash = "doc=" + file;
  }
  document.querySelectorAll(".doc-link").forEach(a => {
    a.onclick = e => { e.preventDefault(); show(a.dataset.file); };
  });
  const m = location.hash.match(/doc=([^&]+)/);
  const first = m ? decodeURIComponent(m[1]) : Object.keys(DATA.docs)[0];
  if (first) show(first);
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  renderMap();
  drawProfile();
  initSlider();
  updatePos(0);
  initDocs();
  window.addEventListener("resize", drawProfile);
});
</script>
</body>
</html>
"""


def build(out: Path = OUT_HTML) -> None:
    run_full = parse_track(RUN_GPX)
    bike_full = parse_track(BIKE_GPX)
    run_track = enrich_track(downsample(run_full, 1500), 100)
    add_assist_phase(run_track)
    bike_track = enrich_track(downsample(bike_full, 2500), 300)

    run_terrain = trim_terrain(json.loads(RUN_TERRAIN.read_text()))
    bike_terrain = trim_terrain(json.loads(BIKE_TERRAIN.read_text()))
    pace = json.loads(PACE_MODEL.read_text())
    bike_ref = json.loads(BIKE_SPEED.read_text())

    run_speeds = {k: v["kmh"] for k, v in pace["aggregate_model"]["grade_buckets"].items()}
    bike_speeds = {}
    for row in bike_ref["estimate"]["rows"]:
        bike_speeds[row["grade"]] = row["kmh"]

    run_times = cum_hours(run_track, run_speeds)
    bike_times = cum_hours(bike_track, bike_speeds)

    bike_h = bike_ref["estimate"]["total_h"]
    run_h = pace["ascend_estimate"]["total_h"]
    km33_h = pace["ascend_km33_estimate"]["total_h"]

    swim_t1 = SWIM_H + T1_H
    run_start_h = swim_t1 + bike_h + T2_H
    t2_clock_h = swim_t1 + bike_h
    finish_h = run_start_h + run_h

    assistance = build_assistance_meta(run_track, run_times, run_start_h)
    assist_i, _ = nearest_at_km(run_track, ASSIST_KM)
    assist_clock = fmt_clock(run_start_h + run_times[assist_i])

    barrier = barrier_rows(km33_h)
    docs, docs_avail = load_docs()

    bike_grade_rows = render_grade_table(
        bike_terrain["grade_summary"],
        {r["grade"]: r["kmh"] for r in bike_ref["estimate"]["rows"]},
    )
    run_grade_rows = render_grade_table(
        run_terrain["grade_summary"],
        {r["grade"]: r["kmh"] for r in pace["ascend_estimate"]["rows"]},
    )

    data = {
        "meta": {
            "race_start_h": 3.0,
            "swim_t1_h": swim_t1,
            "swim_t1_bike_t2_h": swim_t1 + bike_h + T2_H,
            "bike_h": bike_h,
            "run_h": run_h,
            "km33_h": km33_h,
        },
        "run": {"track": run_track, "times": run_times, "terrain": run_terrain},
        "bike": {"track": bike_track, "times": bike_times, "terrain": bike_terrain},
        "pace_model": {
            "aggregate": pace["aggregate_model"],
            "runs": pace["runs"],
            "ascend": pace["ascend_estimate"],
            "km33": pace["ascend_km33_estimate"],
        },
        "bike_pacing": bike_ref,
        "assistance": assistance,
        "docs": docs,
    }

    html = HTML
    html = html.replace("__BIKE_KM__", f"{bike_terrain['distance_km']:.0f}")
    html = html.replace("__BIKE_GAIN__", f"{bike_terrain['gain_m']:.0f}")
    html = html.replace("__RUN_KM__", f"{run_terrain['distance_km']:.1f}")
    html = html.replace("__RUN_GAIN__", f"{run_terrain['gain_m']:.0f}")
    html = html.replace("__BIKE_H__", f"{bike_h:.1f}")
    html = html.replace("__RUN_H__", f"{run_h:.1f}")
    html = html.replace("__KM33_MIN__", f"{km33_h * 60:.0f}")
    html = html.replace("__T2_CLOCK__", fmt_clock(t2_clock_h))
    html = html.replace("__FINISH_CLOCK__", fmt_clock(finish_h))
    html = html.replace("__BARRIER_ROWS__", render_barrier_table(barrier))
    html = html.replace("__BIKE_GRADE_ROWS__", bike_grade_rows)
    html = html.replace("__BIKE_CLIMBS__", render_climb_rows(bike_terrain["climbs"], 25))
    html = html.replace("__PACE_MODEL_ROWS__", render_pace_model_table(pace["aggregate_model"]))
    html = html.replace("__RUN_GRADE_ROWS__", run_grade_rows)
    html = html.replace("__RUNS_ROWS__", render_runs_table(pace["runs"]))
    html = html.replace("__RUN_CLIMBS__", render_climb_rows(run_terrain["climbs"], 15))
    html = html.replace("__DOCS_SIDEBAR__", render_docs_sidebar(docs_avail))
    html = html.replace("__ASSIST_KM__", f"{ASSIST_KM:.0f}")
    html = html.replace("__ASSIST_CLOCK__", assist_clock)
    html = html.replace("__ASSIST_TIMELINE__", render_assist_timeline(assistance["markers"]))
    html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    kb = out.stat().st_size // 1024
    print(f"Wrote {out} ({kb} KB)")


if __name__ == "__main__":
    build()
