import { encodeText, decodeDna, getInfo } from "./api.js";
import { estimateBases, drawPlasmid, splitBlocks } from "./synthesize.js";
import {
  renderDna,
  renderText,
  renderStats,
  hideStats,
  renderIntegrityBadge,
  hideBadge,
  setScrambleBadge,
  setMonochrome,
  showError,
  hideError,
} from "./render.js";

// ---- operation switch ---------------------------------------------------
// Switching updates the hero statement and panel, preserving source content
// (design_v2.md §6.3). Full tablist semantics with arrow-key navigation.
const tabButtons = document.querySelectorAll(".tab-btn");
const panels = {
  encode: document.getElementById("panel-encode"),
  decode: document.getElementById("panel-decode"),
};


for (const button of tabButtons) {
  button.addEventListener("click", () => {
    const tab = button.dataset.tab;
    for (const b of tabButtons) {
      b.classList.toggle("active", b === button);
      b.setAttribute("aria-selected", String(b === button));
    }
    for (const [name, panel] of Object.entries(panels)) panel.hidden = name !== tab;
  });
}

document.querySelector(".tabs").addEventListener("keydown", (event) => {
  const step = { ArrowLeft: -1, ArrowRight: 1 }[event.key];
  if (!step) return;
  const buttons = [...tabButtons];
  const current = buttons.findIndex((b) => b.classList.contains("active"));
  const next = buttons[(current + step + buttons.length) % buttons.length];
  next.click();
  next.focus();
  event.preventDefault();
});


// ---- encode -------------------------------------------------------------
const encodeInput = document.getElementById("encode-input");
const encodeOutput = document.getElementById("encode-output");
const encodeBtn = document.getElementById("encode-btn");
const encodeStats = document.getElementById("encode-stats");
const encodeError = document.getElementById("encode-error");
const encodeCharCount = document.getElementById("encode-char-count");
const encodeBaseCount = document.getElementById("encode-base-count");
const copyDnaBtn = document.getElementById("copy-dna-btn");
const encodePassphrase = document.getElementById("encode-passphrase");
const encodeUseNonce = document.getElementById("encode-use-nonce");
const encodeScrambleBadge = document.getElementById("encode-scramble-badge");
const monoToggle = document.getElementById("mono-toggle");
const viewSeqBtn = document.getElementById("view-seq");
const viewPixelsBtn = document.getElementById("view-pixels");
const synthBtn = document.getElementById("synthesize-btn");
const synthPanel = document.getElementById("synth-panel");
const synthFigure = document.getElementById("synth-figure");
const synthSummary = document.getElementById("synth-summary");
const synthBlocks = document.getElementById("synth-blocks");
const blockCount = document.getElementById("block-count");
const blockHint = document.getElementById("block-hint");

let lastDna = "";
let view = "sequence";
let monochrome = false;

function syncEncodeOutput() {
  // The output panel shows the same division of the sequence as the plasmid.
  renderDna(encodeOutput, lastDna ? splitBlocks(lastDna, chosenBlocks()) : null, view);
  setMonochrome(encodeOutput, monochrome);
}

function chosenBlocks() {
  const v = parseInt(blockCount.value, 10);
  return Number.isFinite(v) ? Math.max(2, Math.min(24, v)) : 4;
}

/** Show what the current text and block count will produce, before Encode. */
function refreshBlockHint() {
  const n = chosenBlocks();
  const source = lastDna || null;
  const bases = source ? source.length : estimateBases(encodeInput.value).bases;
  if (!bases) {
    blockHint.textContent = `${n} blocks · — bases each`;
    return;
  }
  const per = Math.floor(bases / n);
  const extra = bases % n;
  const spread = extra ? `${per + 1}–${per}` : `${per}`;
  blockHint.textContent =
    `${n} blocks · ${spread} bases each · ${bases} total${source ? "" : " (est.)"}`;
}

