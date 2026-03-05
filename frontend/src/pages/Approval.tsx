import { useState, useMemo, useCallback } from "react";
import { useGuitars } from "../lib/guitarQueries";
import GuitarSidebar from "../components/guitars/GuitarSidebar";
import GuitarDetail from "../components/guitars/GuitarDetail";
import type { Guitar } from "../types/guitar";
import "../styles/guitars.css";

export default function Approval() {
  const { data: guitars, isLoading, error } = useGuitars();
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);

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

  const handleToggleCheck = useCallback((id: string) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (checkedIds.size === filtered.length) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(filtered.map((g) => g._db_id)));
    }
  }, [filtered, checkedIds.size]);

  const handleExport = useCallback(async () => {
    if (!guitars || checkedIds.size === 0) return;
    setExporting(true);
    try {
      const selectedGuitars = guitars.filter((g) => checkedIds.has(g._db_id));
      const exportData = {
        twng_import_version: "1.0",
        exported_at: new Date().toISOString(),
        source: "TWNG Story Scanner",
        total_items: selectedGuitars.length,
        items: selectedGuitars.map((g) => ({
          instrument: {
            make: g.brand,
            model: g.model,
            year: g.year_exact,
            serial_number: g.serial_number,
            finish: g.finish,
            country_of_origin: g.country_of_origin,
            description: g.story?.narrative || g.story?.summary || null,
            specs: g.specs || {},
            custom_fields: {
              instrument_type: g.instrument_type,
              dedup_fingerprint: g.dedup_fingerprint,
            },
          },
          owner_contact: {
            source_platform: g.provenance?.source_platform || "unknown",
            source_post_url: g.provenance?.source_url || null,
            display_name: g.owner_contact?.name || null,
            email: g.owner_contact?.email || null,
            facebook_profile: g.owner_contact?.facebook_profile || null,
          },
          images: (g.images || []).map((img: any) => ({
            url: img.url || img.src || null,
            caption: img.caption || null,
            is_main: img.is_main || false,
          })),
          tags: g.tags || [],
          timeline_events: g.timeline_events || [],
          story: g.story || null,
          source_metadata: {
            source_platform: g.provenance?.source_platform || "unknown",
            source_url: g.provenance?.source_url || null,
            confidence_score: g.confidence_score,
          },
        })),
      };
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `twng_export_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }, [guitars, checkedIds]);

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
        checkedIds={checkedIds}
        onToggleCheck={handleToggleCheck}
        onSelectAll={handleSelectAll}
        onExport={handleExport}
        exporting={exporting}
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
