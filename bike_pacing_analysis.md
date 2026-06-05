# Ascend XTri — Analyse vélo & estimation de temps

> Index : `README.md` · Terrain : `bike_terrain_analysis.md` · Contexte : `xtri/context-and-strategy.md` §7

**GPX** : `Ascend_xtri_bike.gpx` (Openrunner / XTRI)  
**Référence puissance** : **Bearman 2023** @ **210–250 W** (≈ **230 W** cible)  
**Généré** : 2026-06-05

---

## Parcours — chiffres GPX

| Indicateur | GPX | Officiel Ascend |
|---|---:|---:|
| Distance | **184,3 km** | ~186 km |
| D+ lissé | **+4 187 m** | ~5 000 m |
| D- lissé | -3 520 m | — |
| Altitude max | 1 734 m | — |
| Bitume (OSM) | **78 %** | route majoritaire |

Le D+ GPX est **~15 % sous l'annonce** — garder une marge sur le temps si la trace est une variante ou si le lissage sous-estime.

**Profil** : Lourdes → cols pyrénéens → T2 au pied du Tourmalet. Quatre « actes » :
1. **km 0–40** — vallonné, cols courts (400–650 m)
2. **km 40–80** — descentes profondes puis remontées
3. **km 80–155** — **cœur montagne** : enchaînement longs cols
4. **km 155–184** — descente / roulage vers **T2**

---

## Vitesses de référence — Bearman 2023 @ 230 W

Extrait de la **course réelle** Bearman 2023 (`/Users/tom/Documents/training/Bike Xtri/Bearman_2023.gpx`, 184,5 km, 8,3 h roulage) via `scripts/race/analyze_ride_speed_power.py` — segments où la puissance instantanée est **210–250 W**.

| Pente | Dist. échantillon @230 W | **km/h @230 W** | km/h course entière |
|---|---:|---:|---:|
| ≤ -6 % | 0,2 km | 43,2 | 49,5 |
| -6 à -3 % | 0,8 km | 45,2 | 45,4 |
| -3 à -1 % | 1,1 km | 41,7 | 34,7 |
| -1 à +1 % | 3,3 km | **28,9** | 29,0 |
| +1 à +3 % | 10,1 km | **23,8** | 23,3 |
| +3 à +6 % | 13,3 km | **17,0** | 16,7 |
| **≥ +6 %** | **16,2 km** | **11,1** | 10,9 |

→ L'échantillon @230 W est **solide en montée** (16 km ≥ 6 %). Les descentes utilisent le fallback « course entière » quand l'échantillon filtré est &lt; 1 km.

**Cross-check Alpsman 2023** @ 230 W (`ref_speed_alpsman_2023_230w.json`) : pentes raides **12,2 km/h**, +3–6 % **18,3 km/h** — cohérent, légèrement plus rapide (course plus courte / fraîcheur).

**Cross-check Faucille** (segment étalon, Z2 ~230 W) : VAM **~835 m/h** → sur une montée de **+700 m** à 230 W ≈ **50 min** ; les bosses Ascend à ~7 % et 11 km/h donnent VAM ~**800 m/h**, aligné.

---

## Estimation globale — roulage seul

Modèle : appliquer les vitesses Bearman @230 W à la **distribution de pentes** du GPX Ascend (`bike_terrain_analysis.json`).

| Pente (part du parcours) | Distance | Temps estimé |
|---|---:|---:|
| ≤ -6 % (14,5 %) | 26,8 km | 33 min |
| -6 à -3 % | 19,1 km | 25 min |
| -3 à -1 % | 23,4 km | 34 min |
| -1 à +1 % | 36,0 km | **1 h 15** |
| +1 à +3 % | 25,0 km | **1 h 03** |
| +3 à +6 % | 18,0 km | **1 h 03** |
| **≥ +6 %** | **36,0 km** | **3 h 14** |
| **TOTAL roulage** | **184,3 km** | **≈ 8 h 07** |

| Scénario | Temps vélo roulage | Notes |
|---|---:|---|
| **Bearman 2023 @ 230 W** (modèle ci-dessus) | **~8 h 07** | Référence retenue |
| Bearman 2023 réel (puissance variable) | 8 h 20 | 184,5 km, même distance ! |
| Table référence autre participant | **8 h 02** | Vitesses médianes xtri |
| + marge D+ GPX vs officiel (+20 %) | **~9 h 30–9 h 45** | Si trace sous-estime le D+ réel |

**Hors modèle** : T1 (~10 min), ravitaillements, fatigue post-3,8 km natation, chaleur juillet → prévoir **+30–60 min** sur le temps « roulage pur » pour une estimation course complète.

**Arrivée T2 indicative** (départ 3h00, swim 1h08, T1 10 min) :
- Vélo 8h07 → **T2 ~12h25** — proche de la table référence (**~12h17**).

---

## Les bosses — montées majeures @ 230 W

Vitesses par boss : pente moyenne du segment → bucket Bearman @230 W.

