# Add-on Tasks — Facebook Archive Mode (Tasks 11–12)

These two tasks enable **Facebook Group Archive Mode** via:
1) A backend batch ingest endpoint for captured search results  
2) A minimal Chrome Extension (MV3) that captures search-result post URLs + snippets from the currently open Facebook group search page.

Important constraints
- No automation that navigates Facebook or bypasses protections.
- The extension only captures **what is already rendered in the page** when the user clicks “Capture”.
- Store minimal data: URL + short excerpt + metadata (group name/query/captured_at). No bulk scraping of full post bodies.

---

## Task 11 — FB-Archive-API: Batch ingest endpoint

Goal
- Add an authenticated endpoint that receives captured Facebook group search results (URLs + excerpts) and stores them as CandidateStory rows with dedupe.

Inputs
- Backend + DB schema exist.
- Auth exists (Task 4). If auth is not yet implemented, still implement the endpoint but keep it under the same auth dependency used for curation routes.

Outputs
- `POST /ingest/facebook/search-results`
- Inserts CandidateStory with `source_type='facebook_group_archive'` and `source_id=sha256(source_url)`

DoD
- Endpoint validates payload, rejects invalid items, and returns counts: inserted/duplicates/invalid.
- Running the same payload twice results in duplicates counted, not inserted.
- Unit test for:
  1) inserts
  2) duplicates
  3) invalid URL rejected

Expected files
- `backend/app/api/routes/ingest_facebook.py`
- `backend/app/core/url_utils.py` (optional)
- `backend/tests/test_ingest_facebook.py`

CODEx prompt (Task 11)
Implement **Task 11 (FB-Archive-API)** ONLY.

Add a new FastAPI route:
- `POST /ingest/facebook/search-results`

Request body:
```json
{
  "group_name": "string (optional)",
  "query": "string (optional)",
  "captured_at": "ISO timestamp (optional)",
  "items": [
    {
      "source_url": "string (required)",
      "title": "string (optional)",
      "excerpt": "string (optional)"
    }
  ]
}
```

Behavior:
- Require auth using the same dependency as your admin routes.
- For each item:
  - Validate `source_url` is a Facebook post URL in one of these patterns:
    - `https://www.facebook.com/groups/<...>/posts/<...>/`
    - `https://www.facebook.com/permalink.php?...`
  - Normalize the URL by removing common tracking params (ref, refid, __cft__, __tn__ if present).
  - Compute `source_id = sha256(normalized_url)` (hex string).
  - Insert CandidateStory:
    - source_type = 'facebook_group_archive'
    - source_id = computed hash
    - source_url = normalized_url
    - title = provided title (nullable)
    - excerpt = provided excerpt (nullable, cap at 500 chars)
    - raw_text = NULL
    - created_at_source = NULL (we don't have it reliably)
    - language = NULL
    - prefilter_flags should include metadata:
      - {"fb_group_name": ..., "fb_query": ..., "captured_at": ..., "capture_method": "extension"}
      (If you have a dedicated `meta` jsonb column, use that; otherwise store in prefilter_flags.)
    - status = 'new'
- Dedupe via the existing unique constraint on (source_type, source_id). Count duplicates.
- Return JSON:
  `{ "inserted": <int>, "duplicates": <int>, "invalid": <int> }`

Testing (pytest):
- Test inserts of 2 valid items
- Test duplicates on re-posting same payload
- Test invalid URL rejected and counted

Definition of Done:
- Endpoint appears in /docs
- Tests pass

Do not implement the Chrome extension in this task.

CLAUDE prompt (Task 11 Review)
Review the endpoint for:
- URL validation correctness and normalization
- hashing and dedupe correctness
- auth enforcement
- safe storage (excerpt caps, no full text)
- test robustness
Return P0/P1/P2 fixes.

---

## Task 12 — FB-Archive-Extension: Chrome MV3 MVP + Admin Inbox entry point

Goal
- Create a minimal “Load unpacked” Chrome extension that captures Facebook group search result post URLs and submits them to the backend batch endpoint.
- Add a small entry point in the Admin Inbox UI to support this workflow (button + instructions + endpoint URL visibility).

Inputs
- Task 11 endpoint exists and is reachable.
- Admin JWT exists (Task 4).

Outputs
- Chrome extension folder: `extension/twng-fb-archive/` with MV3 manifest, popup, content script.
- Frontend Inbox: button “FB Archive (Extension)” opens a modal with steps and shows the backend endpoint URL.

DoD
- Extension can be loaded via Chrome: Extensions -> Developer mode -> Load unpacked.
- On a Facebook page showing group search results, clicking “Capture” collects a list of post URLs (>=1 when page has results).
- Clicking “Send” POSTs to `/ingest/facebook/search-results` and shows response counts.
- Inbox UI contains a button or link that explains the workflow (so admins can actually use it).

Expected files
- `extension/twng-fb-archive/manifest.json`
- `extension/twng-fb-archive/popup.html`
- `extension/twng-fb-archive/popup.js`
- `extension/twng-fb-archive/content.js`
- `frontend/src/components/FbArchiveHelp.tsx` (or similar)
- `frontend/src/pages/Inbox.tsx` (update)

CODEx prompt (Task 12)
Implement **Task 12 (FB-Archive-Extension)** ONLY.

Part A — Chrome Extension (MV3)
Create a folder `extension/twng-fb-archive/` with:
- `manifest.json` (MV3)
- `popup.html`, `popup.js`
- `content.js`

Functional requirements:
- The popup must have inputs:
  - API Base URL (default to http://localhost:8000, store in chrome.storage.local)
  - Admin JWT (store in chrome.storage.local)
  - Query (optional, user-entered)
  - Group name (optional, user-entered)
- Buttons:
  - “Capture Results”: send message to content script to collect post URLs/snippets currently visible.
  - “Send to TWNG”: POSTs batch payload to `${apiBase}/ingest/facebook/search-results` with Authorization header if JWT provided.
- Content script:
  - Collect anchors that match Facebook post patterns:
    - /groups/.../posts/...
    - /permalink.php
  - De-duplicate URLs.
  - Provide a short excerpt by grabbing nearby text (cap 300 chars).
  - Do not attempt to navigate pages or auto-scroll; only capture what is on-screen.

Part B — Admin Inbox UI entry point
- Add a button in the Inbox page header: “FB Archive (Extension)”
- Clicking opens a small modal (or collapsible panel) describing:
  1) open Facebook group
  2) search within group
  3) scroll to load results
  4) click extension Capture + Send
- Display the endpoint path `/ingest/facebook/search-results` and remind that JWT is required.
- No need to build an upload UI; this is just a discoverable entry point.

Definition of Done:
- Extension loads via “Load unpacked” and can capture/send successfully.
- Frontend has the help entry point visible in Inbox.

Do not modify backend endpoints in this task.

CLAUDE prompt (Task 12 Review)
Review extension + UI for:
- MV3 correctness (permissions, host_permissions)
- safe token handling and minimal permissions
- URL capture reliability (dedupe, normalization)
- clear admin instructions
Return prioritized fixes.
