"""Normalize Scanner tags to TWNG guitar_catalog slug taxonomy.

The canonical tag list comes from guitar_catalog.tags (250+ slugs).
We lowercase-normalize everything and check membership.
Known aliases (Scanner → TWNG) are mapped before matching.
"""

# ---- Canonical TWNG tags (lowercase-normalized from guitar_catalog) ----
# This is the full set extracted from SELECT DISTINCT tag FROM guitar_catalog.
_TWNG_TAGS_RAW: set[str] = {
    "12-string", "1980s", "1988-1998", "1989-1998", "24-scale", "3/4 size",
    "30-scale", "44-01", "44-64", "5-string", "55-02", "55-94", "7-string",
    "70s", "abz", "ac/dc", "acoustic", "acoustic-electric", "active",
    "active electronics", "active pickups", "adamas", "afterburner", "alhambra",
    "alternative", "alvarez", "american", "applause", "artist",
    "artist-signature", "auditorium", "balladeer", "baritone", "bass",
    "beginner", "bluegrass", "blues", "bolt-on", "boutique", "breedlove",
    "budget", "by-gibson", "cabronita", "canada", "canadian", "carbon-fiber",
    "cedar", "chambered", "china", "classic", "classical", "coastline",
    "collectible", "combustion", "concert", "cordoba", "corvette", "country",
    "custom", "custom shop", "custom-shop", "cutaway", "czech", "d-roc",
    "dave-grohl", "dingwall", "distressed", "double-locking", "dreadnought",
    "duo-sonic", "eastman", "ebony", "ebony-fretboard", "eco-friendly",
    "electric", "electro-acoustic", "electro-classical", "elite", "emperor",
    "entourage", "entry-level", "es-335", "es-335-copy", "es-les-paul",
    "euro", "evertune", "express", "extended-range", "fender-style",
    "fingerstyle", "flagship", "flame-maple", "flamenco", "florentine",
    "floyd rose", "floyd-rose", "flying-v", "fodera", "folk", "funk",
    "fusion", "g-writer", "g&l", "generation", "germany", "gibson-license",
    "glen-campbell", "golden era", "grand auditorium", "handmade",
    "headless", "hg-neck", "high-end", "high-performance", "high-tech",
    "hollow body", "hs", "hsh", "hss", "humbucker", "humbuckers",
    "humbucking", "humcancelling", "hybrid", "iconic", "iconic shape",
    "imperial", "indie", "indonesia", "jaguar", "japan", "japan-made",
    "japanese", "jazz", "jazz-bass", "jazz-rock", "jazz-style", "jazzmaster",
    "jb", "jumbo", "korea", "kremona", "l-1", "l-2000", "lakland",
    "larrivee", "lattice-bracing", "lawsuit-era", "lead", "legend",
    "les-paul", "les-paul-custom", "les-paul-custom-copy", "les-paul-copy",
    "les-paul-style", "limited", "limited edition", "limited-edition",
    "luxury", "madrid", "mahogany", "malibu", "master", "melody-maker",
    "metal", "metro", "mexico", "mid-range", "midtown", "mini",
    "mini-jumbo", "mint-green", "modern", "modern-metal", "momentum",
    "monarch", "mosaic", "multiscale", "mustang", "mustang-bass",
    "nashville", "neck-through", "ng3", "norlin era", "ns-2", "nyc",
    "nylon-strings", "offset", "offset-body", "om-body", "orchestra",
    "orchestra model", "ovation", "p-90", "p/j", "p90", "parlor",
    "partnership", "passive", "performer", "piezo", "player", "player-plus",
    "pop", "premium", "professional", "progressive", "punk", "qit",
    "ramirez", "rare", "rd", "reissue", "rock", "rockabilly", "rockbass",
    "rosewood", "roundback", "rustic", "s6-classic", "sadowsky", "sb-2",
    "schecter", "seagull", "select", "semi-acoustic", "semi-hollow",
    "set-neck", "sg", "sg-copy", "shallow", "short-scale", "shred", "sigma",
    "signature", "single coil", "single-coil", "single-cut", "sitka-spruce",
    "skyline", "solid body", "solid-body", "spanish", "spector", "spruce",
    "spruce-top", "strat-style", "stratocaster", "streamer", "student",
    "student-professional", "suhr", "superstrat", "surf", "takamine",
    "telecaster", "theodore", "thinline", "thumb", "tom anderson",
    "tom-morello", "travel", "tremolo", "tribute", "trini-lopez",
    "truss-rod", "ultra-luxe", "ultra-premium", "updated", "us-pickups",
    "usa", "usa-made", "value", "versatile", "vintage", "vintage reissue",
    "vintage-modern", "vintera", "warwick", "wraparound", "yamaha",
    # common variants
    "fender", "gibson",
}

# Lowercase lookup set
_TWNG_TAGS_LOWER: set[str] = {t.lower() for t in _TWNG_TAGS_RAW}

# Aliases: Scanner tag (lowered) → canonical TWNG slug
_ALIASES: dict[str, str] = {
    "acoustic-electric": "electro-acoustic",
}


def normalize_tags(scanner_tags: list[str] | None) -> dict:
    """Normalize Scanner tags against TWNG taxonomy.

    Returns:
        {
            "matched": [tags found in TWNG catalog],
            "new_tags": [tags not found — need admin review],
        }
    """
    if not scanner_tags:
        return {"matched": [], "new_tags": []}

    matched: list[str] = []
    new_tags: list[str] = []
    seen: set[str] = set()

    for tag in scanner_tags:
        lowered = tag.lower().strip()
        if not lowered or lowered in seen:
            continue
        seen.add(lowered)

        # Check alias first
        if lowered in _ALIASES:
            canonical = _ALIASES[lowered]
            if canonical not in seen:
                matched.append(canonical)
                seen.add(canonical)
            continue

        # Check TWNG catalog
        if lowered in _TWNG_TAGS_LOWER:
            matched.append(lowered)
        else:
            new_tags.append(lowered)

    return {"matched": matched, "new_tags": new_tags}
