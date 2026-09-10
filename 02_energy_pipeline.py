#!/usr/bin/env python3
"""
STEP 2 — ESG Carbon Calculation Engine (Python / Pandas / NumPy)
Project: Scope 1, 2 & 3 Carbon Emissions & ESG Compliance Audit
Target: EY CCaSS / PwC ESG Consulting
Scope: Multi-facility global supply chain carbon footprint

Methods:
  • Import messy multi-source energy logs (kWh, L, gal, miles, therms)
  • Clean unit mismatches via Pandas mapping / normalization
  • Calculate MTCO2e for Scope 1 (Direct), Scope 2 (Electricity Grid), Scope 3 (Transport + Supply Chain)
  • NumPy conditional logic: ESG Risk Rating by emission intensity / revenue dollar
  • Output: clean dataset + risk-rated facilities + supplier scatter data
"""

import pandas as pd
import numpy as np
import os

EXPORT_DIR = "/home/user/project_esg_carbon_audit/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

np.random.seed(2026)

# ------------------------------------------------------------------
# SYNTHETIC DATA GENERATION — replicating global multi-facility ERP
# ------------------------------------------------------------------

facilities = pd.DataFrame({
    "facility_id": np.arange(1, 51),
    "facility_name": [f"Plant_{chr(65+i//5)}{i%5+1}" for i in range(50)],
    "country": np.random.choice(
        ["USA", "Germany", "India", "China", "Brazil", "UK", "Japan", "Canada", "Australia", "Mexico"], 50),
    "region": np.random.choice(
        ["North America", "EU-West", "APAC", "LATAM", "Africa"], 50),
    "facility_type": np.random.choice(
        ["Manufacturing", "Warehouse", "Office", "Data Center"], 50),
    "revenue_usd": np.round(np.random.lognormal(13, 1.0, 50), 2),
    "net_zero_target_year": np.random.choice([2030, 2035, 2040], 50),
    "geo_lat": np.round(np.random.uniform(-40, 60, 50), 4),
    "geo_lon": np.round(np.random.uniform(-120, 150, 50), 4),
})

# Emission factors (EPA / DEFRA / GHG Protocol representative)
emission_factors = pd.DataFrame({
    "factor_id": np.arange(1, 11),
    "source_category": ["Fuel", "Fuel", "Fuel", "Electricity Grid", "Electricity Grid", "Transport", "Transport", "Transport", "Transport", "Transport"],
    "region": ["Global", "EU-West", "APAC", "North America", "EU-West", "Global", "EU-West", "APAC", "LATAM", "Africa"],
    "fuel_or_source": ["Diesel", "Natural Gas", "Jet Fuel", "Electricity", "Electricity", "Road", "Air", "Sea", "Rail", "Road"],
    "factor_kg_per_unit": [
        2.68, 2.75, 3.16,  # kg CO2e / L diesel, / L gas, / L jet (approx)
        0.42, 0.28,         # kg CO2e / kWh NA grid, EU grid
        0.12, 0.55, 0.04, 0.03, 0.10  # kg CO2e / ton-km or km approximations
    ],
    "standard_year": 2024,
})

# Energy consumption — messy records (dirty flags, mixed units)
energy_logs = pd.DataFrame({
    "consumption_id": np.arange(1, 80001),
    "facility_id": np.random.choice(facilities["facility_id"], 80_000),
    "log_date": pd.date_range("2024-01-01", periods=80_000, freq="30min").to_series().sample(80_000, replace=True).values,
    "energy_source": np.random.choice(["Electricity", "Diesel", "Natural Gas", "Jet Fuel", "Coal"], 80_000),
    "quantity_raw": np.round(np.random.lognormal(4, 1.2, 80_000), 3),
    "unit_raw": np.random.choice(["kWh", "L", "gal", "miles", "therms", "kg"], 80_000, p=[0.55, 0.15, 0.10, 0.08, 0.07, 0.05]),
    "data_quality_flag": np.random.choice(
        ["Clean", "Clean", "Clean", "Dirty", "Estimated", "Missing"], 80_000, p=[0.60, 0.10, 0.10, 0.08, 0.07, 0.05]),
})
# Force some dirty / estimated flags explicitly for consulting demonstration
energy_logs.loc[energy_logs.sample(300, random_state=1).index, "data_quality_flag"] = "Dirty"

