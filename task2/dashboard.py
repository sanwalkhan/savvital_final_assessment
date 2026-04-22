"""
dashboard.py
-------------
Customer Support Operations KPI Dashboard
Savvital Technical Assessment | Task 2

Dataset: Customer Support Ticket Dataset (Kaggle - suraj520)
https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset

Metrics covered:
  1. Volume by pipeline stage (ticket status distribution)
  2. Monthly ticket volume + resolution rate (conversion)
  3. Average resolution time per ticket type (time per stage)
  4. Satisfaction score trend over time (value/quality trend)
  5. Top channels driving new tickets (lead source equivalent)

Run:
    pip install pandas plotly numpy
    python dashboard.py

Output:
    dashboard.html  — open in any browser, fully self-contained
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
# Download from: https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset
# Place customer_support_tickets.csv in the same folder as this script.

try:
    df = pd.read_csv("customer_support_tickets.csv")
    print(f"Loaded dataset: {len(df):,} rows, {df.shape[1]} columns")
except FileNotFoundError:
    print("ERROR: customer_support_tickets.csv not found.")
    print("Download from https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset")
    raise

# ─────────────────────────────────────────────────────────────
# CLEAN & ENGINEER
# ─────────────────────────────────────────────────────────────

# Normalize column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Parse dates
df["date_of_purchase"] = pd.to_datetime(df["date_of_purchase"], errors="coerce")
df["month"]    = df["date_of_purchase"].dt.month
df["month_name"] = df["date_of_purchase"].dt.strftime("%b")
df["year"]     = df["date_of_purchase"].dt.year

# Parse time columns — stored as timedelta strings e.g. "2 days 03:00:00"
# time_to_resolution is only filled for Closed tickets in this dataset
# first_response_time covers more rows so we use it for per-type comparison
time_col = None
for col in df.columns:
    if "resolution" in col and "time" in col:
        time_col = col
        break

resp_col = None
for col in df.columns:
    if "first" in col and "response" in col:
        resp_col = col
        break

for col in [time_col, resp_col]:
    if col and col in df.columns:
        parsed = pd.to_timedelta(df[col], errors="coerce")
        df[col] = parsed.dt.total_seconds() / 3600  # hours

if time_col:
    nn = df[time_col].dropna()
    print(f"  time_to_resolution  : {len(nn):,} non-null rows, sample={nn.head(3).round(1).tolist()}")
if resp_col:
    nn2 = df[resp_col].dropna()
    print(f"  first_response_time : {len(nn2):,} non-null rows, sample={nn2.head(3).round(1).tolist()}")

# Identify key columns (flexible to handle slight naming differences)
def find_col(keywords):
    for col in df.columns:
        if all(k in col for k in keywords):
            return col
    return None

status_col      = find_col(["ticket", "status"])   or "ticket_status"
type_col        = find_col(["ticket", "type"])      or "ticket_type"
channel_col     = find_col(["ticket", "channel"])   or "ticket_channel"
priority_col    = find_col(["priority"])            or "ticket_priority"
satisfaction_col= find_col(["satisfaction", "rating"]) or "customer_satisfaction_rating"

print(f"\nKey columns detected:")
print(f"  Status      : {status_col}")
print(f"  Type        : {type_col}")
print(f"  Channel     : {channel_col}")
print(f"  Priority    : {priority_col}")
print(f"  Satisfaction: {satisfaction_col}")
print(f"  Resolution  : {time_col}")
print(f"\nStatus values : {df[status_col].unique()}")
print(f"Channel values: {df[channel_col].unique()}")

# ─────────────────────────────────────────────────────────────
# AGGREGATIONS
# ─────────────────────────────────────────────────────────────

# 1. Pipeline stage (ticket status counts)
status_order = ["Open", "Pending Customer Response", "Closed"]
status_counts = (
    df[status_col]
    .value_counts()
    .reindex(status_order)
    .fillna(0)
    .astype(int)
)

# 2. Monthly volume + resolution rate
MONTHS_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
monthly = (
    df.groupby("month")
    .agg(
        total    =(status_col, "count"),
        resolved =(status_col, lambda x: (x == "Closed").sum()),
    )
    .reindex(range(1, 13), fill_value=0)
)
monthly["rate"] = (
    monthly["resolved"] / monthly["total"].replace(0, 1) * 100
).round(1)
monthly.index = MONTHS_ORDER

# 3. Avg resolution time per ticket type
# Primary: time_to_resolution (Closed tickets only)
# Fallback: first_response_time (all tickets) when resolution column is mostly empty
active_time_col = None
active_time_label = ""
closed_df = df[df[status_col] == "Closed"]

if time_col and closed_df[time_col].dropna().shape[0] >= 10:
    active_time_col = time_col
    active_time_label = "hrs to resolve"
elif resp_col and df[resp_col].dropna().shape[0] >= 10:
    active_time_col = resp_col
    active_time_label = "hrs to first response"
    closed_df = df  # use all tickets for response time

if active_time_col:
    avg_res_time = (
        closed_df.groupby(type_col)[active_time_col]
        .mean()
        .sort_values(ascending=True)
        .round(1)
        .dropna()
    )
    print(f"\nAvg time per ticket type ({active_time_label}):\n{avg_res_time.to_string()}")
else:
    avg_res_time = pd.Series(dtype=float)
    active_time_label = "hrs"
    print("  WARNING: No usable time column found — resolution time chart will be empty")

# 4. Monthly avg satisfaction
# Use ALL tickets that have a rating — in this dataset rating is not restricted to Closed
df[satisfaction_col] = pd.to_numeric(df[satisfaction_col], errors="coerce")
rated_df = df[df[satisfaction_col].notna()]
print(f"  Satisfaction ratings available: {len(rated_df):,} rows across all statuses")
monthly_sat = (
    rated_df
    .groupby("month")[satisfaction_col]
    .mean()
    .reindex(range(1, 13))
    .round(2)
)
monthly_sat.index = MONTHS_ORDER
print(f"  Monthly satisfaction non-null months: {monthly_sat.notna().sum()}")

# 5. Channel distribution
channel_counts = df[channel_col].value_counts().sort_values(ascending=False)

# 6. Priority breakdown (for KPI / reference)
priority_counts = df[priority_col].value_counts()

# ─────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────
total_tickets    = len(df)
resolution_rate  = round((df[status_col] == "Closed").sum() / total_tickets * 100, 1)
avg_satisfaction = round(df[df[status_col] == "Closed"][satisfaction_col].mean(), 2)
top_channel      = channel_counts.index[0]

# ─────────────────────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────────────────────
STATUS_COLORS  = ["#F59E0B", "#3B82F6", "#10B981"]   # Open, Pending, Closed
CHANNEL_COLORS = ["#3B82F6", "#10B981", "#EC4899", "#F59E0B", "#8B5CF6"]
TYPE_COLORS    = ["#6366F1", "#10B981", "#F59E0B", "#EC4899", "#3B82F6"]

# ─────────────────────────────────────────────────────────────
# BUILD DASHBOARD
# ─────────────────────────────────────────────────────────────
# Layout: 4 rows
#   Row 1: KPI annotation strip        (pure annotations, no subplot needed)
#   Row 2: Status pipeline bar | Channel donut
#   Row 3: Monthly resolution rate line | Monthly satisfaction line
#   Row 4: Avg resolution time per ticket type (horizontal bar, full width)

fig = make_subplots(
    rows=4, cols=2,
    row_heights=[0.08, 0.30, 0.28, 0.34],
    column_widths=[0.54, 0.46],
    specs=[
        [{"type": "scatter", "colspan": 2}, None],   # Row 1: dummy — KPIs via annotations
        [{"type": "bar"},    {"type": "pie"}],        # Row 2
        [{"type": "scatter"},{"type": "scatter"}],   # Row 3
        [{"type": "bar", "colspan": 2}, None],       # Row 4
    ],
    vertical_spacing=0.12,
    horizontal_spacing=0.12,
    subplot_titles=[
        "",                          "",                      # row 1
        "Ticket Status Pipeline",    "Channel Breakdown",     # row 2
        "Monthly Resolution Rate",   "Monthly Avg Satisfaction", # row 3
        "Avg Resolution Time by Ticket Type (hrs)", "",       # row 4
    ],
)

# ── Row 1: Invisible dummy trace so annotation yref="paper" anchors correctly
fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers",
    marker=dict(opacity=0), showlegend=False, hoverinfo="skip"),
    row=1, col=1)

# ── Row 2 left: Pipeline stage volume (bar)
fig.add_trace(go.Bar(
    x=status_counts.index,
    y=status_counts.values,
    marker=dict(color=STATUS_COLORS, line=dict(width=0), cornerradius=6),
    text=status_counts.values,
    textposition="outside",
    textfont=dict(size=13, color="#374151", family="Arial"),
    hovertemplate="<b>%{x}</b><br>%{y:,} tickets<extra></extra>",
    showlegend=False,
), row=2, col=1)

# ── Row 2 right: Channel donut
fig.add_trace(go.Pie(
    labels=channel_counts.index,
    values=channel_counts.values,
    hole=0.58,
    marker=dict(
        colors=CHANNEL_COLORS[:len(channel_counts)],
        line=dict(color="white", width=2)
    ),
    textinfo="percent",
    textfont=dict(size=11, color="white"),
    hovertemplate="<b>%{label}</b><br>%{value:,} tickets · %{percent}<extra></extra>",
    showlegend=True,
), row=2, col=2)

# ── Row 3 left: Monthly resolution rate (line)
sat_median = monthly["rate"].median()
fig.add_trace(go.Scatter(
    x=MONTHS_ORDER,
    y=monthly["rate"].values,
    mode="lines+markers",
    line=dict(color="#10B981", width=2.5, shape="spline"),
    marker=dict(size=6, color="#10B981", line=dict(color="white", width=1.5)),
    fill="tozeroy",
    fillcolor="rgba(16,185,129,0.07)",
    hovertemplate="<b>%{x}</b><br>Resolution rate: %{y:.1f}%<extra></extra>",
    showlegend=False,
), row=3, col=1)

# ── Row 3 right: Monthly avg satisfaction (line)
fig.add_trace(go.Scatter(
    x=MONTHS_ORDER,
    y=monthly_sat.values,
    mode="lines+markers",
    line=dict(color="#F59E0B", width=2.5, shape="spline"),
    marker=dict(size=6, color="#F59E0B", line=dict(color="white", width=1.5)),
    fill="tozeroy",
    fillcolor="rgba(245,158,11,0.07)",
    hovertemplate="<b>%{x}</b><br>Avg satisfaction: %{y:.2f} / 5<extra></extra>",
    showlegend=False,
), row=3, col=2)

# ── Row 4: Avg resolution time per ticket type (horizontal bar)
bar_colors = TYPE_COLORS[:len(avg_res_time)]
fig.add_trace(go.Bar(
    y=avg_res_time.index,
    x=avg_res_time.values,
    orientation="h",
    marker=dict(color=bar_colors, line=dict(width=0), cornerradius=4),
    text=[f"{v:.1f} hrs" for v in avg_res_time.values],
    textposition="outside",
    textfont=dict(size=12, color="#374151", family="Arial"),
    hovertemplate=f"<b>%{{y}}</b><br>%{{x:.1f}} {active_time_label}<extra></extra>",
    showlegend=False,
), row=4, col=1)

# ─────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────
fig.update_layout(
    height=960,
    paper_bgcolor="white",
    plot_bgcolor="#F9FAFB",
    font=dict(family="Arial, sans-serif", color="#111827", size=12),
    title=dict(
        text=(
            "<b>Customer Support Operations</b>"
            "  <span style='font-size:13px;color:#9CA3AF'>KPI Dashboard · 2020–2021</span>"
        ),
        font=dict(size=22, color="#111827"),
        x=0.01, xanchor="left", y=0.99,
    ),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#E5E7EB",
        borderwidth=1,
        font=dict(size=11, color="#6B7280"),
        x=0.99, y=0.68,
        xanchor="right",
        yanchor="top",
    ),
    margin=dict(t=70, b=40, l=60, r=80),
    showlegend=True,
)

# Axis styling
axis_style = dict(
    gridcolor="#E5E7EB",
    linecolor="#E5E7EB",
    zeroline=False,
    tickfont=dict(color="#6B7280", size=10, family="Arial"),
    showgrid=True,
)
for r, c in [(2, 1), (3, 1), (3, 2), (4, 1)]:
    fig.update_xaxes(**axis_style, row=r, col=c)
    fig.update_yaxes(**axis_style, row=r, col=c)

# Row 1 — completely hide (it's just an annotation anchor)
fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1)
fig.update_layout(plot_bgcolor="white")

fig.update_yaxes(showgrid=False, row=2, col=1)
fig.update_xaxes(showgrid=False, row=4, col=1)
fig.update_yaxes(ticksuffix="%", row=3, col=1)
fig.update_yaxes(ticksuffix=" / 5", row=3, col=2)

# ─────────────────────────────────────────────────────────────
# KPI ANNOTATION CARDS (top strip)
# ─────────────────────────────────────────────────────────────
kpi_cards = [
    (0.12, "TOTAL TICKETS",    f"{total_tickets:,}",          "#3B82F6"),
    (0.50, "RESOLUTION RATE",  f"{resolution_rate}%",         "#10B981"),
    (0.88, "AVG SATISFACTION", f"{avg_satisfaction} / 5",     "#F59E0B"),
]
for x_pos, label, value, color in kpi_cards:
    fig.add_annotation(
        x=x_pos, y=0.985, xref="paper", yref="paper",
        text=f"<span style='font-size:10px;color:#9CA3AF;letter-spacing:1.5px'>{label}</span>",
        showarrow=False, align="center",
    )
    fig.add_annotation(
        x=x_pos, y=0.960, xref="paper", yref="paper",
        text=f"<b style='font-size:28px;color:{color}'>{value}</b>",
        showarrow=False, align="center",
    )


for ann in fig.layout.annotations:
    if ann.text:  # subplot title annotations have text; KPI ones are added later
        ann.update(
            font=dict(size=11, color="#6B7280", family="Arial"),
            showarrow=False,
        )

fig.write_html(
    "dashboard.html",
    include_plotlyjs=True,
    full_html=True,
    config={"displayModeBar": False, "scrollZoom": False},
)

print("\nDone.")
print("  dashboard.html — open in any browser")
print(f"\nQuick stats:")
print(f"  Total tickets    : {total_tickets:,}")
print(f"  Resolution rate  : {resolution_rate}%")
print(f"  Avg satisfaction : {avg_satisfaction} / 5")
print(f"  Top channel      : {top_channel}")