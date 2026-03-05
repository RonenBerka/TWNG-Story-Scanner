import type { SeedGuitarRow, Guitar } from "../types/guitar";

export function mapRowToGuitar(row: SeedGuitarRow): Guitar {
  const meta: Record<string, any> = row.extraction_metadata || {};
  const specs = meta.specs || {};
  const searching =
    meta.searching ||
    (meta.twng_tags && meta.twng_tags.includes("searching")
      ? { owner_searching: true }
      : null);

  // Merge provenance: prefer extraction_metadata, fall back to row columns
  const metaProv = meta.provenance || {};
  const provenance = {
    source_url: metaProv.source_url || row.source_url || null,
    source_platform: metaProv.source_platform || row.source_platform || "unknown",
    source_language: metaProv.source_language || row.language || "en",
    extraction_confidence: metaProv.extraction_confidence || {
      brand_model: "medium",
      year: "medium",
      story: "medium",
    },
  };

  // Merge owner_contact: prefer extraction_metadata, enrich with source info
  const metaOC = meta.owner_contact || {};
  const owner_contact = {
    name: metaOC.name || metaOC.display_name || null,
    email: metaOC.email || null,
    facebook_profile: metaOC.facebook_profile || metaOC.source_profile_url || null,
    source_username: metaOC.source_username || null,
    source_profile_url: metaOC.source_profile_url || null,
    invite_sent: metaOC.invite_sent || false,
    invite_sent_at: metaOC.invite_sent_at || null,
  };

  return {
    _db_id: row.id,
    _db_status: row.status,
    _db_claim_token: row.claim_token,
    _db_claim_sent_at: row.claim_sent_at,

    id: meta.id || row.id,
    instrument_type: meta.instrument_type || "guitar",
    brand: row.brand || "Unknown",
    model: row.model || "Unknown",
    year:
      meta.year_text || (row.year ? String(row.year) : "Unknown"),
    year_exact: row.year,
    finish: meta.finish || null,
    serial_number: meta.serial_number || null,
    country_of_origin: meta.country_of_origin || null,
    dedup_fingerprint:
      meta.dedup_fingerprint ||
      `${(row.brand || "").toLowerCase()}|${(row.model || "").toLowerCase()}|${row.year || ""}`,
    status: meta.searching ? "sold_searching" : "owned",

    owner_contact,
    images: meta.images || [],
    tags: meta.tags || meta.twng_tags || [],
    timeline_events: meta.timeline_events || [],
    specs,
    story: meta.story || {
      context: null,
      original_text_translated: row.raw_post_text || null,
      summary: null,
      narrative: row.story || null,
      famous_connection: meta.famous_connection || null,
      notable_events: [],
    },
    provenance,
    searching,
    estimated_value_range_usd:
      meta.estimated_value_usd || meta.estimated_value_range_usd || null,
    confidence_score: row.confidence_score,
  };
}
