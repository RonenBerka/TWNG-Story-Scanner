import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  runClaudeExtraction,
  calcConfidenceScore,
  getSavedApiKey,
  saveApiKey,
} from "../lib/extraction";
import { fetchCandidateRawText, type Candidate } from "../lib/api";
import { useInsertExtraction } from "../lib/guitarQueries";
import { useApprovedCandidates, useMarkExtracted } from "../lib/queries";
import "../styles/extraction.css";

type Step = "idle" | "loading-text" | "claude" | "parse" | "save" | "done" | "error";
type Tab = "queue" | "manual";

export default function Extraction() {
  const navigate = useNavigate();
  const insertMut = useInsertExtraction();
  const markExtracted = useMarkExtracted();
  const { data: approvedData, isLoading: queueLoading } = useApprovedCandidates();

  const [tab, setTab] = useState<Tab>("queue");
  const [text, setText] = useState("");
  const [platform, setPlatform] = useState("facebook");
  const [lang, setLang] = useState("he");
  const [sourceUrl, setSourceUrl] = useState("");
  const [apiKey, setApiKey] = useState(getSavedApiKey);
  const [step, setStep] = useState<Step>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<{ brand: string; model: string; year: string } | null>(null);
  const [extractingId, setExtractingId] = useState<string | null>(null);

  const approvedQueue = approvedData?.items || [];

  async function doExtraction(
    postText: string,
    postPlatform: string,
    postLang: string,
    postSourceUrl: string,
    candidateId?: string,
    authorUsername?: string | null,
    authorProfileUrl?: string | null,
    imageUrls?: string[] | null,
  ) {
    if (!postText.trim()) return alert("No text to extract from.");
    if (!apiKey.trim()) return alert("Please enter your Anthropic API key.");

    saveApiKey(apiKey.trim());
    setStep("claude");
    setErrorMsg("");
    setResult(null);

    try {
      const extracted = await runClaudeExtraction({
        text: postText.trim(),
        platform: postPlatform,
        lang: postLang,
        sourceUrl: postSourceUrl || null,
        apiKey: apiKey.trim(),
      });

      setStep("parse");
      const confidence = calcConfidenceScore(
        extracted.provenance?.extraction_confidence
      );

      setStep("save");

      // Enrich extraction_metadata with source contact & images from candidate
      const enriched = { ...extracted };
      if (postSourceUrl) {
        enriched.provenance = {
          ...enriched.provenance,
          source_url: postSourceUrl,
          source_platform: postPlatform,
        };
      }
      if (authorUsername || authorProfileUrl) {
        enriched.owner_contact = {
          ...enriched.owner_contact,
          source_username: authorUsername || null,
          source_profile_url: authorProfileUrl || null,
        };
      }
      if (imageUrls && imageUrls.length > 0) {
        enriched.images = imageUrls.map((url, i) => ({
          url,
          is_main: i === 0,
          caption: null,
          source_platform: postPlatform,
        }));
      }

      await insertMut.mutateAsync({
        brand: enriched.brand || null,
        model: enriched.model || null,
        year: enriched.year || null,
        story: enriched.story?.narrative || enriched.story?.summary || null,
        source_url: postSourceUrl || null,
        source_platform: postPlatform,
        language: postLang,
        confidence_score: confidence,
        raw_post_text: postText.trim(),
        extraction_metadata: enriched,
      });

      // Mark candidate as extracted if from queue
      if (candidateId) {
        await markExtracted.mutateAsync(candidateId);
      }

      setStep("done");
      setExtractingId(null);
      setResult({
        brand: extracted.brand || "Unknown",
        model: extracted.model || "Unknown",
        year: extracted.year_text || String(extracted.year || "?"),
      });
    } catch (e: any) {
      setStep("error");
      setExtractingId(null);
      setErrorMsg(e.message);
    }
  }

  async function handleExtractFromQueue(candidate: Candidate) {
    if (!apiKey.trim()) return alert("Please enter your Anthropic API key first.");
    setExtractingId(candidate.id);
    setStep("loading-text");
    setErrorMsg("");
    setResult(null);

    try {
      const rawText = await fetchCandidateRawText(candidate.id);
      if (!rawText.trim()) throw new Error("Candidate has no raw text");

      const postPlatform = candidate.source_type || "other";
      const postLang = candidate.language || "en";
      const postSourceUrl = candidate.source_url || "";

      // Use stored author/images, or fetch live from Reddit if missing
      let authorUsername = candidate.author_username;
      let authorProfileUrl = candidate.author_profile_url;
      let imageUrls = candidate.image_urls;

      if (!authorUsername && postSourceUrl.includes("reddit.com")) {
        try {
          const redditJson = await fetch(
            postSourceUrl.replace(/\/?$/, ".json"),
            { headers: { "User-Agent": "TWNG-Scanner/0.1" } }
          ).then((r) => r.json());
          const postData = redditJson?.[0]?.data?.children?.[0]?.data;
          if (postData) {
            authorUsername = postData.author || null;
            authorProfileUrl = postData.author
              ? `https://www.reddit.com/user/${postData.author}`
              : null;
            if (!imageUrls || imageUrls.length === 0) {
              const imgs: string[] = [];
              const pUrl = postData.url || "";
              if (/\.(jpg|jpeg|png|gif|webp)/i.test(pUrl) ||
                  pUrl.includes("i.redd.it") || pUrl.includes("i.imgur.com")) {
                imgs.push(pUrl);
              }
              if (postData.is_gallery && postData.media_metadata) {
                for (const meta of Object.values(postData.media_metadata) as any[]) {
                  const src = meta?.s?.u || meta?.s?.gif;
                  if (src) imgs.push(src.replace(/&amp;/g, "&"));
                }
              }
              if (imgs.length === 0) {
                const preview = postData.preview?.images?.[0]?.source?.url;
                if (preview) imgs.push(preview.replace(/&amp;/g, "&"));
              }
              if (imgs.length > 0) imageUrls = imgs;
            }
          }
        } catch {
          // Non-critical: proceed without Reddit metadata
        }
      }

      await doExtraction(
        rawText, postPlatform, postLang, postSourceUrl, candidate.id,
        authorUsername, authorProfileUrl, imageUrls,
      );
    } catch (e: any) {
      setStep("error");
      setExtractingId(null);
      setErrorMsg(e.message);
    }
  }

  function handleManualExtract() {
    doExtraction(text, platform, lang, sourceUrl);
  }

  const running = step === "loading-text" || step === "claude" || step === "parse" || step === "save";

  const stepIcon = (_s: Step, target: Step) => {
    if (step === "error" && target === step) return "\u2717";
    const order: Step[] = ["loading-text", "claude", "parse", "save", "done"];
    const idx = order.indexOf(step);
    const t = order.indexOf(target);
    if (t < idx || step === "done") return "\u2713";
    if (t === idx) return "\u25CF";
    return "\u25CB";
  };

  const stepClass = (target: Step) => {
    if (step === "error") return "";
    const order: Step[] = ["loading-text", "claude", "parse", "save", "done"];
    const idx = order.indexOf(step);
    const t = order.indexOf(target);
    if (t < idx || step === "done") return "done";
    if (t === idx) return "active";
    return "";
  };

  const fmtDate = (iso: string | null) =>
    iso ? new Date(iso).toLocaleDateString() : "";

  return (
    <div className="ep-page">
      <h2 className="ep-title">Extraction Engine</h2>
      <div className="ep-sub">
        Select an approved story or paste text manually &rarr; Claude extracts structured guitar data &rarr; saved to Supabase
      </div>

      {/* API Key - always visible */}
      <div className="ep-group">
        <label className="ep-label">Anthropic API Key</label>
        <input
          className="ep-input"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-ant-..."
        />
        <div className="ep-key-note">Stored in localStorage only. Never sent anywhere except api.anthropic.com.</div>
      </div>

      {/* Tab selector */}
      <div className="ep-tabs">
        <button
          className={`ep-tab${tab === "queue" ? " active" : ""}`}
          onClick={() => setTab("queue")}
        >
          Approved Queue {approvedQueue.length > 0 && <span className="ep-tab-count">{approvedQueue.length}</span>}
        </button>
        <button
          className={`ep-tab${tab === "manual" ? " active" : ""}`}
          onClick={() => setTab("manual")}
        >
          Manual Entry
        </button>
      </div>

      {/* Queue tab */}
      {tab === "queue" && (
        <div className="ep-queue">
          {queueLoading ? (
            <div className="ep-queue-empty">Loading approved stories...</div>
          ) : approvedQueue.length === 0 ? (
            <div className="ep-queue-empty">
              No approved stories waiting for extraction.
              <br />
              <span className="ep-queue-hint">Approve stories in the Scanner stage first.</span>
            </div>
          ) : (
            <div className="ep-queue-list">
              {approvedQueue.map((c) => (
                <div
                  key={c.id}
                  className={`ep-queue-item${extractingId === c.id ? " extracting" : ""}`}
                >
                  <div className="ep-queue-item-info">
                    <div className="ep-queue-item-title">
                      {c.title || "Untitled"}
                    </div>
                    <div className="ep-queue-item-meta">
                      <span className="ep-queue-item-source">{c.source_type}</span>
                      {c.language && <span className="ep-queue-item-lang">{c.language.toUpperCase()}</span>}
                      {c.story_score != null && (
                        <span className="ep-queue-item-score">
                          Score: {c.story_score.toFixed(2)}
                        </span>
                      )}
                      {c.created_at_source && (
                        <span className="ep-queue-item-date">{fmtDate(c.created_at_source)}</span>
                      )}
                    </div>
                    {c.excerpt && (
                      <div className="ep-queue-item-excerpt">{c.excerpt}</div>
                    )}
                  </div>
                  <button
                    className="btn-run-extract small"
                    onClick={() => handleExtractFromQueue(c)}
                    disabled={running}
                  >
                    {extractingId === c.id ? "Extracting..." : "\u26A1 Extract"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Manual tab */}
      {tab === "manual" && (
        <>
          <div className="ep-group">
            <label className="ep-label">Post Text</label>
            <textarea
              className="ep-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the full post text here (Hebrew or English)..."
            />
          </div>

          <div className="ep-row">
            <div className="ep-group" style={{ flex: 1 }}>
              <label className="ep-label">Source Platform</label>
              <select className="ep-select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
                <option value="facebook">Facebook</option>
                <option value="reddit">Reddit</option>
                <option value="instagram">Instagram</option>
                <option value="forum">Forum</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="ep-group" style={{ flex: 1 }}>
              <label className="ep-label">Original Language</label>
              <select className="ep-select" value={lang} onChange={(e) => setLang(e.target.value)}>
                <option value="he">Hebrew</option>
                <option value="en">English</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="ep-group">
            <label className="ep-label">Source URL (optional)</label>
            <input
              className="ep-input"
              type="text"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://..."
            />
          </div>

          <div className="ep-actions">
            <button className="btn-run-extract" onClick={handleManualExtract} disabled={running}>
              {running ? "Extracting..." : "\u26A1 Extract with Claude"}
            </button>
          </div>
        </>
      )}

      {/* Progress */}
      {step !== "idle" && (
        <div className="ep-progress">
          {extractingId && (
            <div className={`ep-step ${stepClass("loading-text")}`}>
              <span className="ep-step-icon">{stepIcon(step, "loading-text")}</span>
              Fetching story text...
            </div>
          )}
          <div className={`ep-step ${stepClass("claude")}`}>
            <span className="ep-step-icon">{stepIcon(step, "claude")}</span>
            Sending to Claude API...
          </div>
          <div className={`ep-step ${stepClass("parse")}`}>
            <span className="ep-step-icon">{stepIcon(step, "parse")}</span>
            Parsing extraction result...
          </div>
          <div className={`ep-step ${stepClass("save")}`}>
            <span className="ep-step-icon">{stepIcon(step, "save")}</span>
            Saving to Supabase...
          </div>
        </div>
      )}

      {step === "done" && result && (
        <div className="ep-result">
          <div>
            &#10003; Extracted and saved: <strong>{result.brand} {result.model}</strong> ({result.year})
          </div>
          <div className="ep-result-sub">Status: pending &rarr; ready for Pre-Claim review</div>
          <button className="ep-goto-btn" onClick={() => navigate("/approval")}>
            &rarr; View in Pre-Claim
          </button>
        </div>
      )}

      {step === "error" && (
        <div className="ep-error">{errorMsg}</div>
      )}
    </div>
  );
}
