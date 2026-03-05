/** Typed API client — calls Supabase Edge Functions + direct Supabase queries. */

import { EDGE_BASE, supabase } from "./supabase";

async function getToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

async function edgeFetch<T>(fnName: string, path: string, init?: RequestInit): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers as Record<string, string> ?? {}),
  };

  const url = `${EDGE_BASE}/${fnName}${path}`;
  const res = await fetch(url, { ...init, headers });

  if (res.status === 401) {
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || err.detail || `API error ${res.status}`);
  }

  return res.json() as Promise<T>;
}

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface Candidate {
  id: string;
  source_type: string;
  source_id: string;
  source_url: string;
  title: string | null;
  excerpt: string | null;
  raw_text?: string | null;
  created_at_source: string | null;
  ingested_at: string;
  language: string | null;
  prefilter_flags: Record<string, unknown>;
  story_score: number | null;
  score_components: Record<string, unknown>;
  category_pred: string | null;
  category_confidence: number | null;
  entities: Record<string, unknown>;
  summary_draft: string | null;
  tags_pred: string[] | null;
  status: string;
  reviewer_notes: string | null;
}

export interface CandidateList {
  items: Candidate[];
  total: number;
}

export interface CandidateFilters {
  status?: string;
  min_score?: number;
  source?: string;
  lang?: string;
  q?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}

/* ------------------------------------------------------------------ */
/*  API calls                                                          */
/* ------------------------------------------------------------------ */

export function fetchCandidates(filters: CandidateFilters): Promise<CandidateList> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.min_score != null) params.set("min_score", String(filters.min_score));
  if (filters.source) params.set("source", filters.source);
  if (filters.lang) params.set("lang", filters.lang);
  if (filters.q) params.set("q", filters.q);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.offset != null) params.set("offset", String(filters.offset));

  return edgeFetch<CandidateList>("scanner-candidates", `?${params.toString()}`);
}

export function fetchCandidate(id: string): Promise<Candidate> {
  return edgeFetch<Candidate>("scanner-candidates", `/${id}`);
}

export function approveCandidate(id: string): Promise<Candidate> {
  return edgeFetch<Candidate>("scanner-candidates", `/${id}/approve`, { method: "POST" });
}

export function rejectCandidate(id: string, reason?: string): Promise<Candidate> {
  return edgeFetch<Candidate>("scanner-candidates", `/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason || null }),
  });
}

/* ------------------------------------------------------------------ */
/*  Admin tasks                                                        */
/* ------------------------------------------------------------------ */

const DOCKER_BACKEND = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function triggerRedditIngest(limit: number = 20): Promise<{ inserted: number; skipped: number; errors: number }> {
  const res = await fetch(`${DOCKER_BACKEND}/api/public/scan-reddit?limit=${limit}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `Scan failed (${res.status})`);
  }
  return res.json();
}

export async function triggerScoring(): Promise<{ scored: number; errors: number }> {
  return edgeFetch("scanner-score", "", { method: "POST" });
}

/* ------------------------------------------------------------------ */
/*  Direct Supabase queries for Extraction workflow                    */
/* ------------------------------------------------------------------ */

export async function fetchCandidateRawText(id: string): Promise<string> {
  const { data, error } = await supabase
    .from("candidate_stories")
    .select("raw_text")
    .eq("id", id)
    .single();

  if (error) throw new Error(error.message);
  return data?.raw_text || "";
}

export async function markCandidateExtracted(id: string): Promise<void> {
  const { error } = await supabase
    .from("candidate_stories")
    .update({ status: "extracted" })
    .eq("id", id);

  if (error) throw new Error(error.message);
}

/* ------------------------------------------------------------------ */
/*  Viewer data                                                        */
/* ------------------------------------------------------------------ */

export interface ViewerData {
  extraction_metadata: Record<string, unknown>;
  guitars: Record<string, unknown>[];
}

export function fetchViewerData(): Promise<ViewerData> {
  return edgeFetch<ViewerData>("scanner-records", "/viewer");
}

/* ------------------------------------------------------------------ */
/*  Export to TWNG                                                      */
/* ------------------------------------------------------------------ */

export interface TWNGExportData {
  twng_import_version: string;
  exported_at: string;
  source: string;
  total_items: number;
  items: Record<string, unknown>[];
}

export async function exportToTWNG(opts?: {
  visibility?: string;
  ids?: string[];
}): Promise<TWNGExportData> {
  const params = new URLSearchParams();
  if (opts?.visibility) params.set("visibility", opts.visibility);
  if (opts?.ids?.length) params.set("ids", opts.ids.join(","));
  return edgeFetch<TWNGExportData>("scanner-records", `/export-twng?${params.toString()}`);
}

export async function downloadTWNGExport(opts?: {
  visibility?: string;
  ids?: string[];
}): Promise<void> {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  const params = new URLSearchParams({ download: "true" });
  if (opts?.visibility) params.set("visibility", opts.visibility);
  if (opts?.ids?.length) params.set("ids", opts.ids.join(","));

  const res = await fetch(`${DOCKER_BACKEND}/records/export-twng?${params.toString()}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) throw new Error(`Export failed: ${res.status}`);

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const filenameMatch = disposition.match(/filename="?(.+?)"?$/);
  const filename = filenameMatch?.[1] || "twng_export.json";

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
