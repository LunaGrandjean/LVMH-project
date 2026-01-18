# LVMH Supplier Risk Management Platform

LVMH Supplier Risk Management Platform is an interactive Streamlit web application that evaluates supplier risk by combining internal data with real-time, AI-enriched geopolitical and environmental context.

---

## Overview

This project provides a web-based dashboard for managing supplier risk in a luxury fashion context (LVMH-style ecosystem).
It combines a CSV-based supplier dataset with external intelligence (OpenAI) to produce composite risk scores and interactive visualizations.

Main features:

- Multi-factor supplier risk scoring (certifications, compliance, geopolitical, environmental, operational).
- Real-time contextual enrichment using OpenAI for each supplier location (country / city).
- Interactive dashboards: KPIs, distributions, country views, and supplier-level drill-down.

---

## Features

### Supplier Risk Model

- Composite risk score built from:
  - Certification risk (GOTS, GRS, RWS, ZDHC, WRAP, etc.).
  - Compliance risk with a geopolitical component by country.
  - Geopolitical risk (country-level).
  - Environmental / climate risk (location-level).
  - Operational and capacity risk (baseline in this version).
- Risk score normalized between 0 and 1 and mapped to:
  - Low, Medium, High, Critical.

### External Intelligence (OpenAI)

For each supplier (or country sample), the app calls the OpenAI API and retrieves structured JSON containing:

- geopolitical_factors: political / trade tensions, sanctions, regulations.
- geopolitical_score: geopolitical risk score [0–1].
- environmental_factors: climate risks, natural disasters, water stress, pollution.
- environmental_score: environmental risk score [0–1].
- climate_risk: Low / Moderate / High / Critical.
- supply_chain_disruption_risk: Low / Moderate / High / Critical.
- regulatory_changes: recent changes affecting textile / fashion supply chains.

Results are cached per (country, city) with st.session_state to reduce repeated calls.

### Pages and Dashboards

The app is organized into multiple pages using the Streamlit sidebar:

| Page | Description |
|------|-------------|
| Dashboard | Executive view with KPIs, risk distribution, top countries, and Top 5 highest-risk suppliers. |
| Supplier Directory | Filterable directory (risk level, country, category) with CSV export. |
| Supplier Details | Detailed supplier profile (info, certifications, risk, external intelligence). |
| Certification Tracker | Consolidated certification view and counts by type. |
| Risk Analysis | Portfolio analytics (average risk by country, distribution by level, size vs risk). |
| External Intelligence | Country-level panels with geopolitical and environmental narratives and scores. |
| Analytics | Portfolio statistics and detailed supplier list with CSV export. |

---

## Data Model

The app reads an input CSV (suppliers_full_data.csv) with lowercase column names and normalizes them to the internal schema used by the code.
Example CSV Header:
```
name,category,subcategory,certification_score,address,postal_code,city,country,certifications,employees,production_capacity,last_audit_date,audit_status,next_audit_date,grs_expiry,zdhc_expiry,gots_expiry,rwas_expiry,wrap_expiry,has_incidents,incident_type,geopolitical_risk,environmental_risk,compliance_risk
```

### Column Mapping (CSV to internal)

On load, the following columns are renamed:

- name → Name
- category → Supplier Category
- city → City
- country → Country
- certifications → Supplier certifications
- employees → Number of employees
- production_capacity → Production capacity
- address → Company address
- postal_code → Postal code


### Risk Engine Details

- Certification: derived from Supplier certifications by mapping each known certification (GOTS, GRS, RWS, ZDHC, WRAP) to a score and averaging.
- Compliance: base risk plus a country component from GEOPOLITICAL_RISK_BY_COUNTRY.
- Geopolitical / Environmental: either taken from OpenAI context or default fallback values.
- Final weighting:

  - 25%: certification
  - 20%: compliance
  - 20%: geopolitical
  - 20%: environmental
  - 10%: capacity utilization
  - 5%: operational

---

## Installation

### Prerequisites

- Python 3.10+
- A valid OpenAI API key (for external intelligence)
- git and virtualenv

### Setup

```bash
# Clone the repository
git clone https://github.com/LunaGrandjean/LVMH-project
cd LVMH-project

# Create and activate a virtual environment (optional)
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

## OpenAI API Configuration

The app reads the OpenAI API key from:

1. Streamlit secrets (recommended for deployment), or
2. Environment variable.

### Option 1: .streamlit/secrets.toml

Create:

```toml
OPENAI_API_KEY = "sk-..."
```

### Option 2: Environment Variable

```bash
export OPENAI_API_KEY="sk-..."
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
```

Without an API key:

- The app still runs, but
- External intelligence is disabled,
- Risk scores fall back to default baselines.

---

## Running the App

From the project root:

```bash
streamlit run app.py
```

---

## Usage Guide

### 1. Dashboard

- Global KPIs: total suppliers, number of countries, share of High/Critical risk suppliers.
- Charts:
  - Risk level distribution (pie).
  - Top 10 countries by number of suppliers.
- Top 5 Highest Risk Suppliers panel with color-coded risk.

### 2. Supplier Directory

- Filters:
  - Risk level (Low / Medium / High / Critical)
  - Country
  - Supplier category
- Interactive table + CSV export.

### 3. Supplier Details

- Select a supplier from the dropdown.
- View:
  - Country, city, headcount, category, address, capacity.
  - Certifications as badges.
  - External Intelligence block:
    - Geopolitical / environmental narratives
    - Numeric scores (progress bars)
    - Climate Risk and Supply Chain Disruption Risk labels.

### 4. Certification Tracker

- Consolidated view of certifications by type.
- Filter by certification (e.g. GOTS).
- Bar chart of certification counts by type.

### 5. Risk Analysis

- Bar chart: average risk score by country (Top 10).
- Boxplot: distribution of scores by risk level.
- Scatter plot: Number of employees vs Risk_Score to spot large high-risk suppliers.

### 6. External Intelligence

- Select one or more countries to analyze.
- For each country:
  - Geopolitical narrative + score
  - Environmental narrative + score
  - Climate Risk
  - Supply Chain Disruption Risk

### 7. Analytics

- Portfolio KPIs: total suppliers, number of countries, average employees.
- Distribution by supplier category and by country.
- Detailed supplier table with CSV export.

---

## Project Structure

```
.
├── app.py                     # Main Streamlit application
├── create-dataset.py          # Script to create CSV dataset
├── suppliers_full_data.csv    # Supplier dataset 
├── requirements.txt           # Python dependencies
└── .streamlit/
    └── secrets.toml           # OPENAI_API_KEY (optional)
```

---

## Dependencies

Key Python packages required:

- streamlit: Web application framework
- pandas: Data manipulation and analysis
- numpy: Numerical computing
- plotly: Interactive visualizations
- openai: OpenAI API client

---

## Possible Extensions

- Use geopolitical_risk, environmental_risk, compliance_risk columns as overrides when present in the CSV.
- Implement LVMH-specific compliance rules based on the Supplier Code of Conduct.
- Integrate external ESG scores or third-party audit platforms.
- Add alerting (email / Teams / Slack) when a supplier moves from Medium to High/Critical.
- Implement supplier audit scheduling and tracking.
- Add trend analysis over time for risk scores.
- Support for historical data and time-series risk tracking.

---


## Disclaimer

This project is an educational and prototype tool inspired by supplier risk management practices and is not an official LVMH product.
Risk scores and narratives are algorithmic and AI-generated and must not be used as the sole basis for real-world compliance or purchasing decisions.

---

## Authors
- Luna Grandjean -
- Sereine Tawamba -
- Santiago Pastrana -
- Daniel Perez Triana -

---


