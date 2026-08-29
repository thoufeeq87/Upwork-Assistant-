const statusEl = document.getElementById("status");
const captureBtn = document.getElementById("capture");

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = kind || "";
}

document.getElementById("open-options").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});

captureBtn.addEventListener("click", async () => {
  captureBtn.disabled = true;
  setStatus("Capturing…");

  try {
    const { apiBaseUrl, apiToken } = await chrome.storage.local.get(["apiBaseUrl", "apiToken"]);
    if (!apiBaseUrl || !apiToken) {
      setStatus("Set your API URL and token first (link below).", "error");
      return;
    }

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
      setStatus("No active tab found.", "error");
      return;
    }

    const dataUrl = await chrome.tabs.captureVisibleTab({ format: "png" });
    const blob = await (await fetch(dataUrl)).blob();

    const formData = new FormData();
    formData.append("tab_url", tab.url);
    formData.append("image", blob, "screenshot.png");

    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/screenshots/`, {
      method: "POST",
      headers: { Authorization: `Token ${apiToken}` },
      body: formData,
    });

    if (response.ok) {
      setStatus("Screenshot saved to dashboard.", "success");
    } else {
      const body = await response.json().catch(() => ({}));
      setStatus(body.detail || `Upload failed (${response.status}).`, "error");
    }
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    captureBtn.disabled = false;
  }
});
