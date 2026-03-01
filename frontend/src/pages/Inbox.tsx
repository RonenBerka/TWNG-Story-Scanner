import { useState, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { useCandidates, useApprove, useReject } from "../lib/queries";
import type { Candidate, CandidateFilters } from "../lib/api";
import CandidateTable from "../components/CandidateTable";
import CandidatePreview from "../components/CandidatePreview";
import Filters from "../components/Filters";
import FbArchiveHelp from "../components/FbArchiveHelp";

const PAGE_SIZE = 30;

export default function Inbox() {
  const { logout } = useAuth();
  const [filters, setFilters] = useState<CandidateFilters>({
    status: "new",
    limit: PAGE_SIZE,
    offset: 0,
  });
  const [selected, setSelected] = useState<Candidate | null>(null);

  const { data, isLoading, isError, error } = useCandidates(filters);
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

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;
  const currentPage = data ? Math.floor((filters.offset || 0) / PAGE_SIZE) + 1 : 1;

  return (
    <div className="inbox-layout">
      <header className="inbox-header">
        <h1>TWNG Story Scanner</h1>
        <div className="header-right">
          <FbArchiveHelp />
          <span className="total-badge">
            {data ? `${data.total} candidates` : "..."}
          </span>
          <button className="btn btn-logout" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <Filters filters={filters} onChange={setFilters} />

      <div className="inbox-content">
        <div className={`inbox-table-area ${selected ? "has-preview" : ""}`}>
          {isLoading && <div className="loading">Loading candidates...</div>}
          {isError && (
            <div className="error-box">
              Error: {error?.message || "Failed to load candidates"}
            </div>
          )}
          {data && (
            <>
              <CandidateTable
                data={data.items}
                onRowClick={handleRowClick}
                selectedId={selected?.id}
              />
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() =>
                      setFilters((f) => ({ ...f, offset: (f.offset || 0) - PAGE_SIZE }))
                    }
                  >
                    Prev
                  </button>
                  <span>
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() =>
                      setFilters((f) => ({ ...f, offset: (f.offset || 0) + PAGE_SIZE }))
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
          <div className="inbox-preview-area">
            <button
              className="preview-close"
              onClick={() => setSelected(null)}
              title="Close preview"
            >
              &times;
            </button>
            <CandidatePreview
              candidate={selected}
              onApprove={handleApprove}
              onReject={handleReject}
              isApproving={approve.isPending}
              isRejecting={reject.isPending}
            />
          </div>
        )}
      </div>
    </div>
  );
}
