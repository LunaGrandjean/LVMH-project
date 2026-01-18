import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import requests
from functools import lru_cache
import hashlib

# Set page config
st.set_page_config(
    page_title="LVMH Supplier Risk Management",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for caching and user preferences
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None
if 'external_context_cache' not in st.session_state:
    st.session_state.external_context_cache = {}
if 'risk_scores_cache' not in st.session_state:
    st.session_state.risk_scores_cache = None

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
DATA_FILE = "suppliers_full_data.csv"

# Risk scoring weights
RISK_WEIGHTS = {
    'certification': 0.25,
    'geopolitical': 0.20,
    'environmental': 0.20,
    'compliance': 0.20,
    'capacity_utilization': 0.10,
    'operational': 0.05
}

GEOPOLITICAL_RISK_BY_COUNTRY = {
    'CN': 0.65, 'IN': 0.55, 'BD': 0.70, 'VN': 0.50, 'ID': 0.45,
    'PK': 0.75, 'TH': 0.40, 'MM': 0.80, 'KH': 0.65, 'LA': 0.60,
    'KR': 0.25, 'JP': 0.15, 'TW': 0.45, 'IT': 0.30, 'PT': 0.25,
    'ES': 0.30, 'FR': 0.20, 'DE': 0.15, 'UK': 0.25, 'TR': 0.55,
    'BR': 0.50, 'MX': 0.45, 'CL': 0.20, 'AU': 0.10, 'GR': 0.35,
    'BG': 0.40, 'RO': 0.38, 'CZ': 0.20, 'PL': 0.35, 'HU': 0.25
}

# ============================================================================
# OPENAI INTEGRATION FOR EXTERNAL CONTEXT
# ============================================================================

def get_external_context(country, city, supplier_name, production_category):
    """
    Use OpenAI to collect environmental and geopolitical context for a supplier location.
    """
    cache_key = f"{country}_{city}".lower()
    
    if cache_key in st.session_state.external_context_cache:
        return st.session_state.external_context_cache[cache_key]
    
    if not OPENAI_API_KEY:
        st.warning("OpenAI API key not configured. Using baseline risk assessment only.")
        return {
            'geopolitical_factors': 'No external data available',
            'environmental_factors': 'No external data available',
            'geopolitical_score': float(GEOPOLITICAL_RISK_BY_COUNTRY.get(country, 0.50)),
            'environmental_score': 0.50,
            'climate_risk': 'Moderate',
            'supply_chain_disruption_risk': 'Moderate'
        }
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""You are a supply chain risk analyst for LVMH. 
        
Analyze the following supplier location and provide a JSON response with:
1. geopolitical_factors: Current political/trade tensions, sanctions, regulations affecting {country}
2. geopolitical_score: 0-1 risk score (0=safe, 1=critical risk)
3. environmental_factors: Climate risks, natural disasters, water scarcity, pollution issues in {city}, {country}
4. environmental_score: 0-1 risk score (0=safe, 1=critical risk)
5. climate_risk: Brief assessment (Low/Moderate/High/Critical)
6. supply_chain_disruption_risk: Brief assessment (Low/Moderate/High/Critical)
7. regulatory_changes: Any recent regulatory changes affecting textile/fashion supply chain

Supplier Details:
- Name: {supplier_name}
- Location: {city}, {country}
- Category: {production_category}

Focus on factual, recent information as of January 2026. Respond with valid JSON only, no markdown."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a supply chain risk analyst. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content
        
        # Parse JSON response
        try:
            context_data = json.loads(response_text)
            # Ensure scores are floats
            context_data['geopolitical_score'] = float(context_data.get('geopolitical_score', 0.50))
            context_data['environmental_score'] = float(context_data.get('environmental_score', 0.50))
        except (json.JSONDecodeError, ValueError):
            context_data = {
                'geopolitical_factors': response_text[:200],
                'environmental_factors': response_text[200:400] if len(response_text) > 200 else 'N/A',
                'geopolitical_score': float(GEOPOLITICAL_RISK_BY_COUNTRY.get(country, 0.50)),
                'environmental_score': 0.50,
                'climate_risk': 'Moderate',
                'supply_chain_disruption_risk': 'Moderate'
            }
        
        st.session_state.external_context_cache[cache_key] = context_data
        return context_data
        
    except Exception as e:
        st.error(f"Error fetching external context: {str(e)}")
        return {
            'geopolitical_factors': f'Error: {str(e)}',
            'environmental_factors': 'Unable to fetch',
            'geopolitical_score': float(GEOPOLITICAL_RISK_BY_COUNTRY.get(country, 0.50)),
            'environmental_score': 0.50,
            'climate_risk': 'Moderate',
            'supply_chain_disruption_risk': 'Moderate'
        }

# ============================================================================
# DATA LOADING AND PROCESSING
# ============================================================================

@st.cache_data
def load_supplier_data():
    """Load supplier data from CSV."""
    if not os.path.exists(DATA_FILE):
        st.error(f"Data file '{DATA_FILE}' not found. Please ensure it exists in the project directory.")
        return pd.DataFrame()
    
    df = pd.read_csv(DATA_FILE)
    
    column_mapping = {
        'name': 'Name',
        'category': 'Supplier Category',
        'city': 'City',
        'country': 'Country',
        'certifications': 'Supplier certifications',
        'employees': 'Number of employees',
        'production_capacity': 'Production capacity',
        'address': 'Company address',
        'postal_code': 'Postal code'
    }
    
    df = df.rename(columns=column_mapping)
    
    return df

def calculate_certification_score(cert_string):
    """Calculate certification score from certification string."""
    if pd.isna(cert_string) or cert_string == '':
        return 0.0
    
    certs = str(cert_string).split(',')
    cert_map = {'GOTS': 0.90, 'GRS': 0.85, 'RWS': 0.88, 'ZDHC': 0.82, 'WRAP': 0.80}
    
    scores = [cert_map.get(c.strip(), 0.70) for c in certs if c.strip()]
    return np.mean(scores) if scores else 0.0

def calculate_compliance_risk(supplier_data):
    """Calculate compliance risk based on various factors."""
    base_risk = 0.3
    
    if pd.notna(supplier_data.get('Country')):
        country_risk = GEOPOLITICAL_RISK_BY_COUNTRY.get(supplier_data.get('Country'), 0.50)
        base_risk += country_risk * 0.3
    
    return min(base_risk, 1.0)

def calculate_overall_risk_score(supplier_row, external_context=None):
    """
    Calculate overall risk score using multi-factor approach with external context.
    """
    
    # Certification Score (inverse: higher cert = lower risk)
    cert_score = calculate_certification_score(supplier_row.get('Supplier certifications', ''))
    certification_risk = 1.0 - cert_score
    
    # Compliance Risk
    compliance_risk = calculate_compliance_risk(supplier_row)
    
    # Geopolitical Risk
    if external_context and 'geopolitical_score' in external_context:
        geo_risk = float(external_context['geopolitical_score'])
    else:
        country = supplier_row.get('Country', 'XX')
        geo_risk = float(GEOPOLITICAL_RISK_BY_COUNTRY.get(country, 0.50))
    
    # Environmental Risk
    if external_context and 'environmental_score' in external_context:
        env_risk = float(external_context['environmental_score'])
    else:
        env_risk = 0.50
    
    # Operational Risk based on capacity utilization
    operational_risk = 0.2
    
    # Capacity Utilization Risk
    capacity_risk = 0.3
    
    # Ensure all values are floats
    geo_risk = float(geo_risk)
    env_risk = float(env_risk)
    operational_risk = float(operational_risk)
    capacity_risk = float(capacity_risk)
    certification_risk = float(certification_risk)
    compliance_risk = float(compliance_risk)
    
    # Weighted Risk Score
    overall_risk = (
        RISK_WEIGHTS['certification'] * certification_risk +
        RISK_WEIGHTS['compliance'] * compliance_risk +
        RISK_WEIGHTS['geopolitical'] * geo_risk +
        RISK_WEIGHTS['environmental'] * env_risk +
        RISK_WEIGHTS['operational'] * operational_risk +
        RISK_WEIGHTS['capacity_utilization'] * capacity_risk
    )
    
    return min(float(overall_risk), 1.0)

def get_risk_level(score):
    """Convert risk score to risk level."""
    score = float(score)
    if score < 0.25:
        return "Low"
    elif score < 0.50:
        return "Medium"
    elif score < 0.75:
        return "High"
    else:
        return "Critical"

def get_risk_color(level):
    """Return color for risk level."""
    colors = {
        "Low": "#2ECC71",
        "Medium": "#F39C12",
        "High": "#E74C3C",
        "Critical": "#8B0000"
    }
    return colors.get(level, "#95A5A6")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.markdown("""
    <style>
    .main { padding: 2rem; }
    .metric-card { 
        background-color: #f0f2f6; 
        padding: 1.5rem; 
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .risk-critical { color: #8B0000; font-weight: bold; }
    .risk-high { color: #E74C3C; font-weight: bold; }
    .risk-medium { color: #F39C12; font-weight: bold; }
    .risk-low { color: #2ECC71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 LVMH Supplier Risk Management Platform")
    st.markdown("**Real-time risk assessment with environmental & geopolitical intelligence**")
    
    # Load data
    df = load_supplier_data()
    
    if df.empty:
        st.error("No supplier data available.")
        return
    
    # Sidebar navigation
    st.sidebar.markdown("### Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Supplier Directory", "Supplier Details", "Certification Tracker", 
         "Risk Analysis", "External Intelligence", "Analytics"]
    )
    
    if page == "Dashboard":
        show_dashboard(df)
    elif page == "Supplier Directory":
        show_supplier_directory(df)
    elif page == "Supplier Details":
        show_supplier_details(df)
    elif page == "Certification Tracker":
        show_certification_tracker(df)
    elif page == "Risk Analysis":
        show_risk_analysis(df)
    elif page == "External Intelligence":
        show_external_intelligence(df)
    elif page == "Analytics":
        show_analytics(df)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def show_dashboard(df):
    st.header("Executive Dashboard")
    
    # Calculate overall metrics with external context
    with st.spinner("Calculating risk metrics with real-time data..."):
        risk_scores = []
        external_contexts = []
        for idx, row in df.iterrows():
            ext_context = get_external_context(
                row.get('Country', 'XX'),
                row.get('City', 'Unknown'),
                row.get('Name', 'Unknown'),
                row.get('Supplier Category', 'Unknown')
            )
            external_contexts.append(ext_context)
            risk_score = calculate_overall_risk_score(row, ext_context)
            risk_scores.append(risk_score)
        
        df['Risk_Score'] = risk_scores
        df['Risk_Level'] = df['Risk_Score'].apply(get_risk_level)
        df['External_Context'] = external_contexts
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Suppliers", len(df))
    
    with col2:
        high_risk = len(df[df['Risk_Level'].isin(['High', 'Critical'])])
        st.metric("High/Critical Risk", high_risk, f"{high_risk/len(df)*100:.1f}%")
    
    with col3:
        low_risk = len(df[df['Risk_Level'] == 'Low'])
        st.metric("Low Risk", low_risk, f"{low_risk/len(df)*100:.1f}%")
    
    with col4:
        countries = df['Country'].nunique()
        st.metric("Countries", countries)
    
    st.markdown("---")
    
    # Risk Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        risk_dist = df['Risk_Level'].value_counts()
        colors_map = {level: get_risk_color(level) for level in risk_dist.index}
        
        fig = go.Figure(data=[
            go.Pie(
                labels=risk_dist.index,
                values=risk_dist.values,
                marker=dict(colors=[colors_map[level] for level in risk_dist.index])
            )
        ])
        fig.update_layout(title="Risk Distribution", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        country_dist = df['Country'].value_counts().head(10)
        fig = px.bar(
            x=country_dist.values,
            y=country_dist.index,
            orientation='h',
            title="Top 10 Suppliers by Country",
            labels={'x': 'Count', 'y': 'Country'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Top 5 Highest Risk Suppliers")
    
    top_risk = df.nlargest(5, 'Risk_Score')[['Name', 'Country', 'City', 'Risk_Score', 'Risk_Level']]
    
    for idx, supplier in top_risk.iterrows():
        risk_color = get_risk_color(supplier['Risk_Level'])
        st.markdown(f"""
        **{supplier['Name']}** | {supplier['City']}, {supplier['Country']}
        - Risk Score: <span style="color:{risk_color}; font-weight:bold;">{supplier['Risk_Score']:.2f}</span> ({supplier['Risk_Level']})
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE: SUPPLIER DIRECTORY
# ============================================================================

def show_supplier_directory(df):
    st.header("Supplier Directory")
    
    # Calculate risk scores if not already done
    if 'Risk_Score' not in df.columns:
        with st.spinner("Calculating risk metrics..."):
            risk_scores = []
            external_contexts = []
            for idx, row in df.iterrows():
                ext_context = get_external_context(
                    row.get('Country', 'XX'),
                    row.get('City', 'Unknown'),
                    row.get('Name', 'Unknown'),
                    row.get('Supplier Category', 'Unknown')
                )
                external_contexts.append(ext_context)
                risk_score = calculate_overall_risk_score(row, ext_context)
                risk_scores.append(risk_score)
            
            df['Risk_Score'] = risk_scores
            df['Risk_Level'] = df['Risk_Score'].apply(get_risk_level)
            df['External_Context'] = external_contexts
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.multiselect(
            "Filter by Risk Level",
            ["Low", "Medium", "High", "Critical"],
            default=["Low", "Medium", "High", "Critical"]
        )
    
    with col2:
        countries = sorted(df['Country'].unique())
        country_filter = st.multiselect(
            "Filter by Country",
            countries,
            default=countries[:5] if len(countries) > 5 else countries
        )
    
    with col3:
        categories = sorted(df['Supplier Category'].unique())
        category_filter = st.multiselect(
            "Filter by Category",
            categories,
            default=categories if len(categories) <= 3 else categories[:3]
        )
    
    # Apply filters
    filtered_df = df[
        (df['Risk_Level'].isin(risk_filter)) &
        (df['Country'].isin(country_filter)) &
        (df['Supplier Category'].isin(category_filter))
    ]
    
    # Display table
    st.subheader(f"Filtered Suppliers ({len(filtered_df)} / {len(df)})")
    
    display_df = filtered_df[[
        'Name', 'Country', 'City', 'Supplier Category', 'Number of employees', 'Risk_Score', 'Risk_Level'
    ]].copy()
    
    display_df['Risk_Score'] = display_df['Risk_Score'].round(3)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Export option
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"suppliers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ============================================================================
# PAGE: SUPPLIER DETAILS
# ============================================================================

def show_supplier_details(df):
    st.header("Supplier Details")
    
    supplier_name = st.selectbox("Select Supplier", df['Name'].sort_values().unique())
    
    supplier = df[df['Name'] == supplier_name].iloc[0]
    
    # Get external context
    with st.spinner("Fetching external intelligence..."):
        ext_context = get_external_context(
            supplier.get('Country', 'XX'),
            supplier.get('City', 'Unknown'),
            supplier_name,
            supplier.get('Supplier Category', 'Unknown')
        )
    
    # Calculate risk
    risk_score = calculate_overall_risk_score(supplier, ext_context)
    risk_level = get_risk_level(risk_score)
    risk_color = get_risk_color(risk_level)
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Risk Level**: <span style='color:{risk_color}; font-size:20px; font-weight:bold;'>{risk_level}</span>", 
                   unsafe_allow_html=True)
        st.markdown(f"**Risk Score**: {risk_score:.3f}")
    
    with col2:
        st.markdown(f"**Country**: {supplier.get('Country', 'N/A')}")
        st.markdown(f"**City**: {supplier.get('City', 'N/A')}")
    
    with col3:
        st.markdown(f"**Employees**: {supplier.get('Number of employees', 'N/A')}")
        st.markdown(f"**Category**: {supplier.get('Supplier Category', 'N/A')}")
    
    st.markdown("---")
    
    # Company Information
    st.subheader("Company Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Address**: {supplier.get('Company address', 'N/A')}")
        st.markdown(f"**Postal Code**: {supplier.get('Postal code', 'N/A')}")
    with col2:
        st.markdown(f"**Production Capacity**: {supplier.get('Production capacity', 'N/A')}")
        st.markdown(f"**Category**: {supplier.get('Supplier Category', 'N/A')}")
    
    st.markdown("---")
    
    # Certifications
    st.subheader("Certifications")
    
    certs = str(supplier.get('Supplier certifications', '')).split(',') if supplier.get('Supplier certifications') else []
    
    if certs and certs[0] != '':
        col1, col2, col3 = st.columns(3)
        for i, cert in enumerate(certs):
            with [col1, col2, col3][i % 3]:
                st.markdown(f"✓ {cert.strip()}")
    else:
        st.info("No certifications recorded")
    
    st.markdown("---")
    
    # External Intelligence - DISPLAYED PROPERLY
    st.subheader("External Intelligence (Real-time Data from OpenAI)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Geopolitical Assessment**")
        st.info(ext_context.get('geopolitical_factors', 'No data'))
        geo_score = float(ext_context.get('geopolitical_score', 0.5))
        st.markdown(f"**Risk Score**: {geo_score:.2f} / 1.0")
        st.progress(geo_score, f"Geopolitical Risk Level: {geo_score:.1%}")
    
    with col2:
        st.markdown("**Environmental Assessment**")
        st.warning(ext_context.get('environmental_factors', 'No data'))
        env_score = float(ext_context.get('environmental_score', 0.5))
        st.markdown(f"**Risk Score**: {env_score:.2f} / 1.0")
        st.progress(env_score, f"Environmental Risk Level: {env_score:.1%}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Climate Risk**: {ext_context.get('climate_risk', 'N/A')}")
    with col2:
        st.markdown(f"**Supply Chain Disruption Risk**: {ext_context.get('supply_chain_disruption_risk', 'N/A')}")
    
    st.markdown("---")
    
    # Risk Summary
    st.subheader("Risk Assessment Summary")
    
    risk_data = {
        'Factor': ['Certification', 'Compliance', 'Geopolitical', 'Environmental', 'Operational', 'Capacity'],
        'Weight': [
            RISK_WEIGHTS['certification'],
            RISK_WEIGHTS['compliance'],
            RISK_WEIGHTS['geopolitical'],
            RISK_WEIGHTS['environmental'],
            RISK_WEIGHTS['operational'],
            RISK_WEIGHTS['capacity_utilization']
        ]
    }
    
    risk_df = pd.DataFrame(risk_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(risk_df, use_container_width=True)
    
    with col2:
        fig = px.pie(risk_df, values='Weight', names='Factor', title="Risk Factor Weights")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: CERTIFICATION TRACKER
# ============================================================================

def show_certification_tracker(df):
    st.header("Certification Tracker")
    
    st.info("Consolidated view of all certifications across the supplier base")
    
    # Extract certifications
    all_certs = []
    for idx, row in df.iterrows():
        certs = str(row.get('Supplier certifications', '')).split(',')
        for cert in certs:
            if cert.strip():
                all_certs.append({
                    'Supplier': row['Name'],
                    'Country': row['Country'],
                    'Certification': cert.strip(),
                    'Status': 'Valid'
                })
    
    if all_certs:
        certs_df = pd.DataFrame(all_certs)
        
        col1, col2 = st.columns(2)
        
        with col1:
            cert_type = st.selectbox("Filter by Certification Type", certs_df['Certification'].unique())
            filtered_certs = certs_df[certs_df['Certification'] == cert_type]
            st.subheader(f"{cert_type} Certifications")
            st.dataframe(filtered_certs, use_container_width=True)
        
        with col2:
            cert_counts = certs_df['Certification'].value_counts()
            fig = px.bar(x=cert_counts.index, y=cert_counts.values, title="Certifications by Type")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No certifications recorded")

# ============================================================================
# PAGE: RISK ANALYSIS
# ============================================================================

def show_risk_analysis(df):
    st.header("Risk Analysis & Portfolio View")
    
    # Calculate risk scores if needed
    if 'Risk_Score' not in df.columns:
        with st.spinner("Calculating risk metrics..."):
            risk_scores = []
            external_contexts = []
            for idx, row in df.iterrows():
                ext_context = get_external_context(
                    row.get('Country', 'XX'),
                    row.get('City', 'Unknown'),
                    row.get('Name', 'Unknown'),
                    row.get('Supplier Category', 'Unknown')
                )
                external_contexts.append(ext_context)
                risk_score = calculate_overall_risk_score(row, ext_context)
                risk_scores.append(risk_score)
            
            df['Risk_Score'] = risk_scores
            df['Risk_Level'] = df['Risk_Score'].apply(get_risk_level)
            df['External_Context'] = external_contexts
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        risk_by_country = df.groupby('Country')['Risk_Score'].mean().sort_values(ascending=False).head(10)
        fig = px.bar(x=risk_by_country.values, y=risk_by_country.index, orientation='h', 
                    title="Average Risk Score by Country (Top 10)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.box(df, x='Risk_Level', y='Risk_Score', title="Risk Score Distribution by Level")
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk matrix
    st.subheader("Risk Matrix: Company Size vs Risk Score")
    
    fig = px.scatter(df, x='Number of employees', y='Risk_Score', 
                    hover_name='Name', color='Risk_Level',
                    title="Supplier Size vs Risk",
                    color_discrete_map={
                        'Low': '#2ECC71',
                        'Medium': '#F39C12',
                        'High': '#E74C3C',
                        'Critical': '#8B0000'
                    })
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: EXTERNAL INTELLIGENCE
# ============================================================================

def show_external_intelligence(df):
    st.header("External Intelligence Dashboard")
    
    st.markdown("""
    This page shows real-time environmental and geopolitical risk data collected via OpenAI.
    Each supplier location is analyzed for:
    - Current political and trade tensions
    - Environmental and climate risks
    - Supply chain disruption likelihood
    - Recent regulatory changes
    """)
    
    if not OPENAI_API_KEY:
        st.error("OpenAI API key not configured. Please add OPENAI_API_KEY to your Streamlit secrets.")
        return
    
    # Select countries to analyze
    countries = sorted(df['Country'].unique())
    selected_countries = st.multiselect("Select Countries to Analyze", countries, default=countries[:3])
    
    if selected_countries:
        st.markdown("---")
        
        for country in selected_countries:
            country_suppliers = df[df['Country'] == country]
            
            st.subheader(f"{country} - {len(country_suppliers)} Suppliers")
            
            # Get context for first supplier in country to represent country-level data
            sample_supplier = country_suppliers.iloc[0]
            
            with st.spinner(f"Fetching intelligence for {country}..."):
                ext_context = get_external_context(
                    country,
                    sample_supplier.get('City', 'Unknown'),
                    sample_supplier.get('Name', 'Unknown'),
                    sample_supplier.get('Supplier Category', 'Unknown')
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Geopolitical Assessment**")
                st.info(ext_context.get('geopolitical_factors', 'N/A'))
                
                geo_score = float(ext_context.get('geopolitical_score', 0.5))
                st.progress(geo_score, f"Risk Level: {geo_score:.2f} / 1.0")
            
            with col2:
                st.markdown("**Environmental Assessment**")
                st.warning(ext_context.get('environmental_factors', 'N/A'))
                
                env_score = float(ext_context.get('environmental_score', 0.5))
                st.progress(env_score, f"Risk Level: {env_score:.2f} / 1.0")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Climate Risk**: {ext_context.get('climate_risk', 'N/A')}")
            
            with col2:
                st.markdown(f"**Supply Chain Disruption Risk**: {ext_context.get('supply_chain_disruption_risk', 'N/A')}")
            
            st.markdown("---")

# ============================================================================
# PAGE: ANALYTICS
# ============================================================================

def show_analytics(df):
    st.header("Portfolio Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Suppliers", len(df))
    with col2:
        st.metric("Countries", df['Country'].nunique())
    with col3:
        avg_employees = df['Number of employees'].mean()
        st.metric("Avg Employees", f"{avg_employees:.0f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cat_dist = df['Supplier Category'].value_counts()
        fig = px.pie(values=cat_dist.values, names=cat_dist.index, title="Distribution by Category")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Supplier Count by Country")
        country_dist = df['Country'].value_counts().sort_values(ascending=False)
        fig = px.bar(x=country_dist.index, y=country_dist.values, title="Suppliers by Country")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Detailed Supplier List")
    
    display_df = df[['Name', 'Country', 'City', 'Supplier Category', 'Number of employees']].copy()
    st.dataframe(display_df, use_container_width=True)
    
    # Export
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download Full Dataset",
        data=csv,
        file_name=f"suppliers_full_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()