encodeInput.addEventListener("input", () => {
  const n = encodeInput.value.length;
  const { bytes, packet } = estimateBases(encodeInput.value);
  encodeCharCount.textContent = n === 0
    ? "0 characters"
    : `${n} character${n === 1 ? "" : "s"} · ${bytes} B → ${packet} B packet`;
  encodeBtn.disabled = n === 0;
  // A new source invalidates any plasmid drawn from the previous encode.
  lastDna = "";
  synthPanel.hidden = true;
  synthBtn.hidden = true;
  refreshBlockHint();
});

blockCount.addEventListener("input", () => {
  refreshBlockHint();
  syncEncodeOutput();
  if (!synthPanel.hidden) renderPlasmid();
});
encodeBtn.disabled = true;
refreshBlockHint();

// Stepped loading label: four visual steps, no pretence of server progress.
function steppedLabel(button, verb) {
  let step = 0;
  button.textContent = `${verb} 01/04`;
  return setInterval(() => {
    step = (step + 1) % 4;
    button.textContent = `${verb} 0${step + 1}/04`;
  }, 180);
}

encodeBtn.addEventListener("click", async () => {
  hideError(encodeError);
  encodeBtn.disabled = true;
  const ticker = steppedLabel(encodeBtn, "Encoding");
  try {
    const result = await encodeText(encodeInput.value, {
      passphrase: encodePassphrase.value,
      useNonce: encodeUseNonce.checked,
    });
    lastDna = result.dna;
    syncEncodeOutput();
    renderStats(encodeStats, result.stats);
    encodeBaseCount.textContent = `${result.dna.length} bases`;
    copyDnaBtn.disabled = !result.dna;
    setScrambleBadge(encodeScrambleBadge, result.scrambled);
    encodeScrambleBadge.title = result.nonce_hex ? `nonce: ${result.nonce_hex}` : "";
    synthBtn.hidden = !result.dna;
    synthPanel.hidden = true;
    refreshBlockHint();
  } catch (err) {
    lastDna = "";
    syncEncodeOutput();
    hideStats(encodeStats);
    encodeBaseCount.textContent = "— bases";
    copyDnaBtn.disabled = true;
    hideBadge(encodeScrambleBadge);
    synthBtn.hidden = true;
    synthPanel.hidden = true;
    showError(encodeError, "Could not encode", "BioCrypt could not reach the codec service.", err.message);
  } finally {
    clearInterval(ticker);
    encodeBtn.disabled = encodeInput.value.length === 0;
    encodeBtn.textContent = "Encode → DNA";
  }
});

// Copied data is the raw API string -- presentational grouping never leaks in.
copyDnaBtn.addEventListener("click", async () => {
  if (!lastDna) return;
  try {
    await navigator.clipboard.writeText(lastDna);
    copyDnaBtn.textContent = "Copied ✓";
  } catch {
    copyDnaBtn.textContent = "Copy failed — select text";
  }
  setTimeout(() => (copyDnaBtn.textContent = "Copy sequence"), 1500);
});

monoToggle.addEventListener("click", () => {
  monochrome = !monochrome;
  setMonochrome(encodeOutput, monochrome);
  monoToggle.textContent = monochrome ? "Color" : "Monochrome";
  monoToggle.setAttribute("aria-pressed", String(monochrome));
});

function setView(next) {
  view = next;
  viewSeqBtn.setAttribute("aria-pressed", String(next === "sequence"));
  viewPixelsBtn.setAttribute("aria-pressed", String(next === "pixels"));
  syncEncodeOutput();
}
viewSeqBtn.addEventListener("click", () => setView("sequence"));
viewPixelsBtn.addEventListener("click", () => setView("pixels"));

// ---- synthesize: draw the encoded sequence as a plasmid ------------------
function renderPlasmid() {
  if (!lastDna) return;
  const n = chosenBlocks();
  const blocks = drawPlasmid(synthFigure, lastDna, n);
  synthSummary.textContent = `${blocks.length} blocks · ${lastDna.length} bases`;

  synthBlocks.innerHTML = "";
  const list = document.createElement("div");
  list.className = "block-list";
  blocks.forEach((seq, i) => {
    const row = document.createElement("div");
    row.className = "block-row";
    const idx = document.createElement("span");
    idx.className = "bi";
    idx.textContent = String(i + 1);
    const val = document.createElement("span");
    val.textContent = seq;
    row.append(idx, val);
    list.appendChild(row);
  });
  synthBlocks.appendChild(list);
}

