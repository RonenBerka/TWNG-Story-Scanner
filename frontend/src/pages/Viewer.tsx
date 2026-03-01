import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchViewerData, type ViewerData } from "../lib/api";

export default function Viewer() {
  const navigate = useNavigate();
  const [data, setData] = useState<ViewerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  useEffect(() => {
    fetchViewerData()
      .then((d) => {
        setData(d);
        if (d.guitars.length > 0) setSelectedIdx(0);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const guitar = data && selectedIdx !== null ? (data.guitars[selectedIdx] as any) : null;

  return (
    <>
      <style>{VIEWER_CSS}</style>
      <div className="v-app">
        <aside className="v-sidebar">
          <div className="v-s-head">
            <div className="v-s-logo">TWNG</div>
            <div className="v-s-meta">Extraction Viewer &middot; <span>v1.1.0</span></div>
            {data && <div className="v-s-schema">{data.guitars.length} records</div>}
            <button className="v-nav-btn" onClick={() => navigate("/inbox")}>&larr; Back to Inbox</button>
          </div>
          <div className="v-s-list">
            {loading && <div className="v-loading">Loading...</div>}
            {error && <div className="v-error">{error}</div>}
            {data?.guitars.map((g: any, i: number) => (
              <GuitarCard key={g.id || i} g={g} active={i === selectedIdx} onClick={() => setSelectedIdx(i)} />
            ))}
          </div>
          <div className="v-s-footer">TWNG Story Scanner</div>
        </aside>
        <main className="v-main">
          {!guitar ? (
            <div className="v-no-select">
              <div className="v-ns-icon">&#127928;</div>
              <div className="v-ns-t">Select a guitar</div>
              <div className="v-ns-s">{data ? `${data.guitars.length} records` : "Loading..."}</div>
            </div>
          ) : (
            <GuitarDetail g={guitar} metadata={data!.extraction_metadata} />
          )}
        </main>
      </div>
    </>
  );
}

function GuitarCard({ g, active, onClick }: { g: any; active: boolean; onClick: () => void }) {
  const typeLabel = (g.instrument_type || "guitar").replace(/_/g, " ");
  const statusLabel = g.status === "sold_searching" ? "Sold - Searching" : "Owned";
  return (
    <div className={`v-guitar-card${active ? " active" : ""}`} onClick={onClick}>
      <div className="v-gc-top">
        <div>
          <div className="v-gc-instrument">{typeLabel}</div>
          <div className="v-gc-name">{g.brand} {g.model}</div>
        </div>
        <div className="v-gc-year">{g.year}</div>
      </div>
      <div className="v-gc-finish">{g.finish}</div>
      <span className={`v-gc-status ${g.status}`}>{statusLabel}</span>
    </div>
  );
}

function GuitarDetail({ g, metadata }: { g: any; metadata: Record<string, unknown> }) {
  const [showRaw, setShowRaw] = useState(false);
  const typeLabel = (g.instrument_type || "guitar").replace(/_/g, " ");
  const statusLabel = g.status === "sold_searching" ? "Sold - Searching" : "Owned";
  const confEntries = Object.entries(g.provenance?.extraction_confidence || {});
  const primarySpecKeys = ["body_type","body_shape","body","top","neck_material","neck_profile","fingerboard","pickups","bridge","tuners","frets","scale_length_inches","nut_width_mm","weight_lbs"];
  const specs = g.specs || {};
  const extendedSpecKeys = Object.keys(specs).filter((k) => !primarySpecKeys.includes(k));

  return (
    <div className="v-detail shown">
      <div className="v-d-hero">
        <div className="v-d-badge-row">
          <span className="v-badge type">{typeLabel}</span>
          <span className="v-badge src">{g.provenance?.source_platform || "Unknown"} &middot; {g.provenance?.source_language || ""}&#8594;EN</span>
          <span className="v-badge conf">confidence: {confEntries.every(([,v]) => v === "high") ? "all high" : "mixed"}</span>
          {g.estimated_value_range_usd && <span className="v-badge val">${g.estimated_value_range_usd}</span>}
        </div>
        <div className="v-d-make">{g.brand}</div>
        <div className="v-d-name">{g.model} <em>&middot; {g.year}</em></div>
        <div className="v-d-meta-row">
          <div className="v-d-meta"><strong>{g.finish}</strong></div>
          <div className="v-d-meta"><strong>{g.country_of_origin}</strong></div>
          {g.serial_number ? <div className="v-d-meta">Serial <strong>{g.serial_number}</strong></div> : <div className="v-d-meta" style={{color:"var(--v-muted)"}}>Serial: null</div>}
        </div>
        <div className={`v-d-status ${g.status}`}>{statusLabel}</div>
      </div>

      <div className="v-d-grid">
        <div className="v-panel">
          <div className="v-p-label">Timeline Events ({(g.timeline_events||[]).length})</div>
          <Timeline events={g.timeline_events||[]} />
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:"3px"}}>
          <div className="v-panel">
            <div className="v-p-label">Tags ({(g.tags||[]).length})</div>
            <div className="v-tags-wrap">{(g.tags||[]).map((t:string) => <span key={t} className="v-tag">{t}</span>)}</div>
          </div>
          <div className="v-panel amber">
            <div className="v-p-label">Story</div>
            <StoryBlock story={g.story} metadata={metadata} />
          </div>
        </div>
      </div>

      {g.searching && <SearchingBlock searching={g.searching} />}

      <div className="v-d-grid" style={{marginTop:3}}>
        <div className="v-panel"><div className="v-p-label">Primary Specs</div><SpecRows keys={primarySpecKeys} specs={specs} /></div>
        <div className="v-panel"><div className="v-p-label">Extended Specs</div><SpecRows keys={extendedSpecKeys} specs={specs} /></div>
      </div>

      <div className="v-d-grid" style={{marginTop:3}}>
        <div className="v-panel"><div className="v-p-label">Images ({(g.images||[]).length})</div><ImagesBlock images={g.images||[]} /></div>
        <div className="v-panel"><div className="v-p-label">Owner Contact</div><OwnerBlock contact={g.owner_contact} /></div>
      </div>

      <div className="v-d-grid" style={{marginTop:3}}>
        <div className="v-panel">
          <div className="v-p-label">Extraction Confidence</div>
          <div className="v-conf-grid">{confEntries.map(([k,v]) => <div key={k} className="v-cf-item"><span className="v-cf-k">{k}</span><span className={`v-cf-v ${v}`}>{v as string}</span></div>)}</div>
        </div>
        <div className="v-panel">
          <div className="v-p-label">Dedup Fingerprint</div>
          <div className="v-fingerprint">{g.dedup_fingerprint}</div>
          <div style={{marginTop:10}}><div className="v-p-label" style={{marginBottom:8}}>Record ID</div><div className="v-fingerprint"><span style={{color:"var(--v-amber-dim)"}}>{g.id}</span></div></div>
        </div>
      </div>

      <div className="v-panel" style={{marginTop:3}}>
        <div className="v-raw-toggle" onClick={() => setShowRaw(!showRaw)}>{"{ }"} {showRaw ? "Hide raw JSON" : "Show raw JSON"}</div>
        {showRaw && <pre className="v-raw-json">{JSON.stringify(g,null,2)}</pre>}
      </div>

      {g.estimated_value_range_usd && <div style={{marginTop:12}}><div className="v-value-pill">{g.estimated_value_range_usd} USD estimated</div></div>}
    </div>
  );
}

function Timeline({ events }: { events: any[] }) {
  return (
    <div className="v-tl">
      {events.map((ev:any,i:number) => (
        <div key={i} className="v-tl-item">
          <div className="v-tl-spine"><div className={`v-tl-dot ${ev.tier}`} />{i < events.length-1 && <div className="v-tl-line" />}</div>
          <div className="v-tl-body">
            <div className={`v-tl-tier ${ev.tier}`}>{ev.tier.replace("_"," ")}</div>
            <div className="v-tl-title">{ev.title}</div>
            <div className="v-tl-desc">{ev.description}</div>
            <div className="v-tl-foot">
              <span className="v-tl-chip">{ev.event_date ? `${ev.event_date.substring(0,4)} - ${ev.date_precision}` : "date unknown"}</span>
              {ev.location && <span className="v-tl-chip">{ev.location}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function StoryBlock({ story, metadata }: { story: any; metadata: Record<string, unknown> }) {
  if (!story) return <div style={{color:"var(--v-dim)"}}>No story data</div>;
  return (
    <>
      <div className="v-story-q">{story.original_text_translated}</div>
      <div className="v-story-att">Translated from {(metadata.original_language as string)||"source"} &middot; {(metadata.source_platform as string)||""} &middot; {(metadata.extraction_date as string)||""}</div>
      {story.narrative && <div className="v-narrative">{story.narrative}</div>}
      {story.famous_connection && <div className="v-famous">{story.famous_connection}</div>}
    </>
  );
}

function SpecRows({ keys, specs }: { keys: string[]; specs: Record<string, any> }) {
  return <>{keys.filter(k => specs[k] !== undefined).map(k => <div key={k} className="v-spec-row"><span className="v-sk">{k.replace(/_/g," ")}</span><span className="v-sv">{String(specs[k])}</span></div>)}</>;
}

function ImagesBlock({ images }: { images: any[] }) {
  if (images.length === 0) return <div style={{fontSize:12,color:"var(--v-dim)",fontFamily:"monospace"}}>No images — URL not captured at extraction</div>;
  return (
    <div className="v-images-wrap">
      {images.map((img:any,i:number) => (
        <div key={i} className="v-img-item">
          {img.is_main && <span className="v-img-badge">main</span>}
          <div className="v-img-caption">{img.caption}</div>
          {img.url ? <a href={img.url} target="_blank" rel="noreferrer" style={{fontSize:11,color:"var(--v-amber)",fontFamily:"monospace"}}>{img.url}</a> : <div className="v-no-url">url: null</div>}
          {img.confirms && <div className="v-img-confirms">{img.confirms.map((c:string) => <span key={c} className="v-img-cf">{c}</span>)}</div>}
        </div>
      ))}
    </div>
  );
}

function OwnerBlock({ contact }: { contact: any }) {
  if (!contact) return <div style={{color:"var(--v-dim)"}}>No contact data</div>;
  const fields = ["name","email","facebook_profile","invite_sent","invite_sent_at"];
  return <div className="v-owner-row">{fields.map(k => <div key={k} className="v-owner-field"><span className="v-of-k">{k}</span><NullVal v={contact[k]} /></div>)}</div>;
}

function NullVal({ v }: { v: any }) {
  if (v === null || v === undefined || v === "") return <span className="v-of-v null">null</span>;
  if (typeof v === "boolean") return <span className={`v-of-v ${v?"sent":"pending"}`}>{String(v)}</span>;
  return <span className="v-of-v">{String(v)}</span>;
}

function SearchingBlock({ searching }: { searching: Record<string, any> }) {
  return (
    <div style={{marginTop:3}}>
      <div className="v-panel" style={{borderColor:"rgba(248,113,113,0.22)"}}>
        <div className="v-p-label">Searching</div>
        <div className="v-searching-card">
          <div className="v-searching-title">Owner is actively looking for this guitar</div>
          {Object.entries(searching).map(([k,v]) => <div key={k} className="v-sr"><span className="v-sk2">{k.replace(/_/g," ")}</span><span className="v-sv2">{String(v)}</span></div>)}
        </div>
      </div>
    </div>
  );
}

const VIEWER_CSS = `
.v-app{--v-amber:#C8860A;--v-amber-b:#E8A020;--v-amber-dim:#7A520A;--v-ag:rgba(200,134,10,0.10);--v-ab:rgba(200,134,10,0.22);--v-bg:#080705;--v-bg1:#0E0B07;--v-bg2:#161209;--v-bg3:#1E1810;--v-border:#1C1810;--v-border2:#272018;--v-border3:#332A1C;--v-text:#E8DFCF;--v-dim:#7A6E5E;--v-muted:#2E2820;--v-green:#52C97A;--v-blue:#5B9CF6;--v-red:#F87171;--v-purple:#A78BFA}
.v-app{display:grid;grid-template-columns:340px 1fr;min-height:100vh;font-family:'DM Sans',-apple-system,BlinkMacSystemFont,sans-serif;color:var(--v-text);background:var(--v-bg);-webkit-font-smoothing:antialiased}
.v-sidebar{background:var(--v-bg1);border-right:1px solid var(--v-border);position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column}
.v-sidebar::-webkit-scrollbar{width:3px}.v-sidebar::-webkit-scrollbar-thumb{background:var(--v-border2);border-radius:2px}
.v-s-head{padding:24px 20px 16px;border-bottom:1px solid var(--v-border)}
.v-s-logo{font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:500;color:var(--v-amber);letter-spacing:0.14em;margin-bottom:2px}
.v-s-meta{font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--v-dim);letter-spacing:0.08em}.v-s-meta span{color:var(--v-amber-dim)}
.v-s-schema{display:inline-flex;align-items:center;gap:6px;margin-top:8px;background:var(--v-ag);border:1px solid var(--v-ab);border-radius:6px;padding:3px 10px;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--v-amber)}
.v-s-schema::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--v-green);flex-shrink:0}
.v-nav-btn{display:block;margin-top:12px;background:var(--v-ag);border:1px solid var(--v-ab);border-radius:6px;color:var(--v-amber);font-size:11px;font-family:'JetBrains Mono',monospace;padding:5px 12px;cursor:pointer;transition:all .15s}
.v-nav-btn:hover{background:var(--v-ab)}
.v-s-list{padding:12px 10px;flex:1}
.v-s-footer{padding:14px 16px;border-top:1px solid var(--v-border);font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--v-dim)}
.v-guitar-card{padding:14px;border-radius:10px;cursor:pointer;transition:all .18s;margin-bottom:4px;border:1px solid transparent;position:relative}
.v-guitar-card:hover{background:var(--v-bg2);border-color:var(--v-border)}
.v-guitar-card.active{background:var(--v-bg2);border-color:var(--v-ab)}
.v-guitar-card.active::before{content:'';position:absolute;left:0;top:14px;bottom:14px;width:2px;background:var(--v-amber);border-radius:0 2px 2px 0}
.v-gc-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:6px}
.v-gc-instrument{font-size:9px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.12em;color:var(--v-dim);margin-bottom:3px}
.v-gc-name{font-family:'Cormorant Garamond',Georgia,serif;font-size:17px;font-weight:500;line-height:1.2;color:var(--v-text)}
.v-gc-year{font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--v-amber);background:var(--v-ag);border:1px solid var(--v-ab);border-radius:5px;padding:2px 8px;flex-shrink:0;margin-top:2px}
.v-gc-finish{font-size:11px;color:var(--v-dim);margin-bottom:6px}
.v-gc-status{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:600;letter-spacing:.04em;padding:2px 8px;border-radius:5px}
.v-gc-status.owned{background:rgba(82,201,122,0.08);border:1px solid rgba(82,201,122,0.2);color:var(--v-green)}
.v-gc-status.sold_searching{background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.2);color:var(--v-red)}
.v-gc-status.owned::before,.v-gc-status.sold_searching::before{content:'';width:4px;height:4px;border-radius:50%;background:currentColor}
.v-main{overflow-y:auto;position:relative}.v-main::-webkit-scrollbar{width:4px}.v-main::-webkit-scrollbar-thumb{background:var(--v-border2);border-radius:2px}
.v-no-select{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:40px}
.v-ns-icon{font-size:64px;margin-bottom:20px;filter:grayscale(0.4)}.v-ns-t{font-family:'Cormorant Garamond',Georgia,serif;font-size:28px;font-weight:400;color:var(--v-dim);margin-bottom:8px}.v-ns-s{font-size:13px;color:var(--v-muted)}
.v-loading{padding:20px;text-align:center;color:var(--v-dim);font-size:13px}
.v-error{padding:12px;background:rgba(248,113,113,0.1);color:var(--v-red);border-radius:6px;margin:8px;font-size:12px}
.v-detail{padding:40px 44px 80px;min-height:100vh}.v-detail.shown{opacity:1}
.v-d-hero{margin-bottom:32px;padding-bottom:28px;border-bottom:1px solid var(--v-border)}
.v-d-badge-row{display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.v-badge{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-family:'JetBrains Mono',monospace;padding:3px 10px;border-radius:6px;font-weight:500}
.v-badge.type{background:var(--v-bg2);border:1px solid var(--v-border2);color:var(--v-dim)}
.v-badge.src{background:var(--v-ag);border:1px solid var(--v-ab);color:var(--v-amber-dim)}
.v-badge.conf{background:rgba(91,156,246,0.08);border:1px solid rgba(91,156,246,0.2);color:#7BA4F0}
.v-badge.val{background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);color:var(--v-purple)}
.v-d-make{font-size:11px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--v-amber);margin-bottom:6px}
.v-d-name{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(30px,4vw,48px);font-weight:400;line-height:1.1;margin-bottom:8px}.v-d-name em{font-style:italic;color:var(--v-dim)}
.v-d-meta-row{display:flex;gap:24px;flex-wrap:wrap;margin-bottom:12px}
.v-d-meta{font-size:12px;color:var(--v-dim);display:flex;align-items:center;gap:6px}.v-d-meta strong{color:var(--v-text);font-weight:500}
.v-d-status{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:5px 14px;border-radius:8px}
.v-d-status.owned{background:rgba(82,201,122,0.08);border:1px solid rgba(82,201,122,0.22);color:var(--v-green)}
.v-d-status.sold_searching{background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.22);color:var(--v-red)}
.v-d-status::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor;animation:v-pulse 2.4s ease-in-out infinite}
@keyframes v-pulse{0%,100%{opacity:1}50%{opacity:.3}}
.v-d-grid{display:grid;grid-template-columns:1fr 1fr;gap:3px;margin-bottom:3px}
.v-panel{background:var(--v-bg1);border:1px solid var(--v-border);border-radius:12px;padding:20px 22px}
.v-panel.amber{background:linear-gradient(135deg,rgba(200,134,10,0.06),transparent);border-color:var(--v-ab)}
.v-p-label{font-size:9px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--v-dim);font-family:'JetBrains Mono',monospace;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.v-p-label::after{content:'';flex:1;height:1px;background:var(--v-border)}
.v-spec-row{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:6px 0;border-bottom:1px solid var(--v-border)}.v-spec-row:last-child{border-bottom:none}
.v-sk{font-size:11px;color:var(--v-dim);flex-shrink:0}.v-sv{font-size:11px;font-weight:500;text-align:right;color:var(--v-text);font-family:'JetBrains Mono',monospace}
.v-tags-wrap{display:flex;flex-wrap:wrap;gap:6px}
.v-tag{font-size:11px;font-family:'JetBrains Mono',monospace;background:var(--v-ag);border:1px solid var(--v-ab);color:#9A7020;padding:4px 10px;border-radius:6px;transition:all .15s;cursor:default}
.v-tag:hover{background:rgba(200,134,10,0.18);color:var(--v-amber)}
.v-tl{display:flex;flex-direction:column;gap:0}.v-tl-item{display:flex;gap:12px;position:relative}
.v-tl-spine{display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:16px}
.v-tl-dot{width:10px;height:10px;border-radius:50%;border:2px solid;background:var(--v-bg);flex-shrink:0;margin-top:4px}
.v-tl-dot.factual{border-color:var(--v-blue)}.v-tl-dot.documented{border-color:var(--v-green)}.v-tl-dot.story_based{border-color:var(--v-amber)}.v-tl-dot.system{border-color:var(--v-purple)}
.v-tl-line{width:1px;flex:1;min-height:16px;background:var(--v-border2);margin:3px auto}
.v-tl-body{flex:1;padding-bottom:20px}
.v-tl-tier{font-size:9px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.v-tl-tier.factual{color:var(--v-blue)}.v-tl-tier.documented{color:var(--v-green)}.v-tl-tier.story_based{color:var(--v-amber)}.v-tl-tier.system{color:var(--v-purple)}
.v-tl-title{font-size:14px;font-weight:500;margin-bottom:4px;line-height:1.35}
.v-tl-desc{font-size:12px;color:var(--v-dim);line-height:1.65;margin-bottom:4px}
.v-tl-foot{display:flex;gap:12px;flex-wrap:wrap}
.v-tl-chip{font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--v-dim);display:flex;align-items:center;gap:4px}
.v-story-q{font-family:'Cormorant Garamond',Georgia,serif;font-size:18px;font-style:italic;line-height:1.78;color:var(--v-dim);position:relative;padding-left:2px}
.v-story-att{font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--v-dim);margin-top:14px}
.v-narrative{font-size:14px;line-height:1.8;color:var(--v-dim);border-left:2px solid var(--v-ab);padding-left:16px;margin-top:12px}
.v-famous{display:flex;align-items:center;gap:10px;background:rgba(167,139,250,0.05);border:1px solid rgba(167,139,250,0.18);border-radius:8px;padding:10px 14px;margin-top:12px;font-size:12px;color:var(--v-purple)}
.v-owner-row{display:flex;flex-direction:column;gap:8px}
.v-owner-field{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--v-border);font-size:12px}.v-owner-field:last-child{border-bottom:none}
.v-of-k{color:var(--v-dim)}.v-of-v{font-family:'JetBrains Mono',monospace;font-size:11px}.v-of-v.null{color:var(--v-muted);font-style:italic}.v-of-v.sent{color:var(--v-green)}.v-of-v.pending{color:var(--v-amber-dim)}
.v-images-wrap{display:flex;flex-direction:column;gap:8px}
.v-img-item{background:var(--v-bg2);border:1px solid var(--v-border2);border-radius:8px;padding:12px 14px}
.v-img-badge{font-size:9px;font-family:'JetBrains Mono',monospace;color:var(--v-amber);background:var(--v-ag);border:1px solid var(--v-ab);border-radius:4px;padding:2px 7px;display:inline-block;margin-bottom:6px}
.v-img-caption{font-size:12px;color:var(--v-text);margin-bottom:6px;line-height:1.5}
.v-img-confirms{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.v-img-cf{font-size:10px;background:rgba(82,201,122,0.06);border:1px solid rgba(82,201,122,0.18);color:#5CB87A;padding:2px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace}
.v-no-url{font-size:11px;color:var(--v-dim);font-family:'JetBrains Mono',monospace;margin-top:4px}
.v-searching-card{background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.18);border-radius:10px;padding:16px 18px}
.v-searching-title{font-size:12px;font-weight:700;color:var(--v-red);margin-bottom:10px}
.v-sr{display:flex;justify-content:space-between;font-size:12px;padding:5px 0;border-bottom:1px solid rgba(248,113,113,0.1)}.v-sr:last-child{border-bottom:none}
.v-sk2{color:var(--v-dim)}.v-sv2{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--v-red);text-align:right;max-width:60%}
.v-conf-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.v-cf-item{display:flex;justify-content:space-between;align-items:center;padding:5px 8px;background:var(--v-bg2);border-radius:6px;border:1px solid var(--v-border)}
.v-cf-k{font-size:11px;color:var(--v-dim)}.v-cf-v{font-size:10px;font-family:'JetBrains Mono',monospace;font-weight:600}
.v-cf-v.high{color:var(--v-green)}.v-cf-v.medium{color:var(--v-amber)}.v-cf-v.low{color:var(--v-red)}
.v-value-pill{display:inline-flex;align-items:center;gap:8px;background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.22);border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;color:var(--v-purple)}
.v-fingerprint{font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--v-muted);padding:10px 12px;background:var(--v-bg2);border:1px solid var(--v-border);border-radius:6px;word-break:break-all;line-height:1.6}
.v-raw-toggle{font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--v-dim);cursor:pointer;display:flex;align-items:center;gap:6px;padding:8px 0;user-select:none;transition:color .15s}
.v-raw-toggle:hover{color:var(--v-text)}
.v-raw-json{background:var(--v-bg2);border:1px solid var(--v-border);border-radius:8px;padding:16px;font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--v-dim);overflow-x:auto;white-space:pre-wrap;word-break:break-word;line-height:1.7;margin-top:8px}
@media(max-width:900px){.v-app{grid-template-columns:1fr}.v-sidebar{position:relative;height:auto}.v-detail{padding:28px 20px 60px}.v-d-grid{grid-template-columns:1fr}}
`;
