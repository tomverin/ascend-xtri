# Modèle de pacing run XTri (références historiques)

Sources : Icon / Alpsman / Bearman / Celtman — vitesses **en mouvement**
(stops exclus), recoupées pente + type de chemin OSM.

## Courses analysées

| Course | Distance | D+ | D- | Roulage | Moy. km/h |
|---|---:|---:|---:|---:|---:|
| Alpsman 2023 run (32e top finisher) | 42.2 km | +1610 m | -356 m | 5.16 h | 8.1 |
| Bearman 2023 run (5e scratch) | 42.4 km | +2164 m | -2182 m | 5.18 h | 7.9 |
| Icon 2025 run (38e scratch) | 42.5 km | +1778 m | -1040 m | 5.88 h | 7.1 |
| Icon run (tough to the end) | 37.7 km | +1659 m | -1110 m | 5.08 h | 7.2 |
| Celtman run (21e / 4e vétéran) | 42.9 km | +1998 m | -2018 m | 6.01 h | 6.9 |

## Vitesses par pente (agrégat pondéré)

| Pente | Distance cumulée | km/h | min/km |
|---|---:|---:|---:|
| <= -6 % | 35.6 km | 8.8 | 7 |
| -6 to -3 % | 19.1 km | 8.8 | 7 |
| -3 to -1 % | 26.9 km | 9.3 | 6 |
| -1 to +1 % | 45.5 km | 9.5 | 6 |
| +1 to +3 % | 22.2 km | 8.4 | 7 |
| +3 to +6 % | 12.6 km | 7.1 | 8 |
| >= +6 % | 40.3 km | 4.5 | 13 |

## Vitesses par type de chemin

| Terrain | Distance cumulée | km/h | min/km |
|---|---:|---:|---:|
| route | 72.1 km | 9.8 | 6 |
| piste | 47.9 km | 6.5 | 9 |
| sentier | 81.6 km | 6.5 | 9 |
| autre | 0.6 km | 6.4 | 9 |

## Matrice pente × terrain (km/h)

| Pente | Route | Piste | Sentier |
|---|---:|---:|---:|
| <= -6 % | 11.3 | 9.2 | 6.4 |
| -6 to -3 % | 10.0 | 9.0 | 7.6 |
| -3 to -1 % | 9.9 | 8.8 | 8.8 |
| -1 to +1 % | 10.0 | 9.2 | 9.1 |
| +1 to +3 % | 8.6 | 8.4 | 8.2 |
| +3 to +6 % | 7.6 | 7.0 | 6.9 |
| >= +6 % | 5.9 | 4.4 | 4.4 |

## Bosses majeures par course

### Alpsman 2023 run (32e top finisher)

| Km | Long. | D+ | Pente |
|---:|---:|---:|---:|
| 29-31 | 1.6 km | +144 m | 9.3 % |
| 34-36 | 2.3 km | +308 m | 13.5 % |
| 37-42 | 5.4 km | +727 m | 13.5 % |

### Bearman 2023 run (5e scratch)

| Km | Long. | D+ | Pente |
|---:|---:|---:|---:|
| 0-6 | 5.5 km | +977 m | 17.7 % |
| 21-27 | 5.6 km | +991 m | 17.7 % |

### Icon 2025 run (38e scratch)

| Km | Long. | D+ | Pente |
|---:|---:|---:|---:|
| 34-35 | 1.1 km | +176 m | 15.7 % |
| 38-42 | 4.6 km | +734 m | 16.0 % |

### Icon run (tough to the end)

| Km | Long. | D+ | Pente |
|---:|---:|---:|---:|
| 29-30 | 1.1 km | +174 m | 16.1 % |
| 33-38 | 4.6 km | +739 m | 16.0 % |

### Celtman run (21e / 4e vétéran)

| Km | Long. | D+ | Pente |
|---:|---:|---:|---:|
| 4-4 | 0.8 km | +73 m | 8.7 % |
| 18-21 | 3.5 km | +852 m | 24.2 % |
| 23-24 | 1.0 km | +129 m | 12.9 % |

## Application Ascend run (GPX v2)

**Temps roulage estimé (42 km) : 6.45 h** (387 min)

| Pente | Distance | km/h modèle | Temps |
|---|---:|---:|---:|
| <= -6 % | 12.3 km | 8.3 | 89 min |
| -6 to -3 % | 4.0 km | 8.6 | 28 min |
| -3 to -1 % | 2.5 km | 9.0 | 17 min |
| -1 to +1 % | 2.3 km | 9.3 | 15 min |
| +1 to +3 % | 2.1 km | 8.4 | 15 min |
| +3 to +6 % | 2.7 km | 7.1 | 23 min |
| >= +6 % | 15.8 km | 4.7 | 201 min |

### Barrière km 33 @ 18h15

**Run km 0–33 estimé : 311 min** (5.19 h)

| Scénario T2 | Passage km 33 | Marge / 18h15 |
|---|---|---|
| 12h17 (table xtri) | 17h38 | ✅ +37 min |
| 12h25 (vélo @ 230 W) | 17h46 | ✅ +29 min |
| 12h45 (+ stops vélo) | 18h06 | ✅ +9 min |
| 13h00 (vélo lent) | 18h21 | ❌ -6 min |

Comparaison table xtri médiane : km 0–33 ≈ **5h05** · modèle Tom ≈ **311 min**.

## Règles d'usage

- Modèle = **tes** vitesses race, pas la table médiane xtri.
- En montée raide sentier (≥ 6 %), viser **~4–5 km/h** (12–15 min/km).
- Plat route : **~9–11 km/h**.
- Descente : ne pas surestimer — genou / technique.

Régénérer :
```sh
.venv/bin/python scripts/race/build_run_pace_model.py
```
