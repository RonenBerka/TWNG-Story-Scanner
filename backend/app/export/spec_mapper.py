"""Map Scanner extraction specs to TWNG instruments.specs keys.

TWNG instruments.specs uses these core keys (from production data):
  body_material, neck_material, fretboard, num_frets, scale_length,
  pickups, bridge, finish, tuners, controls, neck_profile, color,
  top_material, fretboard_material, pickup_config, bridge_type,
  hardware_finish, neck, body, frets, nut_material, other

Scanner specs have ~30 keys, many of which map directly.
Fields that don't map go to extended_specs (for custom_fields).
"""

# Scanner key → TWNG spec key
_CORE_MAP: dict[str, str] = {
    "body": "body_material",
    "body_material": "body_material",
    "top": "top_material",
    "neck_material": "neck_material",
    "neck_profile": "neck_profile",
    "fingerboard": "fretboard",
    "frets": "num_frets",
    "pickups": "pickups",
    "bridge": "bridge",
    "tuners": "tuners",
    "controls": "controls",
}

# Scanner keys that go to extended_specs (not in TWNG core)
_OVERFLOW_KEYS: set[str] = {
    "body_shape",
    "body_type",
    "back_sides",
    "bracing",
    "neck_joint",
    "fingerboard_radius_inches",
    "scale_length_mm",
    "nut_width_inches",
    "nut_width_mm",
    "fret_size",
    "saddles",
    "switching",
    "electronics",
    "headstock",
    "string_trees",
    "pickguard",
    "truss_rod",
    "neck_plate",
    "inlays",
    "weight_kg",
    "weight_lbs",
    "weight_lbs_typical",
    "finish_type",
    "knobs",
}


def map_specs(
    scanner_specs: dict | None,
    finish: str | None,
) -> dict:
    """Transform Scanner specs into TWNG format.

    Returns:
        {
            "specs": { ... TWNG core keys ... },
            "extended_specs": { ... overflow keys ... },
        }
    """
    if not scanner_specs:
        specs: dict = {}
        if finish:
            specs["finish"] = finish
        return {"specs": specs, "extended_specs": {}}

    twng_specs: dict = {}
    extended: dict = {}

    for key, value in scanner_specs.items():
        if value is None:
            continue

        if key in _CORE_MAP:
            twng_key = _CORE_MAP[key]
            # Don't overwrite if already set (first match wins)
            if twng_key not in twng_specs:
                twng_specs[twng_key] = value
        elif key == "scale_length_inches":
            twng_specs["scale_length"] = f"{value} in"
        elif key in _OVERFLOW_KEYS:
            extended[key] = value
        else:
            # Unknown keys also go to extended
            extended[key] = value

    # finish from root-level field
    if finish and "finish" not in twng_specs:
        twng_specs["finish"] = finish

    return {"specs": twng_specs, "extended_specs": extended}
