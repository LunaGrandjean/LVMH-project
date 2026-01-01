# LVMH Supplier Risk Management Platform

A comprehensive data-driven solution for managing, tracking, and assessing risk across LVMH's global supplier network in the fashion and ready-to-wear sector.

## Project Overview

This project addresses LVMH's critical business challenge of centralizing supplier data, monitoring certifications, assessing multi-factor risks, and managing supplier compliance across the supply chain.

The platform consists of:
- **Phase 1**: Executive dashboard with real-time risk assessment (Production-Ready)
- **Phase 2**: Data collection and management portal for real supplier information (Ready to Deploy)

## Key Problem Solved

Suppliers provide a wide range of information that varies in format, quality, and completeness. Certifications and documents have expiration dates requiring continuous monitoring. Supplier data is often stored across multiple systems, making it difficult to maintain a unified and real-time view of supplier status. This platform centralizes all supplier data and continuously monitors critical compliance metrics.

## Architecture

### Dual Application System

The platform consists of two complementary Streamlit applications:

**Application 1: Dashboard (app.py)**
- Executive overview and analytics
- Real-time risk scoring and alerts
- Certification expiry tracking
- Supplier filtering and search
- CSV data export

**Application 2: Data Collection Portal (data_collection.py)**
- Certification date management
- Audit scheduling and results tracking
- Incident reporting system
- Bulk data upload capability
- Complete activity logging

Both applications share a single data source (`suppliers_full_data.csv`), ensuring data consistency and real-time synchronization.

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone or download the repository
cd lvmh-supplier-risk-management

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

Open two terminal windows:

**Terminal 1 - Dashboard**
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

**Terminal 2 - Data Collection**
```bash
streamlit run data_collection.py
# Opens at http://localhost:8502
```

Both applications will run simultaneously and share the same data file.

## Phase 1: Dashboard Application

### Features

**1. Dashboard Page**
- Real-time key performance indicators (total suppliers, high-risk count, expiring certifications, incidents)
- Risk distribution visualization
- Geographic supplier distribution
- Critical alerts feed
- Top 5 highest risk suppliers

**2. Supplier Directory**
- Browse all 20 suppliers with complete information
- Multi-criteria filtering (risk level, country, audit status)
- Sortable by risk score
- Quick overview of supplier details

**3. Supplier Details**
- Complete supplier profile and company information
- Full certification tracking with expiry dates
- Audit history and next scheduled audit
- Risk factor breakdown (geopolitical, environmental, compliance)
- Incident history

**4. Certification Tracker**
- Timeline view of all certifications across supplier network
- Critical alerts for certifications expiring within 30 days
- Compliant certifications view (valid for 90+ days)
- Days-to-expiry calculations
- Recommended actions for expiring certifications

**5. Risk Assessment**
- Risk score distribution histogram
- Risk factors heatmap by risk level
- Country-level risk analysis and comparison
- Critical supplier identification and details

**6. Analytics & Reporting**
- Portfolio statistics (total suppliers, countries, average risk score)
- Supplier distribution by supply chain category
- Risk vs. supplier size scatter plot
- CSV export functionality for Excel integration

### Risk Scoring Algorithm

The platform implements a weighted multi-factor risk assessment model:

**Overall Risk Score = (Certification Risk × 0.25) + (Audit Risk × 0.20) + (Geopolitical Risk × 0.20) + (Environmental Risk × 0.15) + (Incident Risk × 0.15)**

**Risk Factor Definitions:**

1. **Certification Expiry Risk (25% weight)**
   - Expired: 3.0
   - Expires in <30 days: 2.5
   - Expires in <90 days: 2.0
   - Expires in <180 days: 1.5
   - Valid >180 days: 0.5
   - Missing certifications: 2.0

2. **Audit Status Risk (20% weight)**
   - Passed: 0.5
   - Pending: 1.5
   - Failed: 3.0

3. **Geopolitical Risk (20% weight)**
   - Low: 0.5
   - Medium: 1.5
   - High: 2.5

