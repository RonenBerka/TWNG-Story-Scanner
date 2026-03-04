import type { SeedGuitarRow, Guitar } from "../types/guitar";

export function mapRowToGuitar(row: SeedGuitarRow): Guitar {
  const meta: Record<string, any> = row.extraction_metadata || {};
  const specs = meta.specs || {};
  const searching =
    meta.searching ||
    (meta.twng_tags && meta.twng_tags.includes("searching")
      ? { owner_searching: true }
      : null);

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

    owner_contact: meta.owner_contact || {
      name: null,
      email: null,
      facebook_profile: null,
      invite_sent: false,
      invite_sent_at: null,
    },
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
    provenance: meta.provenance || {
      source_url: row.source_url,
      source_platform: row.source_platform || "Facebook",
      source_language: row.language || "he",
      extraction_confidence: {
        brand_model: "medium",
        year: "medium",
        story: "medium",
      },
    },
    searching,
    estimated_value_range_usd:
      meta.estimated_value_usd || meta.estimated_value_range_usd || null,
    confidence_score: row.confidence_score,
  };
}
