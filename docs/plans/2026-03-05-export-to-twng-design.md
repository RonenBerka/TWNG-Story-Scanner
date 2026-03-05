# Stage 3.5 — Export to TWNG Design Document

**Date:** 2026-03-05
**Goal:** After the Viewer stage, export approved stories as a JSON file compatible with TWNG.com's Supabase schema, enabling direct import into the existing claim workflow.
**Architecture:** New backend export service + API endpoint + CLI command + Viewer UI button

---

## 1. Overview

The Scanner currently ends at Stage 3 (Viewer). This design adds **Stage 3.5 — Export to TWNG**, which transforms Scanner extraction data into a JSON format that maps directly to TWNG.com's Supabase tables.

### Flow
```
Stage 3 (Viewer) → Admin selects stories → Export to TWNG JSON → Import at twng.com
```

### Decisions
- **Trigger:** Viewer button (interactive) + CLI command (automation)
- **Incomplete data:** Export with `completeness_score` + `missing_fields` array
- **ID assignment:** TWNG.com assigns UUIDs on import (same as users)

---

## 2. TWNG.com Supabase Schema Reference

### 2.1 Relevant enums (exact values from PostgreSQL)

**`instrument_type` enum:**
`electric_guitar` | `acoustic_guitar` | `classical_guitar` | `bass_guitar` | `electric_bass` | `acoustic_bass` | `mandolin` | `banjo` | `ukulele` | `other`

**`timeline_tier` enum:**
`system_generated` | `user_reported_fact` | `story_based` | `verified_luthier`

**`timeline_event_type` enum:**
`system_introduced` | `system_ownership_transfer` | `user_manufacture_date` | `user_acquisition_date` | `user_modification` | `story` | `luthier_event`

**`timeline_status` enum:**
`draft` | `soft` | `hard` | `pending_verification` | `verified` | `archived`

### 2.2 `instruments` table columns

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | gen_random_uuid() — assigned by TWNG on import |
| `current_owner_id` | uuid (nullable) | FK to users — set after claim |
| `uploader_id` | uuid | FK to users — the admin who imports |
| `make` | text (nullable) | Brand name |
| `model` | text (nullable) | Model name |
| `year` | integer (nullable) | Year of manufacture |
| `serial_number` | text (nullable) | Serial number |
| `description` | text (nullable) | Story/narrative text |
| `main_image_url` | text (nullable) | Primary image URL |
| `moderation_status` | text | default `'pending'` |
| `specs` | jsonb | default `'{}'` — instrument specifications |
| `custom_fields` | jsonb | default `'{}'` — overflow/extra data |
| `is_for_sale` | boolean | default `false` |
| `created_at` | timestamptz | auto |
| `updated_at` | timestamptz | auto |

**NOTE:** `instruments` table has NO `instrument_type` column. The enum exists in PostgreSQL but is not used as a column. Export places instrument type in `custom_fields.instrument_type` using the exact enum values.

### 2.3 `instruments.specs` — actual keys used in production data

From real instrument records in TWNG:

| Key | Example value |
|---|---|
| `body_material` | `"Alder"`, `"Ash"`, `"Mahogany with Maple Cap"` |
| `neck_material` | `"Maple"`, `"Mahogany"` |
| `fretboard` | `"Rosewood"`, `"Maple"`, `"Ebony"` |
| `num_frets` | `21`, `22`, `24` |
| `scale_length` | `"25.5 in"`, `"24.75 in"` |
| `pickups` | `"3x Single Coil"`, `"2x PAF Humbucker"` |
| `bridge` | `"Synchronized Tremolo"`, `"ABR-1 Tune-o-matic"` |
| `finish` | `"Olympic White"`, `"Cherry Sunburst"` |

Additional keys observed across some records (used when applicable):
`bridge_type`, `body`, `color`, `controls`, `fretboard_material`, `frets`, `hardware_finish`, `neck`, `neck_profile`, `nut_material`, `other`, `pickup_config`, `top_material`, `tuners`

### 2.4 `timeline_events` table columns

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | gen_random_uuid() — assigned by TWNG |
| `instrument_id` | uuid | FK to instruments |
| `event_timestamp` | timestamptz | **Required** — the date of the event |
| `created_by_user_id` | uuid | **Required** — the admin/user who creates it |
| `creator_id` | uuid (nullable) | |
| `original_owner_id` | uuid (nullable) | |
| `tier` | `timeline_tier` enum | **Required** |
| `event_type` | `timeline_event_type` enum | **Required** |
| `title` | text (nullable) | Event title |
| `description` | text (nullable) | Event description |
| `event_data` | jsonb (nullable) | Extra structured data (date_precision, location, source, etc.) |
| `status` | `timeline_status` enum | default `'draft'` |
| `visible_to_owners` | boolean | default `true` |
| `visible_publicly` | boolean | default `true` |
| `transferable` | boolean | default `true` |
| `is_verified` | boolean | default `false` |
| `is_locked` | boolean | default `false` |

