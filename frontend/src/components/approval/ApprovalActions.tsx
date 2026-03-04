import { useState } from "react";
import {
  useApproveGuitar,
  useRejectGuitar,
  useSendClaimEmail,
} from "../../lib/guitarQueries";
import { buildClaimUrl } from "../../lib/guitars";
import type { Guitar } from "../../types/guitar";

interface Props {
  guitar: Guitar;
}

export default function ApprovalActions({ guitar }: Props) {
  const approveMut = useApproveGuitar();
  const rejectMut = useRejectGuitar();
  const emailMut = useSendClaimEmail();

  const [email, setEmail] = useState(guitar.owner_contact?.email || "");
  const [copied, setCopied] = useState(false);
  const [emailNote, setEmailNote] = useState("");

  const isPending = guitar._db_status === "pending";
  const isApproved = guitar._db_status === "approved";
  const isRejected = guitar._db_status === "rejected";

  const claimToken = guitar._db_claim_token || "";
  const claimUrl = claimToken ? buildClaimUrl(claimToken) : "";

  async function handleApprove() {
    try {
      await approveMut.mutateAsync(guitar._db_id);
    } catch (e: any) {
      alert(`Approve failed: ${e.message}`);
    }
  }

  async function handleReject() {
    try {
      await rejectMut.mutateAsync(guitar._db_id);
    } catch (e: any) {
      alert(`Reject failed: ${e.message}`);
    }
  }

  async function handleSendEmail() {
    if (!email.trim()) return alert("Enter an email address.");
    if (!claimToken) return alert("No claim token — approve first.");

    setEmailNote("Sending...");
    try {
      await emailMut.mutateAsync({
        guitar_id: guitar._db_id,
        claim_token: claimToken,
        recipient_email: email.trim(),
        recipient_name: guitar.owner_contact?.name || null,
        brand: guitar.brand,
        model: guitar.model,
        year: guitar.year || null,
      });
      setEmailNote("Email sent successfully!");
    } catch (e: any) {
      setEmailNote(`Error: ${e.message}`);
    }
  }

  function handleCopyLink() {
    navigator.clipboard.writeText(claimUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <>
      <div className="action-row">
        <button
          className={`btn-approve${isApproved ? " done" : ""}`}
          onClick={handleApprove}
          disabled={!isPending || approveMut.isPending}
        >
          {approveMut.isPending
            ? "Saving..."
            : isApproved
              ? "\u2713 Approved"
              : "\u2197 Approve"}
        </button>
        <button
          className={`btn-reject${isRejected ? " done" : ""}`}
          onClick={handleReject}
          disabled={!isPending || rejectMut.isPending}
        >
          {rejectMut.isPending
            ? "Saving..."
            : isRejected
              ? "\u2717 Rejected"
              : "\u2717 Reject"}
        </button>
      </div>

      <div className="approve-note">
        {isApproved
          ? "Approved \u00B7 saved to Supabase"
          : isRejected
            ? "Rejected \u00B7 saved to Supabase"
            : `Status: ${guitar._db_status} \u00B7 changes write to Supabase`}
      </div>

      {isApproved && (
        <div className="claim-email-box">
          <div className="claim-email-label">Send Claim Invitation</div>
          <div className="claim-email-row">
            <input
              type="email"
              className="claim-email-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Owner email"
            />
            <button
              className="btn-send-email"
              onClick={handleSendEmail}
              disabled={emailMut.isPending}
            >
              {emailMut.isPending ? "Sending..." : "\u2709 Send Email"}
            </button>
          </div>
          <div className="claim-email-note">
            {claimToken
              ? `Claim token: ${claimToken.substring(0, 8)}...`
              : "No claim token"}
          </div>
          {claimUrl && (
            <button className="btn-copy-link" onClick={handleCopyLink}>
              {copied ? "\u2713 Copied!" : "Copy claim link"}
            </button>
          )}
          {emailNote && (
            <div
              className="claim-email-note"
              style={{
                marginTop: 6,
                color: emailNote.startsWith("Error") ? "var(--red)" : "var(--green)",
              }}
            >
              {emailNote}
            </div>
          )}
        </div>
      )}
    </>
  );
}
