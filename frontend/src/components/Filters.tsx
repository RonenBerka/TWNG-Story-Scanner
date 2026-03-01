import { useState, useEffect } from "react";
import type { CandidateFilters } from "../lib/api";

interface Props {
  filters: CandidateFilters;
  onChange: (filters: CandidateFilters) => void;
}

export default function Filters({ filters, onChange }: Props) {
  const [search, setSearch] = useState(filters.q || "");

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (search !== (filters.q || "")) {
        onChange({ ...filters, q: search || undefined, offset: 0 });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div className="filters">
      <label>
        Status
        <select
          value={filters.status || ""}
          onChange={(e) => onChange({ ...filters, status: e.target.value || undefined, offset: 0 })}
        >
          <option value="">All</option>
          <option value="new">New</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="reviewed">Reviewed</option>
        </select>
      </label>

      <label>
        Min score
        <input
          type="number"
          step="0.1"
          min="0"
          max="1"
          placeholder="0.0"
          value={filters.min_score ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              min_score: e.target.value ? parseFloat(e.target.value) : undefined,
              offset: 0,
            })
          }
        />
      </label>

      <label>
        Source
        <select
          value={filters.source || ""}
          onChange={(e) =>
            onChange({ ...filters, source: e.target.value || undefined, offset: 0 })
          }
        >
          <option value="">All</option>
          <option value="reddit">Reddit</option>
          <option value="web">Web</option>
        </select>
      </label>

      <label>
        Language
        <select
          value={filters.lang || ""}
          onChange={(e) =>
            onChange({ ...filters, lang: e.target.value || undefined, offset: 0 })
          }
        >
          <option value="">All</option>
          <option value="en">EN</option>
          <option value="he">HE</option>
        </select>
      </label>

      <label>
        Search
        <input
          type="text"
          name="twng-search"
          autoComplete="off"
          placeholder="Search title/excerpt..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
    </div>
  );
}
