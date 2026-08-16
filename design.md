# BioCrypt Design System

Version 1.0 · August 2026

## 1. Direction

BioCrypt should feel like an **editorial laboratory instrument**: scientific,
confident, slightly strange, and precise. The interface combines a saturated
cobalt application frame with a warm paper workbench, oversized editorial
type, compact monospaced controls, and thin technical rules.

The visual reference is [Hermes Agent](https://hermes-agent.nousresearch.com/).
The useful ideas are its electric-blue field, restrained palette, high-contrast
serif display type, uppercase mono annotations, framed composition, near-square
controls, paper interludes, and sparse use of acid color. BioCrypt adapts that
language to a working codec; it does not reuse Hermes trademarks, illustrations,
wordmarks, proprietary fonts, or page composition.

### Product promise

> Turn text into DNA, and back again, without hiding what happens in between.

### Design principles

1. **Instrument first.** The input, output, action, and integrity result always
   dominate decoration.
2. **Editorial scale, technical detail.** Large serif statements establish the
   product; mono labels, values, and sequences make it trustworthy.
3. **Visible transformation.** Encode and decode should read as a clear path
   from source → operation → result.
4. **One vivid world.** Cobalt, paper, ink, and acid form the brand. Nucleotide
   colors are reserved for actual sequence data.
5. **Honest security language.** “Encoding” and optional “scrambling” remain
   visibly distinct. Never imply encryption.
6. **Square, ruled, deliberate.** Prefer lines, frames, and alignment over soft
   cards, large radii, gradients, or floating glass surfaces.

## 2. Brand language

### Personality

- Precise, experimental, direct, open, literate
- More research publication than cyberpunk dashboard
- More lab label than consumer settings screen
- Technically serious without pretending the codec is cryptography

### Signature motifs

- A full-bleed cobalt page with an inset keyline frame
- A centered, two-line `BIO / CRYPT` wordmark
- Serif headlines broken across intentional lines
- Mono metadata such as `FORMAT 01`, `DIGITAL 2-BIT`, and `CRC VERIFIED`
- Thin radial or nucleotide-ladder line art, used only as low-contrast texture
- Numbered modules: `01 SOURCE`, `02 TRANSFORM`, `03 RESULT`
- Small rectangular tags that share borders rather than floating pills

Avoid DNA emoji, lock emoji, generic neon gradients, glowing shadows, hexagon
motifs, and imagery of biological samples. BioCrypt works with a digital DNA
representation, not wet-lab material.

## 3. Foundations

### 3.1 Color

The interface is light-on-cobalt at the brand level and ink-on-paper inside the
workbench. Do not introduce a conventional gray-on-black dark theme; cobalt is
the dark theme.

| Token | Value | Use |
|---|---:|---|
| `--color-cobalt` | `#0808E6` | Page, brand surfaces, primary identity |
| `--color-cobalt-deep` | `#0505B8` | Hover/pressed cobalt, selected data |
| `--color-paper` | `#F7F6EE` | Workbench and light controls |
| `--color-white` | `#FFFFFF` | High-emphasis text and output surface |
| `--color-ink` | `#101018` | Text on paper |
| `--color-ink-muted` | `#5E5E68` | Secondary text on paper |
| `--color-blue-muted` | `#B8B8F4` | Secondary text on cobalt |
| `--color-rule-blue` | `#5D5DF0` | Rules on cobalt |
| `--color-rule-ink` | `#C9C8C0` | Rules on paper |
| `--color-acid` | `#DFFF45` | Focus, active control, primary action |
| `--color-coral` | `#FF6B57` | Errors and destructive warnings |
| `--color-mint` | `#64E6B2` | Validity and successful integrity |
| `--color-amber` | `#FFC857` | Caution and incomplete state |

#### Nucleotide data colors

These colors are semantic only inside DNA sequences, legends, and
nucleotide-specific charts. A letter must always accompany the color.

| Base | Foreground | Soft background |
|---|---:|---:|
| A | `#1748D1` | `#DCE4FF` |
| C | `#B93823` | `#FFE0D9` |
| G | `#087851` | `#D4F5E8` |
| T | `#8B5B00` | `#FFF0C2` |

On a cobalt surface, render all DNA letters in paper white unless they sit in
filled base cells. Never communicate A/C/G/T by color alone.

#### Color proportions

- 55% cobalt application frame
- 35% paper or white work surface
- 8% ink and rules
- 2% acid/status accents

Acid is a signal, not a background theme. It should appear once per viewport as
the dominant action or focus point.

### 3.2 Typography

Use open-source fonts and self-host WOFF2 files in production.

| Role | Family | Fallback | Notes |
|---|---|---|---|
| Display | **Bodoni Moda** | `"Times New Roman", serif` | Headlines and wordmark only |
| Interface | **IBM Plex Mono** | `ui-monospace, monospace` | Controls, labels, values, sequences |
| Reading | **Inter** | `system-ui, sans-serif` | Explanations, warnings, longer copy |

The serif supplies the expressive, editorial character. Mono type is the
default operational voice. Inter is used only where mono would slow reading.

| Style | Size / line-height | Weight | Tracking / case |
|---|---|---:|---|
| Display XL | `clamp(3.75rem, 9vw, 8.5rem) / .84` | 400 | `-.035em`, title case |
| Display L | `clamp(2.75rem, 6vw, 5.5rem) / .9` | 400 | `-.025em`, title case |
| Heading M | `2rem / 1` | 400 | `-.015em`, title case |
| Heading S | `1.25rem / 1.1` | 500 | normal |
| UI label | `.6875rem / 1.2` | 600 | `.14em`, uppercase |
| UI body | `.8125rem / 1.45` | 450 | normal |
| Reading body | `.9375rem / 1.55` | 400 | normal |
| Data | `.875rem / 1.65` | 500 | `.025em`, tabular nums |
| Micro | `.625rem / 1.3` | 600 | `.12em`, uppercase |

Rules:

- Do not set paragraphs or user content in uppercase.
- Use uppercase labels of five words or fewer.
- Preserve user text exactly; never apply text transforms to it.
- DNA, checksums, byte counts, and code always use mono with tabular numerals.
- Use true ellipses and arrows: `…`, `→`, `⇄`.

### 3.3 Spacing

Use a 4px base grid.

| Token | Value | Typical use |
|---|---:|---|
| `--space-1` | `4px` | Inline optical correction |
| `--space-2` | `8px` | Tight icon/label gaps |
| `--space-3` | `12px` | Compact control padding |
| `--space-4` | `16px` | Field gaps |
| `--space-5` | `24px` | Card padding, grouped controls |
| `--space-6` | `32px` | Module gaps |
| `--space-7` | `48px` | Section separation |
| `--space-8` | `64px` | Desktop workbench padding |
| `--space-9` | `96px` | Editorial masthead spacing |

### 3.4 Shape, border, and depth

- Outer app frame: `2px` paper keyline, inset `12px` from the viewport on desktop
- Standard rule: `1px solid currentColor` at 20–28% opacity
- Strong rule: `2px solid currentColor`
- Radii: `0` for layout, `2px` for fields, `4px` maximum for overlays
- Primary button shadow: `4px 4px 0 #101018` on paper only
- No card drop shadows, blur, glassmorphism, or gradient borders
- Texture: optional monochrome noise at 2–3% opacity on large cobalt areas

### 3.5 Iconography

Use simple 20px line icons with a 1.5px stroke, square caps where possible.
Icons support a text label and never replace one for primary actions. Preferred
symbols are arrows, brackets, copy sheets, check marks, and a four-rung DNA
ladder. Do not use emoji in production UI.

## 4. Application layout

### 4.1 Desktop shell (≥ 1024px)

The application occupies the viewport inside the cobalt frame. Content has a
maximum width of `1440px`, centered, with `clamp(24px, 4vw, 64px)` gutters.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ BIOCRYPT / OPEN CODEC       BIO              MODE: DIGITAL 2-BIT    │
│ FORMAT 01                   CRYPT             API ● ONLINE           │
├──────────────────────────────────────────────────────────────────────┤
│ OPEN SOURCE • REVERSIBLE                                              │
│ Text becomes DNA.                   faint nucleotide line artwork    │
│ And back again.                                                       │
│                                                                        │
│ [ ENCODE ] [ DECODE ]                     NOT ENCRYPTION ↗            │
├────────────────────── PAPER WORKBENCH ────────────────────────────────┤
│ 01 SOURCE                         03 RESULT                            │
│ ┌──────────────────────────┐      ┌──────────────────────────────┐    │
│ │ user input               │  →   │ DNA / recovered text         │    │
│ │                          │      │                              │    │
│ └──────────────────────────┘      └──────────────────────────────┘    │
│ SECURITY LAYER / optional           COPY                              │
│ [ passphrase                 ]      [ ENCODE → DNA ]                  │
├──────────────────────────────────────────────────────────────────────┤
│ BASES 320 │ BYTES 80 │ GC 48.7% │ RUN 4 │ CRC VERIFIED               │
└──────────────────────────────────────────────────────────────────────┘
```

#### Regions

1. **Utility masthead** — three columns: product descriptor, centered stacked
   wordmark, mode/service status. Height `88px`; no sticky behavior initially.
2. **Editorial intro** — compact on the working product, `220–320px` tall. It
   carries one headline, one truth statement, and the encode/decode switch.
3. **Paper workbench** — the functional center. It spans the content width and
   uses a 12-column grid with a 32px gutter.
4. **Source and result** — each occupies 6 columns. Both align at the top and
   have equal minimum heights.
5. **Stats rail** — a shared-border strip below the editor, not a set of
   floating tiles.
6. **Format footer** — small cobalt metadata below the workbench.

### 4.2 Tablet (768–1023px)

- Keep the three-part masthead but reduce secondary metadata.
- Intro height is `200px`; headline maxes at `4.5rem`.
- Source and result remain side by side at equal width.
- Move security options beneath the source editor.
- Allow stats to wrap into two rows of three cells.

### 4.3 Mobile (< 768px)

- Remove the inset outer frame; retain a 4px paper rule at the top.
- Masthead becomes two columns: wordmark left, mode/status right.
- Hide decorative art and product descriptor.
- Stack the flow as source → action → result.
- Use a sticky bottom action zone for Encode/Decode when the source is nonempty.
- Stats become a horizontally scrollable, snap-aligned rail.
- Minimum side gutter is 16px and minimum control height is 44px.
- The result must appear immediately after the action; optional security settings
  stay collapsed by default.

## 5. Core components

### 5.1 Wordmark

`BIO` over `CRYPT`, centered on desktop and left-aligned on mobile. Use the UI
mono face, extra-bold, `.08em` tracking, and `0.82` line-height. The display
serif belongs to messaging, not the wordmark. The mark must remain text so it is
crisp and accessible.

### 5.2 Operation switch

A two-cell segmented control with one shared 1px border.

- Inactive: transparent, paper text, 70% opacity
- Hover: paper text, underline 2px below baseline
- Active: paper fill, cobalt text
- Focus: 2px acid outline with 3px offset
- Labels: `ENCODE` and `DECODE`; do not add icons

Changing the operation updates the headline microcopy and workbench labels but
does not animate the entire page.

### 5.3 Workbench module

The workbench is one paper rectangle divided by rules. Avoid nested cards.

- Background: paper
- Foreground: ink
- Top label strip: `40px`
- Main padding: `24px` mobile, `clamp(24px, 3vw, 48px)` desktop
- Module number and label sit on one baseline: `01 / SOURCE TEXT`
- The main action sits at the lower right of the source module

### 5.4 Text editor

- White background, 1px ink rule, 2px radius
- Minimum height: `280px` desktop, `220px` mobile
- User input in mono at 14px/1.65
- Placeholder at 45% ink opacity; no instructional essay inside the field
- Character/base count anchored below the field, right aligned
- Focus uses a 2px cobalt outline; invalid input adds a coral left rail and a
  plain-language message below

Do not resize editors horizontally. Vertical resizing may be enabled on desktop.

### 5.5 DNA output

The output is selectable text, not a decorative visualization.

- Break sequence into visual groups of 4 bases and lines of 48–64 bases
- Insert visual spacing with rendering markup, never into copied data
- Each base uses its semantic color on white; offer a `MONOCHROME` display toggle
  for very long sequences and accessibility preferences
- A line-number gutter appears for output over 3 lines
- `COPY SEQUENCE` stays visible in the output header
- Successful copy changes the label to `COPIED ✓` for 1.5 seconds
- Empty state: a thin four-rung ladder motif plus `SEQUENCE WILL APPEAR HERE`

### 5.6 Primary action

- Acid fill, ink text, 1px ink border, 2px radius
- Mono uppercase label: `ENCODE → DNA` or `DECODE → TEXT`
- Height `48px`; horizontal padding `20px`
- Hover: translate `-2px, -2px`, increasing the offset shadow
- Active: translate to `2px, 2px`, removing the shadow
- Loading: retain width, replace arrow with a four-step text pulse
  `A C G T`; respect reduced-motion preferences
- Disabled: paper background, muted ink, no shadow

Only one acid primary action may appear in a workbench.

### 5.7 Buttons

**Secondary** — transparent, 1px current-color border; used for copy and utility
actions.

**Text** — underline on hover; used for disclosure and help.

**Icon button** — 40×40px minimum, bordered, with an accessible name.

Do not use pill buttons. Do not pair two primary buttons.

### 5.8 Security disclosure

Rename the current disclosure to `SECURITY LAYER / OPTIONAL`. Its collapsed
summary reads `ADD PASSPHRASE SCRAMBLING +`.

When expanded:

- Place it in an ink-keylined inset area inside the source module.
- Label the field `PASSPHRASE`; offer show/hide as a text button.
- Keep nonce enabled by default and shorten its label to `UNIQUE PER MESSAGE`.
- Include the permanent note: `SCRAMBLING REORDERS BLOCKS. IT IS NOT MODERN
  ENCRYPTION.`
- When active, show a rectangular `SCRAMBLED` tag, never a lock icon.

### 5.9 Mode selector

Use a small bordered menu in the masthead. The control label is `MODE`; selected
value is `DIGITAL 2-BIT`. The planned synthesis option reads
`SYNTHESIS-SAFE / PLANNED` and remains disabled with a visible explanation.

### 5.10 Stats rail

Replace individual stat cards with one shared-border grid.

```text
┌────────────┬────────────┬────────────┬────────────┬────────────────┐
│ BASES      │ UTF-8      │ GC CONTENT │ MAX RUN    │ INTEGRITY      │
│ 320        │ 80 B       │ 48.7%      │ 4          │ ✓ VERIFIED     │
└────────────┴────────────┴────────────┴────────────┴────────────────┘
```

- Labels use Micro style; values use 20px mono
- Integrity uses icon + text + color
- GC and homopolymer values stay neutral unless they cross a documented
  synthesis-risk threshold
- Animate numbers only from blank to value, never on every render

### 5.11 Tags and status

Tags are small rectangles with 1px borders and 0 radius. Adjacent tags share a
border. Use icon/symbol + label, never color alone.

- Valid: `✓ CRC VERIFIED` in mint/ink
- Invalid: `× INTEGRITY FAILED` in coral/ink
- Scrambled: `↝ SCRAMBLED` in cobalt/ink
- Service: `● API ONLINE` / `○ API OFFLINE`
- Planned: `— PLANNED`

### 5.12 Messages

Messages occupy a full-width ruled row beneath the relevant module.

- Error: coral 4px left rule, `ERROR /` prefix, plain-language detail
- Warning: amber 4px left rule, `CHECK /` prefix
- Success: normally represented by result/status, not a toast
- Toasts are reserved for clipboard confirmation and disappear after 2 seconds

Never expose raw stack traces. Keep useful API error types as secondary mono
metadata after the human explanation.

## 6. Interaction and motion

Motion should feel mechanical and quick.

| Interaction | Duration | Easing |
|---|---:|---|
| Hover/focus color | `120ms` | `linear` |
| Disclosure | `180ms` | `ease-out` |
| Operation switch | `160ms` | `cubic-bezier(.2,.8,.2,1)` |
| Result reveal | `220ms` | `cubic-bezier(.2,.8,.2,1)` |
| Copy confirmation | `150ms` | `ease-out` |

Result reveal is a simple opacity transition plus a 6px upward movement. Do not
animate every base. No scroll-jacking, parallax, custom cursor, or continuous
ambient motion in the application.

With `prefers-reduced-motion: reduce`, remove transforms and use immediate state
changes. Loading state may still update text without animation.

## 7. Responsive and state behavior

### Empty

- Primary action is available for encode only when text exists.
- Output contains the quiet ladder motif and one short instruction.
- Stats rail is present as structure but values show em dashes.

### Working

- Preserve all source content and previous output.
- Disable the action and announce status through `aria-live="polite"`.
- Use `ENCODING A C G T` or `DECODING T G C A` as the loading label.

### Success

- Reveal output, enable copy, populate stats, and announce completion.
- On mobile, scroll the result heading into view only if it is fully below the
  viewport; never steal focus.

### Failure

- Preserve the submitted input.
- Move focus to the error summary only for submission errors.
- Identify the affected field and provide a recovery action.
- A wrong/missing passphrase should say what to try without claiming the
  passphrase itself was verified.

## 8. Accessibility

- Meet WCAG 2.2 AA: 4.5:1 for normal text and 3:1 for large text and UI graphics.
- Every interaction must work by keyboard and show a 2px acid focus outline.
- Maintain DOM order as source → settings → action → result → stats, even when
  desktop CSS places source and result side by side.
- Tabs use `tablist`, `tab`, and `tabpanel` semantics with arrow-key navigation.
- Use `aria-live="polite"` for process and clipboard messages; use `role="alert"`
  for failed submissions.
- Never rely on color, serif styling, position, or animation as the only signal.
- Keep touch targets at least 44×44px.
- DNA base coloring must have a monochrome alternative and retain visible letters.
- Do not insert spaces into copied DNA; rendering groups are presentational.
- At 200% zoom, the application must become a single column without horizontal
  page scrolling.

## 9. Content style

Use short, declarative, technically accurate language.

| Prefer | Avoid |
|---|---|
| `Encode text` | `Encrypt your message` |
| `DNA sequence` | `Genetic code` |
| `CRC verified` | `100% secure` |
| `Add passphrase scrambling` | `Military-grade protection` |
| `Paste a BioCrypt sequence` | `Paste any DNA` |
| `Synthesis-safe / planned` | `Coming soon! 🚀` |

Headlines may be expressive: `Text becomes DNA.` Supporting text must clarify:
`A reversible digital codec—not encryption and not yet designed for physical
DNA synthesis.`

## 10. CSS token starter

```css
:root {
  color-scheme: light;

  --color-cobalt: #0808e6;
  --color-cobalt-deep: #0505b8;
  --color-paper: #f7f6ee;
  --color-white: #ffffff;
  --color-ink: #101018;
  --color-ink-muted: #5e5e68;
  --color-blue-muted: #b8b8f4;
  --color-rule-blue: #5d5df0;
  --color-rule-ink: #c9c8c0;
  --color-acid: #dfff45;
  --color-coral: #ff6b57;
  --color-mint: #64e6b2;
  --color-amber: #ffc857;

  --base-a: #1748d1;
  --base-c: #b93823;
  --base-g: #087851;
  --base-t: #8b5b00;

  --font-display: "Bodoni Moda", "Times New Roman", serif;
  --font-ui: "IBM Plex Mono", ui-monospace, monospace;
  --font-reading: "Inter", system-ui, sans-serif;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;
  --space-9: 96px;

  --radius-field: 2px;
  --radius-overlay: 4px;
  --content-max: 1440px;
  --frame-inset: 12px;
  --control-height: 44px;
  --transition-fast: 120ms linear;
  --transition-ui: 180ms cubic-bezier(.2, .8, .2, 1);
}
```

## 11. Migration map

The redesign can retain the current HTML IDs and JavaScript behavior. Change
structure and classes in this order:

1. Replace `.viz-root` with the framed cobalt app shell and utility masthead.
2. Replace the emoji brand block with the text wordmark and product metadata.
3. Add the editorial intro and restyle `.tabs` as the operation switch.
4. Merge the two `.card` elements into one ruled `.workbench` grid while keeping
   all form and output IDs intact.
5. Restyle textareas and outputs as editors with numbered module headers.
6. Convert `.stat-row` / `.stat-tile` into the shared-border stats rail.
7. Convert badges to rectangular tags and replace emoji with text symbols.
8. Add loading announcements, keyboard tab behavior, focus management, and the
   monochrome DNA option.
9. Test at 360px, 768px, 1024px, and 1440px; then test keyboard-only, 200% zoom,
   reduced motion, and high-contrast mode.

## 12. Design acceptance checklist

- The product reads as BioCrypt before it reads as a generic developer tool.
- Cobalt dominates the brand shell; paper dominates the working surface.
- One serif statement is visible, but all operational data remains mono.
- Encode/decode, source/result, and plain/scrambled states are immediately clear.
- There is only one acid primary action per view.
- Inputs and results remain the largest functional areas.
- Every status includes text or a symbol in addition to color.
- The interface never describes encoding or scrambling as encryption.
- Mobile preserves the complete source → action → result order.
- No Hermes artwork, font files, brand marks, or unique copy is reproduced.
