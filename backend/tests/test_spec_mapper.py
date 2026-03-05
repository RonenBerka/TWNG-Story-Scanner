"""Tests for spec_mapper — Scanner specs → TWNG instruments.specs keys."""

from app.export.spec_mapper import map_specs


# -- The seed data Fender Stratocaster 1970 has rich specs --
SCANNER_SPECS_STRAT = {
    "body_shape": "Offset Double-Cutaway Solidbody",
    "body_type": "Solidbody Electric",
    "body": "Alder",
    "neck_material": "1-piece Maple",
    "neck_joint": "Bolt-on (4-bolt)",
    "neck_profile": "1969 U shape",
    "fingerboard": "Rosewood veneer",
    "scale_length_inches": 25.5,
    "scale_length_mm": 648,
    "nut_width_inches": 1.625,
    "nut_width_mm": 41.3,
    "frets": 21,
    "fret_size": "Small vintage",
    "fingerboard_radius_inches": 7.25,
    "bridge": "Synchronized tremolo, 2-piece steel block",
    "saddles": "6 pressed-steel (patent pending)",
    "tuners": "Fender F-stamped vintage",
    "pickups": "3x Grey-bobbin single-coil, staggered alnico magnets",
    "switching": "3-way (original)",
    "controls": "Master Volume, Tone 1 (neck), Tone 2 (middle)",
    "headstock": "Large (CBS-era)",
    "string_trees": 1,
    "pickguard": "3-ply white with pearloid backing",
    "truss_rod": "Heel-adjust (vintage style)",
    "weight_lbs_typical": "7.5-8.0",
}


def test_core_keys_mapped():
    """Core TWNG spec keys must be populated from Scanner data."""
    result = map_specs(SCANNER_SPECS_STRAT, finish="3-Tone Sunburst")

    assert result["specs"]["body_material"] == "Alder"
    assert result["specs"]["neck_material"] == "1-piece Maple"
    assert result["specs"]["fretboard"] == "Rosewood veneer"
    assert result["specs"]["num_frets"] == 21
    assert result["specs"]["scale_length"] == "25.5 in"
    assert result["specs"]["pickups"] == "3x Grey-bobbin single-coil, staggered alnico magnets"
    assert result["specs"]["bridge"] == "Synchronized tremolo, 2-piece steel block"
    assert result["specs"]["finish"] == "3-Tone Sunburst"
    assert result["specs"]["tuners"] == "Fender F-stamped vintage"
    assert result["specs"]["controls"] == "Master Volume, Tone 1 (neck), Tone 2 (middle)"


def test_neck_profile_mapped():
    result = map_specs(SCANNER_SPECS_STRAT, finish="Sunburst")
    assert result["specs"]["neck_profile"] == "1969 U shape"


def test_scale_length_formatted_as_string():
    """TWNG stores scale_length as '25.5 in' string."""
    result = map_specs({"scale_length_inches": 24.75}, finish=None)
    assert result["specs"]["scale_length"] == "24.75 in"


def test_overflow_to_extended_specs():
    """Fields not in TWNG core spec keys go to extended_specs."""
    result = map_specs(SCANNER_SPECS_STRAT, finish="Sunburst")
    ext = result["extended_specs"]

    assert ext["body_shape"] == "Offset Double-Cutaway Solidbody"
    assert ext["body_type"] == "Solidbody Electric"
    assert ext["neck_joint"] == "Bolt-on (4-bolt)"
    assert ext["fingerboard_radius_inches"] == 7.25
    assert ext["nut_width_mm"] == 41.3
    assert ext["saddles"] == "6 pressed-steel (patent pending)"
    assert ext["headstock"] == "Large (CBS-era)"


def test_empty_specs():
    """Empty specs should not crash."""
    result = map_specs({}, finish=None)
    assert result["specs"] == {}
    assert result["extended_specs"] == {}


def test_none_specs():
    """None specs should not crash."""
    result = map_specs(None, finish=None)
    assert result["specs"] == {}
    assert result["extended_specs"] == {}


def test_finish_from_root_only():
    """When Scanner specs have no finish but root finish exists."""
    result = map_specs({"body": "Mahogany"}, finish="Cherry Sunburst")
    assert result["specs"]["finish"] == "Cherry Sunburst"
    assert result["specs"]["body_material"] == "Mahogany"
