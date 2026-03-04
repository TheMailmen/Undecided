"""Lakeshore Management — Reusable Streamlit UI components.

Provides institutional-quality primitives that every page can import.

Usage:
    from ui.components import page_header, kpi_row, section_header, badge, styled_table
"""

import streamlit as st
from ui.theme import COLORS, fmt_currency, fmt_pct, fmt_multiple


# ── Page Header ───────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", right_text: str = ""):
    """Render a premium page header with optional subtitle and right-aligned context."""
    right_html = ""
    if right_text:
        right_html = (
            f'<div style="text-align:right;color:{COLORS["muted"]};'
            f'font-size:0.82rem;font-weight:500;padding-top:8px;">'
            f'{right_text}</div>'
        )

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:flex-start;
                margin-bottom:8px;padding-bottom:16px;
                border-bottom:2px solid {COLORS['border']};">
        <div>
            <h1 style="margin:0;padding:0;font-size:1.75rem;font-weight:700;
                        color:{COLORS['primary']};letter-spacing:-0.02em;
                        font-family:'Inter',system-ui,sans-serif;">
                {title}
            </h1>
            {"<p style='margin:4px 0 0 0;color:" + COLORS['muted'] + ";font-size:0.9rem;font-weight:400;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        {right_html}
    </div>
    """, unsafe_allow_html=True)


# ── KPI Row ───────────────────────────────────────────────────────

def kpi_row(kpis: list[dict]):
    """Render a row of styled KPI cards.

    Each dict: {label, value, delta (optional), delta_inverse (optional)}
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        delta = kpi.get("delta")
        delta_color = "inverse" if kpi.get("delta_inverse") else "normal"
        with col:
            st.metric(
                label=kpi["label"],
                value=kpi["value"],
                delta=delta,
                delta_color=delta_color,
            )


# ── Section Header ────────────────────────────────────────────────

def section_header(title: str, help_text: str = ""):
    """Render a clean section divider with optional help text."""
    st.markdown(f"""
    <div style="margin:28px 0 12px 0;">
        <h3 style="margin:0;font-size:1.05rem;font-weight:600;
                    color:{COLORS['primary']};letter-spacing:-0.01em;
                    font-family:'Inter',system-ui,sans-serif;">
            {title}
        </h3>
        {"<p style='margin:2px 0 0 0;font-size:0.8rem;color:" + COLORS['muted'] + ";'>" + help_text + "</p>" if help_text else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Badge ─────────────────────────────────────────────────────────

_BADGE_STYLES = {
    "neutral": (COLORS["border"], COLORS["text"]),
    "success": ("#DCFCE7", COLORS["success"]),
    "warn":    ("#FEF3C7", "#92400E"),
    "error":   ("#FEE2E2", COLORS["error"]),
    "accent":  ("#E0F2FE", COLORS["accent"]),
}


def badge(text: str, kind: str = "neutral"):
    """Render a small pill badge. kind: neutral|success|warn|error|accent"""
    bg, fg = _BADGE_STYLES.get(kind, _BADGE_STYLES["neutral"])
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
        f'font-size:0.72rem;font-weight:600;background:{bg};color:{fg};'
        f'letter-spacing:0.02em;">{text}</span>'
    )


# ── Styled HTML Table ─────────────────────────────────────────────

def styled_table(
    headers: list[str],
    rows: list[list[str]],
    col_align: list[str] | None = None,
    highlight_rows: set[int] | None = None,
    caption: str = "",
    compact: bool = False,
):
    """Render a professionally styled HTML table.

    Args:
        headers: Column header strings.
        rows: List of rows, each a list of cell HTML strings.
        col_align: Per-column alignment ('left', 'center', 'right').
        highlight_rows: Row indices (0-based) to highlight with accent background.
        caption: Optional table caption above the table.
        compact: If True, uses tighter padding.
    """
    if col_align is None:
        col_align = ["left"] + ["right"] * (len(headers) - 1)

    pad = "5px 10px" if compact else "8px 14px"
    hdr_pad = "8px 14px" if compact else "10px 14px"

    html = []
    if caption:
        html.append(
            f'<p style="font-size:0.78rem;color:{COLORS["muted"]};'
            f'margin:0 0 6px 2px;font-weight:500;">{caption}</p>'
        )

    html.append(
        f'<div style="overflow-x:auto;border:1px solid {COLORS["border"]};'
        f'border-radius:12px;margin-bottom:16px;">'
    )
    html.append(
        '<table style="border-collapse:collapse;width:100%;'
        "font-family:'Inter',system-ui,sans-serif;font-size:0.82rem;\">"
    )

    # Header
    html.append("<thead>")
    html.append(
        f'<tr style="background:{COLORS["primary"]};color:white;">'
    )
    for i, h in enumerate(headers):
        align = col_align[i] if i < len(col_align) else "left"
        html.append(
            f'<th style="padding:{hdr_pad};text-align:{align};font-weight:600;'
            f'font-size:0.75rem;text-transform:uppercase;letter-spacing:0.04em;'
            f'white-space:nowrap;">{h}</th>'
        )
    html.append("</tr></thead>")

    # Body
    html.append("<tbody>")
    highlight = highlight_rows or set()
    for ri, row in enumerate(rows):
        if ri in highlight:
            bg = f"background:{COLORS['kpi_bg']};"
            weight = "font-weight:600;"
        elif ri % 2 == 1:
            bg = f"background:{COLORS['row_alt']};"
            weight = ""
        else:
            bg = ""
            weight = ""

        html.append(f'<tr style="{bg}{weight}">')
        for ci, cell in enumerate(row):
            align = col_align[ci] if ci < len(col_align) else "left"
            html.append(
                f'<td style="padding:{pad};text-align:{align};'
                f'border-top:1px solid {COLORS["border"]};white-space:nowrap;">'
                f'{cell}</td>'
            )
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("\n".join(html), unsafe_allow_html=True)


# ── Sensitivity Matrix ────────────────────────────────────────────

def sensitivity_matrix(
    title: str,
    row_label: str,
    col_label: str,
    row_keys: list[str],
    col_keys: list[str],
    values: list[list[str]],
    color_fn=None,
):
    """Render a sensitivity/heat table with conditional coloring.

    Args:
        title: Table title (rendered as section_header).
        row_label / col_label: Axis labels for the corner cell.
        row_keys: Labels for each row.
        col_keys: Labels for each column.
        values: 2D list of pre-formatted cell strings.
        color_fn: Optional fn(row_idx, col_idx, raw_str) → CSS color string.
    """
    html = []
    html.append(
        f'<div style="overflow-x:auto;border:1px solid {COLORS["border"]};'
        f'border-radius:12px;margin-bottom:20px;">'
    )
    html.append(
        '<table style="border-collapse:collapse;width:100%;'
        "font-family:'Inter',system-ui,sans-serif;font-size:0.82rem;text-align:center;\">"
    )

    # Header row
    html.append(
        f'<thead><tr style="background:{COLORS["primary"]};color:white;">'
    )
    html.append(
        f'<th style="padding:10px 14px;text-align:left;font-weight:600;'
        f'font-size:0.75rem;text-transform:uppercase;letter-spacing:0.04em;">'
        f'{row_label} \u2193 / {col_label} \u2192</th>'
    )
    for ck in col_keys:
        html.append(
            f'<th style="padding:10px 14px;font-weight:600;font-size:0.75rem;'
            f'letter-spacing:0.04em;">{ck}</th>'
        )
    html.append("</tr></thead><tbody>")

    for ri, (rk, row) in enumerate(zip(row_keys, values)):
        bg = f"background:{COLORS['row_alt']};" if ri % 2 == 1 else ""
        html.append(f'<tr style="{bg}">')
        html.append(
            f'<td style="padding:8px 14px;font-weight:600;text-align:left;'
            f'border-top:1px solid {COLORS["border"]};">{rk}</td>'
        )
        for ci, cell in enumerate(row):
            color = ""
            if color_fn:
                c = color_fn(ri, ci, cell)
                if c:
                    color = f"color:{c};font-weight:600;"
            html.append(
                f'<td style="padding:8px 14px;border-top:1px solid {COLORS["border"]};{color}">'
                f'{cell}</td>'
            )
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("\n".join(html), unsafe_allow_html=True)


# ── Card Container ────────────────────────────────────────────────

def card(content_html: str):
    """Wrap arbitrary HTML in a card with border, radius, and shadow."""
    st.markdown(
        f'<div style="background:{COLORS["surface"]};border:1px solid {COLORS["border"]};'
        f'border-radius:12px;padding:20px 24px;margin-bottom:16px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,.04);">{content_html}</div>',
        unsafe_allow_html=True,
    )


# ── Scenario Pill Selector ────────────────────────────────────────

def scenario_pills(options: list[str], active: str, key: str = "scenario_pill"):
    """Render a horizontal pill selector and return the selected option."""
    pills_html = []
    for opt in options:
        if opt == active:
            style = (
                f"background:{COLORS['accent']};color:white;border-color:{COLORS['accent']};"
                "font-weight:600;"
            )
        else:
            style = (
                f"background:white;color:{COLORS['text']};border-color:{COLORS['border']};"
                "font-weight:500;"
            )
        pills_html.append(
            f'<span style="display:inline-block;padding:6px 18px;border-radius:999px;'
            f'font-size:0.82rem;border:1px solid;margin-right:6px;{style}">{opt}</span>'
        )
    st.markdown(
        f'<div style="margin-bottom:12px;">{"".join(pills_html)}</div>',
        unsafe_allow_html=True,
    )
    # Actual selector underneath (pills are visual; selectbox is functional)
    return st.selectbox(
        "Select scenario", options, index=options.index(active) if active in options else 0,
        key=key, label_visibility="collapsed",
    )


# ── Spacer ────────────────────────────────────────────────────────

def spacer(px: int = 24):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)


# ── No-Data Warning Page ─────────────────────────────────────

def no_data_page(csv_name: str = "pl_actuals.csv"):
    """Show a friendly empty state when required CSV data is missing.

    Returns True if data is missing (caller should st.stop()), False if OK.
    """
    import os
    BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
    csv_path = os.path.join(BASE_DIR, 'data', csv_name)
    if os.path.exists(csv_path):
        return False

    st.markdown(f"""
    <div style="text-align:center;padding:60px 24px;margin:40px 0;">
        <div style="font-size:3rem;margin-bottom:16px;">📂</div>
        <h2 style="margin:0 0 8px 0;font-size:1.3rem;font-weight:700;
                    color:{COLORS['primary']};font-family:'Inter',system-ui,sans-serif;">
            Data Not Found
        </h2>
        <p style="margin:0 0 20px 0;color:{COLORS['muted']};font-size:0.9rem;max-width:420px;
                  margin-left:auto;margin-right:auto;">
            <code style="background:{COLORS['border']};padding:2px 8px;border-radius:4px;
                         font-size:0.82rem;">{csv_name}</code>
            is required for this page. Upload it on the
            <b>Upload Data</b> page or place it in the <code>data/</code> directory.
        </p>
    </div>
    """, unsafe_allow_html=True)
    return True


# ── File Status Card ─────────────────────────────────────────

def file_status_card(filename: str, label: str, description: str, exists: bool, size: int = 0):
    """Render a styled card showing file status with badge."""
    if exists:
        status_badge = badge("Available", "success")
        size_text = f'<span style="font-size:0.75rem;color:{COLORS["muted"]};">{size:,} bytes</span>'
    else:
        status_badge = badge("Missing", "warn")
        size_text = ""

    st.markdown(f"""
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:16px 20px;margin-bottom:4px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="margin:0;font-weight:600;font-size:0.92rem;color:{COLORS['text']};
                          font-family:'Inter',system-ui,sans-serif;">{label}</p>
                <p style="margin:2px 0 0 0;font-size:0.78rem;color:{COLORS['muted']};">
                    {description}</p>
            </div>
            <div style="text-align:right;">
                {status_badge}<br>{size_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Page Footer ──────────────────────────────────────────────────

def page_footer():
    """Render a consistent page footer with branding."""
    st.markdown(f"""
    <div style="margin-top:48px;padding-top:16px;border-top:1px solid {COLORS['border']};">
        <p style="font-size:0.7rem;color:{COLORS['muted']};margin:0;text-align:center;
                  font-family:'Inter',system-ui,sans-serif;">
            Groves Investor Model &bull; Lakeshore Management &bull; Confidential
        </p>
    </div>
    """, unsafe_allow_html=True)
