"""
Halo CME Detection Dashboard — Aditya-L1 / SWIS-ASPEX
=====================================================
Mission-control style Streamlit dashboard for visualising halo CME
detections derived from Aditya-L1 SWIS-ASPEX solar-wind data.

Run with:
    streamlit run cme_dashboard.py

Expects:
    data/detected_halo_cmes.csv   -> one row per detected CME event
    data/final_dataset.csv        -> full solar-wind time series

Both files are auto-inspected: column roles (time, start, end, duration,
strength, score) are detected from column names, so the dashboard adapts
to whatever your pipeline exports.
"""

import os
import re
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Page config — must be the first Streamlit call
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Halo CME Detection | Aditya-L1",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
DATA_DIR = "data"
DET_PATH = os.path.join(DATA_DIR, "detected_halo_cmes.csv")
FULL_PATH = os.path.join(DATA_DIR, "final_dataset.csv")

# -----------------------------------------------------------------------------
# Theme tokens — dark mission-control
# -----------------------------------------------------------------------------
C = {
    "bg": "#0b0f19",
    "panel": "#121826",
    "border": "#1f2a3d",
    "text": "#e5e7eb",
    "muted": "#8b98ad",
    "cyan": "#22d3ee",
    "amber": "#fbbf24",
    "blue": "#60a5fa",
    "red": "#f87171",
    "green": "#34d399",
    "grid": "#1c2536",
}

STRENGTH_COLORS = {"weak": C["amber"], "moderate": C["blue"], "strong": C["red"]}

CUSTOM_CSS = """
<style>
  .stApp {
    background: radial-gradient(1100px 500px at 15% -5%, #101a2e 0%, #0b0f19 60%) fixed;
    color: #e5e7eb;
  }
  [data-testid="stSidebar"] {
    background-color: #0e1422;
    border-right: 1px solid #1f2a3d;
  }
  h1, h2, h3, h4 { color: #e5e7eb !important; }
  hr { border-color: #1f2a3d; }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: #121826;
    border: 1px solid #1f2a3d;
    border-radius: 10px;
    padding: 14px 16px;
  }
  [data-testid="stMetricLabel"] {
    color: #8b98ad;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.72rem;
  }
  [data-testid="stMetricValue"] {
    color: #22d3ee;
    font-family: 'Consolas', 'SF Mono', 'Roboto Mono', monospace;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #1f2a3d; }
  .stTabs [data-baseweb="tab"] {
    background: #0e1422;
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    color: #8b98ad;
  }
  .stTabs [aria-selected="true"] {
    background: #121826;
    color: #22d3ee !important;
    border-bottom: 2px solid #22d3ee;
  }

  /* Expanders */
  [data-testid="stExpander"] {
    background: #121826;
    border: 1px solid #1f2a3d;
    border-radius: 10px;
  }

  /* Mission-control header */
  .mc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    background: #121826;
    border: 1px solid #1f2a3d;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 8px;
  }
  .mc-title {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: #e5e7eb;
  }
  .mc-sub {
    color: #8b98ad;
    font-size: 0.85rem;
    letter-spacing: 1px;
    margin-top: 2px;
  }
  .pill {
    display: inline-block;
    padding: 3px 12px;
    margin-left: 6px;
    border-radius: 999px;
    font-size: 0.72rem;
    letter-spacing: 1.5px;
    font-family: 'Consolas', 'SF Mono', 'Roboto Mono', monospace;
    border: 1px solid #1f2a3d;
    background: #0e1422;
  }
  .pill-green { color: #34d399; border-color: #14532d; }
  .pill-cyan  { color: #22d3ee; border-color: #164e63; }
  .pill-amber { color: #fbbf24; border-color: #713f12; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _has_word(col_lower: str, words) -> bool:
    """Whole-token match so 'to' doesn't fire inside 'proton' or 'total'."""
    tokens = re.split(r"[^a-z0-9]+", col_lower)
    return any(w in tokens for w in words) or any(
        w in col_lower for w in words if len(w) >= 4
    )


def detect_columns(df: pd.DataFrame) -> dict:
    """Detect column roles from names. start/end take priority over generic time."""
    roles = {k: [] for k in ["time", "start", "end", "duration", "strength", "score", "numeric"]}
    for col in df.columns:
        cl = col.lower()
        if _has_word(cl, ["start", "begin", "onset"]):
            roles["start"].append(col)
        elif _has_word(cl, ["end", "stop", "finish"]):
            roles["end"].append(col)
        elif _has_word(cl, ["time", "date", "datetime", "timestamp", "epoch"]):
            roles["time"].append(col)
        if _has_word(cl, ["duration", "length", "hours", "span"]):
            roles["duration"].append(col)
        if _has_word(cl, ["strength", "class", "type", "category", "level"]):
            roles["strength"].append(col)
        if _has_word(cl, ["score", "composite", "anomaly", "metric"]):
            roles["score"].append(col)
        if pd.api.types.is_numeric_dtype(df[col]):
            roles["numeric"].append(col)
    return roles


