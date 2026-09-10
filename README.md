# ESG Carbon Audit Engine — Scope 1, 2 & 3 Pipeline
## Consulting Portfolio — Sustainability Advisory (EY CCaSS / PwC ESG)

---

## PROJECT OVERVIEW

**Title:** Scope 1, 2 & 3 Carbon Emissions & ESG Compliance Audit Engine  
**Domain:** Sustainability Advisory / ESG Consulting  
**Problem:** Assess corporate supply chain carbon footprints across global facilities; calculate GHG Protocol Scope 1/2/3 emissions; flag high-emission vendor risks for decarbonization.  
**Methodology:** Hypothesis-driven analysis → SQL relational architecture (energy, logistics, suppliers, emission factors) → statistical calculation engine (Python / Pandas / NumPy) → visual trend proof → automated Excel audit workpaper (XLOOKUP + conditional formatting) → interactive Power BI executive command center.

---

## STEP-BY-STEP DELIVERY — SEPARATE FROM FIRST PROJECT

| Step | File | Evidence / Output |
|---|---|---|
| **1. Database Architecture** | `01_database_schema.sql` | PostgreSQL: facilities, energy_consumption, logistics_trips, emission_factors, suppliers; CTE `vw_scope_emissions` with FULL OUTER JOINs; risk-rating view `vw_esg_risk_ratings`; indexes for audit speed |
| **2. Calculation Engine** | `02_energy_pipeline.py` | Executed — synthetic 80K energy logs + 15K logistics trips + 100 suppliers; cleaned dirty/estimated units; calculated MTCO₂e for Scope 1/2/3; NumPy conditional logic for ESG ratings; `pipeline_metrics.txt` + 5 CSV exports |
| **3. Visual Proof** | `03_visualizations.py` | Executed — 3 black/white PNGs: Scope 1/2 trend with clean-energy transition marker; supplier ESG-cost quadrant; facility emission bubble map (geo) |
| **4. Audit Workpaper** | `04_carbon_accounting_workpaper.py` + `.xlsx` | Executed — Excel with XLOOKUP formulas fetching emission factors by fuel/region; conditional formatting (red = Critical intensity, green = Low); landscape print-ready |
| **5. Executive Dashboard** | `05_powerbi_dashboard_spec.md` | Full Power BI spec: data model, DAX measures (Total Footprint, Net Zero Progress, High-Risk Count, Intensity), visual layout (KPIs + bubble map + supplier quadrant + drill-down), stakeholder use cases |

---

## KEY METRICS (From Executed Pipeline)

- **Facilities audited:** 50 (global: USA, Germany, India, China, Brazil, UK, Japan, Canada, Australia, Mexico)
- **Energy logs processed:** 80,000 (with dirty/estimated flags for audit transparency)
- **Logistics trips:** 15,000 (Road / Air / Sea / Rail)
- **Suppliers scored:** 100 (ESG 20–95 scale; intensity factors assigned)
- **Average emission intensity:** ~4,283 kg per $100k revenue (synthetic; demonstrates methodology)
- **Critical / High / Low / Medium rating distribution:** produced via NumPy `np.select()` logic

---

## CONSULTING DELIVERY FORMAT

- **Black-and-white design** (consistent with CV) — all charts, Excel, and spec use grayscale/black typography.
- **Impact quantification** — every output includes metrics (MTCO₂e totals, intensity ratios, supplier counts) framed for client recommendations.
- **Audit-ready documentation** — Excel workpaper mimics Big-4 audit deliverables (red-flag conditions, factor lookup, evidence traceability).
- **Executive communication** — Power BI spec designed for board-level review with geographic bubble maps and net-zero progress tracking.

---

## HOW TO USE IN INTERVIEW / PORTFOLIO

- **Portfolio path:** `/home/user/project_esg_carbon_audit/`
- **Quick demo:** Open `03_visualizations/` PNGs; show `scope1_2_trend.png` + `supplier_risk_quadrant.png`; open `04_carbon_accounting_workpaper.xlsx` to show conditional formatting and XLOOKUP formulas.
- **Consulting case answer:** Problem (global supply chain carbon risk) → Approach (5-step SQL → Python → Visual → Audit → Dashboard) → Evidence (trend deviation, critical facilities, supplier quadrant) → Recommendation (freeze high-risk contracts, renegotiate supplier terms, transition grid contracts).
- **CV insertion:** Project card already integrated into `Kuntal_Dakua_Consulting_CV.html` under **Projects** (second project entry, after Forensic Procurement Pipeline, also black-and-white, impact-quantified).

---

*Prepared separately from the first project. No file mixing. All outputs executable and reproducible.*
