/**
 * TWNG FB Archive — Popup Script
 */

const $ = (sel) => document.querySelector(sel);

const captureBtn = $("#captureBtn");
const sendBtn = $("#sendBtn");
const captureCount = $("#captureCount");
const statusEl = $("#status");
const settingsToggle = $("#settingsToggle");
const settingsPanel = $("#settingsPanel");
const apiBaseInput = $("#apiBase");
const jwtInput = $("#jwt");
const saveSettingsBtn = $("#saveSettings");
const groupNameInput = $("#groupName");
const queryInput = $("#query");

let capturedItems = [];

/* ---- Status helpers ---- */

function showStatus(text, type = "info") {
  statusEl.className = type;
  statusEl.textContent = text;
}

function clearStatus() {
  statusEl.className = "";
  statusEl.style.display = "none";
}

/* ---- Settings ---- */

settingsToggle.addEventListener("click", () => {
  settingsPanel.classList.toggle("open");
});

// Load saved settings
chrome.storage.local.get(["apiBase", "jwt"], (data) => {
  apiBaseInput.value = data.apiBase || "http://localhost:8000";
  jwtInput.value = data.jwt || "";
});

saveSettingsBtn.addEventListener("click", () => {
  chrome.storage.local.set({
    apiBase: apiBaseInput.value.replace(/\/+$/, ""),
    jwt: jwtInput.value.trim(),
  });
  showStatus("Settings saved.", "success");
});

/* ---- Capture ---- */

captureBtn.addEventListener("click", async () => {
  clearStatus();
  captureBtn.disabled = true;
  captureBtn.textContent = "Capturing...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      showStatus("No active tab found.", "error");
      return;
    }

    // Ensure content script is injected (in case it wasn't auto-injected)
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"],
      });
    } catch {
      // Content script may already be injected; ignore errors
    }

    const response = await chrome.tabs.sendMessage(tab.id, { action: "capture" });

    if (response && response.results) {
      capturedItems = response.results;
      captureCount.textContent = capturedItems.length;
      sendBtn.disabled = capturedItems.length === 0;

      if (capturedItems.length === 0) {
        showStatus("No Facebook post links found on this page. Make sure you're on a Facebook group search results page.", "error");
      } else {
        showStatus(`Found ${capturedItems.length} post(s). Click 'Send to TWNG' to ingest.`, "success");
      }
    } else {
      showStatus("No response from content script. Make sure you're on a Facebook page.", "error");
    }
  } catch (err) {
    showStatus("Capture error: " + err.message, "error");
  } finally {
    captureBtn.disabled = false;
    captureBtn.textContent = "\u{1F4F7} Capture Results";
  }
});

/* ---- Send ---- */

sendBtn.addEventListener("click", async () => {
  if (capturedItems.length === 0) return;

  clearStatus();
  sendBtn.disabled = true;
  sendBtn.textContent = "Sending...";

  const settings = await chrome.storage.local.get(["apiBase", "jwt"]);
  const apiBase = settings.apiBase || "http://localhost:8000";
  const jwt = settings.jwt || "";

  if (!jwt) {
    showStatus("No JWT token set. Open Settings and paste your admin token.", "error");
    sendBtn.disabled = false;
    sendBtn.textContent = `\u{1F680} Send to TWNG (${capturedItems.length} posts)`;
    return;
  }

  const payload = {
    group_name: groupNameInput.value.trim() || null,
    query: queryInput.value.trim() || null,
    captured_at: new Date().toISOString(),
    items: capturedItems,
  };

  try {
    const res = await fetch(`${apiBase}/ingest/facebook/search-results`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${jwt}`,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    showStatus(
      `Done! Inserted: ${data.inserted}, Duplicates: ${data.duplicates}, Invalid: ${data.invalid}`,
      "success"
    );

    // Reset
    capturedItems = [];
    captureCount.textContent = "0";
  } catch (err) {
    showStatus("Send error: " + err.message, "error");
  } finally {
    sendBtn.disabled = capturedItems.length === 0;
    sendBtn.textContent = `\u{1F680} Send to TWNG (${capturedItems.length} posts)`;
  }
});
