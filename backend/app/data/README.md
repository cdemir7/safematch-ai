# mahalle_features_full.json — default feature store (all 968 mahalle)

The API loads **`mahalle_features_full.json`** by default (see
`_FEATURES_PATH` in `services/recommendation_service.py`). It's produced by
`data-pipeline/scripts/07_enrich_mahalle_features.py` from the boundary,
earthquake (Vs30 + İBB ilçe hasar tahmini), and AFAD toplanma alanı data in
`data-pipeline/output/` (see `data-pipeline/SOURCES.md` §6–7).

`saglik`, `egitim`, `ulasim`, `sosyal_yasam`, `yasam_kalitesi` are not backed
by real data yet (no POI/transit pipeline run) — every one of the 968
records gets the same default score (50). Since that's true for *all*
records, it isn't repeated per-record; it's stated once, here, and in
`PLACEHOLDER_CRITERIA` at the top of the script. Each record's
`data_quality` block only carries labels that actually vary
mahalle-to-mahalle (`deprem_guvenlik`, `toplanma`, `fiyat`, plus any manual
override). `deprem_guvenlik` **is** real, computed from Vs30 + ilçe damage
ratio (see the script's docstring).

Fix specific records by hand via `data-pipeline/data/manual_overrides.json`
(see `data-pipeline/data/MANUAL_OVERRIDES.md`) instead of editing the
generated file directly — reruns of the script would overwrite hand edits
otherwise.

To regenerate it after touching the pipeline inputs:

```bash
cd data-pipeline && python scripts/07_enrich_mahalle_features.py
cd ../backend && uvicorn app.main:app --reload   # picks it up automatically
```

Once the POI/transit pipeline (Faz 1, rest of §8 in `CLAUDE.md`) is wired up,
rerun `07_enrich_mahalle_features.py` and the placeholder criteria above
become real.

## mahalle_features.json — old 16-entry hand-curated placeholder

Kept for reference / as a quick fallback (e.g. to sanity-check the scoring
engine against a small, fully hand-written dataset). Not loaded by default
anymore. To use it instead:

```bash
FEATURES_PATH=app/data/mahalle_features.json uvicorn app.main:app --reload
```

Each array entry is one neighborhood (mahalle). Both files share this shape:

```json
{
  "mahalle_id": "IST-0017",
  "mahalle_adi": "Örnek Mahalle",
  "ilce": "Örnek İlçe",
  "geometry": { "type": "Polygon", "coordinates": [[[lon, lat], ...]] },
  "scores": {
    "deprem_guvenlik": 0-100,
    "saglik": 0-100,
    "egitim": 0-100,
    "ulasim": 0-100,
    "ulasim_hizli": 0-100,
    "sosyal_yasam": 0-100,
    "yasam_kalitesi": 0-100
  },
  "raw": { "hastane_count": 0, "okul_count": 0, "cami_count": 0, "toplanma_count": 0 },
  "avg_m2_fiyat": 0
}
```

Notes:
- `deprem_guvenlik` in `mahalle_features.json`: higher = safer. Values here
  are illustrative, loosely informed by known soil/liquefaction risk
  patterns — **not verified against AFAD/İBB data**, unlike
  `mahalle_features_full.json`'s Vs30/İBB-derived score.
- `ulasim_hizli`: metro/metrobüs/Marmaray-only transit score, used instead of
  `ulasim` for `ofis`/`hibrit` work types (see `scoring/scorer.py`).
- `FEATURES_PATH` env var can point the backend at any other file without
  code changes (see `services/recommendation_service.py`).
