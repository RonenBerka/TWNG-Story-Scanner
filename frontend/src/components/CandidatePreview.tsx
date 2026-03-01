import { useState } from "react";
import type { Candidate } from "../lib/api";

interface Props {
  candidate: Candidate;
  onApprove: (id: string) => void;
  onReject: (id: string, reason?: string) => void;
  isApproving: boolean;
  isRejecting: boolean;
}

export default function CandidatePreview({
  candidate,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: Props) {
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  const fmtDate = (iso: string | null) =>
    iso ? new Date(iso).toLocaleString() : "—";

  const isActioned = candidate.status === "approved" || candidate.status === "rejected";

  return (
    <div className="preview-panel">
      <h2>{candidate.title || "Untitled"}</h2>

      <div className="preview-meta">
        <span className={`badge badge-${candidate.status}`}>{candidate.status}</span>
        {candidate.story_score != null && (
          <span className="badge badge-score">{candidate.story_score.toFixed(2)}</span>
        )}
        {candidate.category_pred && (
          <span className="badge">{candidate.category_pred}</span>
        )}
        {candidate.language && (
          <span className="badge">{candidate.language.toUpperCase()}</span>
        )}
      </div>

      {candidate.tags_pred && candidate.tags_pred.length > 0 && (
        <div className="preview-tags">
          {candidate.tags_pred.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}

      {candidate.summary_draft && (
        <div className="preview-section">
          <h3>Summary</h3>
          <p>{candidate.summary_draft}</p>
        </div>
      )}

      <div className="preview-section">
        <h3>Excerpt</h3>
        <p>{candidate.excerpt || "No excerpt available"}</p>
      </div>

      <div className="preview-section">
        <h3>Metadata</h3>
        <dl>
          <dt>Source URL</dt>
          <dd>
            <a href={candidate.source_url} target="_blank" rel="noopener noreferrer">
              {candidate.source_url}
            </a>
          </dd>
          <dt>Source date</dt>
          <dd>{fmtDate(candidate.created_at_source)}</dd>
          <dt>Ingested</dt>
          <dd>{fmtDate(candidate.ingested_at)}</dd>
          {candidate.entities && Object.keys(candidate.entities).length > 0 && (
            <>
              <dt>Entities</dt>
              <dd>{JSON.stringify(candidate.entities)}</dd>
            </>
          )}
        </dl>
      </div>

      {!isActioned && (
        <div className="preview-actions">
          <button
            className="btn btn-approve"
            onClick={() => onApprove(candidate.id)}
            disabled={isApproving || isRejecting}
          >
            {isApproving ? "Approving..." : "Approve"}
          </button>

          {!showRejectInput ? (
            <button
              className="btn btn-reject"
              onClick={() => setShowRejectInput(true)}
              disabled={isApproving || isRejecting}
            >
              Reject
            </button>
          ) : (
            <div className="reject-form">
              <input
                type="text"
                placeholder="Reason (optional)"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <button
                className="btn btn-reject"
                onClick={() => {
                  onReject(candidate.id, rejectReason || undefined);
                  setRejectReason("");
                  setShowRejectInput(false);
                }}
                disabled={isRejecting}
              >
                {isRejecting ? "Rejecting..." : "Confirm Reject"}
              </button>
              <button
                className="btn btn-cancel"
                onClick={() => {
                  setShowRejectInput(false);
                  setRejectReason("");
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {candidate.reviewer_notes && (
        <div className="preview-section">
          <h3>Reviewer notes</h3>
          <p>{candidate.reviewer_notes}</p>
        </div>
      )}
    </div>
  );
}
