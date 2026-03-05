import type { Guitar } from "../../types/guitar";

const FILTERS = ["all", "pending", "approved", "rejected", "claimed"] as const;

interface Props {
  guitars: Guitar[];
  total: number;
  filter: string;
  onFilterChange: (f: string) => void;
  selectedId: string | null;
  onSelect: (g: Guitar) => void;
  checkedIds?: Set<string>;
  onToggleCheck?: (id: string) => void;
  onSelectAll?: () => void;
  onExport?: () => void;
  exporting?: boolean;
}

export default function GuitarSidebar({
  guitars,
  total,
  filter,
  onFilterChange,
  selectedId,
  onSelect,
  checkedIds,
  onToggleCheck,
  onSelectAll,
  onExport,
  exporting,
}: Props) {
  const checkedCount = checkedIds?.size || 0;
  const allChecked = checkedCount > 0 && checkedCount === guitars.length;

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

        {onExport && (
          <div className="av-export-bar">
            <label className="av-select-all" onClick={onSelectAll}>
              <input
                type="checkbox"
                checked={allChecked}
                readOnly
                className="av-checkbox"
              />
              <span>Select all</span>
            </label>
            <button
              className="av-export-btn"
              onClick={onExport}
              disabled={checkedCount === 0 || exporting}
            >
              {exporting
                ? "Exporting..."
                : `Export${checkedCount > 0 ? ` (${checkedCount})` : ""}`}
            </button>
          </div>
        )}
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
            checked={checkedIds?.has(g._db_id) || false}
            onCheck={onToggleCheck ? () => onToggleCheck(g._db_id) : undefined}
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
  checked,
  onCheck,
  onClick,
}: {
  g: Guitar;
  active: boolean;
  checked: boolean;
  onCheck?: () => void;
  onClick: () => void;
}) {
  const typeLabel = (g.instrument_type || "guitar").replace(/_/g, " ");
  return (
    <div className={`gc${active ? " active" : ""}${checked ? " checked" : ""}`} onClick={onClick}>
      {onCheck && (
        <input
          type="checkbox"
          className="av-checkbox gc-check"
          checked={checked}
          onClick={(e) => e.stopPropagation()}
          onChange={onCheck}
        />
      )}
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
