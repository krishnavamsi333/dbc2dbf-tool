/* =============================================
   DBC → DBF Converter — Frontend Logic
   ============================================= */

const API_BASE = "";  // relative — works on any host

// --- DOM refs ---
const dropZone    = document.getElementById("dropZone");
const fileInput   = document.getElementById("fileInput");
const fileInfo    = document.getElementById("fileInfo");
const fileName    = document.getElementById("fileName");
const fileSize    = document.getElementById("fileSize");
const clearBtn    = document.getElementById("clearBtn");
const validateBtn = document.getElementById("validateBtn");
const convertBtn  = document.getElementById("convertBtn");
const cleanToggle = document.getElementById("cleanToggle");
const progressWrap= document.getElementById("progressWrap");
const progressBar = document.getElementById("progressBar");
const progressLabel= document.getElementById("progressLabel");
const logBody     = document.getElementById("logBody");
const clearLogBtn = document.getElementById("clearLogBtn");
const statusDot   = document.getElementById("statusDot");
const statusText  = document.getElementById("statusText");
const apiBaseEl   = document.getElementById("apiBase");

apiBaseEl.textContent = window.location.host;

let selectedFile = null;

// ---- Health check ----
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      statusDot.className = "status-dot online";
      statusText.textContent = "API ONLINE";
    } else {
      throw new Error();
    }
  } catch {
    statusDot.className = "status-dot offline";
    statusText.textContent = "API OFFLINE";
  }
}
checkHealth();
setInterval(checkHealth, 30000);

// ---- Logging ----
function log(message, type = "info") {
  const empty = logBody.querySelector(".log-empty");
  if (empty) empty.remove();

  const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.innerHTML = `<span class="ts">${ts}</span><span class="msg">${escapeHtml(message)}</span>`;
  logBody.appendChild(line);
  logBody.scrollTop = logBody.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

clearLogBtn.addEventListener("click", () => {
  logBody.innerHTML = '<p class="log-empty">No output yet. Upload a file to begin.</p>';
});

// ---- File selection ----
function setFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".dbc")) {
    log("Only .dbc files are accepted", "error");
    return;
  }

  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  fileInfo.hidden = false;
  dropZone.classList.add("has-file");
  validateBtn.disabled = false;
  convertBtn.disabled = false;

  log(`Loaded: ${file.name} (${formatSize(file.size)})`, "info");
}

function clearFile() {
  selectedFile = null;
  fileInput.value = "";
  fileInfo.hidden = true;
  dropZone.classList.remove("has-file");
  validateBtn.disabled = true;
  convertBtn.disabled = true;
  hideProgress();
}

clearBtn.addEventListener("click", clearFile);
fileInput.addEventListener("change", () => setFile(fileInput.files[0]));

// ---- Drag and drop ----
["dragenter", "dragover"].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add("drag-over"); })
);
["dragleave", "drop"].forEach(evt =>
  dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove("drag-over"); })
);
dropZone.addEventListener("drop", e => {
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
dropZone.addEventListener("click", e => {
  if (e.target.tagName !== "LABEL") fileInput.click();
});

// ---- Progress helpers ----
function showProgress(label, pct) {
  progressWrap.hidden = false;
  progressBar.style.width = `${pct}%`;
  progressLabel.textContent = label;
}
function hideProgress() {
  progressWrap.hidden = true;
  progressBar.style.width = "0%";
}

function setButtonLoading(btn, loading) {
  if (loading) {
    btn.classList.add("loading");
    btn.disabled = true;
  } else {
    btn.classList.remove("loading");
    btn.disabled = !selectedFile;
  }
}

// ---- Validate ----
validateBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  setButtonLoading(validateBtn, true);
  showProgress("Validating...", 40);
  log("Starting validation...", "info");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`${API_BASE}/api/validate`, { method: "POST", body: formData });
    const data = await res.json();

    showProgress("Done", 100);
    setTimeout(hideProgress, 800);

    if (data.success) {
      const { stats, warnings } = data.validation;
      log(`Validation passed ✓`, "ok");
      log(`  Messages: ${stats.message_count} | Signals: ${stats.signal_count} | Size: ${stats.file_size_kb} KB`, "info");
      if (warnings.length > 0) {
        warnings.forEach(w => log(`  ⚠ ${w}`, "warn"));
      } else {
        log("  No warnings found", "ok");
      }
    } else {
      log(`Validation failed: ${data.error}`, "error");
    }
  } catch (e) {
    log(`Request failed: ${e.message}`, "error");
    hideProgress();
  } finally {
    setButtonLoading(validateBtn, false);
  }
});

// ---- Convert ----
convertBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  setButtonLoading(convertBtn, true);
  setButtonLoading(validateBtn, true);
  showProgress("Uploading...", 20);
  log("Starting conversion...", "info");

  const doClean = cleanToggle.checked;
  if (doClean) log("Auto-sanitize enabled", "info");

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("clean", doClean ? "true" : "false");

  try {
    showProgress("Converting...", 60);

    const res = await fetch(`${API_BASE}/api/convert`, { method: "POST", body: formData });

    if (!res.ok) {
      const data = await res.json();
      log(`Conversion failed: ${data.error}`, "error");
      hideProgress();
      return;
    }

    showProgress("Downloading...", 90);

    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const outName = match ? match[1] : selectedFile.name.replace(/\.dbc$/i, ".dbf");

    // Trigger download
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = outName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showProgress("Complete!", 100);
    setTimeout(hideProgress, 1000);
    log(`Converted successfully → ${outName}`, "ok");
    log(`File size: ${formatSize(blob.size)}`, "info");

  } catch (e) {
    log(`Request failed: ${e.message}`, "error");
    hideProgress();
  } finally {
    setButtonLoading(convertBtn, false);
    setButtonLoading(validateBtn, false);
  }
});

// ---- Utilities ----
function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(2)} MB`;
}