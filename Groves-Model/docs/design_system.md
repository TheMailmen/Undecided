# Groves Apartments — Design System Specification

## Colors

| Token | Hex | Use |
|-------|-----|-----|
| `C_TITLE` | `#0D1B2A` | Title bar (row 1), column headers |
| `C_SUB` | `#1A2332` | Subtitle bar (row 2) |
| `C_ACCENT` | `#1B4F72` | Section divider bars |
| `C_GREEN` | `#1E8449` | NOI/CFADS text, instruction notes |
| `C_RED` | `#C00000` | Variance/warning text |
| `C_GOLD` | `#D4AC0D` | Special accents (DSCR flags) |
| `C_SUBTOTAL` | `#E8EAED` | Subtotal row fill |
| `C_ALT` | `#F7F9FC` | Alternating row fill |
| `C_INPUT_BG` | `#FFF9C4` | Input cell background |
| `C_NOTE_BG` | `#E8F5E9` | NOI/CFADS/Free Cash row fill |
| `C_WARN_BG` | `#FDEDEC` | Variance section fill |
| `C_BODY` | `#000000` | Body text |
| `C_LABEL` | `#2C3E50` | Row labels |
| `C_MUTED` | `#7F8C8D` | GL codes, annotations |
| `C_BLUE` | `#0000FF` | Input cell font |
| `C_CROSS` | `#548235` | Cross-sheet reference font |

## Fonts (max 10 per sheet)

| Name | Size | Bold | Color | Use |
|------|------|------|-------|-----|
| `F_TITLE` | 14pt | Yes | White | Row 1 title only |
| `F_SUB` | 9pt | No | `#AEB6BF` | Row 2 subtitle only |
| `F_HDR` | 10pt | Yes | White | Column headers |
| `F_SECTION` | 10pt | Yes | White | Section bars |
| `F_LABEL` | 10pt | Yes | `#2C3E50` | Row labels |
| `F_BODY` | 10pt | No | Black | Data cells |
| `F_BOLD` | 10pt | Yes | Black | Subtotals |
| `F_INPUT` | 10pt | Yes | `#0000FF` | Editable input cells |
| `F_MUTED` | 9pt | No | `#7F8C8D` | GL codes, annotations |
| `F_GREEN` | 10pt | Yes | `#1E8449` | NOI/CFADS highlights |
| `F_RED` | 10pt | Yes | `#C00000` | Variance/warnings |
| `F_CROSS` | 10pt | No | `#548235` | Cross-sheet references |
| `F_NOTE` | 9pt | Italic | `#1E8449` | Row 2 instructions |

## Number Formats

| Format | Code | Use |
|--------|------|-----|
| Dollars | `$#,##0;($#,##0);"-"` | All currency values |
| Counts | `#,##0;(#,##0);"-"` | Units, counts |
| Percentage | `0.0%` | Rates, ratios |
| Precise % | `0.00%` | Ownership percentages |
| Date | `MMM-YY` | Month headers |
| Decimal | `#,##0.00` | Per-unit calculations |

## Row Heights

| Element | Height |
|---------|--------|
| Title (row 1) | 28px |
| Subtitle (row 2) | 18px |
| Headers | 20px |
| Section bars | 20px |
| Data rows | Default (15px) |

## Column Widths

| Type | Width |
|------|-------|
| Spacer/margin (col A) | 3–5 |
| Label column | 30–40 |
| Data columns | 11–12 |
| Summary columns | 12–14 |
| Notes/description | 50–75 |

## Borders

| Element | Style |
|---------|-------|
| Subtotal rows | Thin top + bottom `#D9D9D9` |
| Section dividers | Medium bottom `#0D1B2A` |
| All other cells | None |

## Sheet Structure

Every visible tab follows this pattern:
1. **Row 1** — Title bar: `#0D1B2A` fill, 14pt Bold White, full width
2. **Row 2** — Subtitle: `#1A2332` fill, 9pt `#AEB6BF`, includes `▶` instruction
3. **Row 3** — Column headers: `#0D1B2A` fill, 10pt Bold White, centered
4. **Row 4+** — Data: alternating `#F7F9FC` / white
5. **Beyond data** — All rows and columns hidden

## Rules

1. Every visible tab uses the same title/subtitle/header treatment
2. Maximum 10 unique font styles per sheet (except Distribution_Model ≤ 15)
3. Input cells always use yellow background + blue bold font
4. Formula cells are never highlighted — black text on white/alt fill
5. Section bars span full data width
6. Numbers right-aligned, text left-aligned, headers center-aligned
7. Hidden rows/cols beyond data boundary on every tab
8. All fonts are Calibri — no exceptions
