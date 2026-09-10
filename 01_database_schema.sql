-- =====================================================================
-- PROJECT: Scope 1, 2 & 3 Carbon Emissions & ESG Compliance Audit Engine
-- TARGET: EY CCaSS / PwC ESG Consulting — Sustainability Advisory
-- SCOPE: Multi-facility global supply chain carbon footprint audit
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS esg_audit;

-- ------------------------------------------------------------------
-- 1. FACILITIES — global sites with regional grid/region context
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_audit.facilities (
    facility_id        SERIAL PRIMARY KEY,
    facility_name      VARCHAR(255) NOT NULL,
    country            VARCHAR(100),
    region             VARCHAR(100),  -- e.g., North America, EU-West, APAC
    facility_type      VARCHAR(50),   -- Manufacturing, Warehouse, Office, Data Center
    revenue_usd        NUMERIC(15,2), -- used for emission intensity denominator
    net_zero_target_year SMALLINT DEFAULT 2035,
    geo_lat            NUMERIC(9,6),
    geo_lon            NUMERIC(9,6)
);

-- ------------------------------------------------------------------
-- 2. ENERGY CONSUMPTION — messy multi-source logs
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_audit.energy_consumption (
    consumption_id     SERIAL PRIMARY KEY,
    facility_id        INT REFERENCES esg_audit.facilities(facility_id),
    log_date           DATE NOT NULL,
    energy_source      VARCHAR(50),   -- Electricity, Natural Gas, Diesel, Coal, Jet Fuel
    quantity_raw       NUMERIC(15,4), -- raw value (may be kWh, liters, gallons, miles)
    unit_raw           VARCHAR(20),   -- kWh, L, gal, miles, therms
    converted_kwh      NUMERIC(15,4), -- normalized
    converted_liters   NUMERIC(15,4),
    data_quality_flag  VARCHAR(20)    -- Clean / Dirty / Estimated / Missing
);

-- ------------------------------------------------------------------
-- 3. LOGISTICS TRIPS — Scope 3 upstream / downstream transport
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_audit.logistics_trips (
    trip_id            SERIAL PRIMARY KEY,
    facility_id        INT REFERENCES esg_audit.facilities(facility_id),
    supplier_id        INT REFERENCES esg_audit.suppliers(supplier_id),
    trip_date          DATE NOT NULL,
    mode               VARCHAR(30),   -- Road, Air, Sea, Rail
    distance_km        NUMERIC(10,2),
    weight_kg          NUMERIC(10,2),
    fuel_type          VARCHAR(30)
);

-- ------------------------------------------------------------------
-- 4. EMISSION FACTORS — EPA / DEFRA / GHG Protocol standards
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_audit.emission_factors (
    factor_id          SERIAL PRIMARY KEY,
    source_category    VARCHAR(50),   -- Fuel, Electricity Grid, Transport
    region             VARCHAR(100),
    fuel_or_source     VARCHAR(100),
    factor_kg_per_unit NUMERIC(10,6), -- kg CO2e per unit (kWh, L, km, etc.)
    standard_year      SMALLINT DEFAULT 2024,
    source_reference   VARCHAR(255)
);

-- ------------------------------------------------------------------
-- 5. SUPPLIERS — ESG-scored vendors with cost data
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS esg_audit.suppliers (
    supplier_id        SERIAL PRIMARY KEY,
    supplier_name      VARCHAR(255) NOT NULL,
    supplier_category  VARCHAR(100),  -- Raw Material, Logistics, Packaging, Services
    country            VARCHAR(100),
    contract_cost_usd  NUMERIC(15,2),
    esg_score          NUMERIC(5,2),  -- 0-100 (higher = better sustainability)
    scope_3_intensity_kg_per_usd NUMERIC(15,6) DEFAULT 0,
    decarbonization_target_year SMALLINT DEFAULT 2030
);

-- ------------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_energy_facility ON esg_audit.energy_consumption(facility_id, log_date);
CREATE INDEX IF NOT EXISTS idx_energy_source ON esg_audit.energy_consumption(energy_source);
CREATE INDEX IF NOT EXISTS idx_logistics_facility ON esg_audit.logistics_trips(facility_id, trip_date);
CREATE INDEX IF NOT EXISTS idx_logistics_mode ON esg_audit.logistics_trips(mode);
CREATE INDEX IF NOT EXISTS idx_factors_region_source ON esg_audit.emission_factors(region, fuel_or_source);
CREATE INDEX IF NOT EXISTS idx_suppliers_category ON esg_audit.suppliers(supplier_category);