4. **Environmental Risk (15% weight)**
   - Low: 0.5
   - Medium: 1.5
   - High: 2.5

5. **Incident Risk (15% weight)**
   - No incidents: 0.5
   - Has incidents: 2.5

**Risk Level Classification:**
- Low: 0.0 - 1.5
- Medium: 1.5 - 2.0
- High: 2.0 - 2.5
- Critical: 2.5+

## Phase 2: Data Collection Portal

### Features

**1. Certification Updates**
- Manual entry of certification expiry dates
- Support for 5 certification types (GRS, ZDHC, GOTS, RWS, WRAP GOLD)
- Optional issue date tracking
- Certificate file upload (PDF, JPG, PNG)
- Notes and comments field
- Real-time CSV update

**2. Audit Scheduling**
- Record audit dates and results
- Support for multiple audit types (Certification, Quality, Compliance, Re-Audit, Surprise)
- Track auditor information
- Schedule next audit date
- Document corrective actions for failed audits
- Detailed findings and observations

**3. Incident Reporting**
- Document supplier incidents and controversies
- 9 incident types (Labor, Environmental, Quality, Safety, Sanction, Bankruptcy, Media, Regulatory, Other)
- Severity classification (Low, Medium, High, Critical)
- Source tracking with optional URL reference
- Status management (Open, Under Investigation, Resolved, Monitoring)
- Resolution documentation

**4. Bulk Upload**
- CSV file import for batch updates
- Support for updating certifications, audits, and incidents simultaneously
- Validation before processing
- Preview of data before import
- Complete activity logging

**5. Data History**
- View all changes made to supplier data
- Filter by action type, supplier, and time period
- Complete timestamps for all updates
- Full details of each change
- Compliance-ready audit trail

### Activity Logging

All changes are automatically logged to `data_log.jsonl` with:
- Timestamp of change
- Type of action performed
- Affected supplier
- Complete details of what changed
- User-provided notes and context

## Data Structure

### Supplier Dataset (suppliers_full_data.csv)

The platform manages 20 suppliers with 24 data fields:

**Basic Information:**
- Supplier name, address, city, country
- Supply chain category and subcategories
- Number of employees
- Production capacity

**Certification Data:**
- Types held (GRS, ZDHC, GOTS, RWS, WRAP GOLD)
- Expiry dates for each certification
- Certification score (0-5 legacy field)

**Audit Data:**
- Last audit date and status (Passed/Pending/Failed)
- Next scheduled audit date

**Risk Indicators:**
- Geopolitical risk level (Low/Medium/High)
- Environmental risk level (Low/Medium/High)
- Compliance risk level (Low/Medium/High)
- Incident flag and incident type

**Calculated Fields (Auto-updated):**
- Overall risk score
- Risk level classification
- Days to nearest certification expiry

## Current Dataset

The platform comes with initial data for 20 suppliers:

**Geographic Coverage:**
- Italy: 6 suppliers (30%)
- China: 3 suppliers (15%)
- Other EU countries: 6 suppliers (30%)
- Rest of world: 5 suppliers (25%)
- 11 unique countries total

**Supply Chain Coverage:**
- Raw material extraction (breeding, harvesting, preparation, tanning)
- Material transformation (spinning, dyeing, weaving, knitting, non-woven processing)
- Manufacturing (ready-to-wear, shoes, trims/buttons, laundry, vulcanization)

**Certification Coverage:**
- GRS: 45% of suppliers
- ZDHC: 40% of suppliers
- GOTS: 35% of suppliers
- WRAP GOLD: 20% of suppliers
- RWS: 15% of suppliers

## Development Status

### Phase 1: Complete (Production-Ready)
- Dashboard with 6 pages and all features
- Risk scoring algorithm implemented
- Data loading and caching
- Interactive Plotly visualizations
- Comprehensive documentation
- All features tested and working

### Phase 2: Complete (Ready to Deploy)
- Data collection portal with 5 modes
- Certification management system
- Audit tracking system
- Incident reporting system
- Bulk import capability
- Activity logging system
- All features tested and working

