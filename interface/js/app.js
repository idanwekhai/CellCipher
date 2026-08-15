import { encodeText, decodeDna, getInfo } from "./api.js";
import {
  renderDna,
  renderText,
  renderStats,
  hideStats,
  renderIntegrityBadge,
  hideBadge,
  showError,
  hideError,
} from "./render.js";

// ---- tabs -------------------------------------------------------------
const tabButtons = document.querySelectorAll(".tab-btn");
const panels = { encode: document.getElementById("panel-encode"), decode: document.getElementById("panel-decode") };

for (const button of tabButtons) {
  button.addEventListener("click", () => {
    for (const b of tabButtons) {
      b.classList.toggle("active", b === button);
      b.setAttribute("aria-selected", String(b === button));
    }
    for (const [name, panel] of Object.entries(panels)) {
      panel.hidden = name !== button.dataset.tab;
      panel.classList.toggle("active", name === button.dataset.tab);
    }
  });
}

// ---- encode -------------------------------------------------------------
const encodeInput = document.getElementById("encode-input");
const encodeOutput = document.getElementById("encode-output");
const encodeBtn = document.getElementById("encode-btn");
const encodeStats = document.getElementById("encode-stats");
const encodeError = document.getElementById("encode-error");
const encodeCharCount = document.getElementById("encode-char-count");
const copyDnaBtn = document.getElementById("copy-dna-btn");

let lastDna = "";

encodeInput.addEventListener("input", () => {
  encodeCharCount.textContent = `${encodeInput.value.length} character${encodeInput.value.length === 1 ? "" : "s"}`;
});

encodeBtn.addEventListener("click", async () => {
  const text = encodeInput.value;
  hideError(encodeError);
  encodeBtn.disabled = true;
  encodeBtn.textContent = "Encoding…";
  try {
    const result = await encodeText(text);
    lastDna = result.dna;
    renderDna(encodeOutput, result.dna);
    renderStats(encodeStats, result.stats);
    copyDnaBtn.disabled = !result.dna;
  } catch (err) {
    lastDna = "";
    renderDna(encodeOutput, "");
    hideStats(encodeStats);
    copyDnaBtn.disabled = true;
    showError(encodeError, `Encode failed: ${err.message}`);
  } finally {
    encodeBtn.disabled = false;
    encodeBtn.textContent = "Encode → DNA";
  }
});

copyDnaBtn.addEventListener("click", async () => {
  if (!lastDna) return;
  await navigator.clipboard.writeText(lastDna);
  const original = copyDnaBtn.textContent;
  copyDnaBtn.textContent = "Copied!";
  setTimeout(() => (copyDnaBtn.textContent = original), 1200);
});

// ---- decode -------------------------------------------------------------
const decodeInput = document.getElementById("decode-input");
const decodeOutput = document.getElementById("decode-output");
const decodeBtn = document.getElementById("decode-btn");
const decodeStats = document.getElementById("decode-stats");
const decodeError = document.getElementById("decode-error");
const decodeCharCount = document.getElementById("decode-char-count");
const integrityBadge = document.getElementById("integrity-badge");

decodeInput.addEventListener("input", () => {
  const bases = decodeInput.value.replace(/\s/g, "").length;
  decodeCharCount.textContent = `${bases} base${bases === 1 ? "" : "s"}`;
});

decodeBtn.addEventListener("click", async () => {
  const dna = decodeInput.value;
  hideError(decodeError);
  decodeBtn.disabled = true;
  decodeBtn.textContent = "Decoding…";
  try {
    const result = await decodeDna(dna);
    if (result.valid) {
      renderText(decodeOutput, result.text);
      renderStats(decodeStats, result.stats);
      renderIntegrityBadge(integrityBadge, true);
    } else {
      renderText(decodeOutput, "");
      hideStats(decodeStats);
      renderIntegrityBadge(integrityBadge, false);
      showError(decodeError, `${result.error_type}: ${result.error}`);
    }
  } catch (err) {
    renderText(decodeOutput, "");
    hideStats(decodeStats);
    hideBadge(integrityBadge);
    showError(decodeError, `Decode request failed: ${err.message}`);
  } finally {
    decodeBtn.disabled = false;
    decodeBtn.textContent = "Decode → Text";
  }
});

// ---- footer: format info --------------------------------------------------
(async () => {
  const footer = document.getElementById("format-info");
  try {
    const info = await getInfo();
    const modeList = info.modes.map((m) => `${m.name}${m.implemented ? "" : " (planned)"}`).join(", ");
    footer.textContent = `Packet format v${info.format_version} · magic "${info.magic}" · modes: ${modeList}`;
  } catch {
    footer.textContent = "biocrypt — text ⇄ DNA encoding/storage codec.";
  }
})();
