/** Typed API client — calls Supabase Edge Functions. */

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

export async function triggerRedditIngest(limit: number = 20): Promise<{ inserted: number; skipped: number; errors: number }> {
  return edgeFetch("scanner-ingest-reddit", `?limit=${limit}`, { method: "POST" });
}

export async function triggerScoring(): Promise<{ scored: number; errors: number }> {
  return edgeFetch("scanner-score", "", { method: "POST" });
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
