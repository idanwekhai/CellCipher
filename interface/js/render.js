// DOM rendering helpers. No fetch calls here -- this module only turns data
// already in hand into markup.

const BASE_CLASS = { A: "base-A", C: "base-C", G: "base-G", T: "base-T" };

/** Render a DNA string as colorized per-base spans (A/C/G/T get fixed hues). */
export function renderDna(container, dna) {
  container.innerHTML = "";
  if (!dna) {
    container.innerHTML = '<span class="placeholder">DNA output will appear here.</span>';
    return;
  }
  const fragment = document.createDocumentFragment();
  for (const base of dna) {
    const span = document.createElement("span");
    span.className = BASE_CLASS[base] ?? "";
    span.textContent = base;
    fragment.appendChild(span);
  }
  container.appendChild(fragment);
}

export function renderText(container, text) {
  container.innerHTML = "";
  if (!text) {
    container.innerHTML = '<span class="placeholder">Decoded text will appear here.</span>';
    return;
  }
  container.textContent = text;
}

const STAT_FIELDS = [
  { key: "byte_count", label: "Text bytes", format: (v) => `${v} B` },
  { key: "dna_length", label: "DNA length", format: (v) => `${v} bases` },
  { key: "gc_content_percent", label: "GC content", format: (v) => `${v.toFixed(1)}%` },
  {
    key: "compression_ratio",
    label: "Compression",
    format: (v, s) => (s.compressed ? `${v.toFixed(2)}×` : "none"),
  },
  { key: "bits_per_base", label: "Bits / base", format: (v) => v.toFixed(2) },
  { key: "checksum_hex", label: "CRC32", format: (v) => v, mono: true },
];

/** Render the byte count / DNA length / GC% / compression ratio / checksum stat-tile row. */
export function renderStats(container, stats) {
  container.innerHTML = "";
  container.hidden = false;
  const fragment = document.createDocumentFragment();
  for (const field of STAT_FIELDS) {
    const tile = document.createElement("div");
    tile.className = "stat-tile";
    const label = document.createElement("div");
    label.className = "stat-label";
    label.textContent = field.label;
    const value = document.createElement("div");
    value.className = "stat-value";
    if (field.mono) value.style.fontFamily = "var(--mono)";
    value.style.fontSize = field.mono ? "14px" : "";
    value.textContent = field.format(stats[field.key], stats);
    tile.append(label, value);
    fragment.appendChild(tile);
  }
  container.appendChild(fragment);
}

export function hideStats(container) {
  container.hidden = true;
  container.innerHTML = "";
}

/** Status badge: icon + label + color -- never color alone (see dataviz status rules).
 * "Invalid" covers more than a checksum mismatch -- bad alphabet, bad magic
 * bytes, wrong version, or wrong passphrase can all land here. */
export function renderIntegrityBadge(el, valid) {
  el.hidden = false;
  el.className = `badge ${valid ? "good" : "critical"}`;
  el.textContent = valid ? "✓ Verified" : "✗ Invalid";
}

export function hideBadge(el) {
  el.hidden = true;
}

export function setScrambleBadge(el, scrambled) {
  el.hidden = !scrambled;
}

export function showError(el, message) {
  el.hidden = false;
  el.textContent = message;
}

export function hideError(el) {
  el.hidden = true;
  el.textContent = "";
}
