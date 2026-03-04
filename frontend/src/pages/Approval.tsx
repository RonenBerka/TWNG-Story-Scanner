import { useState, useMemo } from "react";
import { useGuitars } from "../lib/guitarQueries";
import GuitarSidebar from "../components/guitars/GuitarSidebar";
import GuitarDetail from "../components/guitars/GuitarDetail";
import type { Guitar } from "../types/guitar";
import "../styles/guitars.css";

export default function Approval() {
  const { data: guitars, isLoading, error } = useGuitars();
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!guitars) return [];
    if (filter === "all") return guitars;
    return guitars.filter((g) => g._db_status === filter);
  }, [guitars, filter]);

  const selected = useMemo(
    () => filtered.find((g) => g._db_id === selectedId) || null,
    [filtered, selectedId]
  );

  function handleSelect(g: Guitar) {
    setSelectedId(g._db_id);
  }

  if (isLoading) {
    return (
      <div className="av-layout">
        <aside className="av-sidebar">
          <div className="av-loading">
            <div className="av-spinner" />
            Loading guitars...
          </div>
        </aside>
        <main className="av-main" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="av-layout">
        <aside className="av-sidebar">
          <div className="av-error">Error: {error.message}</div>
        </aside>
        <main className="av-main" />
      </div>
    );
  }

  return (
    <div className="av-layout">
      <GuitarSidebar
        guitars={filtered}
        total={guitars?.length || 0}
        filter={filter}
        onFilterChange={setFilter}
        selectedId={selectedId}
        onSelect={handleSelect}
      />
      <main className="av-main">
        {!selected ? (
          <div className="av-no-select">
            <div className="av-ns-icon">&#127928;</div>
            <div className="av-ns-title">Select a guitar</div>
            <div className="av-ns-sub">
              {filtered.length} guitars
              {filter !== "all" ? ` with status "${filter}"` : ""}
            </div>
          </div>
        ) : (
          <GuitarDetail guitar={selected} />
        )}
      </main>
    </div>
  );
}
