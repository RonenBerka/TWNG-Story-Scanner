import { useState, useEffect, useRef } from "react";
import type { Guitar } from "../../types/guitar";
import ApprovalActions from "../approval/ApprovalActions";

interface Props {
  guitar: Guitar;
}

export default function GuitarDetail({ guitar }: Props) {
  const [shown, setShown] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setShown(false);
    setShowRaw(false);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => setShown(true));
    });
    ref.current?.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [guitar._db_id]);

  const g = guitar;
  const typeLabel = (g.instrument_type || "guitar").replace(/_/g, " ");
  const confEntries = g.provenance?.extraction_confidence
    ? Object.entries(g.provenance.extraction_confidence)
    : [];
  const primarySpecKeys = [
    "body_type", "body_shape", "body", "top", "neck_material",
    "neck_profile", "fingerboard", "pickups", "bridge", "tuners",
    "frets", "scale_length_inches", "nut_width_mm", "weight_lbs",
  ];
  const allSpecKeys = Object.keys(g.specs || {});
  const extendedSpecKeys = allSpecKeys.filter((k) => !primarySpecKeys.includes(k));

  return (
    <div ref={ref} className={`av-detail${shown ? " shown" : ""}`}>
      {/* HERO */}
      <div className="d-hero">
        <div className="d-badge-row">
          <span className="badge type">{typeLabel}</span>
          <span className="badge src">
            {g.provenance?.source_platform || "Unknown"} &middot;{" "}
            {g.provenance?.source_language || "?"}
          </span>
          <span className={`badge db-status ${g._db_status}`}>{g._db_status}</span>
          {confEntries.length > 0 && (
            <span className="badge conf">
              confidence:{" "}
              {confEntries.every(([, v]) => v === "high") ? "all high" : "mixed"}
            </span>
          )}
          {!confEntries.length && g.confidence_score != null && (
            <span className="badge conf">
              score: {g.confidence_score.toFixed(2)}
            </span>
          )}
          {g.estimated_value_range_usd && (
            <span className="badge val">${g.estimated_value_range_usd}</span>
          )}
        </div>
        <div className="d-make">{g.brand}</div>
        <div className="d-name">
          {g.model} <em>&middot; {g.year}</em>
        </div>
        <div className="d-meta-row">
          {g.finish && (
            <div className="d-meta">
              <strong>{g.finish}</strong>
            </div>
          )}
          {g.country_of_origin && (
            <div className="d-meta">
              <strong>{g.country_of_origin}</strong>
            </div>
          )}
          {g.serial_number ? (
            <div className="d-meta">
              Serial <strong>{g.serial_number}</strong>
            </div>
          ) : (
            <div className="d-meta" style={{ color: "var(--muted)" }}>
              Serial: null
            </div>
          )}
        </div>

        <ApprovalActions guitar={g} />
      </div>

      {/* TIMELINE + TAGS + STORY */}
      <div className="d-grid" style={{ marginBottom: 3 }}>
        <div className="panel">
          <div className="p-label">
            Timeline Events ({(g.timeline_events || []).length})
          </div>
          <Timeline events={g.timeline_events || []} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <div className="panel">
            <div className="p-label">Tags ({(g.tags || []).length})</div>
            <div className="tags-wrap">
              {(g.tags || []).length > 0 ? (
                g.tags.map((t) => (
                  <span key={t} className="tag">{t}</span>
                ))
              ) : (
                <span style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
                  No tags
                </span>
              )}
            </div>
          </div>
          <div className="panel amber">
            <div className="p-label">Story</div>
            <StoryBlock story={g.story} provenance={g.provenance} />
          </div>
        </div>
      </div>

      {/* SEARCHING */}
      {g.searching && <SearchingBlock searching={g.searching} />}

      {/* SPECS */}
      {allSpecKeys.length > 0 && (
        <div className="d-grid" style={{ marginBottom: 3 }}>
          <div className="panel">
            <div className="p-label">Primary Specs</div>
            <SpecRows keys={primarySpecKeys} specs={g.specs} />
          </div>
          <div className="panel">
            <div className="p-label">Extended Specs</div>
            <SpecRows keys={extendedSpecKeys} specs={g.specs} />
          </div>
        </div>
      )}

      {/* IMAGES + OWNER */}
      <div className="d-grid" style={{ marginBottom: 3 }}>
        <div className="panel">
          <div className="p-label">Images ({(g.images || []).length})</div>
          <ImagesBlock images={g.images || []} />
        </div>
        <div className="panel">
          <div className="p-label">Owner Contact</div>
          <OwnerBlock contact={g.owner_contact} />
        </div>
      </div>

      {/* CONFIDENCE + ID */}
      <div className="d-grid" style={{ marginBottom: 3 }}>
        <div className="panel">
          <div className="p-label">Extraction Confidence</div>
          <div className="conf-grid">
            {confEntries.length > 0 ? (
              confEntries.map(([k, v]) => (
                <div key={k} className="cf-item">
                  <span className="cf-k">{k}</span>
                  <span className={`cf-v ${v}`}>{v}</span>
                </div>
              ))
            ) : (
              <div className="cf-item">
                <span className="cf-k">overall</span>
                <span
                  className={`cf-v ${
                    (g.confidence_score || 0) > 0.8
                      ? "high"
                      : (g.confidence_score || 0) > 0.5
                        ? "medium"
                        : "low"
                  }`}
                >
                  {g.confidence_score ? g.confidence_score.toFixed(2) : "n/a"}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="panel">
          <div className="p-label">Dedup Fingerprint</div>
          <div className="fingerprint">{g.dedup_fingerprint}</div>
          <div style={{ marginTop: 10 }}>
            <div className="p-label" style={{ marginBottom: 8 }}>
              Database ID
            </div>
            <div className="fingerprint">
              <span style={{ color: "var(--amber-dim)" }}>{g._db_id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* VALUE */}
      {g.estimated_value_range_usd && (
        <div style={{ marginBottom: 16 }}>
          <div className="value-pill">
            {g.estimated_value_range_usd} USD estimated
          </div>
        </div>
      )}

      {/* RAW JSON */}
      <div className="panel" style={{ marginTop: 3 }}>
        <div className="raw-toggle" onClick={() => setShowRaw(!showRaw)}>
          {"{ }"} {showRaw ? "Hide raw JSON" : "Show raw JSON"}
        </div>
        {showRaw && (
          <pre className="raw-json">{JSON.stringify(g, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ── */

function Timeline({ events }: { events: any[] }) {
  if (events.length === 0) {
    return (
      <div style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
        No timeline events
      </div>
    );
  }
  return (
    <div className="tl">
      {events.map((ev: any, i: number) => (
        <div key={i} className="tl-item">
          <div className="tl-spine">
            <div className={`tl-dot ${ev.tier || "story_based"}`} />
            {i < events.length - 1 && <div className="tl-line" />}
          </div>
          <div className="tl-body">
            <div className={`tl-tier ${ev.tier || "story_based"}`}>
              {(ev.tier || "story").replace(/_/g, " ")}
            </div>
            <div className="tl-title">{ev.title}</div>
            <div className="tl-desc">{ev.description}</div>
            <div className="tl-foot">
              <span className="tl-chip">
                {ev.event_date
                  ? `${ev.event_date.substring(0, 4)} \u00B7 ${ev.date_precision}`
                  : "date unknown"}
              </span>
              {ev.location && <span className="tl-chip">{ev.location}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function StoryBlock({
  story,
  provenance,
}: {
  story: Guitar["story"];
  provenance: Guitar["provenance"];
}) {
  if (!story) {
    return (
      <div style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
        No story data
      </div>
    );
  }
  const storyText =
    story.original_text_translated || story.narrative || story.context || "";
  if (!storyText) {
    return (
      <div style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
        No story text
      </div>
    );
  }
  return (
    <>
      <div className="story-q">{storyText}</div>
      <div className="story-att">
        {provenance?.source_language === "he"
          ? "Translated from Hebrew"
          : provenance?.source_language || ""}{" "}
        &middot; {provenance?.source_platform || "Unknown source"}
      </div>
      {story.narrative && story.narrative !== storyText && (
        <div className="narrative">{story.narrative}</div>
      )}
      {story.famous_connection && (
        <div className="famous">{story.famous_connection}</div>
      )}
    </>
  );
}

function SpecRows({ keys, specs }: { keys: string[]; specs: Record<string, any> }) {
  const filtered = keys.filter((k) => specs[k] !== undefined);
  if (filtered.length === 0) {
    return (
      <div style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
        No specs
      </div>
    );
  }
  return (
    <>
      {filtered.map((k) => (
        <div key={k} className="spec-row">
          <span className="sk">{k.replace(/_/g, " ")}</span>
          <span className="sv">{String(specs[k])}</span>
        </div>
      ))}
    </>
  );
}

function ImagesBlock({ images }: { images: any[] }) {
  if (images.length === 0) {
    return (
      <div style={{ fontSize: 12, color: "var(--dim)", fontFamily: "monospace" }}>
        No images
      </div>
    );
  }
  return (
    <div className="images-wrap">
      {images.map((img: any, i: number) => (
        <div key={i} className="img-item">
          {img.is_main && <span className="img-badge">main</span>}
          <div className="img-caption">{img.caption || ""}</div>
          {img.url ? (
            <a
              href={img.url}
              target="_blank"
              rel="noreferrer"
              style={{
                fontSize: 11,
                color: "var(--amber)",
                fontFamily: "monospace",
              }}
            >
              {img.url}
            </a>
          ) : (
            <div className="no-url">url: null</div>
          )}
          {img.confirms && (
            <div className="img-confirms">
              {img.confirms.map((c: string) => (
                <span key={c} className="img-cf">{c}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function OwnerBlock({ contact }: { contact: Guitar["owner_contact"] }) {
  if (!contact) {
    return (
      <div style={{ color: "var(--dim)" }}>No contact data</div>
    );
  }
  const fields: (keyof typeof contact)[] = [
    "name",
    "email",
    "facebook_profile",
    "invite_sent",
    "invite_sent_at",
  ];
  return (
    <div className="owner-row">
      {fields.map((k) => (
        <div key={k} className="owner-field">
          <span className="of-k">{k}</span>
          <NullVal v={contact[k]} />
        </div>
      ))}
    </div>
  );
}

function NullVal({ v }: { v: any }) {
  if (v === null || v === undefined || v === "") {
    return <span className="of-v null">null</span>;
  }
  if (typeof v === "boolean") {
    return (
      <span className={`of-v ${v ? "sent" : "pending"}`}>{String(v)}</span>
    );
  }
  return <span className="of-v">{String(v)}</span>;
}

function SearchingBlock({ searching }: { searching: Record<string, any> }) {
  return (
    <div style={{ marginBottom: 3 }}>
      <div className="panel" style={{ borderColor: "rgba(220,38,38,0.22)" }}>
        <div className="p-label">Searching</div>
        <div className="searching-card">
          <div className="searching-title">
            Owner is actively looking for this guitar
          </div>
          {Object.entries(searching).map(([k, v]) => (
            <div key={k} className="sr">
              <span className="sk2">{k.replace(/_/g, " ")}</span>
              <span className="sv2">{String(v)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
