// DOM rendering helpers. No fetch calls here -- this module only turns data
// already in hand into markup.
//
// The sequence is shown split into the blocks the user asked for -- one row
// per block, numbered -- so the output panel and the plasmid map divide it the
// same way. The pixel view gives every base a 14px cell with its letter still
// inside (design_v2.md §6.6), stats render as a shared-border ledger with
// tabular numerals (§6.11), and block rows never enter copied data.

const BASE_CLASS = { A: "base-A", C: "base-C", G: "base-G", T: "base-T" };

const MAX_PIXEL_CELLS = 2000;

const EMPTY_FIELD_CELLS = 32; // 8 x 4 pale field for the empty state (§9)

function emptyState(container, label) {
  container.innerHTML = "";
  const field = document.createElement("span");
  field.className = "placeholder-field";
  field.setAttribute("aria-hidden", "true");
  for (let i = 0; i < EMPTY_FIELD_CELLS; i++) field.appendChild(document.createElement("i"));
  const text = document.createElement("span");
  text.className = "placeholder mono-label";
  text.textContent = label;
  container.append(field, text);
}

/** Sequence view: one flowing run of coloured bases with a gap at each block
 * boundary, so the grouping you see is the grouping you chose. */
function renderSequenceView(container, blocks) {
  const wrap = document.createElement("div");
  wrap.className = "dna-groups";

  blocks.forEach((seq) => {
    const group = document.createElement("span");
    group.className = "base-group";
    for (const base of seq) {
      const span = document.createElement("span");
      span.className = BASE_CLASS[base] ?? "";
      span.textContent = base;
      group.appendChild(span);
    }
    wrap.appendChild(group);
  });

  container.appendChild(wrap);
}

/** Pixel view: every base keeps its own 14px coloured cell, in one continuous
 * field, with a gap between blocks. */
function renderPixelView(container, blocks) {
  const total = blocks.reduce((n, b) => n + b.length, 0);
  let drawn = 0;

  const grid = document.createElement("div");
  grid.className = "pixel-grid";

  for (const seq of blocks) {
    if (drawn >= MAX_PIXEL_CELLS) break;
    const group = document.createElement("span");
    group.className = "pixel-block";
    for (const base of seq) {
      if (drawn >= MAX_PIXEL_CELLS) break;
      const cell = document.createElement("span");
      cell.className = `pixel-cell ${BASE_CLASS[base] ?? ""}`;
      cell.textContent = base;
      group.appendChild(cell);
      drawn += 1;
    }
    grid.appendChild(group);
  }
  container.appendChild(grid);

  if (total > MAX_PIXEL_CELLS) {
    const note = document.createElement("p");
    note.className = "pixel-truncated mono-label";
    note.textContent = `Showing ${MAX_PIXEL_CELLS.toLocaleString()} of ${total.toLocaleString()}`;
    container.appendChild(note);
  }
}

/** Render `blocks` (an array of base runs) in the requested view. */
export function renderDna(container, blocks, view = "sequence") {
  if (!blocks || !blocks.length) {
    emptyState(container, "Output appears here.");
    return;
  }
  container.innerHTML = "";
  if (view === "pixels") renderPixelView(container, blocks);
  else renderSequenceView(container, blocks);
}

export function renderText(container, text) {
  container.innerHTML = "";
  if (!text) {
    const span = document.createElement("span");
    span.className = "placeholder mono-label";
    span.textContent = "Recovered text appears here.";
    container.appendChild(span);
    return;
  }
  container.textContent = text;
}

export function setMonochrome(container, on) {
  container.classList.toggle("monochrome", on);
}

// Zero-pad for scanning; the accessible name keeps the natural number (§6.11).
const pad = (n, width) => String(n).padStart(width, "0");

const STAT_FIELDS = [
  { key: "dna_length", label: "Bases", format: (v) => pad(v, 4), plain: (v) => `${v} bases` },
  { key: "byte_count", label: "UTF-8", format: (v) => `${pad(v, 4)} B`, plain: (v) => `${v} bytes` },
  { key: "gc_content_percent", label: "GC content", format: (v) => `${v.toFixed(1)}%`, plain: (v) => `${v.toFixed(1)} percent` },
  { key: "longest_homopolymer", label: "Max run", format: (v) => pad(v, 2), plain: (v) => `${v}` },
  {
    key: "compression_ratio",
    label: "Compression",
    format: (v, s) => (s.compressed ? `${v.toFixed(2)}×` : "—"),
    plain: (v, s) => (s.compressed ? `${v.toFixed(2)} times` : "none"),
  },
  { key: "checksum_hex", label: "CRC32", format: (v) => v, plain: (v) => v },
];

/** Shared-border stats ledger. */
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

    const raw = stats[field.key];
    const value = document.createElement("div");
    value.className = "stat-value";
    value.textContent = raw === undefined || raw === null ? "—" : field.format(raw, stats);
    if (raw !== undefined && raw !== null) {
      value.setAttribute("aria-label", `${field.label}: ${field.plain(raw, stats)}`);
    }

    tile.append(label, value);
    fragment.appendChild(tile);
  }
  container.appendChild(fragment);
}

export function hideStats(container) {
  container.hidden = true;
  container.innerHTML = "";
}

/** Status tag: symbol + label + color, never color alone (§6.12).
 * "Invalid" covers more than a checksum mismatch -- bad alphabet, bad magic
 * bytes, wrong version, or a wrong passphrase can all land here. */
export function renderIntegrityBadge(el, valid) {
  el.hidden = false;
  el.className = `badge ${valid ? "good" : "critical"}`;
  el.textContent = valid ? "✓ CRC verified" : "× Integrity failed";
}

export function hideBadge(el) {
  el.hidden = true;
}

export function setScrambleBadge(el, scrambled) {
  el.hidden = !scrambled;
}

/** Ruled message row: plain language first, API error type as muted
 * technical metadata after it (§6.14). */
export function showError(el, heading, message, type) {
  el.hidden = false;
  el.innerHTML = "";

  const prefix = document.createElement("span");
  prefix.className = "err-prefix";
  prefix.textContent = heading;

  const detail = document.createElement("span");
  detail.textContent = message;

  el.append(prefix, detail);

  if (type) {
    const meta = document.createElement("span");
    meta.className = "err-type";
    meta.textContent = type;
    el.appendChild(meta);
  }
}

export function hideError(el) {
  el.hidden = true;
  el.textContent = "";
}
