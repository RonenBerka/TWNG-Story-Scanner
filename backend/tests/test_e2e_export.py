"""End-to-end test: load seed_viewer_data.json → export → validate TWNG schema."""

import json
from pathlib import Path

from app.export.twng_mapper import build_twng_export

SEED_PATH = Path(__file__).resolve().parent.parent / "seed_viewer_data.json"

# TWNG enum whitelists (from Supabase production)
VALID_TIERS = {"system_generated", "user_reported_fact", "story_based", "verified_luthier"}
VALID_EVENT_TYPES = {
    "system_introduced", "system_ownership_transfer",
    "user_manufacture_date", "user_acquisition_date", "user_modification",
    "story", "luthier_event",
}
VALID_STATUSES = {"draft", "soft", "hard", "pending_verification", "verified", "archived"}
VALID_SPEC_KEYS = {
    "body_material", "neck_material", "fretboard", "num_frets", "scale_length",
    "pickups", "bridge", "finish", "tuners", "controls", "neck_profile",
    "top_material",
}


def _load_seed_guitars() -> list[dict]:
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["guitars"]


def test_seed_data_exists():
    assert SEED_PATH.exists(), f"seed file not found: {SEED_PATH}"


def test_export_all_seed_guitars():
    guitars = _load_seed_guitars()
    assert len(guitars) > 0, "No guitars in seed data"

    export = build_twng_export(guitars)
    assert export["twng_import_version"] == "1.0"
    assert export["total_items"] == len(guitars)
    assert export["source"] == "TWNG Story Scanner"


def test_every_item_has_required_fields():
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        assert "instrument" in item, f"Item {i} missing instrument"
        assert "owner_contact" in item, f"Item {i} missing owner_contact"
        assert "tags" in item, f"Item {i} missing tags"
        assert "timeline_events" in item, f"Item {i} missing timeline_events"
        assert "source_metadata" in item, f"Item {i} missing source_metadata"
        assert "completeness" in item, f"Item {i} missing completeness"


def test_instrument_specs_only_use_valid_keys():
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        specs = item["instrument"]["specs"]
        for key in specs:
            assert key in VALID_SPEC_KEYS, f"Item {i} has invalid spec key: {key}"


def test_timeline_events_use_valid_enums():
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        for j, ev in enumerate(item["timeline_events"]):
            assert ev["tier"] in VALID_TIERS, f"Item {i} event {j}: invalid tier '{ev['tier']}'"
            assert ev["event_type"] in VALID_EVENT_TYPES, f"Item {i} event {j}: invalid event_type '{ev['event_type']}'"
            assert ev["status"] in VALID_STATUSES, f"Item {i} event {j}: invalid status '{ev['status']}'"
            # date_precision, location, source must be in event_data, NOT top level
            assert "date_precision" not in ev or "event_data" in ev, f"Item {i} event {j}: date_precision should be in event_data"


def test_tags_structure():
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        tags = item["tags"]
        assert "matched" in tags, f"Item {i}: tags missing 'matched'"
        assert "new_tags" in tags, f"Item {i}: tags missing 'new_tags'"
        assert isinstance(tags["matched"], list)
        assert isinstance(tags["new_tags"], list)


def test_completeness_scores_are_valid():
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        c = item["completeness"]
        assert 0.0 <= c["score"] <= 1.0, f"Item {i}: score {c['score']} out of range"
        assert isinstance(c["missing_fields"], list)
        assert isinstance(c["warnings"], list)


def test_no_none_in_spec_values():
    """Spec values should not be None — missing keys should be absent entirely."""
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    for i, item in enumerate(export["items"]):
        for k, v in item["instrument"]["specs"].items():
            assert v is not None, f"Item {i}: spec '{k}' is None (should be absent)"


def test_export_json_serializable():
    """The entire export must be JSON-serializable (no datetime objects etc)."""
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)
    # This will raise TypeError if anything is not serializable
    json_str = json.dumps(export, ensure_ascii=False)
    assert len(json_str) > 100


def test_print_export_summary():
    """Not a real assertion — prints a human-readable summary for review."""
    guitars = _load_seed_guitars()
    export = build_twng_export(guitars)

    print(f"\n{'='*60}")
    print(f"TWNG Export Summary")
    print(f"{'='*60}")
    print(f"Total items: {export['total_items']}")

    for i, item in enumerate(export["items"]):
        inst = item["instrument"]
        c = item["completeness"]
        print(f"\n  [{i+1}] {inst['make']} {inst['model']} ({inst['year']})")
        print(f"      Type: {inst['custom_fields']['instrument_type']}")
        print(f"      Specs: {list(inst['specs'].keys())}")
        print(f"      Tags matched: {item['tags']['matched']}")
        print(f"      Tags new: {item['tags']['new_tags']}")
        print(f"      Timeline events: {len(item['timeline_events'])}")
        print(f"      Owner: {item['owner_contact']['source_username'] or 'N/A'}")
        print(f"      Image: {'Yes' if inst['main_image_url'] else 'No'}")
        print(f"      Completeness: {c['score']:.0%}")
        if c["missing_fields"]:
            print(f"      Missing: {c['missing_fields']}")
        if c["warnings"]:
            print(f"      Warnings: {c['warnings']}")

    print(f"\n{'='*60}")
