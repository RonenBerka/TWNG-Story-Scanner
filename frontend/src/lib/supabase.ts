/** Supabase client singleton. */

import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://wtqylorvckigssjlurwj.supabase.co";
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cXlsb3J2Y2tpZ3Nzamx1cndqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTczNjEyNDMsImV4cCI6MjA3MjkzNzI0M30.bkD-pSp4cc3B_bj-pAjjYGj_GCs6Sepsj6G6fUwgPmo";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
export const EDGE_BASE = `${SUPABASE_URL}/functions/v1`;