# Logistics trips (Scope 3 transport)
logistics_trips = pd.DataFrame({
    "trip_id": np.arange(1, 15_001),
    "facility_id": np.random.choice(facilities["facility_id"], 15_000),
    "supplier_id": np.random.choice(np.arange(1, 101), 15_000),
    "trip_date": pd.date_range("2024-01-01", periods=15_000, freq="2h").to_series().sample(15_000, replace=True).values,
    "mode": np.random.choice(["Road", "Air", "Sea", "Rail"], 15_000, p=[0.50, 0.20, 0.20, 0.10]),
    "distance_km": np.round(np.random.lognormal(6, 1.0, 15_000), 2),
    "weight_kg": np.round(np.random.uniform(50, 50000, 15_000), 0),
    "fuel_type": np.random.choice(["Diesel", "Jet Fuel", "Marine Fuel", "Electric Truck"], 15_000),
})

# Suppliers with ESG scores
suppliers = pd.DataFrame({
    "supplier_id": np.arange(1, 101),
    "supplier_name": [f"Supplier_{chr(65+i//10)}{i%10+1}" for i in range(100)],
    "supplier_category": np.random.choice(
        ["Raw Material", "Logistics", "Packaging", "IT Services", "Energy"], 100),
    "country": np.random.choice(
        ["USA", "Germany", "India", "China", "Mexico", "UK"], 100),
    "contract_cost_usd": np.round(np.random.lognormal(8, 1.3, 100), 2),
    "esg_score": np.round(np.clip(np.random.normal(55, 15, 100), 20, 95), 1),  # 0-100 scale
    "scope_3_intensity_kg_per_usd": np.round(np.random.uniform(0.05, 0.45, 100), 6),
    "decarbonization_target_year": np.random.choice([2030, 2035, 2040], 100),
})

# ------------------------------------------------------------------
# CLEANING & NORMALIZATION — unit mismatch resolution
# ------------------------------------------------------------------

def normalize_units(row):
    """Consulting data-quality step: standardize messy units."""
    val = float(row["quantity_raw"])
    u = str(row["unit_raw"]).lower()
    if u in ("kwh",):
        # Electricity -> MWh for consistency with grid factors
        return val / 1000.0, "mwh"
    elif u in ("l", "liters", "litres"):
        return val, "l"
    elif u in ("gal", "gallons"):
        return val * 3.78541, "l"
    elif u in ("miles",):
        # Transport distance -> km
        return val * 1.60934, "km"
    elif u in ("therms",):
        # 1 therm ≈ 29.3 kWh (natural gas energy content); convert to MWh approx
        return (val * 29.3) / 1000.0, "mwh"
    elif u in ("kg",):
        # Direct fuel mass -> approximate to L using density 0.85 for diesel-like
        return val / 0.85, "l"
    else:
        return val, u

energy_logs[["normalized_qty", "unit_std"]] = energy_logs.apply(
    lambda row: pd.Series(normalize_units(row)), axis=1)

# Mark dirty / estimated for audit transparency
energy_logs["audit_note"] = np.where(
    energy_logs["data_quality_flag"] == "Dirty",
    "Unit mismatch / missing source; estimated via regional benchmark",
    np.where(energy_logs["data_quality_flag"] == "Estimated", "Interpolated from peer facility", "Direct measurement")
)

# ------------------------------------------------------------------
# CALCULATION ENGINE — Scope 1 / 2 / 3 MTCO2e
# ------------------------------------------------------------------

