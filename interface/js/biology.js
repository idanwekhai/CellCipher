// The biology panel: what FLIP(i, j) does to a message plasmid.
//
// States here are the real output of biocrypt.cipher.operations.flip() on a
// four-block plasmid, so the diagram can't drift from the implementation:
//
//   start      +1 - +A - +2 - +B - +3 - +C - +4 - +D - +5   ATCGGGTATTACCAGT
//   FLIP(2,4)  +1 - +A - +2 - -C - -3 - -B - +4 - +D - +5   ATCGGTAATACCCAGT
//
// Blocks (A-D) carry the message and move. Sites (1-5) are recognition
// sequences -- addresses the recombinase can actually see. Sites 1 and 5 are
// the same physical point, since a plasmid is a closed loop.

const SEQ = { A: "ATCG", B: "GGTA", C: "TTAC", D: "CAGT" };
const RC = { A: "CGAT", B: "TACC", C: "GTAA", D: "ACTG" };
const HUE = { A: "var(--base-a)", B: "var(--base-c)", C: "var(--base-g)", D: "var(--base-t)" };

const START = { blocks: [["A", 1], ["B", 1], ["C", 1], ["D", 1]], sites: [1, 1, 1, 1] };
const FLIPPED = { blocks: [["A", 1], ["C", -1], ["B", -1], ["D", 1]], sites: [1, 1, -1, 1] };

const STEPS = [
  {
    state: START,
    mark: [],
    title: "The message plasmid",
    body: "Blocks A–D carry the message. The numbered sites between them are recombinase recognition sequences — addresses, not positions. Sites 1 and 5 are the same point: a plasmid is a closed loop.",
  },
  {
    state: START,
    mark: [2, 4],
    title: "FLIP(2, 4) — the enzyme grabs two sites",
    body: "A recombinase recognises sites 2 and 4 and cuts. Everything between them — block B, site 3, block C — is about to turn around. The two boundary sites are the crossover points, so they stay put.",
  },
  {
    state: FLIPPED,
    mark: [2, 4],
    title: "After the inversion",
    body: "B and C swapped places and each became its reverse complement (GGTA → TACC). Site 3 was inside the interval, so it inverted too — same address, now −3. Blocks A and D never moved.",
  },
  {
    state: START,
    mark: [2, 4],
    title: "FLIP(2, 4) again — back to the start",
    body: "Inversion is self-inverse, so the decoder needs no new machinery: it runs the encoder's operations backwards. Because intervals overlap, flips don't commute — which is what makes the ordered program a key rather than a set.",
  },
];

