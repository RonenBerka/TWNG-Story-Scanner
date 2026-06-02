import { useState, useCallback, useEffect, useRef } from "react";
import { useCandidates, useApprove, useReject } from "../lib/queries";
import { ingestRedditBatch, triggerScoring } from "../lib/api";
import type { Candidate, CandidateFilters } from "../lib/api";
import CandidateTable from "../components/CandidateTable";
import CandidatePreview from "../components/CandidatePreview";
import Filters from "../components/Filters";
import FbArchiveHelp from "../components/FbArchiveHelp";

const PAGE_SIZE = 30;

export default function Scanner() {
  const [filters, setFilters] = useState<CandidateFilters>({
    status: "new",
    limit: PAGE_SIZE,
    offset: 0,
  });
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [scoring, setScoring] = useState(false);

  const { data, isLoading, isError, error, refetch } = useCandidates(filters);
  const approve = useApprove();
  const reject = useReject();
  const importedRef = useRef(false);

  // Auto-import Reddit posts handed off by the "TWNG Scan" bookmarklet.
  // The bookmarklet runs on reddit.com (same-origin fetch works there),
  // stashes the posts in window.name, and navigates here. Insert-only.
  useEffect(() => {
    if (importedRef.current) return;
    const raw = window.name;
    if (typeof raw !== "string" || !raw.startsWith("TWNG:")) return;
    importedRef.current = true;
    const payload = raw.slice(5);
    window.name = ""; // clear immediately so it can't re-import
    let items: unknown[] = [];
    try {
      items = JSON.parse(payload);
    } catch {
      return;
    }
    if (!Array.isArray(items) || items.length === 0) return;
    ingestRedditBatch(items)
      .then((r) => {
        alert(`Reddit scan imported ✓  New: ${r.inserted} · Duplicates: ${r.skipped} (of ${r.received})`);
        refetch();
      })
      .catch((e: any) => alert(`Import failed: ${e?.message || e}`));
  }, [refetch]);

  const handleRowClick = useCallback((candidate: Candidate) => {
    setSelected(candidate);
  }, []);

  const handleApprove = useCallback(
    (id: string) => {
      approve.mutate(id, {
        onSuccess: () => setSelected(null),
      });
    },
    [approve]
  );

  const handleReject = useCallback(
    (id: string, reason?: string) => {
      reject.mutate(
        { id, reason },
        { onSuccess: () => setSelected(null) }
      );
    },
    [reject]
  );

  const scanReddit = useCallback(() => {
    // Reddit blocks server-side scanning, so the scan runs in your own browser:
    // open Reddit, then click the "TWNG Scan" bookmarklet. It collects posts and
    // returns here automatically, where they are imported (insert-only).
    alert(
      "Opening Reddit. Once it loads, click your 'TWNG Scan' bookmark.\n\n" +
      "It will collect guitar posts (~40s) and jump back here automatically to import them."
    );
    window.open("https://www.reddit.com/", "_blank", "noopener");
  }, []);

  const scoreAll = useCallback(async () => {
    setScoring(true);
    try {
      const result = await triggerScoring();
      alert(`Scoring complete: ${result.scored} scored, ${result.errors} errors`);
      refetch();
    } catch (err: any) {
      alert(`Scoring failed: ${err.message}`);
    } finally {
      setScoring(false);
    }
  }, [refetch]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;
  const currentPage = data ? Math.floor((filters.offset || 0) / PAGE_SIZE) + 1 : 1;

  return (
    <div className="inbox-layout">
      <header className="inbox-header">
        <h1>Story Scanner</h1>
        <div className="header-right">
          <button
            className="btn btn-scan"
            onClick={scanReddit}
          >
            Scan Reddit ↗
          </button>
          <button className="btn btn-score" onClick={scoreAll} disabled={scoring}>
            {scoring ? "Scoring..." : "Score All"}
          </button>
          <FbArchiveHelp />
          <span className="total-badge">
            {data ? `${data.total} candidates` : "..."}
          </span>
        </div>
      </header>

      <Filters filters={filters} onChange={setFilters} />

      <div className="inbox-content">
        <div className={`inbox-table-area ${selected ? "has-preview" : ""}`}>
          {isLoading && <div className="loading">Loading candidates...</div>}
          {isError && (
            <div className="error-box">
              Error: {(error as Error)?.message || "Unknown error"}
            </div>
          )}
          {data && (
            <>
              <CandidateTable
                data={data.items}
                selectedId={selected?.id}
                onRowClick={handleRowClick}
              />
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="btn btn-sm"
                    disabled={currentPage <= 1}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        offset: Math.max(0, (f.offset || 0) - PAGE_SIZE),
                      }))
                    }
                  >
                    Prev
                  </button>
                  <span>
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    className="btn btn-sm"
                    disabled={currentPage >= totalPages}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        offset: (f.offset || 0) + PAGE_SIZE,
                      }))
                    }
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {selected && (
          <CandidatePreview
            candidate={selected}
            onApprove={handleApprove}
            onReject={handleReject}
            isApproving={approve.isPending}
            isRejecting={reject.isPending}
          />
        )}
      </div>
    </div>
  );
}
