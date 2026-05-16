"""Helpers for styled dataframe presentation."""
import pandas as pd


def style_congress_trades(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Colour-code transaction type and flag late disclosures."""
    def _row_style(row):
        styles = [""] * len(row)
        idx_map = {col: i for i, col in enumerate(df.columns)}

        tx_col = idx_map.get("transaction_type")
        if tx_col is not None:
            tx = str(row.get("transaction_type", "")).lower()
            if "purchase" in tx or "buy" in tx:
                styles[tx_col] = "color: #1a7a1a; font-weight: bold"
            elif "sale" in tx or "sell" in tx:
                styles[tx_col] = "color: #c0392b; font-weight: bold"

        days_col = idx_map.get("days_to_disclose")
        if days_col is not None:
            days = row.get("days_to_disclose")
            try:
                if int(days) > 45:
                    styles[days_col] = "background-color: #ffd6d6; color: #c0392b"
            except (TypeError, ValueError):
                pass

        return styles

    display_cols = [
        "member_name", "party", "state", "ticker", "asset_name",
        "transaction_type", "amount_range", "transaction_date",
        "disclosure_date", "days_to_disclose",
    ]
    cols = [c for c in display_cols if c in df.columns]
    styled = df[cols].style.apply(_row_style, axis=1)
    return styled


def format_value(v: float | None) -> str:
    if v is None:
        return "—"
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.0f}"
