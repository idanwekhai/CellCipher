// "Synthesize": turn the encoded sequence into a plasmid map.
//
// The number of blocks is the user's choice -- ask for 4 and the sequence is
// divided into 4 arcs, each one a contiguous run of bases. Sites sit at the
// block boundaries; site 1 and the final site are the same physical point,
// because a plasmid is a closed loop.

const BASES_PER_BYTE = 4;

// Packet framing from packet.py: magic(2) version(1) mode(1) flags(1)
// original_length(4) | payload | crc32(4).
const HEADER_BYTES = 9;
const CRC_BYTES = 4;

export const DEFAULT_BLOCKS = 4;

const HUES = ["var(--base-a)", "var(--base-c)", "var(--base-g)", "var(--base-t)"];

/** Sequence length this text will produce, assuming the payload is stored
 * uncompressed. Brotli only wins on longer or repetitive input, in which case
 * the real sequence is shorter -- so this is exact for short messages and an
 * upper bound otherwise. The post-encode figure is always the truth. */
export function estimateBases(text) {
  const bytes = new TextEncoder().encode(text).length;
  if (!bytes) return { bytes: 0, packet: 0, bases: 0 };
  const packet = HEADER_BYTES + bytes + CRC_BYTES;
  return { bytes, packet, bases: packet * BASES_PER_BYTE };
}

/** Split `dna` into `count` contiguous blocks as evenly as possible. Any
 * remainder is spread one base at a time across the leading blocks, so the
 * sizes never differ by more than one. */
export function splitBlocks(dna, count) {
  const n = Math.max(1, Math.min(count, dna.length));
  const base = Math.floor(dna.length / n);
  const extra = dna.length % n;
  const out = [];
  let at = 0;
  for (let i = 0; i < n; i++) {
    const size = base + (i < extra ? 1 : 0);
    out.push(dna.slice(at, at + size));
    at += size;
  }
  return out;
}

const NS = "http://www.w3.org/2000/svg";
const el = (name, attrs = {}) => {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};
const polar = (cx, cy, r, deg) => {
  const rad = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
};

/** Arc path between two angles. `sweep` 1 runs clockwise, 0 anticlockwise. */
function arcPath(cx, cy, r, from, to, sweep = 1) {
  const [x1, y1] = polar(cx, cy, r, from);
  const [x2, y2] = polar(cx, cy, r, to);
  const large = Math.abs(to - from) > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} ${sweep} ${x2} ${y2}`;
}

/** Text following the ring. Below the horizontal the baseline is drawn
 * anticlockwise at a slightly larger radius, otherwise the glyphs would hang
 * upside down on the bottom of the circle. */
function curvedLabel(svg, defs, id, { cx, cy, r, from, to, text, fill, size, weight, opacity, spacing }) {
  const mid = (from + to) / 2;
  const flipped = mid > 90 && mid < 270;
  const path = el("path", {
    id,
    d: flipped
      ? arcPath(cx, cy, r + size * 0.9, to, from, 0)
      : arcPath(cx, cy, r, from, to, 1),
    fill: "none",
  });
  defs.appendChild(path);

  const label = el("text", {
    fill,
    "font-family": "var(--font-mono)",
    "font-size": String(size),
    "font-weight": weight || "500",
    "letter-spacing": spacing || "0",
    opacity: opacity || "1",
  });
  const tp = el("textPath", { href: `#${id}`, startOffset: "50%", "text-anchor": "middle" });
  tp.setAttribute("xlink:href", `#${id}`);
  tp.textContent = text;
  label.appendChild(tp);
  svg.appendChild(label);
}