-- ------------------------------------------------------------------
-- 6. CTE CALCULATION ENGINE — Scope 1 / Scope 2 / Scope 3
-- ------------------------------------------------------------------
CREATE OR REPLACE VIEW esg_audit.vw_scope_emissions AS
WITH energy_converted AS (
    SELECT
        ec.facility_id,
        ec.log_date,
        ec.energy_source,
        -- Normalize to common units for calculation
        CASE
            WHEN ec.unit_raw IN ('L','l','liters','litres') THEN ec.quantity_raw
            WHEN ec.unit_raw IN ('gal','gallons') THEN ec.quantity_raw * 3.78541
            WHEN ec.unit_raw IN ('kWh','kwh') THEN ec.quantity_raw / 1000.0  -- MWh
            ELSE ec.quantity_raw
        END AS normalized_quantity,
        ec.data_quality_flag
    FROM esg_audit.energy_consumption ec
),
scope1_direct AS (
    -- Direct fuel combustion (diesel, natural gas, coal, jet fuel) = Scope 1
    SELECT
        ec.facility_id,
        ec.log_date,
        SUM(ec.normalized_quantity * ef.factor_kg_per_unit) / 1000.0 AS scope1_mtco2e
    FROM energy_converted ec
    JOIN esg_audit.emission_factors ef
        ON ec.energy_source = ef.fuel_or_source
        AND ef.source_category = 'Fuel'
        AND ef.region = (SELECT region FROM esg_audit.facilities f WHERE f.facility_id = ec.facility_id)
    WHERE ec.energy_source IN ('Diesel','Natural Gas','Coal','Jet Fuel')
    GROUP BY ec.facility_id, ec.log_date
),
scope2_electricity AS (
    -- Electricity = Scope 2 (purchased grid power)
    SELECT
        ec.facility_id,
        ec.log_date,
        SUM(ec.normalized_quantity * ef.factor_kg_per_unit) / 1000.0 AS scope2_mtco2e
    FROM energy_converted ec
    JOIN esg_audit.emission_factors ef
        ON ec.energy_source = ef.fuel_or_source
        AND ef.source_category = 'Electricity Grid'
        AND ef.region = (SELECT region FROM esg_audit.facilities f WHERE f.facility_id = ec.facility_id)
    WHERE ec.energy_source = 'Electricity'
    GROUP BY ec.facility_id, ec.log_date
),
scope3_transport AS (
    -- Logistics / transport = Scope 3 upstream/downstream
    SELECT
        lt.facility_id,
        lt.trip_date AS log_date,
        SUM(lt.distance_km * ef.factor_kg_per_unit) / 1000.0 AS scope3_transport_mtco2e
    FROM esg_audit.logistics_trips lt
    JOIN esg_audit.emission_factors ef
        ON lt.mode = ef.fuel_or_source  -- simplified mapping; real-world uses mode-factor table
        AND ef.source_category = 'Transport'
    GROUP BY lt.facility_id, lt.trip_date
),
scope3_suppliers AS (
    -- Supply chain intensity based on supplier cost * intensity factor
    SELECT
        lt.facility_id,
        lt.trip_date AS log_date,
        SUM(s.contract_cost_usd * s.scope_3_intensity_kg_per_usd) / 1000.0 AS scope3_supplier_mtco2e
    FROM esg_audit.logistics_trips lt
    JOIN esg_audit.suppliers s ON lt.supplier_id = s.supplier_id
    GROUP BY lt.facility_id, lt.trip_date
)
SELECT
    COALESCE(s1.facility_id, s2.facility_id, s3.facility_id, s4.facility_id) AS facility_id,
    COALESCE(s1.log_date, s2.log_date, s3.log_date, s4.log_date) AS log_date,
    COALESCE(s1.scope1_mtco2e, 0) AS scope1_mtco2e,
    COALESCE(s2.scope2_mtco2e, 0) AS scope2_mtco2e,
    COALESCE(s3.scope3_transport_mtco2e, 0) + COALESCE(s4.scope3_supplier_mtco2e, 0) AS scope3_mtco2e,
    COALESCE(s1.scope1_mtco2e, 0) + COALESCE(s2.scope2_mtco2e, 0) + COALESCE(s3.scope3_transport_mtco2e, 0) + COALESCE(s4.scope3_supplier_mtco2e, 0) AS total_mtco2e
FROM scope1_direct s1
FULL OUTER JOIN scope2_electricity s2 ON s1.facility_id = s2.facility_id AND s1.log_date = s2.log_date
FULL OUTER JOIN scope3_transport s3 ON s1.facility_id = s3.facility_id AND s1.log_date = s3.log_date
FULL OUTER JOIN scope3_suppliers s4 ON s1.facility_id = s4.facility_id AND s1.log_date = s4.log_date;

COMMENT ON VIEW esg_audit.vw_scope_emissions IS
'ESG Consulting deliverable — Scope 1/2/3 carbon calculation engine with region-specific emission factors (EPA/DEFRA).';

-- ------------------------------------------------------------------
-- 7. ESG RISK RATING VIEW — NumPy-style conditional logic in SQL
-- ------------------------------------------------------------------
CREATE OR REPLACE VIEW esg_audit.vw_esg_risk_ratings AS
SELECT
    f.facility_id,
    f.facility_name,
    f.country,
    f.revenue_usd,
    e.total_mtco2e,
    CASE
        WHEN f.revenue_usd > 0 THEN (COALESCE(e.total_mtco2e, 0) / f.revenue_usd) * 1000000
        ELSE NULL
    END AS emission_intensity_kg_per_usd,
    CASE
        WHEN f.revenue_usd > 0 AND (COALESCE(e.total_mtco2e, 0) / f.revenue_usd) < 0.05 THEN 'Low'
        WHEN f.revenue_usd > 0 AND (COALESCE(e.total_mtco2e, 0) / f.revenue_usd) < 0.15 THEN 'Medium'
        WHEN f.revenue_usd > 0 AND (COALESCE(e.total_mtco2e, 0) / f.revenue_usd) < 0.30 THEN 'High'
        ELSE 'Critical'
    END AS esg_risk_rating
FROM esg_audit.facilities f
LEFT JOIN esg_audit.vw_scope_emissions e
    ON f.facility_id = e.facility_id
    AND e.log_date = CURRENT_DATE;  -- latest snapshot for consulting review
