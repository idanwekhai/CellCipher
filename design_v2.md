# BioCrypt Design System v2

Version 2.0 · August 2026  
Direction: **Encoded Precision**

## 1. Purpose

BioCrypt turns text into a digital DNA representation and back again. Its
interface should make a technical transformation feel understandable,
deliberate, and a little playful.

This system takes visual inspiration from
[Craft, engineered](https://craft.wild.as/): bright editorial space, a strict
pixel grid, oversized grotesk typography, hairline dividers, black rounded
feature panels, stepped-corner controls, and expressive pixel fields. Those
ideas are adapted into an original product interface. Do not copy Wild’s logo,
copy, proprietary Sneak font, canvas artwork, smileys, Tetris interaction, or
page composition.

### Product statement

> Text, encoded as DNA. Every step visible.

### Experience goal

The product should feel like a beautifully engineered instrument with a human
hand still visible in it: exact enough to trust, lively enough to explore.

## 2. Design principles

1. **Make the mechanism visible.** Source, transformation, output, and integrity
   form one readable sequence.
2. **Snap to the system.** Layout, spacing, data cells, and motion share a 14px
   grid wherever practical.
3. **Use play to explain.** Pixel interactions visualize encoding or system
   state; they never compete with the task.
4. **Editorial outside, operational inside.** Headlines establish character;
   controls and data remain compact and direct.
5. **Reserve contrast for meaning.** Black chapters, blue actions, neon focus,
   and nucleotide colors each have a narrow role.
6. **Be exact about security.** Encoding is not encryption. Passphrase
   scrambling is an optional transposition layer and is described honestly.
7. **Progressive delight.** The core experience works without canvas,
   animation, hover, or JavaScript-enhanced decoration.

## 3. Visual concept

### Precision with a pulse

The default canvas is white with subtle 14px grid alignment. A large, neutral
grotesk headline introduces the operation. Hairline rules divide the interface
like a technical publication. The codec workspace is quiet and rectangular;
its primary action and small numeric markers use pixel-stepped corners.

DNA output becomes the signature visual: letters remain readable, while groups
of bases align to cells and can expand into a colored pixel map. Motion advances
in discrete steps, echoing the conversion from bytes to bases.

### Brand attributes

- Rigorous
- Open
- Experimental
- Contemporary
- Candid
- Playful in small doses

### Avoid

- Cybersecurity clichés, locks, shields, glowing green code, or “hacker” black
- Biological photography, microscopes, wet-lab imagery, or double-helix stock art
- Glass surfaces, gradients on controls, soft floating cards, or heavy shadows
- Emoji in product UI
- Pixel decoration that changes or obscures source data
- Claims that encoded or scrambled output is fully encrypted

## 4. Foundations

### 4.1 The 14px grid

`--cell: 14px` is the base unit. Major spacing is expressed in whole cells;
compact spacing may use half-cells.

| Token | Value | Cells | Use |
|---|---:|---:|---|
| `--space-0-5` | `7px` | 0.5 | Tight inline gap |
| `--space-1` | `14px` | 1 | Field and label gap |
| `--space-2` | `28px` | 2 | Control groups, mobile gutter |
| `--space-3` | `42px` | 3 | Column gap, panel padding |
| `--space-4` | `56px` | 4 | Desktop gutter |
| `--space-6` | `84px` | 6 | Section separation |
| `--space-8` | `112px` | 8 | Editorial section padding |
| `--space-10` | `140px` | 10 | Large chapter spacing |

Alignment matters more than forcing every control dimension to 14px. Touch
targets remain at least 44px; use 48px or 56px where the grid permits.

### 4.2 Color

The system is primarily white, ink, and gray. Blue is the functional brand
accent. Neon, yellow, and red are short-lived signals or visualization colors.

| Token | Value | Role |
|---|---:|---|
| `--paper` | `#FFFFFF` | Page and primary surface |
| `--ink` | `#0A0A0A` | Primary text and black panels |
| `--ink-soft` | `#2A2A2A` | Body copy |
| `--muted` | `#858585` | Supporting labels and inactive states |
| `--line` | `rgba(10,10,10,.12)` | Standard rule |
| `--line-soft` | `rgba(10,10,10,.06)` | Grid and subtle division |
| `--blue` | `#3B5BD9` | Primary action and active state |
| `--blue-deep` | `#263B98` | Pressed state |
| `--navy` | `#1C2541` | Dense data and secondary dark tone |
| `--neon` | `#D8FF00` | Focus and live transformation signal |
| `--yellow` | `#F5C518` | Caution and visualization band |
| `--red` | `#E0492A` | Errors and high-intensity visualization |
| `--valid` | `#16845B` | Verified integrity |
| `--invalid` | `#C43D28` | Invalid or corrupt result |

#### Nucleotide palette

Nucleotide colors borrow from the heat-field palette but are adjusted for
legible text on white.

| Base | Solid | Pale cell | Meaning |
|---|---:|---:|---|
| A | `#3B5BD9` | `#E3E8FF` | Adenine |
| C | `#D4472D` | `#FFE4DE` | Cytosine |
| G | `#718700` | `#EDFFC2` | Guanine |
| T | `#9A7300` | `#FFF0B5` | Thymine |

Every colored base contains its letter. Provide a monochrome sequence mode.
Never assign nucleotide colors to unrelated UI states.

#### Color ratios

- 78% paper
- 14% ink and dark panels
- 5% gray rules and muted text
- 2% blue
- 1% neon, yellow, red, and nucleotide accents

### 4.3 Typography

Use self-hosted, open-source font files in production.

| Role | Family | Fallback | Use |
|---|---|---|---|
| Display/UI | **Geist** | `"Helvetica Neue", Arial, sans-serif` | Headlines, controls, body |
| Technical | **IBM Plex Mono** | `ui-monospace, monospace` | Labels, sequence, counts, metadata |

Geist provides the neutral grotesk character without reproducing Craft’s
proprietary typography. Use optical sizing and tabular numerals when available.

| Style | Size / line-height | Weight | Tracking |
|---|---|---:|---:|
| Hero | `clamp(3rem, 7.5vw, 7.25rem) / .90` | 400 | `-.045em` |
| Display | `clamp(2.25rem, 4.5vw, 4.5rem) / .96` | 400 | `-.035em` |
| Section heading | `clamp(1.75rem, 3vw, 2.875rem) / 1.06` | 400 | `-.025em` |
| Component heading | `1.25rem / 1.15` | 500 | `-.015em` |
| Body | `1rem / 1.62` | 400 | normal |
| UI | `.9375rem / 1.35` | 500 | `-.01em` |
| Mono label | `.6875rem / 1.3` | 500 | `.16em` |
| Sequence | `.875rem / 1.75` | 500 | `.04em` |
| Micro | `.625rem / 1.3` | 500 | `.12em` |

Rules:

- Hero headings may use uppercase; sentence case is preferred elsewhere.
- Keep operational labels to three words when possible.
- Use uppercase mono for metadata: `FORMAT V1`, `80 UTF-8 BYTES`.
- Never uppercase user content or decoded text.
- Use tabular numbers for counts, GC percentage, byte size, and run length.
- Limit explanatory copy to 58 characters per line.

### 4.4 Rules and surfaces

- Standard divider: `1px solid var(--line)`
- Strong divider: `1px solid rgba(10,10,10,.28)`
- Page sections use rules instead of container shadows
- Fields are white or `#FAFAF8`; no tinted glass
- Standard field radius: `0`
- Compact control radius: `8px`
- Feature panel radius: `26px`
- Feature panels sit 8px from viewport edges on small screens
- Shadows are limited to overlays: `0 12px 40px rgba(10,10,10,.12)`

### 4.5 Pixel-stepped shape

The stepped corner is a brand accent for primary buttons, numbered markers, and
compact active tags. It is not a universal container shape.

```css
.pixel-corners {
  clip-path: polygon(
    10px 0, calc(100% - 10px) 0,
    calc(100% - 10px) 5px, calc(100% - 5px) 5px,
    calc(100% - 5px) 10px, 100% 10px,
    100% calc(100% - 10px), calc(100% - 5px) calc(100% - 10px),
    calc(100% - 5px) calc(100% - 5px), calc(100% - 10px) calc(100% - 5px),
    calc(100% - 10px) 100%, 10px 100%,
    10px calc(100% - 5px), 5px calc(100% - 5px),
    5px calc(100% - 10px), 0 calc(100% - 10px),
    0 10px, 5px 10px, 5px 5px, 10px 5px
  );
}
```

Always provide a normal rectangular fallback before `clip-path`.

### 4.6 Iconography

Use 18–20px line icons with 1.5px strokes. Icons are geometric and quiet:
arrows, copy sheets, eye/show, check, close, chevron, and bracket shapes. Do not
use decorative lab or security icons. Primary actions retain visible text.

## 5. Application architecture

### 5.1 Desktop layout (≥ 1024px)

Maximum content width is `1176px`. The page gutter is 56px. The layout follows
a 12-column grid with 28px gutters.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ BIOCRYPT / FORMAT 01                    DIGITAL 2-BIT      API ● ONLINE │
├─────────────────────────────────────────────────────────────────────────┤
│ TEXT,                                        A REVERSIBLE DIGITAL       │
│ ENCODED AS DNA.                              CODEC. NOT ENCRYPTION.     │
│                                                                         │
│ [ ENCODE ] [ DECODE ]                         A  C  G  T                │
├─────────────────────────────────────────────────────────────────────────┤
│ 01 SOURCE                              02 OUTPUT                         │
│ ┌──────────────────────────────┐      ┌──────────────────────────────┐  │
│ │ Text input                   │  →   │ C A A C  C G C C  …         │  │
│ │                              │      │ sequence / recovered text    │  │
│ │                              │      │                              │  │
│ └──────────────────────────────┘      └──────────────────────────────┘  │
│ 18 CHARACTERS    SECURITY +           124 BASES      COPY SEQUENCE     │
│                                                                         │
│                    [ ENCODE → DNA ]                                     │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│ BASES 0124  │ BYTES 0031  │ GC 48.4%    │ MAX RUN 03  │ ✓ CRC VERIFIED │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
```

#### Regions

1. **Masthead** — a 42px metadata bar, divided from the page by a hairline.
2. **Hero/control header** — two editorial columns. The operation switch lives
   beneath the headline, not in global navigation.
3. **Codec workspace** — a two-column functional area with equal-height editors.
4. **Action bridge** — desktop action sits visually between source and output;
   DOM order remains source, settings, action, output.
5. **Stats ledger** — shared-border cells across the full workspace width.
6. **Technical footer** — packet format and repository information in mono.

### 5.2 Wide desktop (≥ 1440px)

- Keep the content at 1176px rather than stretching fields indefinitely.
- A decorative DNA pixel field may occupy the outer right margin.
- The field must be `aria-hidden`, ignore pointer input over controls, and use no
  more than 8% of frame time on a mid-range laptop.

### 5.3 Tablet (680–1023px)

- Use a 28px gutter.
- Hero remains two columns until 820px, then stacks.
- Source and output stack at widths below 900px.
- The action becomes full-width between source and output.
- Stats wrap into a 3 + 2 grid while sharing borders.

### 5.4 Mobile (< 680px)

- Page gutter: 28px; compact controls may extend to a 14px edge inset.
- Masthead becomes two rows: identity/status, then mode.
- Hero headline is 48–64px and no more than three lines.
- Source → settings → action → output → stats is a single vertical flow.
- Primary action becomes sticky at the bottom only while source is nonempty and
  the result is not in view.
- Stats become a two-column grid; integrity spans both columns.
- Hide nonessential pixel fields. Keep only static DNA cell grouping.
- All editors, result panels, and messages fit without horizontal page scroll.

## 6. Core components

### 6.1 Masthead

Height is three grid cells (`42px`) on desktop. It uses mono uppercase text at
10–11px. Left: `BIOCRYPT / FORMAT 01`. Right: mode and service state.

- Background: paper
- Bottom rule: standard divider
- No large logo or emoji
- Status dot includes text: `● ONLINE`, not a dot alone
- On mobile, increase total height as content wraps; never shrink type below 10px

### 6.2 Hero header

The left column contains the operation-specific statement:

- Encode: `TEXT, / ENCODED AS DNA.`
- Decode: `DNA, / RECOVERED AS TEXT.`

The right column is separated by a vertical hairline and contains:

`A REVERSIBLE DIGITAL CODEC.`  
`NOT ENCRYPTION.`

Below it, four 14px cells labeled A/C/G/T establish the data palette. Keep the
working product hero between 224px and 336px high; this is not a marketing page.

### 6.3 Operation switch

The switch is two adjacent text buttons below the hero statement.

- Active: ink text with a 3px blue underline
- Inactive: muted text
- Hover: ink text; underline grows in four discrete steps
- Focus: 3px neon outline, 2px offset
- Use correct `tablist`, `tab`, and `tabpanel` behavior
- Preserve source content when switching unless the user explicitly clears it

### 6.4 Codec workspace

The workspace is a ruled grid, not a collection of floating cards.

- Top border and bottom border span both panels
- Column divider appears only in two-column layouts
- Each panel begins with a 42px header row
- Panel labels: `01 SOURCE` and `02 OUTPUT`
- Panel horizontal padding: 28px desktop, 0–14px mobile depending on edge
- The output uses the same dimensions as the source to communicate reversibility

### 6.5 Editor field

- Background: `#FAFAF8`
- Border: `1px solid var(--line)`
- Radius: 0
- Minimum height: 294px (21 cells) desktop; 224px (16 cells) mobile
- Padding: 14px
- Font: IBM Plex Mono 14px/1.7
- Caret: blue
- Placeholder: muted; one sentence maximum
- Focus: 1px ink border plus 3px neon outer outline
- Vertical resize is allowed on desktop, disabled on mobile
- Count and validation sit in the metadata row below, never over the content

### 6.6 DNA sequence output

Text is the canonical output. Pixel visualization is a derived view.

#### Sequence view

- Group bases in sets of four with a 14px gap every fourth base
- Wrap lines at a stable multiple of four, based on available width
- Presentational gaps must not enter copied data
- For sequences above three lines, add a muted mono line-number gutter
- Base letters use the nucleotide palette and remain readable at 200% zoom
- Selection uses navy background and white text

#### Pixel view

An optional `SEQUENCE / PIXELS` two-state toggle converts each base into a
colored 14px square containing the letter. It is useful for pattern inspection,
not the default for long sequences.

- Maximum 2,000 rendered cells; virtualize or truncate beyond this threshold
- Add `SHOWING 2,000 OF …` when truncated
- Canvas may be used only if an equivalent accessible text sequence remains in
  the DOM
- Pixel view is static unless the user starts a new encode operation

### 6.7 Primary action

Primary actions use the pixel-stepped shape.

- Default: ink background, white text
- Hover: blue background
- Focus: neon 3px outline with 3px offset
- Active: blue-deep background
- Height: 56px; padding: 0 36px
- Label: `Encode → DNA` or `Decode → Text`
- Loading label: `Encoding 01/04`, advancing to `04/04` in steps without
  pretending to report server progress
- Disabled: `#E9E9E9` background, muted text

Do not move the button on hover. Pixel flicker may affect its background edge
for 180ms, but the label and hit target remain stable.

### 6.8 Secondary and utility buttons

**Secondary button** — white, ink border, 8px radius, 44px minimum height.  
**Text button** — no container; animated stepped underline on hover.  
**Icon button** — 44×44px, 1px rule, accessible label and tooltip.  
**Compact toggle** — shared-border cells, 36px high, mono micro labels.

Use sentence case for action buttons and uppercase mono for data-view toggles.

### 6.9 Copy control

`COPY SEQUENCE` lives in the output metadata row and remains visible while the
result scrolls.

- Default: text button with copy icon
- Success: `COPIED ✓` for 1.5 seconds
- Failure: `COPY FAILED — SELECT TEXT` and selects the sequence when possible
- Clipboard confirmation is announced through a polite live region

### 6.10 Security layer

The disclosure label is `SECURITY LAYER +`. Expanded content remains part of
the source panel.

- Heading: `Passphrase scrambling`
- Field label: `PASSPHRASE`
- Nonce checkbox label: `UNIQUE OUTPUT EACH TIME`
- Always show: `Reorders DNA blocks. This is not modern encryption.`
- Active state: blue marker plus text `SCRAMBLING ON`
- Do not use lock or shield icons
- Wrong or missing passphrase messages explain the next action without claiming
  the passphrase itself was verified

### 6.11 Stats ledger

Stats share one outer border. Each cell is separated by a hairline.

```text
┌────────────┬────────────┬────────────┬────────────┬────────────────┐
│ BASES      │ UTF-8      │ GC CONTENT │ MAX RUN    │ INTEGRITY      │
│ 0124       │ 0031 B     │ 48.4%      │ 03         │ ✓ CRC VERIFIED │
└────────────┴────────────┴────────────┴────────────┴────────────────┘
```

- Label: mono micro, muted
- Value: mono 20px, tabular numerals
- Pad integer display only when it improves scanning; accessible names use the
  natural number (`124`, not `zero one two four`)
- Integrity uses symbol + label + color
- Empty values display `—`, not zero
- GC and max-run warnings require documented thresholds and explanatory text

### 6.12 Status tags

Tags use 8px radius or the small stepped shape. They are compact, never pill
shaped.

- `✓ CRC VERIFIED` — valid green
- `× INTEGRITY FAILED` — invalid red
- `↝ SCRAMBLED` — blue
- `● API ONLINE` — ink
- `○ API OFFLINE` — red
- `PLANNED` — muted outline

Status is never communicated through color alone.

### 6.13 Result chapter

For a successful decode, the output may expand into a black rounded chapter
panel when the recovered text is the focus.

- Background: ink
- Text: paper
- Radius: 26px
- Margin from viewport edge: 8px minimum
- Padding: 42–84px
- Small label: `RECOVERED TEXT`
- User text: Geist 24–46px depending on length; long text reverts to 18px body
- Integrity and copy controls remain visible in a compact header

This treatment is optional for short decoded text and should not be used for
raw DNA output, errors, or empty states.

### 6.14 Messages

Messages are ruled rows tied to the relevant panel.

- Error: red 4px top rule, `COULD NOT DECODE` heading
- Warning: yellow 4px top rule, `CHECK INPUT` heading
- Info: blue 4px top rule
- Success is usually expressed by output plus integrity status, not a toast
- Preserve API error type as muted technical metadata after plain language
- Toasts are used only for clipboard confirmation

## 7. Data visualization language

### 7.1 Transformation field

During encode or decode, a small grid between source and output may show cells
moving through four discrete phases:

1. Read source
2. Build packet
3. Map bytes
4. Verify output

It is a state illustration, not a progress meter. If actual phase information
is unavailable, do not imply timing percentages.

### 7.2 Pixel field rules

- Cell sizes: 7px, 14px, or 28px only
- Keep 1px paper gutters between cells
- Palette order for non-nucleotide heat: navy → blue → yellow → red → neon
- Never put ambient pixels behind body text or form controls
- Decorative fields are `aria-hidden` and `pointer-events: none`
- Cap device pixel ratio at 2 for canvas work
- Pause canvas animation when offscreen or when the tab is hidden
- Replace animated fields with a static poster under reduced motion

## 8. Motion and interaction

Motion is stepped, brief, and tied to state.

| Interaction | Duration | Easing |
|---|---:|---|
| Color hover | `150ms` | `ease` |
| Underline reveal | `280ms` | `steps(4)` |
| Panel reveal | `420ms` | `steps(6)` |
| Disclosure | `220ms` | `cubic-bezier(.16,1,.3,1)` |
| Result reveal | `360ms` | `steps(5)` |
| Copy confirmation | `150ms` | `ease-out` |

Page entrance may reveal the two hero lines in six vertical steps. Run this once
per page load. Do not animate each DNA letter continuously or attach ambient
effects to cursor position inside the working application.

Under `prefers-reduced-motion: reduce`, remove stepped transforms, pixel flicker,
and canvas animation. State changes remain immediate and legible.

## 9. Product states

### Empty

- Source contains a short placeholder
- Output shows a static 8×4 field of pale cells and `OUTPUT APPEARS HERE`
- Stats show em dashes
- Primary action is disabled until valid source exists

### Ready

- Count updates in real time
- Primary action is enabled
- Previous output remains until a new operation starts

### Working

- Preserve source and previous result
- Disable repeated submission
- Update the button label in four visual steps
- Announce `Encoding started` or `Decoding started` through `aria-live="polite"`

### Success

- Replace output atomically
- Populate stats and integrity status
- Enable copy
- On mobile, reveal the result without moving keyboard focus

### Invalid input

- Keep the submitted value
- Apply an invalid border and an adjacent plain-language error
- Move focus to an error summary only after explicit submission
- For DNA input, identify illegal characters and their first position when known

### Network failure

- Preserve all content
- Say `BioCrypt could not reach the codec service.`
- Offer `Try again`; show technical detail only in a disclosure
- API status changes to `○ OFFLINE`

## 10. Accessibility

- Meet WCAG 2.2 AA: 4.5:1 for normal text and 3:1 for large text and UI graphics.
- All controls work with keyboard and show a 3px neon focus indicator with an
  ink inner edge where neon would lack contrast.
- DOM order is source → security → action → output → stats regardless of desktop
  placement.
- Operation controls implement full tab semantics and arrow-key navigation.
- Use live regions for request status and copy confirmation.
- Use `role="alert"` only for submission failures that require attention.
- Colorful DNA retains visible letters and has a monochrome mode.
- Pixel/canvas visuals have accessible text equivalents or are decorative.
- Touch targets are at least 44×44px.
- At 200% zoom, the layout becomes one column and the page does not scroll
  horizontally.
- Respect reduced motion, forced colors, increased contrast, and text resizing.
- Do not insert presentation spaces or line numbers into copied sequence data.

## 11. Content system

### Voice

Direct, calm, and technically exact. Short headlines may be playful; all
security and error copy is literal.

| Use | Avoid |
|---|---|
| `Encode text` | `Encrypt message` |
| `DNA sequence` | `Genetic material` |
| `CRC verified` | `Completely secure` |
| `Passphrase scrambling` | `Unbreakable protection` |
| `Paste a BioCrypt sequence` | `Paste any DNA` |
| `Synthesis-safe / planned` | `Lab-ready` |

### Core copy

Hero:

> TEXT,  
> ENCODED AS DNA.

Clarifier:

> A reversible digital codec. Not encryption. Not yet intended for physical DNA
> synthesis.

Empty output:

> Output appears here.

Decode failure:

> This sequence could not be decoded. Check that it came from BioCrypt and was
> copied completely.

## 12. Token starter

```css
:root {
  color-scheme: light;

  --paper: #ffffff;
  --ink: #0a0a0a;
  --ink-soft: #2a2a2a;
  --muted: #858585;
  --line: rgba(10, 10, 10, 0.12);
  --line-soft: rgba(10, 10, 10, 0.06);
  --blue: #3b5bd9;
  --blue-deep: #263b98;
  --navy: #1c2541;
  --neon: #d8ff00;
  --yellow: #f5c518;
  --red: #e0492a;
  --valid: #16845b;
  --invalid: #c43d28;

  --base-a: #3b5bd9;
  --base-c: #d4472d;
  --base-g: #718700;
  --base-t: #9a7300;

  --font-ui: "Geist", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;

  --cell: 14px;
  --space-0-5: 7px;
  --space-1: 14px;
  --space-2: 28px;
  --space-3: 42px;
  --space-4: 56px;
  --space-6: 84px;
  --space-8: 112px;
  --space-10: 140px;

  --gutter: 56px;
  --content-max: 1176px;
  --radius-control: 8px;
  --radius-chapter: 26px;
  --transition-fast: 150ms ease;
  --transition-step: 280ms steps(4);
}

@media (max-width: 680px) {
  :root { --gutter: 28px; }
}
```

## 13. Migration from the current interface

The existing element IDs and API behavior can remain intact.

1. Replace the current dark page with the paper canvas, metadata masthead, and
   operation-specific hero.
2. Remove emoji brand and security indicators; use text marks and symbols.
3. Convert `.tabs` into the underlined operation switch with complete keyboard
   behavior.
4. Replace the two floating `.card` elements with a single ruled workspace while
   preserving editor and output IDs.
5. Add source/output module headers and metadata rows.
6. Reformat DNA into visual groups of four without changing copied content.
7. Convert `.stat-row` and `.stat-tile` into the shared-border stats ledger.
8. Restyle badges as compact status tags; keep icon + text + color.
9. Add optional sequence/pixel and color/monochrome view toggles.
10. Add stepped loading, live announcements, focus management, and error summary.
11. Introduce decorative pixel fields only after the functional experience passes
    performance and accessibility checks.
12. Test at 360px, 680px, 900px, 1176px, and 1440px; then test keyboard-only,
    200% zoom, reduced motion, forced colors, and slow network behavior.

## 14. Acceptance checklist

- The interface is recognizable as BioCrypt without using a DNA emoji or stock
  helix artwork.
- Layout and spacing visibly follow the 14px grid.
- White space, grotesk type, hairline rules, and pixel accents create the core
  visual identity.
- Source, action, output, and integrity are clear within three seconds.
- There is one primary action per operation.
- DNA remains selectable, copyable, and readable without color.
- Pixel effects explain state and never sit beneath controls or copy.
- Dark rounded panels are rare, intentional chapters—not generic cards.
- Encode, scramble, and encrypt are never conflated.
- The complete task works without animation or decorative canvas.
- No Wild trademarks, proprietary fonts, illustrations, copy, or signature
  interactions are reproduced.