| Km | Long. | D+ | Pente | km/h @230 W | **Temps** | Col / secteur (approx.) |
|---|---:|---:|---:|---:|---:|---|
| 16–18 | 2,2 km | +126 m | 5,7 % | 17,0 | **8 min** | Approche / Bidalet |
| 26–28 | 2,0 km | +131 m | 6,6 % | 11,1 | **11 min** | Mauvezin / Sarp |
| 39–42 | 3,2 km | +181 m | 5,7 % | 17,0 | **11 min** | Col de Balès (approche) |
| 43–46 | 2,6 km | +96 m | 3,7 % | 17,0 | **9 min** | Transition vallée |
| **80–101** | **21,0 km** | **+1 190 m** | 5,7 % | 17,0 | **1 h 14** | **Peyragudes → Peyresourdes** |
| 116–126 | 9,6 km | +702 m | 7,3 % | 11,1 | **52 min** | **Val Lauron d'Azet** |
| 134–143 | 8,4 km | +609 m | 7,3 % | 11,1 | **45 min** | **Col d'Aspin** |
| 167–179 | 11,8 km | +757 m | 6,4 % | 11,1 | **1 h 04** | Approche **T2 / Tourmalet** |
| | | | | **Σ bosses** | **~4 h 34** | (montées détectées uniquement) |

**Bosses décisives** :
1. **km 80–101** — 21 km / +1 190 m : la plus longue ; à 230 W ≈ **1h14**, VAM ~960 m/h (légèrement au-dessus Faucille Z2 — pente moyenne modérée, volume élevé).
2. **km 116–143** — enchaînement Azet + Aspin : **~1h37** cumulé @ 230 W.
3. **km 167–179** — dernière montée avant T2 : **~1h04** ; jambes post-6h+ vélo.

---

## Descentes majeures @ 230 W (réf. descente Bearman)

| Km | Long. | D- | Pente | km/h | Temps |
|---|---:|---:|---:|---:|---:|
| 34–39 | 5,2 km | -256 m | -4,9 % | 45 | 7 min |
| **101–116** | **15,2 km** | **-869 m** | -5,7 % | 45 | **20 min** |
| 126–134 | 8,4 km | -616 m | -7,3 % | 50 | 10 min |
| 144–155 | 11,8 km | -740 m | -6,3 % | 50 | 14 min |
| 179–184 | 5,1 km | -366 m | -7,2 % | 50 | 6 min |

La descente **km 101–116** (-869 m) est le principal « gain » de temps après le bloc Peyragudes.

---

## Surfaces & types de chemin

| Type OSM | Distance | Part |
|---|---:|---:|
| Route secondaire / tertiaire | 139 km | 76 % |
| Route principale | 22 km | 12 % |
| Piste / sentier | 7 km | 4 % |

Course **majoritairement bitume** — pas de contrainte gravel type Corsica. Les vitesses Bearman (triathlon route / chemins roulants) sont **directement transférables**.

---

## Fichiers & commandes

```sh
# Terrain (bosses, pentes, surfaces)
.venv/bin/python scripts/race/analyze_gpx_osm_surface.py --mode bike \
  AscendXtri/Ascend_xtri_bike.gpx \
  --cache AscendXtri/.cache/osm_bike.json --chunk-km 15 \
  --out AscendXtri/bike_terrain_analysis.md \
  --json-out AscendXtri/bike_terrain_analysis.json

# Vitesses @ 230 W depuis Bearman 2023 + estimation
.venv/bin/python scripts/race/analyze_ride_speed_power.py \
  "/Users/tom/Documents/training/Bike Xtri/Bearman_2023.gpx" \
  --power-min 210 --power-max 250 \
  --json-out AscendXtri/ref_speed_bearman_2023_230w.json \
  --terrain-json AscendXtri/bike_terrain_analysis.json \
  --estimate-label "Ascend bike @ Bearman 230W"
```

Sources historiques externes (hors repo) :
- `~/Documents/training/Bike Xtri/Bearman_2023.gpx`
- `~/Documents/training/Bike Xtri/Alpsman_2023.gpx`

---

## Limites & interprétation

- **Puissance 230 W** = effort type **bosses / seuil bas** Bearman, pas la moyenne NP de toute la course (qui inclut descentes et plats).
- Pas de modèle de **fatigue cumulative** (heure 7 ≠ heure 1) — la table référence xtri intègre déjà un rythme médian.
- **Post-swim** : épaule + début de vélo à 3h00 du matin non modélisés.
- Trace GPX **D+ 4 187 m** vs **5 000 m** officiel : si le parcours réel est plus long en D+, ajouter ~**1–1,5 h** (≈ +20 % temps en montée).
- Les noms de cols sont **approximatifs** (géolocalisation par km + profil, pas de POI officiels dans le GPX).

**En synthèse** : à **230 W sur les bosses** (profil Bearman 2023), le vélo Ascend se situe autour de **8 h de roulage** sur cette trace — aligné avec Bearman réel et la table xtri (~8 h). Les deux séquences à ne pas sous-estimer : **km 80–101** (~1h15) et **km 116–179** (~2h40 de montées cumulées).
