import { buildSystemPrompt, buildUserMessage } from "./extractionPrompt";

const API_KEY_STORAGE = "twng_anthropic_key";

export function getSavedApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE) || "";
}

export function saveApiKey(key: string) {
  localStorage.setItem(API_KEY_STORAGE, key);
}

export function calcConfidenceScore(
  conf: Record<string, string> | undefined
): number {
  if (!conf) return 0.5;
  const vals = Object.values(conf);
  const map: Record<string, number> = { high: 1, medium: 0.6, low: 0.3 };
  return vals.reduce((sum, v) => sum + (map[v] || 0.5), 0) / vals.length;
}

export async function runClaudeExtraction(params: {
  text: string;
  platform: string;
  lang: string;
  sourceUrl: string | null;
  apiKey: string;
}): Promise<Record<string, any>> {
  const { text, platform, lang, apiKey } = params;

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 2000,
      system: buildSystemPrompt(lang),
      messages: [{ role: "user", content: buildUserMessage(text, platform, lang) }],
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      `API error ${res.status}: ${err?.error?.message || res.statusText}`
    );
  }

  const json = await res.json();
  const block = json.content?.find((b: any) => b.type === "text");
  if (!block) throw new Error("No text response from Claude");

  const cleaned = block.text.replace(/```json|```/g, "").trim();
  return JSON.parse(cleaned);
}