/** Draw `dna` as a plasmid of `count` blocks. Returns the blocks drawn. */
export function drawPlasmid(svg, dna, count) {
  svg.textContent = "";
  if (!dna) return [];

  const uid = `p${(drawPlasmid.seq = (drawPlasmid.seq || 0) + 1)}`;
  const defs = el("defs");
  svg.appendChild(defs);

  const blocks = splitBlocks(dna, count);
  const n = blocks.length;
  const cx = 240;
  const cy = 240;
  const R = 150;
  const W = n > 16 ? 14 : 20;
  // Only print sequences when they will actually be readable on the ring.
  const showSeq = n <= 8 && blocks[0].length <= 24;
  const step = 360 / n;
  const gap = Math.min(3.2, step * 0.12);

  blocks.forEach((seq, i) => {
    const start = i * step;
    const end = start + step;
    const [sx, sy] = polar(cx, cy, R, start + gap);
    const [ex, ey] = polar(cx, cy, R, end - gap);
    const large = step - gap * 2 > 180 ? 1 : 0;

    svg.appendChild(
      el("path", {
        d: `M ${sx} ${sy} A ${R} ${R} 0 ${large} 1 ${ex} ${ey}`,
        fill: "none",
        stroke: HUES[i % HUES.length],
        "stroke-width": W,
      })
    );

    // Bases ride the ring itself; the block number sits just outside it.
    const numSize = n > 16 ? 11 : 15;
    curvedLabel(svg, defs, `${uid}n${i}`, {
      cx, cy, r: R + W / 2 + (showSeq ? 26 : 14), from: start + gap, to: end - gap,
      text: String(i + 1), fill: HUES[i % HUES.length], size: numSize, weight: "600",
    });

    if (showSeq) {
      curvedLabel(svg, defs, `${uid}s${i}`, {
        cx, cy, r: R - 4, from: start + gap, to: end - gap,
        text: seq, fill: "var(--paper)", size: 10.5, weight: "600", spacing: "1.4",
      });
    }
  });

  // Boundary sites — the addresses a recombinase would recognise.
  for (let i = 0; i < n; i++) {
    const ang = i * step;
    const [ix, iy] = polar(cx, cy, R - W / 2 - 5, ang);
    const [ox, oy] = polar(cx, cy, R + W / 2 + 5, ang);
    svg.appendChild(
      el("line", {
        x1: ix, y1: iy, x2: ox, y2: oy,
        stroke: "var(--blue)", "stroke-width": n > 16 ? 1.4 : 2.2,
        "stroke-linecap": "round", opacity: i === 0 ? "1" : ".65",
      })
    );
  }

  // Origin marker: where site 1 and the final site meet.
  const [ox0, oy0] = polar(cx, cy, R + W / 2 + 5, 0);
  svg.appendChild(el("circle", { cx: ox0, cy: oy0, r: 4.5, fill: "var(--blue)" }));
  const origin = el("text", {
    x: ox0, y: oy0 - 13, "text-anchor": "middle", fill: "var(--blue)",
    "font-family": "var(--font-mono)", "font-size": "11", "font-weight": "600",
  });
  origin.textContent = "ORI";
  svg.appendChild(origin);

  // Centre readout.
  const count_t = el("text", {
    x: cx, y: cy - 4, "text-anchor": "middle", fill: "var(--ink)",
    "font-family": "var(--font-mono)", "font-size": "40", "font-weight": "500",
  });
  count_t.textContent = String(n);
  svg.appendChild(count_t);

  const unit = el("text", {
    x: cx, y: cy + 20, "text-anchor": "middle", fill: "var(--muted)",
    "font-family": "var(--font-mono)", "font-size": "11", "letter-spacing": "1.6",
  });
  unit.textContent = n === 1 ? "BLOCK" : "BLOCKS";
  svg.appendChild(unit);

  const bases = el("text", {
    x: cx, y: cy + 42, "text-anchor": "middle", fill: "var(--muted)",
    "font-family": "var(--font-mono)", "font-size": "11", "letter-spacing": "1.2",
  });
  bases.textContent = `${dna.length} BASES`;
  svg.appendChild(bases);

  return blocks;
}
