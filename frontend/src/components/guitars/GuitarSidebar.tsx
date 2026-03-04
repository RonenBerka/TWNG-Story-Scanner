import type { Guitar } from "../../types/guitar";

const FILTERS = ["all", "pending", "approved", "rejected", "claimed"] as const;

interface Props {
  guitars: Guitar[];
  total: number;
  filter: string;
  onFilterChange: (f: string) => void;
  selectedId: string | null;
  onSelect: (g: Guitar) => void;
}

export default function GuitarSidebar({
  guitars,
  total,
  filter,
  onFilterChange,
  selectedId,
  onSelect,
}: Props) {
  return (
    <aside className="av-sidebar">
      <div className="av-s-head">
        <div className="av-s-schema">seed_guitars &middot; {total} records</div>
        <div className="av-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`av-filter${filter === f ? " active" : ""}`}
              onClick={() => onFilterChange(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="av-s-list">
        {guitars.length === 0 && (
          <div className="av-loading" style={{ minHeight: 80 }}>
            No guitars with status &ldquo;{filter}&rdquo;
          </div>
        )}
        {guitars.map((g) => (
          <GuitarCard
            key={g._db_id}
            g={g}
            active={g._db_id === selectedId}
            onClick={() => onSelect(g)}
          />
        ))}
      </div>

      <div className="av-s-footer">TWNG Story Scanner</div>
    </aside>
  );
}

function GuitarCard({
  g,
  active,
  onClick,
}: {
  g: Guitar;
  active: boolean;
  onClick: () => void;
}) {
  const typeLabel = (g.instrument_type || "guitar").replace(/_/g, " ");
  return (
    <div className={`gc${active ? " active" : ""}`} onClick={onClick}>
      <div className="gc-top">
        <div>
          <div className="gc-instrument">{typeLabel}</div>
          <div className="gc-name">
            {g.brand} {g.model}
          </div>
        </div>
        <div className="gc-year">{g.year || "?"}</div>
      </div>
      {g.finish && <div className="gc-finish">{g.finish}</div>}
      <span className={`gc-status ${g._db_status}`}>{g._db_status}</span>
    </div>
  );
}
