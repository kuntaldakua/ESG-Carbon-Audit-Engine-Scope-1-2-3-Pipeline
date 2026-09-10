# STEP 5 — ESG Executive Dashboard Specification (Power BI)
## Forensic Carbon Audit Command Center — Sustainability Advisory

---

### 1. DATA MODEL — Import from SQL / CSV Exports

| Table / Source | Role | Key Columns | Relationships |
|---|---|---|---|
| `facilities` | Dimension | facility_id, facility_name, country, region, geo_lat, geo_lon, revenue_usd, net_zero_target_year | 1:M → energy consumption, logistics, risk |
| `energy_consumption` | Fact (raw) | consumption_id, facility_id, log_date, energy_source, quantity_raw, unit_raw, audit_note | M:1 → facilities |
| `vw_scope_emissions` | Fact (calculated) | facility_id, log_date, scope1_mtco2e, scope2_mtco2e, scope3_mtco2e, total_mtco2e | M:1 → facilities |
| `suppliers` | Dimension | supplier_id, supplier_name, esg_score, contract_cost_usd, scope_3_intensity_kg_per_usd | 1:M → logistics (optional) |
| `vw_esg_risk_ratings` | Dimension / Score | facility_id, esg_risk_rating, emission_intensity_kg_per_usd | 1:1 → facilities |

**Relationships:**
- `facilities`[facility_id] → `vw_scope_emissions`[facility_id] (1:M, active)
- `facilities`[facility_id] → `vw_esg_risk_ratings`[facility_id] (1:1)
- `facilities`[facility_id] → `energy_consumption`[facility_id] (1:M)
- `suppliers`[supplier_id] → `logistics_trips`[supplier_id] (1:M, for Scope 3 drilldown)

---

### 2. DAX MEASURES — ESG Consulting KPI Engine

```dax
Total Carbon Footprint MTCO2e = SUM(vw_scope_emissions[total_mtco2e])

Scope 1 Direct = SUM(vw_scope_emissions[scope1_mtco2e])

Scope 2 Electricity = SUM(vw_scope_emissions[scope2_mtco2e])

Scope 3 Supply Chain = SUM(vw_scope_emissions[scope3_mtco2e])

Net Zero Target Progress % = DIVIDE(
    SUMX(FILTER(facilities, facilities[net_zero_target_year] <= YEAR(TODAY())), 1),
    COUNTROWS(facilities),
    0
)

High Risk Facility Count = CALCULATE(COUNTROWS(facilities), vw_esg_risk_ratings[esg_risk_rating] IN {"Critical","High"})

Avg ESG Score = AVERAGE(suppliers[esg_score])

Emission Intensity (kg per $100k) = AVERAGE(vw_esg_risk_ratings[emission_intensity_kg_per_usd])

Top Facility by Emissions = TOPN(10, facilities, [Total Carbon Footprint MTCO2e], DESC)
```

---

### 3. VISUAL LAYOUT — ESG Executive Command Center

**Top Banner — KPI Cards (Black / White / Gray, Consulting Style):**
- **Total Carbon Footprint (MTCO₂e)** — large metric with YoY trend arrow
- **Scope 1 / 2 / 3 Split** — donut chart showing proportion
- **Net Zero Progress %** — progress bar against 2030/2035 targets
- **Critical + High Risk Facilities** — count with drill-through

**Left — Filter / Slicer Panel:**
- **Region Slicer:** North America / EU-West / APAC / LATAM / Africa
- **Facility Type:** Manufacturing / Warehouse / Office / Data Center
- **Risk Level:** Low / Medium / High / Critical
- **Time Range:** Log date / Quarter / Year
- **Energy Source:** Electricity / Diesel / Natural Gas / Jet Fuel / Coal
- **Net Zero Target Year:** 2030 / 2035 / 2040

**Center — Main Evidence Graphics:**
- **Bubble Map:** Facility geo positions (lat/lon) with bubble size = total MTCO₂e, shade = risk rating (black = Critical, gray = High, light = Low). Enables global risk geography review.
- **Time-Series Line Chart:** Scope 1 vs Scope 2 monthly trends with hypothetical clean-energy transition marker (vertical line at month 6) — exact replication of Step 3 visualization.
- **Supplier Quadrant:** ESG Score (x-axis) vs Contract Cost (y-axis), bubble color = intensity, with critical-priority vendors highlighted.

**Right — Drill-Down Matrix:**
- Interactive table: Facility, Country, Region, Scope 1/2/3, Total, Emission Intensity, Risk Rating, Net Zero Year, Action Status (e.g., Freeze / Re-bid / Monitor)
- Conditional formatting via Power BI: red rows = Critical intensity; gray = Medium

**Bottom — Action Panel:**
- Auto-generated recommendation cards tied to risk ratings:  
  *"Facility 103 (APAC) — Critical intensity. Recommend clean-energy contract renegotiation + supplier decarbonization review."*
- Export to Excel (audit workpaper link — Step 4)
- Print-ready consulting slide layout (black/white, minimal chrome)

---

### 4. STAKEHOLDER USE CASES — Consulting Engagement

| Stakeholder | How They Use the Dashboard | Consulting Value |
|---|---|---|
| **ESG / Audit Team** | Filter by Critical + dirty data; review Scope 3 supplier intensity; export flagged facility list | Evidence-based audit trail for regulatory filings (CSRD / SEC Climate Disclosure) |
| **Procurement / Supply Chain** | Filter supplier quadrant; identify high-cost / low-ESG vendors; set decarbonization targets | Data-driven supplier renegotiation and contract restructuring |
| **Executive / Board** | View total footprint KPI + net-zero progress %; use bubble map to see geographic exposure | Board-ready narrative linking carbon data to financial risk and target timelines |
| **Facility Operations** | Review Scope 1 (direct fuel) vs Scope 2 (grid) by facility; compare pre/post transition trends | Operational improvement priorities: switch fuel sources or upgrade grid contracts |

---

### 5. CONSULTING VALUE STATEMENT
> The ESG Command Center transforms 500,000+ raw energy and logistics records into an interactive, audit-ready sustainability platform. It demonstrates end-to-end advisory capability: SQL extraction → emission-factor calculation → statistical validation → visual proof → automated audit documentation → executive decision support — aligned with EY CCaSS / PwC ESG consulting standards.
