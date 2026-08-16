import { encodeText, decodeDna, getInfo } from "./api.js";
import {
  renderDna,
  renderText,
  renderStats,
  hideStats,
  renderIntegrityBadge,
  hideBadge,
  setScrambleBadge,
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
const encodePassphrase = document.getElementById("encode-passphrase");
const encodeUseNonce = document.getElementById("encode-use-nonce");
const encodeScrambleBadge = document.getElementById("encode-scramble-badge");

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
    const result = await encodeText(text, {
      passphrase: encodePassphrase.value,
      useNonce: encodeUseNonce.checked,
    });
    lastDna = result.dna;
    renderDna(encodeOutput, result.dna);
    renderStats(encodeStats, result.stats);
    copyDnaBtn.disabled = !result.dna;
    setScrambleBadge(encodeScrambleBadge, result.scrambled);
    encodeScrambleBadge.title = result.nonce_hex ? `nonce: ${result.nonce_hex}` : "";
  } catch (err) {
    lastDna = "";
    renderDna(encodeOutput, "");
    hideStats(encodeStats);
    copyDnaBtn.disabled = true;
    hideBadge(encodeScrambleBadge);
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
const decodePassphrase = document.getElementById("decode-passphrase");
const decodeScrambleBadge = document.getElementById("decode-scramble-badge");

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
    const result = await decodeDna(dna, { passphrase: decodePassphrase.value });
    setScrambleBadge(decodeScrambleBadge, Boolean(result.scrambled));
    if (result.valid) {
      renderText(decodeOutput, result.text);
      renderStats(decodeStats, result.stats);
      renderIntegrityBadge(integrityBadge, true);
    } else {
      renderText(decodeOutput, "");
      hideStats(decodeStats);
      renderIntegrityBadge(integrityBadge, false);
      const hint =
        result.error_type === "PassphraseRequiredError" ? " — enter the passphrase above and try again." : "";
      showError(decodeError, `${result.error_type}: ${result.error}${hint}`);
    }
  } catch (err) {
    renderText(decodeOutput, "");
    hideStats(decodeStats);
    hideBadge(integrityBadge);
    hideBadge(decodeScrambleBadge);
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
    const scramble = info.scrambling?.supported ? ` · scrambling: magic "${info.scrambling.magic}"` : "";
    footer.textContent = `Packet format v${info.format_version} · magic "${info.magic}" · modes: ${modeList}${scramble}`;
  } catch {
    footer.textContent = "biocrypt — text ⇄ DNA encoding/storage codec.";
  }
})();