# Scope 1: Direct fuel combustion (diesel, natural gas, jet fuel, coal) using fuel factors
# We map energy_source to factor row
fuel_factors = emission_factors[emission_factors["source_category"] == "Fuel"]
# Simple merge for demo: assign regional factor roughly
def get_fuel_factor(region, source):
    if source == "Diesel": return 2.68
    if source == "Natural Gas": return 2.75
    if source == "Jet Fuel": return 3.16
    if source == "Coal": return 3.5
    return 0.0

# Scope 1 calculation
energy_logs["scope1_kg_co2e"] = np.where(
    energy_logs["energy_source"].isin(["Diesel", "Natural Gas", "Jet Fuel", "Coal"]),
    energy_logs["normalized_qty"] * energy_logs.apply(
        lambda r: get_fuel_factor(r["facility_id"], r["energy_source"]), axis=1),
    0.0
)

# Scope 2: Electricity grid — use regional factor from emission_factors (simplified mapping)
grids = {
    "North America": 0.42,
    "EU-West": 0.28,
    "APAC": 0.45,
    "LATAM": 0.50,
    "Africa": 0.55,
}
facilities["grid_factor"] = facilities["region"].map(grids)
energy_merged = energy_logs.merge(facilities[["facility_id", "region", "grid_factor"]], on="facility_id", how="left")

energy_merged["scope2_kg_co2e"] = np.where(
    energy_merged["energy_source"] == "Electricity",
    energy_merged["normalized_qty"] * energy_merged["grid_factor"] * 1000,  # MWh to kWh approximation handled via qty
    0.0
)
# Note: for simplicity, normalized_qty for electricity already in MWh; multiply by factor (kg/kWh * 1000 to get kg/MWh approx or adjust)
# We simplify: assume factor is kg/kWh and qty is kWh for electricity; but our normalization converted to MWh.
# Correct approach: multiply MWh * factor_kg_per_kWh * 1000
energy_merged["scope2_kg_co2e"] = np.where(
    energy_merged["energy_source"] == "Electricity",
    energy_merged["normalized_qty"] * 1000 * energy_merged["grid_factor"],
    0.0
)

# Scope 3 Transport: logistics distance * mode factor
transport_factors = {"Road": 0.12, "Air": 0.55, "Sea": 0.04, "Rail": 0.03}
logistics_trips["transport_factor"] = logistics_trips["mode"].map(transport_factors)
logistics_trips["scope3_transport_kg_co2e"] = logistics_trips["distance_km"] * logistics_trips["transport_factor"] * logistics_trips["weight_kg"] / 1000.0

# Scope 3 Suppliers: intensity * contract cost
suppliers_merged = suppliers.copy()
suppliers_merged["scope3_supplier_kg_co2e"] = suppliers_merged["contract_cost_usd"] * suppliers_merged["scope_3_intensity_kg_per_usd"]

# Aggregate by facility and month for time-series
energy_merged["month"] = pd.to_datetime(energy_merged["log_date"]).dt.to_period("M").astype(str)
scope_agg = energy_merged.groupby(["facility_id", "month"])[["scope1_kg_co2e", "scope2_kg_co2e"]].sum().reset_index()
scope_agg["scope1_mtco2e"] = scope_agg["scope1_kg_co2e"] / 1000.0
scope_agg["scope2_mtco2e"] = scope_agg["scope2_kg_co2e"] / 1000.0
scope_agg.to_csv(os.path.join(EXPORT_DIR, "facility_scope1_2_monthly.csv"), index=False)

# Facility-level totals for risk rating
facility_totals = energy_merged.groupby("facility_id")[["scope1_kg_co2e", "scope2_kg_co2e"]].sum().reset_index()
facility_totals["scope1_mtco2e"] = facility_totals["scope1_kg_co2e"] / 1000.0
facility_totals["scope2_mtco2e"] = facility_totals["scope2_kg_co2e"] / 1000.0

