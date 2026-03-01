import { useState } from "react";

export default function FbArchiveHelp() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button className="btn btn-fb-archive" onClick={() => setOpen(true)}>
        FB Archive (Extension)
      </button>

      {open && (
        <div className="modal-overlay" onClick={() => setOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Facebook Group Archive</h2>
              <button className="modal-close" onClick={() => setOpen(false)}>
                &times;
              </button>
            </div>

            <div className="modal-body">
              <p style={{ marginBottom: "12px", color: "#555" }}>
                Use the TWNG FB Archive Chrome extension to capture post URLs
                from Facebook group search results and ingest them into the
                scanner.
              </p>

              <h3>How to use</h3>
              <ol>
                <li>
                  Install the extension: Chrome &rarr; <code>chrome://extensions</code> &rarr;
                  Developer mode &rarr; Load unpacked &rarr; select{" "}
                  <code>extension/twng-fb-archive/</code>
                </li>
                <li>Open a Facebook group and use the group search</li>
                <li>Scroll to load the results you want to capture</li>
                <li>
                  Click the extension icon &rarr; <strong>Capture Results</strong>
                </li>
                <li>
                  Click <strong>Send to TWNG</strong> to ingest
                </li>
              </ol>

              <h3>Extension settings</h3>
              <p>Click the gear icon in the extension popup to configure:</p>
              <ul>
                <li>
                  <strong>API Base URL:</strong>{" "}
                  <code>http://localhost:8000</code> (default)
                </li>
                <li>
                  <strong>Admin JWT:</strong> paste the token you get from login
                </li>
              </ul>

              <h3>Endpoint</h3>
              <p>
                <code>POST /ingest/facebook/search-results</code>
              </p>
              <p style={{ fontSize: "12px", color: "#888", marginTop: "4px" }}>
                Requires <code>Authorization: Bearer &lt;JWT&gt;</code> header.
                See <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs</a> for payload format.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
