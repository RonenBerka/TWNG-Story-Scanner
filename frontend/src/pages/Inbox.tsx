import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
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
          <button
            className="btn btn-viewer"
            onClick={() => navigate("/viewer")}
          >
            Viewer
          </button>
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
              Error: {(error as Error)?.message || "Unknown error"}
            </div>
          )}
          {data && (
            <>
              <CandidateTable
                candidates={data.items}
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
            onClose={() => setSelected(null)}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        )}
      </div>
    </div>
  );
}
