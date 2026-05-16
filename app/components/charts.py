"""Reusable Plotly chart builders."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def bar_senator_activity(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Bar chart: top N senators by trade count."""
    counts = (
        df.groupby("member_name")
        .size()
        .reset_index(name="trades")
        .sort_values("trades", ascending=False)
        .head(top_n)
    )
    fig = px.bar(
        counts,
        x="trades",
        y="member_name",
        orientation="h",
        title=f"Top {top_n} Most Active Congress Traders",
        labels={"member_name": "", "trades": "# Trades"},
        color="trades",
        color_continuous_scale="Blues",
    )
    fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
    return fig


def treemap_portfolio(df: pd.DataFrame, fund_name: str) -> go.Figure:
    """Treemap of fund holdings by USD value."""
    plot_df = df[df["value_usd"].notna() & (df["value_usd"] > 0)].copy()
    plot_df["value_usd"] = plot_df["value_usd"] * 1000  # stored in thousands

    fig = px.treemap(
        plot_df,
        path=["asset_name"],
        values="value_usd",
        title=f"{fund_name} — Portfolio Composition",
        color="value_usd",
        color_continuous_scale="Greens",
    )
    fig.update_traces(textinfo="label+percent root")
    return fig


def line_position_history(df: pd.DataFrame, ticker: str, fund_name: str) -> go.Figure:
    """Line chart: fund's share count for a ticker over quarters."""
    t = df[df["ticker"].str.upper() == ticker.upper()].sort_values("period_of_report")
    fig = px.line(
        t,
        x="period_of_report",
        y="shares",
        title=f"{fund_name} — {ticker} position history",
        markers=True,
        labels={"period_of_report": "Quarter", "shares": "Shares"},
    )
    return fig


def heatmap_sector_signals(df: pd.DataFrame) -> go.Figure:
    """Bar chart of conviction scores grouped by ticker (top 20)."""
    top = df.nlargest(20, "conviction_score")
    fig = px.bar(
        top,
        x="ticker",
        y="conviction_score",
        color="conviction_score",
        color_continuous_scale="RdYlGn",
        title="Top Tickers by Conviction Score",
        labels={"ticker": "Ticker", "conviction_score": "Score"},
    )
    return fig