**NOTE:** `date_precision`, `location`, and `source` are NOT columns — they go into `event_data` jsonb.

### 2.5 `users` table columns (relevant for owner contact)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Comes from Supabase Auth |
| `username` | text (nullable) | |
| `display_name` | varchar (nullable) | |
| `email` | varchar (nullable) | |
| `location` | varchar (nullable) | |
| `social_links` | jsonb | default `'{}'` — facebook, reddit, etc. |
| `role` | varchar | default `'user'` |

### 2.6 `ownership_claims` table columns

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | gen_random_uuid() |
| `instrument_id` | uuid (nullable) | FK to instruments |
| `claimer_id` | uuid (nullable) | FK to users |
| `status` | text | default `'pending'` |
| `proof_description` | text (nullable) | Claim justification |
| `proof_images` | text[] (nullable) | Array of image URLs |
| `reviewed_by` | uuid (nullable) | |
| `reviewed_at` | timestamptz (nullable) | |
| `rejection_reason` | text (nullable) | |

### 2.7 `tags` table + `instrument_tags` (many-to-many)

**`tags` table:**
`id` (uuid), `name` (text), `slug` (text), `description` (text nullable), `usage_count` (integer, default 0)

**`instrument_tags` table:**
`id` (uuid), `instrument_id` (uuid FK), `tag_id` (uuid FK)

**NOTE:** `tags` table is currently empty (0 rows). Tags in `guitar_catalog` are stored as jsonb arrays. The export should provide tag slugs that match `guitar_catalog` conventions for future use when `tags` table is populated.

### 2.8 `guitar_catalog` — tag taxonomy reference (250+ slugs)

Tags from `guitar_catalog.tags` (jsonb arrays), used as the canonical tag vocabulary:

- **Brand:** `fender`, `gibson`, `ovation`, `g&l`, `schecter`, `suhr`, `takamine`, `yamaha`, `cordoba`, `breedlove`, `eastman`...
- **Type/Body:** `electric`, `acoustic`, `bass`, `classical`, `semi-hollow`, `solid-body`, `dreadnought`, `jumbo`, `parlor`, `auditorium`, `offset`...
- **Pickup/Electronics:** `active`, `passive`, `humbucking`, `humcancelling`, `single-coil`, `p-90`, `P90`, `piezo`, `HSS`, `HSH`, `HS`...
- **Hardware:** `Floyd-Rose`, `Floyd Rose`, `tremolo`, `wraparound`, `double-locking`, `evertune`...
- **Origin:** `usa`, `USA`, `japan`, `Japan`, `korea`, `indonesia`, `mexico`, `canada`, `germany`, `czech`...
- **Era/Style:** `vintage`, `Vintage`, `modern`, `Modern`, `boutique`, `Boutique`, `custom-shop`, `Custom Shop`, `limited-edition`, `Limited Edition`, `reissue`, `Reissue`, `70s`, `1980s`...
- **Genre:** `Jazz`, `Metal`, `Blues`, `Rock`, `Country`, `Funk`, `Surf`, `Punk`, `Rockabilly`, `Progressive`...
- **Price tier:** `budget`, `Budget`, `mid-range`, `Mid-Range`, `premium`, `Premium`, `high-end`, `ultra-premium`, `Luxury`...
- **Feature:** `cutaway`, `Cutaway`, `headless`, `baritone`, `7-string`, `7-String`, `12-String`, `extended-range`, `multiscale`, `short-scale`...
- **Material:** `mahogany`, `ebony`, `rosewood`, `spruce`, `cedar`, `flame-maple`, `carbon-fiber`...
- **Signature/Special:** `signature`, `Signature`, `artist-signature`, `iconic`, `Iconic`, `rare`, `Collectible`...

**NOTE:** Tag casing is inconsistent in `guitar_catalog` (e.g., `vintage` AND `Vintage`). The export should lowercase-normalize all tags.

---

## 3. Field Mapping: Scanner → TWNG Export JSON

### 3.1 Instrument mapping

