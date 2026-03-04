import { supabase, EDGE_BASE } from "./supabase";
import { mapRowToGuitar } from "./guitarMapper";
import type { SeedGuitarRow, Guitar } from "../types/guitar";

export async function fetchAllGuitars(
  status?: string
): Promise<Guitar[]> {
  let q = supabase
    .from("seed_guitars")
    .select("*")
    .order("created_at", { ascending: true });

  if (status && status !== "all") {
    q = q.eq("status", status);
  }

  const { data, error } = await q;
  if (error) throw new Error(error.message);
  return (data as SeedGuitarRow[]).map(mapRowToGuitar);
}

export async function approveGuitar(id: string) {
  const claimToken = crypto.randomUUID();
  const { error } = await supabase
    .from("seed_guitars")
    .update({
      status: "approved",
      approved_at: new Date().toISOString(),
      approved_by: "viewer_admin",
      claim_token: claimToken,
    })
    .eq("id", id);

  if (error) throw new Error(error.message);
  return claimToken;
}

export async function rejectGuitar(id: string) {
  const { error } = await supabase
    .from("seed_guitars")
    .update({ status: "rejected" })
    .eq("id", id);

  if (error) throw new Error(error.message);
}

export async function insertExtractedGuitar(row: {
  brand: string | null;
  model: string | null;
  year: number | null;
  story: string | null;
  source_url: string | null;
  source_platform: string;
  language: string;
  confidence_score: number;
  raw_post_text: string;
  extraction_metadata: Record<string, any>;
}): Promise<SeedGuitarRow> {
  const { data, error } = await supabase
    .from("seed_guitars")
    .insert([{ ...row, status: "pending" }])
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as SeedGuitarRow;
}

export async function sendClaimEmail(params: {
  guitar_id: string;
  claim_token: string;
  recipient_email: string;
  recipient_name: string | null;
  brand: string;
  model: string;
  year: string | null;
}) {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token;

  const res = await fetch(`${EDGE_BASE}/send-claim-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token || ""}`,
    },
    body: JSON.stringify(params),
  });

  const result = await res.json();
  if (!res.ok) throw new Error(result.error || `HTTP ${res.status}`);

  // Update claim_sent_at
  await supabase
    .from("seed_guitars")
    .update({ claim_sent_at: new Date().toISOString() })
    .eq("id", params.guitar_id);

  return result;
}

export const CLAIM_BASE_URL = "twng-claim-v5.html";

export function buildClaimUrl(claimToken: string) {
  return `${CLAIM_BASE_URL}?token=${claimToken}`;
}
