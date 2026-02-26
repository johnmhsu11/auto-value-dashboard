import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Auto True Value vs Price", page_icon="🚗", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #111827; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    /* Expander dark theme */
    [data-testid="stExpander"] details {
        background-color: #1f2937;
        border: 1px solid #374151 !important;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    [data-testid="stExpander"] summary { color: #f9fafb !important; }
    [data-testid="stExpander"] summary:hover { background-color: #374151 !important; border-radius: 8px; }
    h1, h2, h3, p, label { color: #f9fafb !important; }
    [data-testid="metric-container"] {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 1rem 1.25rem;
    }
    [data-testid="metric-container"] label { color: #9ca3af !important; font-size: 0.8rem; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f9fafb !important; }
    .stMultiSelect [data-baseweb="tag"] { background-color: #6366f1; }

    /* ── Mobile adjustments ───────────────────────────────────── */
    @media (max-width: 640px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 1rem !important;
        }
        h1 { font-size: 1.4rem !important; }
        /* Wrap 4-column KPI row into a 2×2 grid */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        /* Shrink metric values so long model names don't overflow */
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 0.8rem !important;
            word-break: break-word !important;
        }
        [data-testid="metric-container"] { padding: 0.75rem 1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="#1f2937",
        plot_bgcolor="#1f2937",
        font=dict(color="#f9fafb", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="#374151", linecolor="#374151", zerolinecolor="#374151"),
        yaxis=dict(gridcolor="#374151", linecolor="#374151", zerolinecolor="#374151"),
        margin=dict(t=40, b=40, l=40, r=40),
    )
)

@st.cache_data
def load_data():
    df = pd.read_csv("auto_values.csv")
    # True Value Score: 40% reliability, 35% residual value, 25% safety
    df["True_Value_Score"] = (
        (df["Reliability_Score"] / 10 * 40) +
        (df["Residual_5yr_Pct"] / 100 * 35) +
        (df["Safety_Score"] / 5 * 25)
    ).round(1)
    # Value per Dollar: how much true value you get per $10k spent
    df["Value_Per_Dollar"] = (df["True_Value_Score"] / (df["MSRP_USD"] / 10000)).round(2)
    # 5-year total cost of ownership
    df["Five_yr_Cost_USD"] = (
        df["MSRP_USD"] +
        (df["Annual_Maintenance_USD"] * 5) -
        (df["MSRP_USD"] * df["Residual_5yr_Pct"] / 100)
    ).astype(int)
    df["Model_Full"] = df["Brand"] + " " + df["Model"]
    return df

df = load_data()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🚗 Automobile True Value vs. Price")
st.markdown(
    "<p style='color:#9ca3af;margin-top:-0.5rem;margin-bottom:1rem'>"
    "How much are you actually getting for your money? Comparing sticker price against "
    "a composite score built from reliability, depreciation, and safety.</p>",
    unsafe_allow_html=True,
)

# ── Filters ─────────────────────────────────────────────────────────────────────
with st.expander("⚙️ Filters", expanded=False):
    all_brands = sorted(df["Brand"].unique())
    b1, b2 = st.columns(2)
    if b1.button("Select All", use_container_width=True):
        st.session_state["brands"] = all_brands
    if b2.button("Clear All", use_container_width=True):
        st.session_state["brands"] = []

    selected_brands = st.multiselect(
        "Brands", all_brands,
        default=st.session_state.get("brands", all_brands),
        key="brands",
    )

    f1, f2 = st.columns(2)
    all_classes = sorted(df["Class"].unique())
    selected_classes = f1.multiselect("Vehicle Class", all_classes, default=all_classes)

    f2.markdown("**Off-Road Capability**")
    off_road_filter = f2.radio(
        "Off-Road Capability",
        options=["All Vehicles", "Off-Road Capable (Good or better)", "Excellent Only", "Not Off-Road"],
        index=0,
        label_visibility="collapsed",
    )

    price_min, price_max = int(df["MSRP_USD"].min()), int(df["MSRP_USD"].max())
    price_range = st.slider(
        "MSRP Range (USD)", price_min, price_max, (price_min, price_max), step=1000,
        format="$%d",
    )
    st.markdown(
        "<small style='color:#9ca3af'>Reliability & safety data sourced from "
        "Consumer Reports and NHTSA (2023). Residual values from iSeeCars.</small>",
        unsafe_allow_html=True,
    )

off_road_map = {
    "All Vehicles": ["Excellent", "Good", "Moderate", "No"],
    "Off-Road Capable (Good or better)": ["Excellent", "Good"],
    "Excellent Only": ["Excellent"],
    "Not Off-Road": ["No"],
}

filtered = df[
    df["Brand"].isin(selected_brands) &
    df["Class"].isin(selected_classes) &
    df["MSRP_USD"].between(*price_range) &
    df["Off_Road_Rating"].isin(off_road_map[off_road_filter])
]

# ── KPIs ───────────────────────────────────────────────────────────────────────
if not filtered.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Models", len(filtered))
    m2.metric("Avg MSRP", f"${filtered['MSRP_USD'].mean():,.0f}")
    best = filtered.loc[filtered["Value_Per_Dollar"].idxmax()]
    worst = filtered.loc[filtered["Value_Per_Dollar"].idxmin()]
    m3.metric("Best Value/Dollar", f"{best['Model_Full']}")
    m4.metric("Worst Value/Dollar", f"{worst['Model_Full']}")

st.markdown("---")

# ── Main scatter: MSRP vs True Value Score ─────────────────────────────────────
st.markdown("### MSRP vs. True Value Score")
st.markdown(
    "<p style='color:#9ca3af;font-size:0.85rem;margin-top:-0.75rem'>"
    "Top-left = best value (low price, high score). Bottom-right = poorest value.</p>",
    unsafe_allow_html=True,
)

if not filtered.empty:
    avg_msrp = filtered["MSRP_USD"].mean()
    avg_score = filtered["True_Value_Score"].mean()

    fig_scatter = px.scatter(
        filtered,
        x="MSRP_USD",
        y="True_Value_Score",
        color="Brand",
        size="Value_Per_Dollar",
        hover_name="Model_Full",
        hover_data={
            "MSRP_USD": ":$,.0f",
            "True_Value_Score": ":.1f",
            "Value_Per_Dollar": ":.2f",
            "Reliability_Score": ":.1f",
            "Residual_5yr_Pct": ":.0f%%",
            "Five_yr_Cost_USD": ":$,.0f",
            "Off_Road_Rating": True,
            "Brand": False,
        },
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={
            "MSRP_USD": "MSRP (USD)",
            "True_Value_Score": "True Value Score (0–100)",
            "Value_Per_Dollar": "Value/Dollar",
            "Reliability_Score": "Reliability",
            "Residual_5yr_Pct": "5yr Residual",
            "Five_yr_Cost_USD": "5yr Total Cost",
            "Off_Road_Rating": "Off-Road",
        },
        size_max=22,
    )
    # Quadrant reference lines
    fig_scatter.add_hline(y=avg_score, line_dash="dot", line_color="#374151")
    fig_scatter.add_vline(x=avg_msrp, line_dash="dot", line_color="#374151")
    fig_scatter.update_layout(
        **TEMPLATE["layout"],
        height=540,
        xaxis_tickprefix="$",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.18,
            xanchor="left", x=0,
            bgcolor="rgba(31,41,55,0.8)",
            bordercolor="#374151", borderwidth=1,
            font=dict(size=9),
        ),
        legend_itemclick="toggleothers",
        legend_itemdoubleclick="toggle",
    )
    # Extra bottom margin so the horizontal legend doesn't get clipped
    fig_scatter.update_layout(margin=dict(b=130))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Value per Dollar by brand ──────────────────────────────────────────────────
st.markdown("### Average Value per Dollar by Brand")
st.markdown(
    "<p style='color:#9ca3af;font-size:0.85rem;margin-top:-0.75rem'>"
    "True Value Score ÷ (MSRP / $10,000) — higher means more value for your money.</p>",
    unsafe_allow_html=True,
)

brand_avg = (
    filtered.groupby("Brand")["Value_Per_Dollar"]
    .mean()
    .reset_index()
    .sort_values("Value_Per_Dollar", ascending=True)
)

fig_brand = px.bar(
    brand_avg,
    x="Value_Per_Dollar",
    y="Brand",
    orientation="h",
    color="Value_Per_Dollar",
    color_continuous_scale=["#312e81", "#6366f1", "#a5b4fc"],
    labels={"Value_Per_Dollar": "Avg Value per Dollar"},
)
fig_brand.update_layout(
    **TEMPLATE["layout"],
    height=max(300, len(brand_avg) * 22),
    coloraxis_showscale=False,
    xaxis_title="Value per Dollar Score",
    yaxis_title=None,
)
st.plotly_chart(fig_brand, use_container_width=True)

# ── Data table ─────────────────────────────────────────────────────────────────
st.markdown("### Full Data Table")
table_df = (
    filtered[[
        "Brand", "Model", "Class", "MSRP_USD", "True_Value_Score",
        "Value_Per_Dollar", "Reliability_Score", "Residual_5yr_Pct",
        "Safety_Score", "Annual_Maintenance_USD", "Five_yr_Cost_USD",
        "Off_Road_Rating",
    ]]
    .sort_values("Value_Per_Dollar", ascending=False)
    .rename(columns={
        "MSRP_USD": "MSRP",
        "True_Value_Score": "Value Score",
        "Value_Per_Dollar": "Value/Dollar",
        "Reliability_Score": "Reliability",
        "Residual_5yr_Pct": "5yr Residual %",
        "Safety_Score": "Safety",
        "Annual_Maintenance_USD": "Maint./yr",
        "Five_yr_Cost_USD": "5yr Total Cost",
        "Off_Road_Rating": "Off-Road",
    })
)
st.dataframe(
    table_df.style.format({
        "MSRP": "${:,.0f}",
        "Value Score": "{:.1f}",
        "Value/Dollar": "{:.2f}",
        "Reliability": "{:.1f}",
        "5yr Residual %": "{:.0f}%",
        "Safety": "{:.0f}",
        "Maint./yr": "${:,.0f}",
        "5yr Total Cost": "${:,.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Methodology + Sources ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Methodology & Data Sources")
st.markdown("""
**True Value Score (0–100)** is a composite metric:
- **40%** — Reliability Score (1–10, from Consumer Reports)
- **35%** — 5-Year Residual Value (% of MSRP retained after 5 years)
- **25%** — Safety Score (1–5 NHTSA stars)

**Value per Dollar** = True Value Score ÷ (MSRP / $10,000). Higher is better.

**5-Year Total Cost** = MSRP + (Annual Maintenance × 5) − Resale Value.

| Source | Data Used | Link |
|---|---|---|
| **Consumer Reports** | Reliability scores by model | [consumerreports.org](https://www.consumerreports.org/cars/) |
| **NHTSA** | Safety star ratings | [nhtsa.gov](https://www.nhtsa.gov/ratings) |
| **iSeeCars** | 5-year residual value by model | [iseecars.com](https://www.iseecars.com/car-depreciation-study) |
| **RepairPal** | Average annual maintenance costs | [repairpal.com](https://repairpal.com/reliability) |

*Data reflects 2023 model year estimates. Figures are approximate and may vary by trim level and region.*
""")
