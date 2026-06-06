# Ascend XTri — dossier parcours

Matériel d'analyse **vélo** (~186 km / 5 000 m D+) et **CAP** (42 km / 2 600 m D+) de l'[Ascend XTri](https://www.xtriworldtour.com/ascend) (25 juillet 2026).

## Fichiers

### Vélo

| Fichier | Rôle |
|---|---|
| `Ascend_xtri_bike.gpx` | Trace vélo Openrunner / XTRI |
| `bike_terrain_analysis.md` / `.json` | Terrain auto (mode `bike`) : bosses, descentes, surfaces |
| `bike_pacing_analysis.md` | **Estimation temps ~8 h07** @ 230 W (réf. Bearman 2023) |
| `ref_speed_bearman_2023_230w.json` | Vitesses par pente filtrées 210–250 W |
| `ref_speed_alpsman_2023_230w.json` | Cross-check Alpsman 2023 @ 230 W |
| `.cache/osm_bike.json` | Cache Overpass vélo (gitignored) |

### Course à pied

| Fichier | Rôle |
|---|---|
| `Ascend_run_official_2026-06.gpx` | **GPX officiel CAP** (site juin 2026, modif assistance km 25) |
| `Ascend xtri run v2.gpx` | Ancienne trace Strava ([route](https://www.strava.com/routes/3497605010760440364)) |
| `terrain_analysis.md` / `.json` | Terrain auto v2 Strava (mode `run`) |
| `terrain_analysis_official.md` / `.json` | Terrain auto GPX officiel |
| `run_course_analysis.md` | Synthèse coaching CAP |
| `run_pace_model.md` / `.json` | **Modèle pacing** (Icon / Alpsman / Bearman / Celtman) |
| `.cache/osm_surface.json` | Cache Overpass run (gitignored) |

Contexte stratégique global : `xtri/context-and-strategy.md` §7 · Go/no-go : `xtri/ascend-go-nogo.md`

### WhatsApp (orga)

| Fichier | Rôle |
|---|---|
| `whatsapp/info/ascend2026_info_chat.txt` | Groupe **Ascend2026** — infos officielles |
| `whatsapp/athletes/ascend_athletes_chat.txt` | Groupe **ASCEND Athletes** |
| `whatsapp/athletes/parcours_support_run.gpx` | GPX run partagé par les athlètes |

Voir `whatsapp/README.md` pour ré-exporter.

## Chiffres clés (GPX v2, mode `run`)

- **41,8 km** · **+2 585 m** / **-1 568 m** · alt **784–2 847 m**
- **38 %** du parcours en pente **≥ 6 %** · **28 %** en pente **≤ -6 %**
- **~68 %** sentier + piste (OSM) · **~32 %** route
- **Barrière horaire** : km **33** avant **18h15** (top finishers → Pic du Midi)

## Structure du parcours (4 actes)

1. **km 0–9** — Descente vers ~800 m (km 8), remontée modérée
2. **km 9–21** — Route / piste / sentier, bosses intermédiaires (Courade approche)
3. **km 21–36** — Bloc décisif : **+1 423 m en 9 km** (km 26–35) vers Pic du Midi
4. **km 36–42** — Descente piste Tourmalet (**-731 m en 6,5 km**)

### Montées majeures (GPX)

| Km | D+ | Long. | Pente moy. | Nom / secteur |
|---|---:|---:|---:|---|
| 9–11 | +175 m | 1,7 km | ~10 % | Entrée single track |
| 15–18 | +192 m | 2,4 km | ~8 % | Piste forestière |
| 18–20 | +351 m | 2,4 km | ~15 % | **Col de la Courade** |
| 21–23 | +160 m | ~1,4 km | variable | Sortie Courade / Arrizes |
| **26–35** | **+1 423 m** | **9,1 km** | **~16 %** | **Sencours + Pic du Midi** |

### Descentes à risque (chondropathie)

| Km | D- | Pente moy. | Note |
|---|---:|---:|---|
| 25,3–26,2 | -158 m | **-18 %** | Très raide, avant grosse montée |
| **35,3–41,8** | **-731 m** | **-11 %** | Finale épuisée, piste Tourmalet |

## Script d'analyse

Le script `scripts/race/analyze_gpx_osm_surface.py` interroge OpenStreetMap (Overpass), recalcule le profil altimétrique et classe les surfaces.

### Mode `run` vs `bike`

| Paramètre | `bike` (défaut) | `run` |
|---|---|---|
| Pas GPX | 200 m | 40 m |
| Fenêtre pente locale | 300 m | 100 m |
| Montée majeure | ≥ 1,5 km, +60 m | ≥ 0,8 km, +60 m |
| Bosses intermédiaires | — | ≥ 0,35 km, +25 m, pente ≥ 5 % |
| Rélances courtes | — | ≥ 0,12 km, +12 m, pente ≥ 10 % |
| Profil alti (pas) | 25 km | 2 km |

Le mode **run** détecte des bosses plus courtes et raides, pertinentes à pied. Le mode **bike** reste adapté au gravel (Corsica, TPR).

### Régénérer l'analyse

```sh
.venv/bin/python scripts/race/analyze_gpx_osm_surface.py --mode run \
  "AscendXtri/Ascend xtri run v2.gpx" \
  --cache AscendXtri/.cache/osm_surface.json \
  --out AscendXtri/terrain_analysis.md \
  --json-out AscendXtri/terrain_analysis.json
```

Premier run : fetch Overpass ~15–30 s (cache ensuite instantané). Connexion réseau requise.

### Sorties du script

- **Profil altimétrique** (tous les 2 km en mode run)
- **Grade summary** (% distance par bucket de pente)
- **Major climbs / descents** — montées et descentes structurantes
- **Bosses / rélances** — pentes moyennes et courtes (run only)
- **Highway / surface / tracktype** — répartition OSM + tronçons sentier/piste
- **Surface cross-ref** — recoupement pente × surface (paved / unpaved)

## Limites connues

- OSM incomplet en montagne : beaucoup de tags `unknown` ; `suspect_unpaved` sur path/track sans `surface=*`.
- D+/D- GPX lissé ≠ montre Garmin (smoothing elevation).
- Pas de POIs / ravitaillements intégrés (contrairement au pipeline Corsica).
- Le découpage km du directeur de course est **qualitatif** ; le GPX affine les pentes et altitudes.

## Implications entraînement

Voir `run_course_analysis.md` et `xtri/context-and-strategy.md` §7. En bref :

- **Genou** : volume D- progressif ; finale km 36–42 et descente km 25 à espacer à l'entraînement.
- **Épaule / bâtons** : 9 km de montée sentier km 26–35 — intégrer bâtons en long run trail.
- **Pacing** : modèle Tom (`run_pace_model.md`) — **~6h16** roulage (42 km) · km 0–33 **~5h00** · montée ≥ 6 % sentier **~4,4 km/h** (vs table xtri ~4 km/h).

## Vélo — estimation rapide

- **184 km** · **+4 187 m** GPX · **~78 % bitume**
- **~8 h07** roulage @ **230 W** (profil bosses Bearman 2023)
- Bosses clés : **km 80–101** (+1 190 m, ~1h14) · **km 116–143** (Azet+Aspin, ~1h37) · **km 167–179** (~1h04)
- Détail : `bike_pacing_analysis.md`

```sh
.venv/bin/python scripts/race/analyze_gpx_osm_surface.py --mode bike \
  AscendXtri/Ascend_xtri_bike.gpx --cache AscendXtri/.cache/osm_bike.json --chunk-km 15 \
  --out AscendXtri/bike_terrain_analysis.md --json-out AscendXtri/bike_terrain_analysis.json

.venv/bin/python scripts/race/analyze_ride_speed_power.py \
  "$HOME/Documents/training/Bike Xtri/Bearman_2023.gpx" \
  --power-min 210 --power-max 250 \
  --json-out AscendXtri/ref_speed_bearman_2023_230w.json \
  --terrain-json AscendXtri/bike_terrain_analysis.json
```

### Site public (GitHub Pages)

Dashboard interactif : carte, profil altimétrique, pacing vélo/run, documents.

```sh
.venv/bin/python scripts/race/build_ascend_site.py
scripts/race/deploy_ascend_site.sh          # → https://tomverin.github.io/ascend-xtri/
```

Sortie locale : `AscendXtri/site/index.html` (~680 KB, autonome).

### Modèle pacing run (références historiques)

Sources GPX : `archive/past-races/` (Alpsman, Bearman, Icon 2025, Icon tough, Celtman).

```sh
.venv/bin/python scripts/race/build_run_pace_model.py
```

Produit `run_pace_model.md` / `.json` : vitesses par pente, par surface (route/piste/sentier), matrice croisée, estimation Ascend + barrière km 33.

## Historique

- **2026-06-05** : analyse CAP (GPX v2, `--mode run`) + analyse vélo + pacing @ 230 W Bearman 2023.
- **2026-06-05** : modèle pacing run depuis GPX courses (Icon / Alpsman / Bearman / Celtman).