synthBtn.addEventListener("click", () => {
  if (!lastDna) return;
  renderPlasmid();
  synthPanel.hidden = false;
  synthPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

// ---- decode -------------------------------------------------------------
const decodeInput = document.getElementById("decode-input");
const decodeOutput = document.getElementById("decode-output");
const decodeBtn = document.getElementById("decode-btn");
const decodeStats = document.getElementById("decode-stats");
const decodeError = document.getElementById("decode-error");
const decodeCharCount = document.getElementById("decode-char-count");
const decodeMeta = document.getElementById("decode-meta");
const integrityBadge = document.getElementById("integrity-badge");
const decodePassphrase = document.getElementById("decode-passphrase");
const decodeScrambleBadge = document.getElementById("decode-scramble-badge");
const chapter = document.getElementById("decode-chapter");
const chapterText = document.getElementById("decode-chapter-text");
const copyTextBtn = document.getElementById("copy-text-btn");

decodeInput.addEventListener("input", () => {
  const bases = decodeInput.value.replace(/\s/g, "").length;
  decodeCharCount.textContent = `${bases} base${bases === 1 ? "" : "s"}`;
  decodeBtn.disabled = bases === 0;
});
decodeBtn.disabled = true;

decodeBtn.addEventListener("click", async () => {
  hideError(decodeError);
  decodeBtn.disabled = true;
  const ticker = steppedLabel(decodeBtn, "Decoding");
  try {
    const result = await decodeDna(decodeInput.value, { passphrase: decodePassphrase.value });
    setScrambleBadge(decodeScrambleBadge, Boolean(result.scrambled));

    if (result.valid) {
      renderText(decodeOutput, result.text);
      renderStats(decodeStats, result.stats);
      renderIntegrityBadge(integrityBadge, true);
      decodeMeta.textContent = `${result.text.length} characters`;
      // Short recovered text gets the dark chapter treatment (§6.13).
      const short = result.text.length <= 280;
      chapter.hidden = !short;
      chapterText.textContent = short ? result.text : "";
    } else {
      renderText(decodeOutput, "");
      hideStats(decodeStats);
      renderIntegrityBadge(integrityBadge, false);
      chapter.hidden = true;
      decodeMeta.textContent = "—";
      const next =
        result.error_type === "PassphraseRequiredError"
          ? "This sequence was scrambled. Enter the passphrase and try again."
          : "This sequence could not be decoded. Check that it came from BioCrypt and was copied completely.";
      showError(decodeError, "Could not decode", next, result.error_type);
    }
  } catch (err) {
    renderText(decodeOutput, "");
    hideStats(decodeStats);
    hideBadge(integrityBadge);
    hideBadge(decodeScrambleBadge);
    chapter.hidden = true;
    showError(decodeError, "Could not decode", "BioCrypt could not reach the codec service.", err.message);
  } finally {
    clearInterval(ticker);
    decodeBtn.disabled = decodeInput.value.replace(/\s/g, "").length === 0;
    decodeBtn.textContent = "Decode → Text";
  }
});

copyTextBtn.addEventListener("click", async () => {
  if (!chapterText.textContent) return;
  await navigator.clipboard.writeText(chapterText.textContent);
  copyTextBtn.textContent = "Copied ✓";
  setTimeout(() => (copyTextBtn.textContent = "Copy text"), 1500);
});

// ---- format info ----------------------------------------------------------
(async () => {
  const footer = document.getElementById("format-info");
  const status = document.getElementById("api-status");
  try {
    const info = await getInfo();
    const modes = info.modes.map((m) => `${m.name}${m.implemented ? "" : " / planned"}`).join(" · ");
    const scramble = info.scrambling?.supported ? ` · scramble magic "${info.scrambling.magic}"` : "";
    footer.textContent = `Packet format v${info.format_version} · magic "${info.magic}" · ${modes}${scramble}`;
    status.textContent = "● API Online";
  } catch {
    footer.textContent = "BioCrypt could not reach the codec service.";
    status.textContent = "○ API Offline";
  }
})();