| Scanner field | TWNG JSON key | Target table.column | Transform |
|---|---|---|---|
| `brand` | `instrument.make` | `instruments.make` | Direct (rename) |
| `model` | `instrument.model` | `instruments.model` | Direct |
| `year_exact` | `instrument.year` | `instruments.year` | Use `year_exact` (integer) when available; else parse `year` string |
| `serial_number` | `instrument.serial_number` | `instruments.serial_number` | Direct |
| `story.narrative` | `instrument.description` | `instruments.description` | Direct |
| `images[0].url` (is_main=true) | `instrument.main_image_url` | `instruments.main_image_url` | **Currently null — needs Ingest fix** |
| `instrument_type` | `instrument.custom_fields.instrument_type` | `instruments.custom_fields` | Map to enum: see below |
| mapped specs | `instrument.specs` | `instruments.specs` | Map to TWNG keys: see below |
| overflow data | `instrument.custom_fields` | `instruments.custom_fields` | Confidence, dedup, estimated value |

### 3.2 Instrument Type mapping (Scanner → TWNG enum)

| Scanner `instrument_type` | TWNG `instrument_type` enum value | Extra tag to add |
|---|---|---|
| `electric_guitar` | `electric_guitar` | — |
| `acoustic_guitar` | `acoustic_guitar` | — |
| `acoustic_electric_guitar` | `acoustic_guitar` | `electro-acoustic` |
| `classical_guitar` | `classical_guitar` | — |
| `bass_guitar` | `bass_guitar` | — |
| `electric_bass` | `electric_bass` | — |
| (any unknown) | `other` | — |

### 3.3 Specs mapping (Scanner → TWNG `instruments.specs`)

| TWNG spec key | Scanner source | Transform |
|---|---|---|
| `body_material` | `specs.body` | Direct |
| `top_material` | `specs.top` | Direct |
| `neck_material` | `specs.neck_material` | Direct |
| `neck_profile` | `specs.neck_profile` | Direct |
| `fretboard` | `specs.fingerboard` | Direct (rename) |
| `num_frets` | `specs.frets` | Direct (rename) |
| `scale_length` | `specs.scale_length_inches` | Format: `"{value} in"` |
| `pickups` | `specs.pickups` | Direct |
| `bridge` | `specs.bridge` | Direct |
| `finish` | root `finish` or `specs.finish_type` | Direct |
| `tuners` | `specs.tuners` | Direct |
| `controls` | `specs.controls` | Direct |
| `color` | root `finish` | Same as finish for now |

Remaining Scanner spec fields (body_shape, body_type, back_sides, bracing, neck_joint, fingerboard_radius, nut_width, weight, saddles, electronics, etc.) → packed into `instrument.custom_fields.extended_specs` as a flat object.

### 3.4 Owner Contact mapping

| JSON field | Source | Maps to TWNG |
|---|---|---|
| `source_platform` | `CandidateStory.source_type` | `users.social_links.{platform}` |
| `source_username` | **NEW — from Ingest** | `users.username` (candidate) |
| `source_profile_url` | **NEW — from Ingest** | `users.social_links.{platform}_url` |
| `source_post_url` | `CandidateStory.source_url` | for `outreach_log` / `ownership_claims.proof_description` |
| `display_name` | From extraction | `users.display_name` |
| `email` | From extraction (rare) | `users.email` |

### 3.5 Tags mapping

1. Lowercase-normalize all Scanner tags
2. Match against `guitar_catalog` tag slugs (lowercase-normalized)
3. Split into `matched` (existing in TWNG) and `new_tags` (need admin review)
4. Add extra tags from instrument_type mapping (e.g., `electro-acoustic`)

### 3.6 Timeline Events mapping

| Scanner field | TWNG JSON field | Target column | Transform |
|---|---|---|---|
| `tier` | `tier` | `timeline_events.tier` | Map: `factual`→`user_reported_fact`, `documented`→`user_reported_fact`, `story_based`→`story_based`, `system`→`system_generated` |
| `event_type` | `event_type` | `timeline_events.event_type` | Map: `manufacture`→`user_manufacture_date`, `acquisition`→`user_acquisition_date`, `performance`→`story`, `milestone`→`story`, `transfer`→`system_ownership_transfer`, `provenance`→`story`, `search_active`→`system_introduced` |
| `title` | `title` | `timeline_events.title` | Direct |
| `description` | `description` | `timeline_events.description` | Direct |
| `event_date` | `event_timestamp` | `timeline_events.event_timestamp` | Parse to ISO 8601 timestamptz |
| `date_precision` | `event_data.date_precision` | `timeline_events.event_data` (jsonb) | Into event_data |
| `location` | `event_data.location` | `timeline_events.event_data` (jsonb) | Into event_data |
| `source` | `event_data.source` | `timeline_events.event_data` (jsonb) | Into event_data |