### Phase 3: Planned (Future Development)
- Machine learning-based risk prediction
- Financial stability scoring
- Geopolitical risk index integration
- Water stress and environmental assessment
- ESG performance metrics
- Real-time incident detection
- Advanced risk analytics

### Phase 4: Planned (Future Development)
- Automated mitigation recommendations
- Supplier diversification analysis
- Corrective action plan tracking
- Risk-based supplier prioritization

### Phase 5: Planned (Future Development)
- Multi-user access control
- Admin dashboard
- Real-time alert system
- Cloud deployment
- API integration

## File Structure

```
project/
├── app.py                      # Main dashboard application (500+ lines)
├── data_collection.py          # Data entry portal (600+ lines)
├── suppliers_full_data.csv     # Supplier dataset (20 records, 24 fields)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
```

## Dependencies
- **streamlit** (1.32.0) - Web application framework
- **pandas** (2.1.3) - Data manipulation and analysis
- **plotly** (5.18.0) - Interactive visualization
- **numpy** (1.26.2) - Numerical operations
- **python-dateutil** (2.8.2) - Date handling

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Modifying Risk Thresholds

Edit the `calculate_overall_risk()` function in `app.py` to adjust:
- Certification expiry alert threshold (currently 30 days)
- Risk factor weights (currently 25%, 20%, 20%, 15%, 15%)
- Risk level classification boundaries

### Customizing Certification Types

To add a new certification type:
1. Add column to `suppliers_full_data.csv` (e.g., `iso_expiry`)
2. Update certification column mappings in `data_collection.py`
3. Add to dropdown options in data entry forms

### Changing Risk Factors

To modify geopolitical or environmental risk levels:
1. Update risk factor mapping in `calculate_overall_risk()` function
2. Adjust weights if needed
3. Recalculate risk scores (automatic on dashboard reload)

## Usage Examples

### Finding Expiring Certifications
1. Open Dashboard (app.py)
2. Go to "Certification Tracker" page
3. Switch to "Critical (<30 days)" tab
4. See all suppliers needing urgent action

### Recording a New Audit
1. Open Data Collection portal (data_collection.py)
2. Select "Audit Scheduling" mode
3. Choose supplier and audit type
4. Enter audit date and result
5. Click "Save Audit Record"
6. Check Dashboard immediately for updated data

### Bulk Importing Supplier Data
1. Prepare CSV with columns: supplier_name, cert_type, expiry_date, etc.
2. Open Data Collection portal
3. Go to "Bulk Upload" mode
4. Upload CSV file
5. Review preview and validation
6. Click "Process Upload"

### Viewing Change History
1. Open Data Collection portal
2. Select "Data History" mode
3. Filter by action type, supplier, or date range
4. Click on any entry to see full details
5. Export for compliance records

## Best Practices

### Data Entry
- Use official certification documents as source
- Verify supplier names exactly match database
- Record audit dates when they occur
- Document incidents promptly with source information
- Schedule next audits during current audit process

### Regular Maintenance
- Review dashboard daily for critical alerts
- Update certification dates before expiration (at least 30 days in advance)
- Process bulk audit updates quarterly
- Archive activity logs monthly
- Backup suppliers_full_data.csv weekly

### Risk Assessment
- Investigate high-risk suppliers immediately
- Verify geopolitical and environmental factors regularly
- Update incident flags when issues resolve
- Consider supplier diversification for critical materials
- Use risk scores to prioritize audit scheduling

## Data Privacy and Security

- All data stored locally in CSV format
- No cloud uploads or external API calls
- Compatible with corporate firewalls
- Activity log provides compliance audit trail
- Ready for enterprise deployment

## Integration with External Systems

### Phase 3 Planned Integrations
- World Bank geopolitical risk indices
- Environmental performance databases
- Financial credit rating services
- News and incident detection APIs
- ESG performance databases

### Current Integration
- Single CSV data source
- Easy Excel import/export
- Compatible with SQL databases (Phase 3)