# Merge supplier scope 3 by facility (approximated via logistics trips + supplier mapping)
# Simplified: aggregate supplier emissions per facility via random assignment for demo
facility_supplier = logistics_trips.groupby("facility_id")["supplier_id"].nunique().reset_index()
facility_supplier = facility_supplier.merge(suppliers[["supplier_id", "scope_3_intensity_kg_per_usd", "contract_cost_usd"]], on="supplier_id", how="left")
# Aggregate supplier intensity per facility (approximate consulting model)
facility_supplier_agg = facility_supplier.groupby("facility_id").agg({
    "contract_cost_usd": "sum",
    "scope_3_intensity_kg_per_usd": "mean"
}).reset_index()
facility_supplier_agg["scope3_mtco2e_approx"] = facility_supplier_agg["contract_cost_usd"] * facility_supplier_agg["scope_3_intensity_kg_per_usd"] / 1000.0

# Combine all scopes per facility for risk rating
facility_risk = facilities.merge(facility_totals[["facility_id", "scope1_mtco2e", "scope2_mtco2e"]], on="facility_id", how="left")
facility_risk = facility_risk.merge(facility_supplier_agg[["facility_id", "scope3_mtco2e_approx"]], on="facility_id", how="left")
facility_risk[["scope1_mtco2e", "scope2_mtco2e", "scope3_mtco2e_approx"]] = facility_risk[["scope1_mtco2e", "scope2_mtco2e", "scope3_mtco2e_approx"]].fillna(0)
facility_risk["total_mtco2e"] = facility_risk["scope1_mtco2e"] + facility_risk["scope2_mtco2e"] + facility_risk["scope3_mtco2e_approx"]

# NumPy conditional logic: ESG Risk Rating by emission intensity per revenue dollar
facility_risk["emission_intensity_per_100k"] = np.where(
    facility_risk["revenue_usd"] > 0,
    (facility_risk["total_mtco2e"] / facility_risk["revenue_usd"]) * 100000,
    np.nan
)

# Apply risk thresholds (consulting / audit framework)
facility_risk["esg_risk_rating"] = np.select(
    condlist=[
        facility_risk["emission_intensity_per_100k"] < 15,
        facility_risk["emission_intensity_per_100k"] < 40,
        facility_risk["emission_intensity_per_100k"] < 90,
    ],
    choicelist=["Low", "Medium", "High"],
    default="Critical"
)

facility_risk_export = facility_risk[[
    "facility_id", "facility_name", "country", "region", "revenue_usd",
    "scope1_mtco2e", "scope2_mtco2e", "scope3_mtco2e_approx", "total_mtco2e",
    "emission_intensity_per_100k", "esg_risk_rating", "net_zero_target_year"
]]
facility_risk_export.to_csv(os.path.join(EXPORT_DIR, "facility_risk_ratings.csv"), index=False)

# Supplier scatter data (ESG Score vs Contract Cost)
supplier_scatter = suppliers[["supplier_id", "supplier_name", "supplier_category", "contract_cost_usd", "esg_score", "scope_3_intensity_kg_per_usd", "decarbonization_target_year"]].copy()
supplier_scatter.to_csv(os.path.join(EXPORT_DIR, "supplier_esg_scatter.csv"), index=False)

# Metrics summary for consulting report
metrics = {
    "total_facilities": len(facilities),
    "total_energy_logs": len(energy_logs),
    "total_logistics_trips": len(logistics_trips),
    "total_suppliers": len(suppliers),
    "average_emission_intensity_kg_per_100k": float(facility_risk["emission_intensity_per_100k"].mean()),
    "critical_risk_facilities": int((facility_risk["esg_risk_rating"] == "Critical").sum()),
    "high_risk_facilities": int((facility_risk["esg_risk_rating"] == "High").sum()),
    "low_risk_facilities": int((facility_risk["esg_risk_rating"] == "Low").sum()),
}
with open(os.path.join(EXPORT_DIR, "pipeline_metrics.txt"), "w") as f:
    for k, v in metrics.items():
        f.write(f"{k}: {v}\n")

print("STEP 2 COMPLETE — ESG pipeline executed.")
print("Exports:", EXPORT_DIR)
print("Key metrics:", metrics)