**Default values for new timeline events:**
- `status`: `draft`
- `visible_to_owners`: `true`
- `visible_publicly`: `true`
- `transferable`: `true`
- `is_verified`: `false`
- `is_locked`: `false`

---

## 4. Completeness Scoring

Each exported item gets a `completeness` block:

```json
"completeness": {
  "score": 0.65,
  "missing_fields": ["owner_contact.source_username", "instrument.main_image_url"],
  "warnings": ["year is approximate (decade), not exact integer"]
}
```

**Scoring weights:**
- `owner_contact.source_username` or `source_profile_url` present: 30%
- `instrument.main_image_url` present: 25%
- `instrument.make` + `instrument.model` present: 20%
- `instrument.year` is exact integer: 10%
- At least 1 timeline event: 10%
- At least 1 matched tag: 5%

---

## 5. Export JSON Schema (complete example)

```json
{
  "twng_import_version": "1.0",
  "exported_at": "2026-03-05T12:00:00Z",
  "source": "TWNG Story Scanner",
  "total_items": 1,
  "items": [
    {
      "instrument": {
        "make": "Fender",
        "model": "Stratocaster",
        "year": 1970,
        "serial_number": null,
        "description": "A father who grew up playing Hofner and Eko guitars — European brands that were within reach — but never a Fender. Fender was only for the rich. During a posting in France, he decided his 8-year-old son should learn guitar. The teacher spotted this 1970 Stratocaster and was mesmerized. The father immediately pulled out cash — fulfilling his own dream through his son. 29 years later, every scratch, every ding is real.",
        "main_image_url": "https://i.redd.it/abc123.jpg",
        "specs": {
          "body_material": "Alder",
          "neck_material": "1-piece Maple",
          "neck_profile": "1969 U shape",
          "fretboard": "Rosewood veneer",
          "num_frets": 21,
          "scale_length": "25.5 in",
          "pickups": "3x Grey-bobbin single-coil, staggered alnico magnets",
          "bridge": "Synchronized tremolo, 2-piece steel block",
          "finish": "3-Tone Sunburst",
          "tuners": "Fender F-stamped vintage",
          "controls": "Master Volume, Tone 1 (neck), Tone 2 (middle)"
        },
        "custom_fields": {
          "instrument_type": "electric_guitar",
          "extended_specs": {
            "body_shape": "Offset Double-Cutaway Solidbody",
            "body_type": "Solidbody Electric",
            "neck_joint": "Bolt-on (4-bolt)",
            "fingerboard_radius_inches": 7.25,
            "nut_width_mm": 41.3,
            "fret_size": "Small vintage",
            "saddles": "6 pressed-steel (patent pending)",
            "headstock": "Large (CBS-era)",
            "string_trees": 1,
            "pickguard": "3-ply white with pearloid backing",
            "truss_rod": "Heel-adjust (vintage style)"
          },
          "scanner_extraction_confidence": {
            "brand_model": "high",
            "year": "high",
            "finish": "high",
            "specs": "high",
            "story": "high"
          },
          "dedup_fingerprint": "fender|stratocaster|1970",
          "estimated_value_range_usd": null
        }
      },

      "owner_contact": {
        "source_platform": "facebook",
        "source_username": null,
        "source_profile_url": null,
        "source_post_url": "https://facebook.com/groups/guitars/posts/123456",
        "display_name": null,
        "email": null
      },

      "tags": {
        "matched": [
          "fender", "stratocaster", "vintage", "usa",
          "electric", "single-coil", "70s"
        ],
        "new_tags": [
          "29-years-owned", "first-guitar", "purchased-in-france",
          "not-relic", "all-original"
        ]
      },

      "timeline_events": [
        {
          "tier": "user_reported_fact",
          "event_type": "user_manufacture_date",
          "title": "Manufactured — Fender, Fullerton, 1970",
          "description": "Last year of the 4-bolt neck plate, original synchronized tremolo with steel saddles, and heel-adjust truss rod.",
          "event_timestamp": "1970-01-01T00:00:00Z",
          "event_data": {
            "date_precision": "year",
            "location": "Fullerton, California, USA",
            "source": "Model specifications and Fender production records"
          },
          "status": "draft",
          "visible_to_owners": true,
          "visible_publicly": true,
          "transferable": true,
          "is_verified": false,
          "is_locked": false
        },
        {
          "tier": "story_based",
          "event_type": "user_acquisition_date",
          "title": "Father buys Strat for his 8-year-old son — France",
          "description": "While on a posting in France, the owner's father went searching with his son's first guitar teacher. At a second-hand shop, the teacher spotted this 1970 Stratocaster. The father pulled out cash on the spot.",
          "event_timestamp": "1997-01-01T00:00:00Z",
          "event_data": {
            "date_precision": "year",
            "location": "France",
            "source": "Owner's Facebook post (Hebrew)"
          },
          "status": "draft",
          "visible_to_owners": true,
          "visible_publicly": true,
          "transferable": true,
          "is_verified": false,
          "is_locked": false
        },
        {
          "tier": "story_based",
          "event_type": "story",
          "title": "29 years of continuous ownership — primary guitar",
          "description": "The guitar has been with the owner since age 8 and remains his number one instrument. Every scratch and ding is genuine — not relic.",
          "event_timestamp": "2026-01-01T00:00:00Z",
          "event_data": {
            "date_precision": "year",
            "location": "Israel",
            "source": "Owner's Facebook post (Hebrew)"
          },
          "status": "draft",
          "visible_to_owners": true,
          "visible_publicly": true,
          "transferable": true,
          "is_verified": false,
          "is_locked": false
        }
      ],

      "source_metadata": {
        "scanner_record_id": "uuid-from-scanner-db",
        "source_url": "https://facebook.com/groups/guitars/posts/123456",
        "source_platform": "facebook",
        "original_language": "Hebrew",
        "story_score": 8.5,
        "extraction_date": "2026-03-05"
      },

      "completeness": {
        "score": 0.40,
        "missing_fields": [
          "owner_contact.source_username",
          "owner_contact.source_profile_url",
          "instrument.main_image_url"
        ],
        "warnings": [
          "Owner identification incomplete — only source_post_url available"
        ]
      }
    }
  ]
}
```

