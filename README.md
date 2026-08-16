# biocrypt

A text ⇄ DNA codec. The base pipeline is **encoding, not encryption** — text
becomes a sequence of `A`/`C`/`G`/`T`, and back, using a published, versioned
format with no secret key; treat it like base64 or hex. On top of that,
there's an *optional* passphrase-scrambled mode that is a real (if simple)
keyed cipher — see [Scrambling](#scrambling-optional-keyed-layer) for exactly
what that does and doesn't protect against.

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
| `/api/encode`     | POST   | `{"text": "...", "passphrase"?, "use_nonce"?}` → DNA + stats |
| `/api/decode`     | POST   | `{"dna": "...", "passphrase"?}` → text + integrity status    |
| `/api/info`       | GET    | Format version, magic bytes, supported modes, scrambling info |
| `/api/health`     | GET    | Liveness check                                 |

`/api/decode` never 500s on bad input — malformed, foreign, corrupted, or
wrongly/un-scrambled DNA comes back as
`{"valid": false, "error": "...", "error_type": "..."}` with HTTP 200, since
decoding untrusted/damaged input is the expected use case, not an exceptional
one. The response also always includes `"scrambled": true/false`, detected
from the DNA's own (unscrambled) preamble even when decoding fails — so a
client can tell "wrong/missing passphrase" apart from "not scrambled at all."

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

## Scrambling (optional keyed layer)

Passing a `passphrase` wraps the digital-mode DNA in a second, independent
step: a **keyed block-transposition cipher**. It shuffles the DNA in 4-byte
(16-base) blocks, using a permutation derived from the passphrase, so the
result can't be reordered back to text without that same passphrase.

```
dna (from digital.encode)
  -> pad to a multiple of 4 bytes (0-3 padding bytes, length recorded)
  -> split into N 4-byte blocks
  -> derive a permutation from HMAC-SHA256(sha256(passphrase), nonce, counter)
  -> reorder the blocks by that permutation
  -> prepend an unscrambled preamble: magic("SC") | version | flags | pad_len [ | nonce ]
```

The preamble is deliberately **not** scrambled — a decoder (or the UI) can
always read it to learn "this is scrambled" and pull out the nonce, with no
passphrase needed. Only the block *order* is secret-dependent. This is also
how `is_scrambled()` distinguishes scrambled output from plain digital-mode
DNA (which starts with a different magic, `"BC"`) without needing a key.

**Nonce**, toggled per-request via `use_nonce` (default on): a random 8-byte
value mixed into the permutation so the same passphrase shuffles differently
every time. Without it, the same passphrase + same block count always
produces byte-for-byte identical scrambled DNA — fine for reproducibility,
but it means an attacker who collects multiple messages under one reused key
can start correlating fixed structure (like the packet header always being
in the same disguised position).

**Wrong passphrase, by design, isn't specially detected.** `scramble.py` has
no way to know a passphrase is wrong — it just produces a different (wrong)
block order. That wrong order then fails one of `digital.decode`'s own
checks one layer up (almost always the packet's magic bytes, since
reordering displaces the header) and comes back as a normal decode error —
reusing integrity checks we already had, instead of adding a second one.

**Honest limitations** (this is a transposition cipher, not a substitution
one):
- It preserves the exact multiset of block contents — only their order
  changes. Long messages with repeated/structured content can still leak
  patterns to frequency analysis.
- Short messages are brute-forceable regardless of passphrase strength: N
  blocks have N! possible orderings, and small N is small. Five blocks is
  only 120 arrangements — trying all of them and checking which one passes
  the packet's checksum takes microseconds. Real security needs enough
  blocks and/or a second, substitution-based layer (e.g. XOR-ing the payload
  against a passphrase-derived keystream before this).
- The passphrase is turned into key bytes with a single SHA-256 (no salt, no
  iteration count) — fine for demonstrating the permutation mechanism, but
  it means the passphrase itself is only as hard to brute-force as one hash
  per guess. A hardened version would use PBKDF2/scrypt instead.

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
│   │   ├── scramble.py        #   optional keyed block-transposition layer
│   │   ├── pipeline.py        #   composes digital.py + scramble.py
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
notebook independent of the API: `biocrypt.encode("hi")` /
`biocrypt.decode(dna)` for the full pipeline (pass `passphrase=` to opt into
scrambling), or `biocrypt.codec.digital.encode("hi")` directly for plain
digital-mode only.

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
