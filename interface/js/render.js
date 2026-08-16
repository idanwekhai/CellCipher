// DOM rendering helpers. No fetch calls here -- this module only turns data
// already in hand into markup.
//
// Follows design_v2.md: bases group in fours on a 14px rhythm (§6.6), the
// pixel view gives every base a 14px cell with its letter still inside, stats
// render as a shared-border ledger with tabular numerals (§6.11), and
// presentational grouping never enters copied data.

const BASE_CLASS = { A: "base-A", C: "base-C", G: "base-G", T: "base-T" };

const BASES_PER_GROUP = 4;
const BASES_PER_LINE = 64;
const GUTTER_MIN_LINES = 3;
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

/** Sequence view: colored letters, grouped in fours, line-numbered past 3 lines. */
function renderSequenceView(container, dna) {
  const lineCount = Math.ceil(dna.length / BASES_PER_LINE);
  const showGutter = lineCount > GUTTER_MIN_LINES;
  const fragment = document.createDocumentFragment();

  for (let start = 0; start < dna.length; start += BASES_PER_LINE) {
    const line = document.createElement("div");
    line.className = "dna-line";

    if (showGutter) {
      const gutter = document.createElement("span");
      gutter.className = "dna-gutter";
      gutter.textContent = String(start + 1);
      line.appendChild(gutter);
    }

    const groups = document.createElement("span");
    groups.className = "dna-groups";
    const text = dna.slice(start, start + BASES_PER_LINE);

    for (let g = 0; g < text.length; g += BASES_PER_GROUP) {
      const group = document.createElement("span");
      group.className = "base-group";
      for (const base of text.slice(g, g + BASES_PER_GROUP)) {
        const span = document.createElement("span");
        span.className = BASE_CLASS[base] ?? "";
        span.textContent = base;
        group.appendChild(span);
      }
      groups.appendChild(group);
    }

    line.appendChild(groups);
    fragment.appendChild(line);
  }
  container.appendChild(fragment);
}

/** Pixel view: one 14px cell per base, letter retained inside the cell. */
function renderPixelView(container, dna) {
  const shown = Math.min(dna.length, MAX_PIXEL_CELLS);
  const grid = document.createElement("div");
  grid.className = "pixel-grid";

  for (let i = 0; i < shown; i++) {
    const cell = document.createElement("span");
    cell.className = `pixel-cell ${BASE_CLASS[dna[i]] ?? ""}`;
    cell.textContent = dna[i];
    grid.appendChild(cell);
  }
  container.appendChild(grid);

  if (dna.length > MAX_PIXEL_CELLS) {
    const note = document.createElement("p");
    note.className = "pixel-truncated mono-label";
    note.textContent = `Showing ${MAX_PIXEL_CELLS.toLocaleString()} of ${dna.length.toLocaleString()}`;
    container.appendChild(note);
  }
}

/** Render `dna` in the requested view ("sequence" | "pixels"). */
export function renderDna(container, dna, view = "sequence") {
  if (!dna) {
    emptyState(container, "Output appears here.");
    return;
  }
  container.innerHTML = "";
  if (view === "pixels") renderPixelView(container, dna);
  else renderSequenceView(container, dna);
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
