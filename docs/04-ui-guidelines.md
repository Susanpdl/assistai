# 04 · UI Design Guidelines (Minimal)

**Rule:** every screen we build follows this. Consistency is a feature — it makes the app feel
trustworthy and easy to learn. These guidelines describe the design system already implemented in
[`src/styles.css`](../src/styles.css); when building new UI, **reuse these tokens and components
instead of inventing new styles.**

## Design principles

1. **Monochrome by default.** Black/near-black text on white, with a gray scale for hierarchy. The
   *only* color is the green "live" dot — because color should carry meaning, not decoration.
2. **Flat, not glossy.** No gradients, no drop shadows (except a single subtle one on floating
   elements). Structure comes from thin 1px borders and whitespace.
3. **Whitespace over dividers.** Prefer spacing to separate things; use a hairline border only when
   spacing isn't enough.
4. **Few weights, clear hierarchy.** Regular text, medium for emphasis, semibold for headings.
   Avoid bold everywhere.
5. **Quiet states.** Badges and pills are outlines or small dots, not loud filled colors.

## Design tokens (the variables to reuse)

These are CSS custom properties defined in `:root` in `styles.css`. Use the variable, never a raw
hex value. *(A "token" is a named design value — change it once and the whole app updates.)*

### Color
| Token | Value | Use |
|-------|-------|-----|
| `--ink` | `#18181b` | Primary text, primary buttons, selected states. |
| `--ink-soft` | `#52525b` | Secondary text. |
| `--muted` | `#a1a1aa` | Tertiary text, captions, placeholders. |
| `--faint` | `#d4d4d8` | Disabled, subtle fills. |
| `--line` | `#ececee` | Hairline borders / dividers. |
| `--line-strong` | `#e0e0e3` | Input + card borders. |
| `--bg` / `--surface` | `#ffffff` | Page and card background. |
| `--surface-2` | `#fafafa` | Subtle raised/recessed fill. |
| `--live` | `#16a34a` | The one accent — live/online only. |

### Shape & depth
| Token | Value |
|-------|-------|
| `--radius` / `--radius-sm` / `--radius-lg` | `8px` / `6px` / `10px` |
| `--shadow` | `0 1px 2px rgba(24,24,27,.04)` (subtle) |
| `--shadow-lg` | floating elements only |

### Type
- Font: **Inter** (system sans fallback).
- Headings: semibold (600), slightly negative letter-spacing.
- Body: ~14.5px, line-height ~1.6.

## Component patterns (already built — reuse them)

- **Buttons:** `.btn--primary` (solid `--ink`), `.btn--ghost` (outline). Hover = subtle opacity/border.
- **Avatars:** `.avatar` — flat `--ink` circle with initials. Monochrome (tone variants collapse to neutral).
- **Cards:** `.card`, `.stat-card` — white, 1px `--line` border, no shadow.
- **Chat:** `.bubble` (AI = bordered white, user = `--surface-2`), `.source-pill` (renders "Source · …").
- **Poll:** `.poll-card`, `.poll-opt` (selected = `--ink` border + key chip filled).
- **Badges:** `.status-badge` — outline + a small dot (`○` needs / `●` done), never a loud fill.
- **Inputs:** `.composer__inner` — border focuses to `--ink`.
- **Nav:** `.nav-item` — active = `--surface-2` fill, not a colored highlight.

## Do / Don't

| ✅ Do | ❌ Don't |
|------|---------|
| Use `--ink` for the primary action on a screen. | Introduce a new brand color. |
| Separate sections with whitespace. | Add gradients or heavy shadows. |
| Use outline badges with a dot. | Use filled red/green/blue status pills. |
| Reuse existing component classes. | Write one-off inline styles for new colors. |
| Keep one clear primary action per view. | Compete several bright buttons for attention. |

## When adding a genuinely new component

1. Build it from the tokens above.
2. Add its class to `styles.css` near related components (keep the file organized).
3. If it introduces a new pattern, add a one-line note to the "Component patterns" list here so the
   next screen can reuse it.

*(The point: the design system grows by reuse, not by each screen reinventing its look.)*
