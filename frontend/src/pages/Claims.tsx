import { useState } from "react";
import { useGuitars, useSendClaimEmail } from "../lib/guitarQueries";
import { buildClaimUrl } from "../lib/guitars";
import type { Guitar } from "../types/guitar";
import "../styles/claims.css";

export default function Claims() {
  const { data: guitars, isLoading, error } = useGuitars();
  const [previewToken, setPreviewToken] = useState<string | null>(null);

  // Only show approved + claimed guitars
  const claimable = (guitars || []).filter(
    (g) => g._db_status === "approved" || g._db_status === "claimed"
  );

  if (isLoading) {
    return (
      <div className="cl-page">
        <h2 className="cl-title">Claim Page Generator</h2>
        <div className="cl-sub">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cl-page">
        <h2 className="cl-title">Claim Page Generator</h2>
        <div style={{ color: "var(--red)", fontSize: 13 }}>
          Error: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="cl-page">
      <h2 className="cl-title">Claim Page Generator</h2>
      <div className="cl-sub">
        Approved &amp; claimed guitars &middot; send claim invitations via email or DM &middot;
        preview public claim pages
      </div>

      {claimable.length === 0 ? (
        <div className="cl-empty">
          No approved or claimed guitars yet. Approve guitars in the Pre-Claim
          stage first.
        </div>
      ) : (
        <div className="cl-table-wrap">
          <table className="cl-table">
            <thead>
              <tr>
                <th>Guitar</th>
                <th>Year</th>
                <th>Source</th>
                <th>Status</th>
                <th>Invited</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {claimable.map((g) => (
                <ClaimRow
                  key={g._db_id}
                  guitar={g}
                  onPreview={(token) => setPreviewToken(token)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {previewToken && (
        <div className="cl-preview-wrap">
          <div className="cl-preview-header">
            <span className="cl-preview-title">
              Claim Page Preview
            </span>
            <button
              className="cl-btn"
              onClick={() => setPreviewToken(null)}
            >
              Close
            </button>
          </div>
          <iframe
            className="cl-preview-frame"
            src={buildClaimUrl(previewToken)}
            title="Claim page preview"
          />
        </div>
      )}
    </div>
  );
}

type InviteMode = "email" | "dm";

function ClaimRow({
  guitar,
  onPreview,
}: {
  guitar: Guitar;
  onPreview: (token: string) => void;
}) {
  const emailMut = useSendClaimEmail();
  const [email, setEmail] = useState(guitar.owner_contact?.email || "");
  const [copied, setCopied] = useState(false);
  const [dmCopied, setDmCopied] = useState(false);
  const [emailStatus, setEmailStatus] = useState("");
  const [inviteMode, setInviteMode] = useState<InviteMode>("email");

  const token = guitar._db_claim_token || "";
  const claimUrl = token ? buildClaimUrl(token) : "";
  const emailSentAt = guitar._db_claim_sent_at;
  const sourcePlatform = guitar.provenance?.source_platform || "unknown";
  const sourceUrl = guitar.provenance?.source_url || "";

  function handleCopy() {
    if (!claimUrl) return;
    navigator.clipboard.writeText(claimUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function buildDmTemplate(): string {
    const guitarName = `${guitar.brand} ${guitar.model}${guitar.year ? ` (${guitar.year})` : ""}`;
    return [
      `Hi! I came across your post about your ${guitarName} and I'm writing on behalf of TWNG \u2014 a project that collects and preserves remarkable guitar stories from around the world.`,
      ``,
      `Your guitar's story caught our attention and we'd love to feature it in our collection. If you're interested, just follow the link below to share more details and claim your guitar's story:`,
      ``,
      claimUrl,
      ``,
      `It only takes a few minutes. No obligations and no charge, just a chance to be part of something cool.`,
      ``,
      `Thanks!`,
      `\u2014 TWNG Team`,
    ].join("\n");
  }

  function handleCopyDm() {
    const dmText = buildDmTemplate();
    navigator.clipboard.writeText(dmText);
    setDmCopied(true);
    setTimeout(() => setDmCopied(false), 2000);
  }

  async function handleSend() {
    if (!email.trim()) return alert("Enter email address.");
    if (!token) return alert("No claim token.");

    setEmailStatus("sending");
    try {
      await emailMut.mutateAsync({
        guitar_id: guitar._db_id,
        claim_token: token,
        recipient_email: email.trim(),
        recipient_name: guitar.owner_contact?.name || null,
        brand: guitar.brand,
        model: guitar.model,
        year: guitar.year || null,
      });
      setEmailStatus("sent");
    } catch (e: any) {
      setEmailStatus(`error: ${e.message}`);
    }
  }

  return (
    <tr>
      <td>
        <div className="cl-brand">
          {guitar.brand} {guitar.model}
        </div>
      </td>
      <td>
        <span className="cl-year">{guitar.year || "?"}</span>
      </td>
      <td>
        <span className="cl-source">
          {sourcePlatform}
          {sourceUrl && (
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="cl-source-link" title="Open source">
              &#8599;
            </a>
          )}
        </span>
      </td>
      <td>
        <span className={`cl-status ${guitar._db_status}`}>
          {guitar._db_status}
        </span>
      </td>
      <td>
        <span className={`cl-email-sent${emailSentAt ? " yes" : ""}`}>
          {emailSentAt
            ? new Date(emailSentAt).toLocaleDateString()
            : emailStatus === "sent"
              ? "Just sent"
              : "Not sent"}
        </span>
      </td>
      <td>
        <div className="cl-invite-section">
          {/* Mode toggle */}
          <div className="cl-mode-toggle">
            <button
              className={`cl-mode-btn${inviteMode === "email" ? " active" : ""}`}
              onClick={() => setInviteMode("email")}
            >
              Email
            </button>
            <button
              className={`cl-mode-btn${inviteMode === "dm" ? " active" : ""}`}
              onClick={() => setInviteMode("dm")}
            >
              DM
            </button>
          </div>

          {inviteMode === "email" ? (
            <div className="cl-actions">
              <input
                type="email"
                className="cl-email-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="owner@email.com"
              />
              <button
                className="cl-btn send"
                onClick={handleSend}
                disabled={emailMut.isPending || emailStatus === "sending"}
              >
                {emailStatus === "sending" ? "..." : "\u2709 Send"}
              </button>
            </div>
          ) : (
            <div className="cl-actions">
              <button
                className="cl-btn send"
                onClick={handleCopyDm}
              >
                {dmCopied ? "\u2713 Copied!" : "Copy DM Text"}
              </button>
              {sourceUrl && (
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cl-btn"
                >
                  {sourcePlatform} &#8599;
                </a>
              )}
            </div>
          )}

          <div className="cl-actions-secondary">
            <button
              className="cl-btn"
              onClick={handleCopy}
              disabled={!token}
            >
              {copied ? "\u2713 Copied" : "Copy URL"}
            </button>
            {token && (
              <button
                className="cl-btn"
                onClick={() => onPreview(token)}
              >
                Preview
              </button>
            )}
          </div>
        </div>
        {emailStatus.startsWith("error") && (
          <div style={{ fontSize: 10, color: "var(--red)", marginTop: 4 }}>
            {emailStatus}
          </div>
        )}
      </td>
    </tr>
  );
}
