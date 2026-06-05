# Ascend XTri — Analyse du parcours CAP (GPX v2)

> Index du dossier : `README.md` · Contexte stratégique : `xtri/context-and-strategy.md` §7

Source : `Ascend xtri run v2.gpx` (Strava route)  
Analyse auto : `terrain_analysis.md` / `terrain_analysis.json` — mode **run**  
Distance GPX : **41,8 km** · D+ lissé **+2 585 m** · D- **-1 568 m** · Alt **784–2 847 m**  
Généré : 2026-06-05

> Les pentes et surfaces viennent du GPX + OpenStreetMap. Le découpage officiel
> (directeur de course) est rappelé pour comparaison. OSM est incomplet en montagne :
> beaucoup de `unknown` / `suspect_unpaved`.

---

## Vue d'ensemble

| Indicateur | Valeur | Commentaire |
|---|---:|---|
| Distance | 41,8 km | Proche des 42 km officiels |
| D+ GPX | 2 585 m | Proche des 2 600 m annoncés |
| Pente ≥ 6 % | **38 %** du parcours | Course très montagneuse |
| Pente ≤ -6 % | **28 %** | Descentes techniques à gérer (genou) |
| Sentier + piste (OSM) | **~68 %** | path 34 % + track 33 % |
| Route (OSM) | **~32 %** | surtout début et transitions |

**Structure en 4 actes :**
1. **km 0–9** — Descente puis faux-plat / montée modérée (Payolle → vallée)
2. **km 9–21** — Alternance route / piste / sentier, montées intermédiaires
3. **km 21–36** — **Bloc décisif** : grosse montée technique vers Pic du Midi + sommet
4. **km 36–42** — Longue descente piste vers Tourmalet (arrivée)

---

## Profil altimétrique (tous les 2 km)

| Km | Alt | | Km | Alt |
|---:|---:|---|---:|---:|
| 0 | 1 098 | départ haut | 22 | 1 622 |
| 4 | 1 006 | ↓ | 26 | 1 450 |
| 8 | 806 | point bas ~km 8 | 30 | 2 010 |
| 12 | 998 | | 34 | 2 605 |
| 16 | 1 049 | | 38 | 2 432 |
| 20 | 1 521 | début gros D+ | 42 | 2 115 |

Le point bas (~800 m) est vers **km 8**. Le sommet GPX (~2 847 m) est vers **km 35**.

---

## Les bosses — montées majeures

### 1. Montée km 9,2 → 10,9 (+175 m / 1,7 km, ~10 %)
- Entrée dans la partie « vallonnée » après la descente initiale.
- OSM : piste/sentier partiel en fin de segment.
- **Alignement DC** : zone km 9–14 (single track officiel).

### 2. Montée km 15,3 → 17,7 (+192 m / 2,4 km, ~8 %)
- Montée régulière sur route/piste.
- **Alignement DC** : km 15–18 piste forestière + transition.

### 3. Montée km 18,0 → 20,4 (+351 m / 2,4 km, ~15 %) — **Col de la Courade**
- Pente soutenue, sentier dominant.
- **Alignement DC** : km 15–20 (montée Courade, ~4 km/h cible table).
- Surface : **hors route**, engagement cartilage en descente derrière.

### 4. Bosses km 20,8–22,8 (+~160 m cumulé)
- Deux relances : 20,8–21,4 (+40 m) puis 22,0–22,8 (+123 m, ~15 %).
- Sortie de Courade / approche secteur Arrizes.
- **Alignement DC** : km 20–23.

### 5. **LA montée km 26,2 → 35,3 (+1 423 m / 9,1 km, ~16 %)** — bloc Pic du Midi
- Cœur de la course : **+1 400 m en 9 km**, pente moyenne très élevée.
- Sentier km 26–32 puis piste/sentier sommet km 32–36.
- **Alignement DC** :
  - km 21–32 : single track montagne D+ fort
  - km 30–33 : montée Col de Sencours (~4 km/h)
  - km 33 : **barrière horaire 18h15**
  - km 33–36 : A/R Pic du Midi (3–5 km/h)
- Surface OSM : quasi tout **hors goudron** sur ce bloc.
- **Limiteur genou + épaule/bâtons** : montée longue en posture, descentes techniques après.

---

## Descentes à risque (chondropathie)

