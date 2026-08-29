const apiBaseUrlEl = document.getElementById("apiBaseUrl");
const apiTokenEl = document.getElementById("apiToken");
const statusEl = document.getElementById("status");

chrome.storage.local.get(["apiBaseUrl", "apiToken"], ({ apiBaseUrl, apiToken }) => {
  if (apiBaseUrl) apiBaseUrlEl.value = apiBaseUrl;
  if (apiToken) apiTokenEl.value = apiToken;
});

document.getElementById("save").addEventListener("click", async () => {
  await chrome.storage.local.set({
    apiBaseUrl: apiBaseUrlEl.value.trim(),
    apiToken: apiTokenEl.value.trim(),
  });
  statusEl.textContent = "Saved.";
  setTimeout(() => (statusEl.textContent = ""), 2000);
});
