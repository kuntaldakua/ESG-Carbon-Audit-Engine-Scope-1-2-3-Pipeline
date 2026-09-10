#!/usr/bin/env python3
"""
STEP 3 — Visual Trend Analysis (Matplotlib)
Output: PNG charts for consulting / audit presentation
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

EXPORT_DIR = "/home/user/project_esg_carbon_audit/exports"
OUTPUT_DIR = "/home/user/project_esg_carbon_audit/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "figure.facecolor": "white",
    "axes.edgecolor": "#111111",
    "axes.labelcolor": "#111111",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "text.color": "#111111",
    "figure.dpi": 200,
})

# Load monthly aggregated scope 1/2 data
scope_agg = pd.read_csv(os.path.join(EXPORT_DIR, "facility_scope1_2_monthly.csv"))
scope_agg["month"] = pd.to_datetime(scope_agg["month"])

# ------------------------------------------------------------------
# 3A — Time-Series: Scope 1 vs Scope 2 Before / After Transition
# ------------------------------------------------------------------
# Simulate a hypothetical clean-energy transition at month 6 for demo
monthly_avg = scope_agg.groupby("month")[["scope1_mtco2e", "scope2_mtco2e"]].mean().reset_index()
monthly_avg = monthly_avg.sort_values("month")

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(monthly_avg["month"], monthly_avg["scope1_mtco2e"], marker="o", markersize=3, label="Scope 1 — Direct (Fuel/Combustion)", color="#111111", linewidth=2)
ax.plot(monthly_avg["month"], monthly_avg["scope2_mtco2e"], marker="s", markersize=3, label="Scope 2 — Electricity (Grid)", color="#777777", linewidth=2, linestyle="--")
# Hypothetical transition marker
transition_month = monthly_avg["month"].iloc[len(monthly_avg)//2]
ax.axvline(transition_month, color="#777777", linestyle=":", alpha=0.7, label="Clean Energy Transition (Hypothetical)")
ax.set_title("ESG Compliance — Scope 1 vs Scope 2 Time-Series\nBefore & After Hypothetical Clean Energy Transition")
ax.set_ylabel("Metric Tons CO₂e (MTCO₂e)")
ax.set_xlabel("Month (2024)")
ax.legend(frameon=True, facecolor="white", edgecolor="#bbbbbb", loc="upper right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "scope1_2_trend.png"))
plt.close(fig)

# ------------------------------------------------------------------
# 3B — Scatter: Supplier ESG Score vs Contract Cost (Risk Quadrant)
# ------------------------------------------------------------------
suppliers = pd.read_csv(os.path.join(EXPORT_DIR, "supplier_esg_scatter.csv"))
fig, ax = plt.subplots(figsize=(8, 5))
# Quadrant coloring based on ESG score / cost
colors = np.where(suppliers["esg_score"] > 60, "#333333", np.where(suppliers["esg_score"] > 35, "#777777", "#bbbbbb"))
scatter = ax.scatter(suppliers["contract_cost_usd"]/1000, suppliers["esg_score"],
                     c=colors, s=60, alpha=0.8, edgecolors="#111111", zorder=3)
# Quadrant lines
ax.axhline(60, color="#333333", linestyle="--", alpha=0.4, label="ESG Score = 60 (Threshold)")
ax.axvline(50, color="#333333", linestyle="--", alpha=0.4, label="Contract Cost = $50K")
ax.set_xlabel("Contract Cost (USD Thousands)")
ax.set_ylabel("Supplier ESG Score (0–100)")
ax.set_title("ESG Advisory — Supplier Risk Quadrant\nHigh-Cost / Low-ESG = Critical Decarbonization Priority")
ax.set_xlim(0, 250)
ax.set_ylim(10, 100)
ax.legend(frameon=True, facecolor="white", edgecolor="#bbbbbb", loc="lower left", fontsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "supplier_risk_quadrant.png"))
plt.close(fig)

# ------------------------------------------------------------------
# 3C — Facility Bubble Map (Emission Intensity by Geo)
# ------------------------------------------------------------------
fac_risk = pd.read_csv(os.path.join(EXPORT_DIR, "facility_risk_ratings.csv"))
fac_risk["geo_lon"] = np.random.uniform(-120, 150, len(fac_risk))
fac_risk["geo_lat"] = np.random.uniform(-40, 60, len(fac_risk))
fig, ax = plt.subplots(figsize=(8, 5))
# Bubble size = total emissions; color = risk rating (black/gray scale)
risk_colors = {"Low": "#bbbbbb", "Medium": "#777777", "High": "#333333", "Critical": "#111111"}
colors_map = fac_risk["esg_risk_rating"].map(risk_colors)
sizes = fac_risk["total_mtco2e"] * 30 + 20
scatter = ax.scatter(fac_risk["geo_lon"], fac_risk["geo_lat"], s=sizes, c=colors_map, alpha=0.85, edgecolors="#111111", zorder=3)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("ESG Audit — Facility Emission Bubble Map\nBubble Size = Total MTCO₂e | Shade = Risk Rating")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
# Legend for risk levels
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor="#bbbbbb", edgecolor="#111111", label="Low"),
                   Patch(facecolor="#777777", edgecolor="#111111", label="Medium"),
                   Patch(facecolor="#333333", edgecolor="#111111", label="High"),
                   Patch(facecolor="#111111", edgecolor="#111111", label="Critical")]
ax.legend(handles=legend_elements, title="ESG Risk", loc="lower left", frameon=True, facecolor="white", edgecolor="#bbbbbb")
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "facility_bubble_map.png"))
plt.close(fig)

print("STEP 3 COMPLETE — ESG visualizations saved to:", OUTPUT_DIR)
print("  • scope1_2_trend.png")
print("  • supplier_risk_quadrant.png")
print("  • facility_bubble_map.png")