| Km | Longueur | D- | Pente moy. | Notes |
|---|---:|---:|---:|---|
| 1,6–2,5 | 0,9 km | -72 m | -8 % | Début de course, sentier |
| 6,5–8,3 | 1,8 km | -112 m | -6 % | Descente vers point bas |
| 12,2–12,9 | 0,7 km | -63 m | -9 % | Après secteur piste km 10–13 |
| 22,8–24,6 | 1,7 km | -166 m | -10 % | Sortie Courade → Arrizes |
| 25,3–26,2 | 0,9 km | -158 m | **-18 %** | **Très raide** — prudence genou |
| **35,3–41,8** | **6,5 km** | **-731 m** | **-11 %** | **Descente finale Tourmalet** — piste, fatigue maximale |

La descente **km 25,3–26,2** (-18 %) et la **finale km 35+** sont les deux secteurs à traiter en priorité pour la stratégie genou (marche/trail si besoin, pas de surcharge en fin de course).

---

## Types de chemin (OSM)

| Type | Distance | Part | D+ |
|---|---:|---:|---:|
| Sentier / chemin (`path`) | 14,3 km | 34 % | +1 706 m |
| Piste (`track`) | 14,0 km | 33 % | +419 m |
| Route locale | 10,6 km | 25 % | +348 m |
| Autres routes | 2,9 km | 7 % | +111 m |

### Tronçons sentier significatifs
- **km 18,5–22,8** (4,3 km, +521 m) — montée Courade / sortie
- **km 25,5–32,0** (6,6 km, +958 m) — cœur montée vers Pic
- **km 34,4–36,1** (1,6 km) — zone sommet / transition

### Tronçons piste significatifs
- **km 0–0,4** — départ
- **km 10–13** — secteur Payolle/Campan
- **km 22,8–24,3** — descente post-Courade
- **km 32–34** — approche sommet
- **km 36–42** — **descente arrivée Tourmalet** (5,6 km, -532 m)

**Comparaison directeur de course :**

| Km officiel | Surface annoncée | GPX/OSM |
|---|---|---|
| 0–2 | Chemin + piste | piste + sentier ✓ |
| 2–9 | Route | route + descente ✓ |
| 9–14 | Single track | sentier + piste ✓ |
| 21–32 | ST montagne D+ fort | sentier km 18–32 ✓ |
| 32–34 | Piste Pic du Midi | piste ✓ |
| 34–36 | ST sommet A/R | sentier/piste ✓ |
| 36–42 | Piste descente Tourmalet | piste km 36–42 ✓ |

---

## Implications entraînement / course

1. **Pas un marathon de route** : 68 % sentier/piste, 38 % du parcours en pente ≥ 6 %.
2. **Trois cols « nommés » dans la logique course** : Courade (~km 20), Arrizes (~km 23–28), Sencours + Pic du Midi (~km 30–36).
3. **Barrière km 33** : se situe dans la fin de la mega-montée km 26–35 — il faut arriver sur ce bloc avec du jambes et gérer le début de course sans sur-dépenser.
4. **Genou** : espacer les grosses descentes à l'entraînement ; la finale -731 m en 6,5 km après 30+ km de jambes est le test cartilage.
5. **Épaule / bâtons** : 9 km de montée technique km 26–35 en sentier — le volume de bâtons en long run trail sera déterminant.
6. **Pacing cible** : voir `run_pace_model.md` (Icon / Alpsman / Bearman / Celtman) — vitesses race recoupées pente × surface. Montée raide sentier ≥ 6 % : **~4–5 km/h** (vs table xtri ~4 km/h).

### Barrière km 33 @ 18h15 (modèle Tom)

| Scénario fin vélo (T2) | Passage km 33 | Marge / 18h15 |
|---|---|---|
| 12h17 (table xtri) | ~17h26 | +49 min |
| 12h25 (vélo @ 230 W) | ~17h34 | +41 min |
| 12h45 (+ stops) | ~17h54 | +21 min |
| 13h00 (vélo lent) | ~18h09 | +6 min |

Hypothèse : T2 = 10 min après rack vélo. Le goulot reste le **vélo** si T2 > ~13h00.

---

## Fichiers générés

```bash
.venv/bin/python scripts/race/analyze_gpx_osm_surface.py --mode run \
  "AscendXtri/Ascend xtri run v2.gpx" \
  --cache AscendXtri/.cache/osm_surface.json \
  --out AscendXtri/terrain_analysis.md \
  --json-out AscendXtri/terrain_analysis.json
```

Le mode `run` utilise une fenêtre de pente plus courte (100 m), un pas GPX plus fin (40 m) et des seuils de bosses adaptés à la course à pied (`--mode bike` reste le défaut pour le gravel/TPR).

Modèle pacing (vitesses race recoupées pente × surface) :

```bash
.venv/bin/python scripts/race/build_run_pace_model.py
```