def strength_color(value, alpha=None) -> str:
    """Map a strength label to its theme colour (hex, or rgba if alpha given)."""
    v = str(value).lower()
    hex_c = next((c for k, c in STRENGTH_COLORS.items() if k in v), C["muted"])
    if alpha is None:
        return hex_c
    r, g, b = (int(hex_c[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def style_fig(fig: go.Figure, height=450) -> go.Figure:
    """Apply the mission-control plot theme."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=C["panel"],
        font=dict(color=C["text"]),
        hovermode="x unified",
        margin=dict(l=45, r=20, t=45, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08),
    )
    fig.update_xaxes(gridcolor=C["grid"], zeroline=False, linecolor=C["border"])
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False, linecolor=C["border"])
    return fig


def downsample(df: pd.DataFrame, max_points=20000) -> pd.DataFrame:
    """Thin very long series so Plotly stays responsive in the browser."""
    if len(df) <= max_points:
        return df
    step = int(np.ceil(len(df) / max_points))
    return df.iloc[::step]


def fmt_dt(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.strftime("%Y-%m-%d %H:%M")
    return series


# -----------------------------------------------------------------------------
# Data loading — file checks OUTSIDE the cache, parsing INSIDE it (done once)
# -----------------------------------------------------------------------------
missing = [p for p in (DET_PATH, FULL_PATH) if not os.path.exists(p)]
if missing:
    st.error(
        "Missing data file(s): " + ", ".join(f"`{p}`" for p in missing)
        + " — place the pipeline CSVs in the `data/` folder and reload."
    )
    st.stop()


@st.cache_data(show_spinner="Loading SWIS-ASPEX data…")
def load_data(det_path: str, full_path: str):
    detections = pd.read_csv(det_path)
    full_data = pd.read_csv(full_path)

    det_cols = detect_columns(detections)
    data_cols = detect_columns(full_data)

    # Parse datetimes once, inside the cache
    if data_cols["time"]:
        tc = data_cols["time"][0]
        full_data[tc] = pd.to_datetime(full_data[tc], errors="coerce")
        full_data = full_data.dropna(subset=[tc]).sort_values(tc).reset_index(drop=True)

    for key in ("start", "end"):
        if det_cols[key]:
            c = det_cols[key][0]
            detections[c] = pd.to_datetime(detections[c], errors="coerce")

    return full_data, detections, det_cols, data_cols


full_data, detections, det_cols, data_cols = load_data(DET_PATH, FULL_PATH)

time_col = data_cols["time"][0] if data_cols["time"] else None
start_col = det_cols["start"][0] if det_cols["start"] else None
end_col = det_cols["end"][0] if det_cols["end"] else None
duration_col = det_cols["duration"][0] if det_cols["duration"] else None
strength_col = det_cols["strength"][0] if det_cols["strength"] else None
score_col = det_cols["score"][0] if det_cols["score"] else None

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="mc-header">
      <div>
        <div class="mc-title">☀️ HALO CME DETECTION</div>
        <div class="mc-sub">ADITYA-L1 · SWIS-ASPEX · SOLAR WIND ION SPECTROMETER</div>
      </div>
      <div>
        <span class="pill pill-green">● DATA LOADED</span>
        <span class="pill pill-cyan">L1 HALO ORBIT</span>
        <span class="pill pill-amber">{len(detections)} EVENTS</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Sidebar — filters (these now actually filter the data)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Mission Filters")

    # Date range
    date_range = None
    if time_col is not None:
        min_d = full_data[time_col].min().date()
        max_d = full_data[time_col].max().date()
        date_range = st.date_input(
            "Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
        )
    else:
        st.warning("No time column detected — time filtering disabled.")

    # Strength multiselect
    selected_strengths = None
    if strength_col is not None:
        options = sorted(detections[strength_col].astype(str).unique())
        selected_strengths = st.multiselect("CME strength", options, default=options)

    # Parameter to plot
    param_options = data_cols["numeric"]
    if not param_options:
        st.error("No numeric columns found in the main dataset.")
        st.stop()
    default_param = next(
        (c for c in data_cols["score"] if c in param_options), param_options[0]
    )
    selected_param = st.selectbox(
        "Primary parameter", param_options, index=param_options.index(default_param)
    )

    st.markdown("---")
    st.subheader("📈 Plot options")
    show_shading = st.checkbox("Shade CME intervals", value=True)
    show_rolling = st.checkbox("Rolling-mean overlay", value=True)
    roll_window = st.slider("Rolling window (samples)", 5, 500, 60, step=5,
                            disabled=not show_rolling)
    log_scale = st.checkbox("Log-scale y-axis", value=False)

    st.markdown("---")
    with st.expander("🔧 Detected columns (debug)"):
        st.write("**Detection file**")
        for k, v in det_cols.items():
            if v:
                st.write(f"- {k}: `{v[:4]}`")
        st.write("**Main dataset**")
        for k, v in data_cols.items():
            if v:
                st.write(f"- {k}: `{v[:6]}`")

# -----------------------------------------------------------------------------
# Apply filters
# -----------------------------------------------------------------------------
fdata = full_data
fdet = detections

t0 = t1 = None
if time_col is not None and date_range is not None and len(date_range) == 2:
    t0 = pd.Timestamp(date_range[0])
    t1 = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
    fdata = full_data[(full_data[time_col] >= t0) & (full_data[time_col] < t1)]
    if start_col is not None:
        fdet = fdet[(fdet[start_col] >= t0) & (fdet[start_col] < t1)]

if strength_col is not None and selected_strengths is not None:
    fdet = fdet[fdet[strength_col].astype(str).isin(selected_strengths)]

fdet = fdet.reset_index(drop=True)

if fdata.empty:
    st.warning("No time-series data in the selected date range.")
    st.stop()

# -----------------------------------------------------------------------------
# Metric readouts
# -----------------------------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("CME Events", len(fdet),
          delta=None if len(fdet) == len(detections)
          else f"{len(fdet) - len(detections)} filtered")

if strength_col is not None and len(fdet):
    n_strong = fdet[strength_col].astype(str).str.lower().str.contains("strong").sum()
    m2.metric("Strong Events", int(n_strong))
else:
    m2.metric("Strong Events", "—")

if duration_col is not None and len(fdet):
    m3.metric("Avg Duration", f"{fdet[duration_col].mean():.1f} h")
else:
    m3.metric("Avg Duration", "—")

if score_col is not None and score_col in fdet.columns and len(fdet):
    m4.metric("Peak Score", f"{fdet[score_col].max():.2f}")
else:
    m4.metric(f"Max {selected_param[:14]}", f"{fdata[selected_param].max():.2f}")

if time_col is not None:
    span_days = (fdata[time_col].max() - fdata[time_col].min()).days + 1
    m5.metric("Coverage", f"{span_days} d / {len(fdata):,} pts")
else:
    m5.metric("Data Points", f"{len(fdata):,}")

st.markdown("")

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
tab_overview, tab_events, tab_params, tab_data = st.tabs(
    ["📡 Overview", "🎯 Event Analysis", "📊 Parameters", "📋 Data"]
)

# ================================ OVERVIEW ===================================
with tab_overview:
    st.subheader(f"Solar-wind time series — {selected_param}")

    if time_col is None:
        st.info("Time-series view requires a detectable time column.")
    else:
        plot_df = downsample(fdata[[time_col, selected_param]].dropna())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_df[time_col], y=plot_df[selected_param],
            mode="lines", name=selected_param,
            line=dict(color=C["cyan"], width=1.6),
        ))

        if show_rolling and len(plot_df) > roll_window:
            rolled = plot_df[selected_param].rolling(roll_window, center=True).mean()
            fig.add_trace(go.Scatter(
                x=plot_df[time_col], y=rolled,
                mode="lines", name=f"rolling mean ({roll_window})",
                line=dict(color=C["amber"], width=2.2),
            ))

        # CME interval shading, colour-coded by strength
        if show_shading and start_col is not None and end_col is not None:
            for idx, ev in fdet.iterrows():
                if pd.isna(ev[start_col]) or pd.isna(ev[end_col]):
                    continue
                fig.add_vrect(
                    x0=ev[start_col], x1=ev[end_col],
                    fillcolor=strength_color(
                        ev[strength_col] if strength_col else "", alpha=0.18),
                    line_width=0,
                    annotation_text=f"CME {idx + 1}" if idx < 12 else "",
                    annotation_position="top left",
                    annotation_font=dict(size=10, color=C["muted"]),
                )

        fig.update_xaxes(
            rangeslider=dict(visible=True, thickness=0.06,
                             bgcolor=C["panel"], bordercolor=C["border"]),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All"),
                ],
                bgcolor=C["panel"], activecolor=C["border"],
                font=dict(color=C["text"]),
            ),
        )
        if log_scale:
            fig.update_yaxes(type="log")
        st.plotly_chart(style_fig(fig, height=520), use_container_width=True)

    col_l, col_r = st.columns(2)

    # ---- Event timeline (Gantt-style) ----
    with col_l:
        st.subheader("Event timeline")
        if start_col is not None and end_col is not None and len(fdet):
            fig_t = go.Figure()
            for idx, ev in fdet.iterrows():
                if pd.isna(ev[start_col]) or pd.isna(ev[end_col]):
                    continue
                col = strength_color(ev[strength_col] if strength_col else "")
                hover = f"<b>CME {idx + 1}</b>"
                if strength_col is not None:
                    hover += f"<br>Strength: {ev[strength_col]}"
                if duration_col is not None:
                    hover += f"<br>Duration: {ev[duration_col]:.1f} h"
                hover += (f"<br>Start: {ev[start_col]:%Y-%m-%d %H:%M}"
                          f"<br>End: {ev[end_col]:%Y-%m-%d %H:%M}")
                fig_t.add_trace(go.Scatter(
                    x=[ev[start_col], ev[end_col]], y=[idx + 1, idx + 1],
                    mode="lines+markers",
                    line=dict(color=col, width=7),
                    marker=dict(size=9, color=col),
                    hovertext=hover, hoverinfo="text", showlegend=False,
                ))
            fig_t.update_layout(xaxis_title="Time", yaxis_title="Event #")
            fig_t.update_layout(hovermode="closest")
            st.plotly_chart(style_fig(fig_t, height=400), use_container_width=True)
        else:
            st.info("Timeline requires start and end time columns.")

    # ---- Distributions ----
    with col_r:
        st.subheader("Distribution")
        if strength_col is not None and len(fdet):
            counts = fdet[strength_col].astype(str).value_counts()
            fig_d = go.Figure(go.Bar(
                x=counts.index, y=counts.values,
                marker_color=[strength_color(s) for s in counts.index],
                text=counts.values, textposition="auto",
            ))
            fig_d.update_layout(xaxis_title="Strength", yaxis_title="Count")
            st.plotly_chart(style_fig(fig_d, height=400), use_container_width=True)
        elif duration_col is not None and len(fdet):
            fig_d = go.Figure(go.Histogram(
                x=fdet[duration_col], nbinsx=20, marker_color=C["blue"]))
            fig_d.update_layout(xaxis_title=duration_col, yaxis_title="Count")
            st.plotly_chart(style_fig(fig_d, height=400), use_container_width=True)
        else:
            st.info("No strength or duration data available for a distribution.")

        if duration_col is not None and strength_col is not None and len(fdet):
            with st.expander("Duration histogram"):
                fig_h = go.Figure(go.Histogram(
                    x=fdet[duration_col], nbinsx=20, marker_color=C["cyan"]))
                fig_h.update_layout(xaxis_title=f"{duration_col} (h)",
                                    yaxis_title="Count")
                st.plotly_chart(style_fig(fig_h, height=320),
                                use_container_width=True)

# ============================== EVENT ANALYSIS ===============================
with tab_events:
    st.subheader("Single-event drill-down")

    if start_col is None or time_col is None or not len(fdet):
        st.info("Event analysis needs a time column, event start times, and at "
                "least one event in the current filter.")
    else:
        labels = []
        for idx, ev in fdet.iterrows():
            lab = f"CME {idx + 1}"
            if pd.notna(ev[start_col]):
                lab += f" — {ev[start_col]:%Y-%m-%d %H:%M}"
            if strength_col is not None:
                lab += f" ({ev[strength_col]})"
            labels.append(lab)

        c_sel, c_pad = st.columns([3, 1])
        pick = c_sel.selectbox("Event", labels)
        pad_h = c_pad.slider("Context (± hours)", 6, 96, 24, step=6)
        ev = fdet.iloc[labels.index(pick)]

        w0 = ev[start_col] - pd.Timedelta(hours=pad_h)
        w1 = (ev[end_col] if end_col is not None and pd.notna(ev[end_col])
              else ev[start_col]) + pd.Timedelta(hours=pad_h)
        window = full_data[(full_data[time_col] >= w0) & (full_data[time_col] <= w1)]

        if window.empty:
            st.warning("No time-series samples inside this event window.")
        else:
            fig_e = go.Figure(go.Scatter(
                x=window[time_col], y=window[selected_param],
                mode="lines", name=selected_param,
                line=dict(color=C["cyan"], width=1.8),
            ))
            if end_col is not None and pd.notna(ev[end_col]):
                fig_e.add_vrect(
                    x0=ev[start_col], x1=ev[end_col],
                    fillcolor=strength_color(
                        ev[strength_col] if strength_col else "", alpha=0.22),
                    line_width=0,
                )
            else:
                fig_e.add_vline(x=ev[start_col], line_color=C["red"],
                                line_dash="dash")
            st.plotly_chart(style_fig(fig_e, height=460), use_container_width=True)

            valid = window[[time_col, selected_param]].dropna()
            e1, e2, e3, e4 = st.columns(4)
            if strength_col is not None:
                e1.metric("Strength", str(ev[strength_col]))
            else:
                e1.metric("Strength", "—")
            if duration_col is not None:
                e2.metric("Duration", f"{ev[duration_col]:.1f} h")
            else:
                e2.metric("Duration", "—")
            if len(valid):
                peak_i = valid[selected_param].idxmax()
                e3.metric(f"Peak {selected_param[:12]}",
                          f"{valid.loc[peak_i, selected_param]:.2f}")
                e4.metric("Peak time",
                          f"{valid.loc[peak_i, time_col]:%m-%d %H:%M}")

# ================================ PARAMETERS =================================
with tab_params:
    st.subheader("Multi-parameter comparison (z-score normalised)")

    if time_col is None:
        st.info("Parameter comparison requires a time column.")
    else:
        compare = st.multiselect(
            "Parameters", param_options,
            default=[selected_param],
            max_selections=5,
        )
        if compare:
            plot_df = downsample(fdata[[time_col] + compare].dropna())
            palette = [C["cyan"], C["amber"], C["blue"], C["red"], C["green"]]
            fig_c = go.Figure()
            for i, p in enumerate(compare):
                s = plot_df[p]
                std = s.std()
                z = (s - s.mean()) / std if std and not np.isclose(std, 0) else s * 0
                fig_c.add_trace(go.Scatter(
                    x=plot_df[time_col], y=z, mode="lines", name=p,
                    line=dict(color=palette[i % len(palette)], width=1.5),
                ))
            fig_c.update_layout(yaxis_title="z-score")
            st.plotly_chart(style_fig(fig_c, height=460), use_container_width=True)

    st.subheader("Parameter correlations")
    corr_cols = st.multiselect(
        "Columns for correlation matrix", param_options,
        default=param_options[: min(8, len(param_options))],
    )
    if len(corr_cols) >= 2:
        corr = fdata[corr_cols].corr()
        fig_h = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.columns,
            colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
            text=np.round(corr.values, 2), texttemplate="%{text}",
            colorbar=dict(outlinewidth=0),
        ))
        fig_h.update_layout(hovermode="closest")
        st.plotly_chart(style_fig(fig_h, height=max(420, 55 * len(corr_cols))),
                        use_container_width=True)
    else:
        st.info("Pick at least two columns to build the correlation matrix.")

    st.subheader(f"Summary statistics — {selected_param}")
    st.dataframe(
        fdata[selected_param].describe().to_frame().T.round(3),
        use_container_width=True,
    )

# =================================== DATA ====================================
with tab_data:
    st.subheader("Detected CME events")

    if len(fdet):
        table = fdet.copy()
        table.insert(0, "CME #", range(1, len(table) + 1))
        for col in table.columns:
            table[col] = fmt_dt(table[col])
            if pd.api.types.is_float_dtype(table[col]):
                table[col] = table[col].round(3)
        st.dataframe(table, use_container_width=True, height=420)

        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇ Download filtered events (CSV)",
            fdet.to_csv(index=False).encode(),
            file_name="halo_cme_events_filtered.csv",
            mime="text/csv",
        )
        d2.download_button(
            "⬇ Download filtered time series (CSV)",
            fdata.to_csv(index=False).encode(),
            file_name="swis_timeseries_filtered.csv",
            mime="text/csv",
        )
    else:
        st.info("No CME events match the current filters.")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
f1, f2, f3 = st.columns(3)
f1.caption(f"Generated {datetime.now():%Y-%m-%d %H:%M:%S}")
f2.caption(f"{len(fdet)} events shown · {len(fdata):,} samples in range")
f3.caption("Data: Aditya-L1 · SWIS-ASPEX (ISRO)")
