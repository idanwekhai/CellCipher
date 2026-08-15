# biocrypt

A text ⇄ DNA **encoding/storage** codec — not encryption. Text becomes a
sequence of `A`/`C`/`G`/`T`, and back, using a published, versioned format.
Anyone who knows the format (documented below) can decode it; there is no
secret key. Treat it like base64 or hex, not like a cipher.

The project ships two things sharing one codec library:

- **API** — a FastAPI service (`POST /api/encode`, `POST /api/decode`)
- **Frontend** — a static web UI (`interface/`) served by the same app

## Why this exists

Two substantially different products live under "text-to-DNA":

1. A **software codec** — represent text as A/C/G/T for fun, for storage-format
   experiments, for teaching bit-packing. Fast, simple, lossless.
2. A **storage codec for real DNA synthesis/sequencing** — must also avoid long
   homopolymers, control GC content, chunk into synthesizable oligos, and add
   error correction (substitutions/indels/dropped fragments are real for
   physical DNA).

This MVP builds (1) — **digital mode** — with the packet format designed so
(2) — a future **synthesis-safe mode** — can be added without breaking the
format or the API contract. See [Format](#packet-format) and
[Roadmap](#roadmap-synthesis-safe-mode) below.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (Python 3.13) — no separate frontend
build step, the API serves the static UI directly.

```bash
uv run main.py
# -> http://localhost:8000        (web UI)
# -> http://localhost:8000/docs   (OpenAPI/Swagger)
```

Run the tests:

```bash
uv run pytest
```

## API

| Endpoint          | Method | Description                                   |
|-------------------|--------|------------------------------------------------|
| `/api/encode`     | POST   | `{"text": "..."}` → DNA + stats                |
| `/api/decode`     | POST   | `{"dna": "..."}` → text + integrity status     |
| `/api/info`       | GET    | Format version, magic bytes, supported modes   |
| `/api/health`     | GET    | Liveness check                                 |

`/api/decode` never 500s on bad input — malformed, foreign, or corrupted DNA
comes back as `{"valid": false, "error": "...", "error_type": "..."}` with
HTTP 200, since decoding untrusted/damaged DNA is the expected use case, not
an exceptional one.

Example:

```bash
curl -s localhost:8000/api/encode -d '{"text":"Hello, DNA!"}' | python3 -m json.tool
curl -s localhost:8000/api/decode -d '{"dna":"<paste dna here>"}' | python3 -m json.tool
```

## Pipeline (digital mode)

```
text -> UTF-8 bytes -> pick smaller of {raw, Brotli-compressed}
      -> versioned packet (magic | version | mode | flags | original_length | payload | crc32)
      -> direct 2-bit mapping (2 bits -> 1 base, 4 bases per byte)
      -> DNA string
```

Decoding reverses every step and verifies the CRC32 before trusting the
payload. `00→A 01→C 10→G 11→T`, most-significant bit-pair first — e.g. the
byte for `"A"` (`01000001`) encodes as `C A A C`.

Compression is chosen per-message: both the raw and Brotli-compressed payload
are tried, and whichever produces the shorter DNA sequence wins (for short
strings, compression overhead usually loses). A flag bit records which one
was used so decoding doesn't have to guess.

## Packet format

```
magic (2B) | version (1B) | mode (1B) | flags (1B) | original_length (4B) | payload (N) | crc32 (4B)
```

- **magic** — `"BC"`. DNA that doesn't decode to this magic wasn't produced by
  this codec (arbitrary/biological DNA does not inherently decode to text).
- **version** — bumps only if this header layout changes.
- **mode** — which encoding scheme was applied to the payload. Today only
  `1 = digital-2bit` exists. This is the extension point for constraint-aware
  encoding later (see below) — a new mode value, a new codec module, one new
  branch in the decoder's dispatch, and the framing above is untouched.
- **flags** — a bitfield for orthogonal choices, currently bit 0 = "payload is
  Brotli-compressed".
- **original_length** — length of the original UTF-8 bytes, checked after
  decompression to catch corruption that CRC32 alone might miss post-decode.
- **crc32** — computed over header + payload; detects corruption, doesn't
  repair it.

`GET /api/info` returns this format's version/magic/modes at runtime so
clients don't have to hardcode assumptions about it.

## Project layout

```
biocrypt/
├── main.py                    # `uv run main.py` — starts the API + UI
├── src/biocrypt/
│   ├── codec/                 # framework-agnostic; no FastAPI/pydantic here
│   │   ├── nucleotide.py      #   raw bytes <-> DNA string (2-bit mapping)
│   │   ├── compression.py     #   Brotli wrapper
│   │   ├── packet.py          #   versioned header framing + CRC32
│   │   ├── digital.py         #   the mode-1 pipeline (encode/decode)
│   │   ├── stats.py           #   byte count, GC%, homopolymer run, etc.
│   │   └── errors.py          #   typed exceptions (DecodeError subclasses)
│   └── api/
│       ├── app.py             # FastAPI app, CORS, mounts interface/ as static
│       ├── routes.py          # /api/encode, /decode, /info, /health
│       └── schemas.py         # pydantic request/response models
├── interface/                 # static frontend (no build step)
│   ├── index.html
│   ├── styles.css
│   └── js/{api,render,app}.js # fetch wrapper / DOM rendering / wiring
└── tests/
```

The codec package has no web dependencies, so it's usable from a script or
notebook (`from biocrypt.codec import digital; digital.encode("hi")`)
independent of the API.

## Modes

- **Digital** *(implemented)* — the pipeline above. Optimizes for simplicity
  and software round-tripping, not physical synthesis. It can (and, on real
  text, often does) produce long homopolymer runs or skewed GC content — the
  UI's "longest homopolymer" and "GC content" stats make this limitation
  visible rather than hiding it.
- **Synthesis-safe** *(planned, `mode = 2`, exposed in `/api/info` as
  `implemented: false`)* — for physical DNA synthesis/sequencing, which
  requires:
  - avoiding long homopolymers and extreme GC content (rotating/ternary
    codes, finite-state constrained coding, or screening candidate encodings)
  - chunking into synthesizable oligos with sequence numbers/identifiers
  - error correction beyond detection — Reed-Solomon and/or fountain codes,
    since physical DNA introduces substitutions, indels, and dropped
    fragments that a checksum can only detect, not repair

  Practical density for constrained encodings is commonly ~1.5–1.9 bits/base
  before primers, indexes, and error-correction overhead, versus the 2
  bits/base ceiling of direct mapping.

## Roadmap (synthesis-safe mode)

The packet format's `mode` byte and `codec/` module boundary exist specifically
so this can be added later without breaking `mode = 1` clients:

1. New `codec/constrained.py` — homopolymer/GC-aware bytes→bases mapping.
2. New `codec/chunking.py` — split large payloads into fixed-size oligos, each
   with a sequence number, total-chunk count, and its own local checksum.
   Add Reed-Solomon and/or fountain-code redundancy across chunks.
3. `packet.MODE_SYNTHESIS_SAFE = 2`, wired into `digital.decode()`'s mode
   dispatch (or a sibling `synthesis.py` with its own `encode`/`decode`).
4. API: `mode` becomes a real request parameter instead of always
   `"digital"`; `/api/info` flips that mode's `implemented` to `true`.
5. UI: enable the already-present (currently disabled) "Synthesis-safe" mode
   option, and surface chunk count / redundancy level as additional stats.