const NS = "http://www.w3.org/2000/svg";
const svgEl = (name, attrs = {}) => {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};
const polar = (cx, cy, r, deg) => {
  const rad = ((deg - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
};

function drawPlasmid(svg, state, mark = [], shade = false) {
  svg.textContent = "";
  const cx = 210;
  const cy = 180;
  const R = 112;
  const W = 14;

  if (shade) {
    const [x0, y0] = polar(cx, cy, R + 32, 90);
    const [x1, y1] = polar(cx, cy, R + 32, 270);
    svg.appendChild(
      svgEl("path", {
        d: `M ${cx} ${cy} L ${x0} ${y0} A ${R + 32} ${R + 32} 0 0 1 ${x1} ${y1} Z`,
        fill: "var(--blue)",
        opacity: ".10",
      })
    );
  }

  state.blocks.forEach(([label, dir], i) => {
    const start = i * 90;
    const end = start + 90;
    const pad = 7;
    const [sx, sy] = polar(cx, cy, R, start + pad);
    const [ex, ey] = polar(cx, cy, R, end - pad);

    svg.appendChild(
      svgEl("path", {
        d: `M ${sx} ${sy} A ${R} ${R} 0 0 1 ${ex} ${ey}`,
        fill: "none",
        stroke: HUE[label],
        "stroke-width": W,
      })
    );

    // Orientation arrowhead, pointing with the block.
    const at = dir === 1 ? end - pad - 9 : start + pad + 9;
    const [ax, ay] = polar(cx, cy, R, at);
    const t = ((at + (dir === 1 ? 90 : -90)) * Math.PI) / 180;
    const ux = Math.cos(t);
    const uy = Math.sin(t);
    svg.appendChild(
      svgEl("path", {
        d:
          `M ${ax + ux * 10} ${ay + uy * 10} ` +
          `L ${ax - ux * 2 - uy * 7} ${ay - uy * 2 + ux * 7} ` +
          `L ${ax - ux * 2 + uy * 7} ${ay - uy * 2 - ux * 7} Z`,
        fill: "var(--paper)",
      })
    );

    const [lx, ly] = polar(cx, cy, R + 44, start + 45);
    const name = svgEl("text", {
      x: lx, y: ly, "text-anchor": "middle", fill: HUE[label],
      "font-family": "var(--font-mono)", "font-size": "18", "font-weight": "600",
    });
    name.textContent = (dir === 1 ? "+" : "−") + label;
    svg.appendChild(name);

    const seq = svgEl("text", {
      x: lx, y: ly + 16, "text-anchor": "middle", fill: HUE[label],
      "font-family": "var(--font-mono)", "font-size": "12", "letter-spacing": "1.4", opacity: ".8",
    });
    seq.textContent = dir === 1 ? SEQ[label] : RC[label];
    svg.appendChild(seq);
  });

  [0, 90, 180, 270].forEach((ang, i) => {
    const highlighted = mark.includes(i + 1);
    const [ix, iy] = polar(cx, cy, R - W / 2 - 6, ang);
    const [ox, oy] = polar(cx, cy, R + W / 2 + 6, ang);

    svg.appendChild(
      svgEl("line", {
        x1: ix, y1: iy, x2: ox, y2: oy,
        stroke: highlighted ? "var(--blue)" : "var(--muted)",
        "stroke-width": highlighted ? 4 : 2.2, "stroke-linecap": "round",
      })
    );
    if (highlighted) {
      svg.appendChild(svgEl("circle", { cx: ox, cy: oy, r: 4.5, fill: "var(--blue)" }));
    }

    const [tx, ty] = polar(cx, cy, R - W / 2 - 21, ang);
    const label = svgEl("text", {
      x: tx, y: ty + 5, "text-anchor": "middle",
      fill: highlighted ? "var(--blue)" : "var(--muted)",
      "font-family": "var(--font-mono)", "font-size": highlighted ? "16" : "13",
      "font-weight": highlighted ? "600" : "400",
    });
    label.textContent = i === 0 ? "1·5" : (state.sites[i] === 1 ? "" : "−") + (i + 1);
    svg.appendChild(label);
  });
}

function renderMap(node, state) {
  node.textContent = "";
  const parts = [];
  state.blocks.forEach(([label, dir], i) => {
    parts.push({ site: i + 1, dir: state.sites[i] });
    parts.push({ block: label, dir });
  });
  parts.push({ site: 5, dir: 1 });

  parts.forEach((part, index) => {
    if (index) {
      const sep = document.createElement("span");
      sep.className = "map-sep";
      sep.textContent = "–";
      node.appendChild(sep);
    }
    const span = document.createElement("span");
    if (part.site !== undefined) {
      span.className = "map-site";
      span.textContent = (part.dir === 1 ? "+" : "−") + part.site;
    } else {
      span.className = `map-block block-${part.block}`;
      span.textContent = (part.dir === 1 ? "+" : "−") + part.block;
    }
    node.appendChild(span);
  });
}

const chain = (state) => state.blocks.map(([l, d]) => (d === 1 ? SEQ[l] : RC[l])).join("");

export function mountBiology(root) {
  const svg = root.querySelector("#bio-figure");
  const title = root.querySelector("#bio-title");
  const body = root.querySelector("#bio-body");
  const map = root.querySelector("#bio-map");
  const seq = root.querySelector("#bio-seq");
  const dots = root.querySelector("#bio-dots");
  const prev = root.querySelector("#bio-prev");
  const next = root.querySelector("#bio-next");

  let index = 0;

  STEPS.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "bio-dot";
    dot.setAttribute("aria-label", `Step ${i + 1}`);
    dot.addEventListener("click", () => show(i));
    dots.appendChild(dot);
  });

  function show(i) {
    index = (i + STEPS.length) % STEPS.length;
    const step = STEPS[index];
    drawPlasmid(svg, step.state, step.mark, index === 1);
    title.textContent = step.title;
    body.textContent = step.body;
    renderMap(map, step.state);
    seq.textContent = chain(step.state);
    [...dots.children].forEach((d, k) => d.classList.toggle("active", k === index));
  }

  prev.addEventListener("click", () => show(index - 1));
  next.addEventListener("click", () => show(index + 1));
  show(0);
}