---

## 6. Implementation Scope

### 6.1 Backend — New files

| File | Purpose |
|---|---|
| `backend/app/export/__init__.py` | Package init |
| `backend/app/export/twng_mapper.py` | Core mapping: Scanner extraction → TWNG JSON |
| `backend/app/export/spec_mapper.py` | Specs key mapping with overflow to custom_fields |
| `backend/app/export/tag_normalizer.py` | Tag normalization against guitar_catalog slugs |
| `backend/app/export/timeline_mapper.py` | Timeline tier/event_type enum mapping + event_data packing |
| `backend/app/export/completeness.py` | Completeness scoring |
| `backend/app/api/routes/export.py` | API endpoint: `GET /records/export-twng` |

### 6.2 Backend — Modified files

| File | Change |
|---|---|
| `backend/app/main.py` | Register export router |
| `backend/app/cli.py` | Add `export-twng` CLI command |
| `Makefile` | Add `make export-twng` target |

### 6.3 Ingest prerequisite changes

| File | Change |
|---|---|
| `backend/app/collectors/reddit_collector.py` | Capture `author`, `author_fullname`, image URLs from Reddit API response |
| `backend/app/db/models.py` | Add `author_username` (text), `author_profile_url` (text), `image_urls` (ARRAY text) to `CandidateStory` |
| New Alembic migration | Add columns to `candidate_stories` table |

### 6.4 Frontend changes

| File | Change |
|---|---|
| `frontend/src/pages/Viewer.tsx` | Add "Export to TWNG" button in header |
| `frontend/src/lib/api.ts` | Add `exportToTWNG()` API call |

### 6.5 Tests

| File | Covers |
|---|---|
| `backend/tests/test_twng_mapper.py` | Field mapping, instrument_type mapping |
| `backend/tests/test_spec_mapper.py` | Spec key mapping, overflow handling |
| `backend/tests/test_tag_normalizer.py` | Tag normalization, matched vs new_tags split |
| `backend/tests/test_timeline_mapper.py` | Tier/event_type enum mapping, event_data packing |
| `backend/tests/test_completeness.py` | Scoring logic |
| `backend/tests/test_export_endpoint.py` | API endpoint integration |

---

## 7. Out of scope (for now)

- Direct API push to TWNG.com Supabase (currently file-based export only)
- Automatic user creation in TWNG
- Image downloading/re-hosting (we pass original source URLs)
- Facebook author identification (depends on Facebook API access)
- Populating `tags` table (currently empty in TWNG — export provides slugs for future use)
- `ownership_claims` creation (handled by TWNG admin after import)
