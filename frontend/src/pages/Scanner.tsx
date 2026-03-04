import { useState, useCallback } from "react";
import { useCandidates, useApprove, useReject } from "../lib/queries";
import { triggerRedditIngest, triggerScoring } from "../lib/api";
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
  const [scanning, setScanning] = useState(false);
  const [scoring, setScoring] = useState(false);

  const { data, isLoading, isError, error, refetch } = useCandidates(filters);
  const approve = useApprove();
  const reject = useReject();

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

  const scanReddit = useCallback(async () => {
    setScanning(true);
    try {
      const result = await triggerRedditIngest(50);
      alert(`Scan complete: ${result.inserted} new, ${result.skipped} duplicates, ${result.errors} errors`);
      refetch();
    } catch (err: any) {
      if (err instanceof TypeError && err.message.includes("fetch")) {
        alert("Reddit scanning requires the local Docker backend.\n\nRun 'docker compose up' on your machine to enable scanning.");
      } else {
        alert(`Scan failed: ${err.message}`);
      }
    } finally {
      setScanning(false);
    }
  }, [refetch]);

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
          <button className="btn btn-scan" onClick={scanReddit} disabled={scanning}>
            {scanning ? "Scanning..." : "Scan Reddit"}
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
