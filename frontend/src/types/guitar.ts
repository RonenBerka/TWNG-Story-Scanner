export interface SeedGuitarRow {
  id: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  story: string | null;
  source_url: string | null;
  source_platform: string | null;
  language: string | null;
  confidence_score: number | null;
  status: string;
  raw_post_text: string | null;
  extraction_metadata: Record<string, any> | null;
  claim_token: string | null;
  approved_at: string | null;
  approved_by: string | null;
  claim_sent_at: string | null;
  claimed_at: string | null;
  created_at: string;
}

export interface Guitar {
  _db_id: string;
  _db_status: string;
  _db_claim_token: string | null;
  _db_claim_sent_at: string | null;
  id: string;
  instrument_type: string;
  brand: string;
  model: string;
  year: string;
  year_exact: number | null;
  finish: string | null;
  serial_number: string | null;
  country_of_origin: string | null;
  dedup_fingerprint: string;
  status: string;
  owner_contact: {
    name: string | null;
    email: string | null;
    facebook_profile: string | null;
    source_username: string | null;
    source_profile_url: string | null;
    invite_sent: boolean;
    invite_sent_at: string | null;
  };
  images: any[];
  tags: string[];
  timeline_events: any[];
  specs: Record<string, any>;
  story: {
    context: string | null;
    original_text_translated: string | null;
    summary: string | null;
    narrative: string | null;
    famous_connection: string | null;
    notable_events: string[];
  };
  provenance: {
    source_url: string | null;
    source_platform: string;
    source_language: string;
    extraction_confidence: Record<string, string>;
  };
  searching: Record<string, any> | null;
  estimated_value_range_usd: string | null;
  confidence_score: number | null;
}
