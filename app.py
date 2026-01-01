import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="LVMH Supplier Risk Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .risk-high { background-color: #ff4444; color: white; padding: 8px 12px; border-radius: 5px; }
    .risk-medium { background-color: #ffb74d; color: white; padding: 8px 12px; border-radius: 5px; }
    .risk-low { background-color: #4caf50; color: white; padding: 8px 12px; border-radius: 5px; }
    .audit-passed { color: #4caf50; font-weight: bold; }
    .audit-failed { color: #ff4444; font-weight: bold; }
    .audit-pending { color: #ffb74d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('suppliers_full_data.csv')
    # Convert date columns to datetime
    date_columns = ['last_audit_date', 'next_audit_date', 'grs_expiry', 'zdhc_expiry', 'gots_expiry', 'rwas_expiry', 'wrap_expiry']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

df = load_data()

# Risk scoring function
def calculate_overall_risk(row):
    """Calculate overall risk score based on multiple factors"""
    risk_score = 0
    weights = {}
    
    # 1. Certification expiry risk (25%)
    cert_dates = [row['grs_expiry'], row['zdhc_expiry'], row['gots_expiry'], row['rwas_expiry'], row['wrap_expiry']]
    cert_dates = [d for d in cert_dates if pd.notna(d)]
    
    if cert_dates:
        days_to_expiry = [(d - pd.Timestamp.now()).days for d in cert_dates]
        min_days = min(days_to_expiry)
        
        if min_days < 0:
            cert_risk = 3  # Expired
        elif min_days < 30:
            cert_risk = 2.5  # Critical - expiring soon
        elif min_days < 90:
            cert_risk = 2  # High - expiring within 3 months
        elif min_days < 180:
            cert_risk = 1.5  # Medium
        else:
            cert_risk = 0.5  # Low
    else:
        cert_risk = 2  # Missing certifications = high risk
    
    # 2. Audit status risk (20%)
    audit_risk_map = {'Passed': 0.5, 'Pending': 1.5, 'Failed': 3}
    audit_risk = audit_risk_map.get(row['audit_status'], 2)
    
    # 3. Geopolitical risk (20%)
    geo_risk_map = {'Low': 0.5, 'Medium': 1.5, 'High': 2.5}
    geo_risk = geo_risk_map.get(row['geopolitical_risk'], 1.5)
    
    # 4. Environmental risk (15%)
    env_risk_map = {'Low': 0.5, 'Medium': 1.5, 'High': 2.5}
    env_risk = env_risk_map.get(row['environmental_risk'], 1.5)
    
    # 5. Incidents (15%)
    incident_risk = 2.5 if row['has_incidents'] else 0.5
    
    # Calculate weighted overall risk
    overall_risk = (cert_risk * 0.25 + audit_risk * 0.20 + geo_risk * 0.20 + env_risk * 0.15 + incident_risk * 0.15)
    
    return overall_risk

# Add risk score to dataframe
df['overall_risk_score'] = df.apply(calculate_overall_risk, axis=1)
df['risk_level'] = df['overall_risk_score'].apply(
    lambda x: 'Critical' if x >= 2.5 else ('High' if x >= 2 else ('Medium' if x >= 1.5 else 'Low'))
)

# Days to expiry calculation
def get_days_to_nearest_expiry(row):
    cert_dates = [row['grs_expiry'], row['zdhc_expiry'], row['gots_expiry'], row['rwas_expiry'], row['wrap_expiry']]
    cert_dates = [d for d in cert_dates if pd.notna(d)]
    if cert_dates:
        days = [(d - pd.Timestamp.now()).days for d in cert_dates]
        return min(days)
    return 999

df['days_to_expiry'] = df.apply(get_days_to_nearest_expiry, axis=1)

# Sidebar Navigation
st.sidebar.title("LVMH Supplier Risk Management")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Page",
    ["Dashboard", "Supplier Directory", "Supplier Details", "Certification Tracker", "Risk Assessment", "Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.info("**Data Status**: 20 suppliers tracked | Last updated: Today")

#  PAGE 1: DASHBOARD 
if page == "Dashboard":
    st.title("LVMH Supplier Risk Management Dashboard")
    st.markdown("Real-time overview of supplier health, certifications, and risks across your supply chain")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # KPIs
    total_suppliers = len(df)
    high_risk = len(df[df['risk_level'].isin(['Critical', 'High'])])
    expiring_soon = len(df[df['days_to_expiry'] < 30])
    incidents = len(df[df['has_incidents'] == True])
    
    with col1:
        st.metric("Total Suppliers", total_suppliers, "20 tracked")
    with col2:
        st.metric("High Risk Suppliers", high_risk, f"{int(high_risk/total_suppliers*100)}% of portfolio")
    with col3:
        st.metric("Expiring Soon (<30d)", expiring_soon, "Action needed")
    with col4:
        st.metric("Suppliers w/ Incidents", incidents, "Require attention")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    # Risk distribution by level
    with col1:
        st.subheader("Risk Distribution")
        risk_counts = df['risk_level'].value_counts()
        colors = {'Critical': '#ff4444', 'High': '#ff9800', 'Medium': '#ffb74d', 'Low': '#4caf50'}
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk by country
    with col2:
        st.subheader("Suppliers by Country")
        country_counts = df['country'].value_counts()
        fig = px.bar(
            x=country_counts.index,
            y=country_counts.values,
            labels={'x': 'Country', 'y': 'Number of Suppliers'},
            color=country_counts.values,
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Critical Alerts")
    # Alerts section
    alerts = []
    
    # Expiring certifications
    expiring = df[df['days_to_expiry'] < 30][['name', 'country', 'days_to_expiry']].sort_values('days_to_expiry')
    if len(expiring) > 0:
        for idx, row in expiring.iterrows():
            if row['days_to_expiry'] < 0:
                alerts.append(f"🔴 **{row['name']} ({row['country']})**: CERTIFICATION EXPIRED {abs(row['days_to_expiry'])} days ago")
            else:
                alerts.append(f"🟠 **{row['name']} ({row['country']})**: Certification expires in {row['days_to_expiry']} days")
    
    # Failed audits
    failed_audits = df[df['audit_status'] == 'Failed'][['name', 'country']]
    for idx, row in failed_audits.iterrows():
        alerts.append(f"🔴 **{row['name']} ({row['country']})**: FAILED AUDIT - Immediate action required")
    
    # Incidents
    incidents_df = df[df['has_incidents'] == True][['name', 'country', 'incident_type']]
    for idx, row in incidents_df.iterrows():
        alerts.append(f"⚠️ **{row['name']} ({row['country']})**: {row['incident_type'].upper()} reported")
    
    if alerts:
        for alert in alerts[:10]:  # Show top 10 alerts
            st.warning(alert)
    else:
        st.success("No critical alerts at this time")
    
    st.markdown("---")
    st.subheader("Top 5 Highest Risk Suppliers")
    top_risk = df.nlargest(5, 'overall_risk_score')[['name', 'country', 'risk_level', 'overall_risk_score', 'audit_status']]
    st.dataframe(top_risk, use_container_width=True, hide_index=True)

# PAGE 2: SUPPLIER DIRECTORY 
elif page == "Supplier Directory":
    st.title("Supplier Directory")
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.multiselect("Filter by Risk Level", ['Low', 'Medium', 'High', 'Critical'], default=['Low', 'Medium', 'High', 'Critical'])
    with col2:
        country_filter = st.multiselect("Filter by Country", sorted(df['country'].unique()))
    with col3:
        audit_filter = st.multiselect("Filter by Audit Status", df['audit_status'].unique(), default=df['audit_status'].unique())
    
    # Apply filters
    filtered_df = df[
        (df['risk_level'].isin(risk_filter)) &
        (df['country'].isin(country_filter) if country_filter else True) &
        (df['audit_status'].isin(audit_filter))
    ]
    
    # Display table
    display_cols = ['name', 'city', 'country', 'category', 'certifications', 'risk_level', 'overall_risk_score', 'audit_status']
    st.dataframe(
        filtered_df[display_cols].sort_values('overall_risk_score', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "overall_risk_score": st.column_config.NumberColumn("Risk Score", format="%.2f"),
        }
    )
    
    st.info(f"Showing {len(filtered_df)} out of {len(df)} suppliers")

# PAGE 3: SUPPLIER DETAILS
elif page == "Supplier Details":
    st.title("Supplier Profile & Details")
    
    supplier_name = st.selectbox("Select Supplier", sorted(df['name'].unique()))
    supplier = df[df['name'] == supplier_name].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_color = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}
        st.metric("Risk Level", f"{risk_color.get(supplier['risk_level'])} {supplier['risk_level']}", f"Score: {supplier['overall_risk_score']:.2f}")
    with col2:
        st.metric("Last Audit", pd.Timestamp(supplier['last_audit_date']).strftime('%Y-%m-%d'), supplier['audit_status'])
    with col3:
        st.metric("Certifications", len(supplier['certifications'].split(', ')), supplier['certifications'])
    st.markdown("---")
    
    # Company information
    st.subheader("Company Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Address:** {supplier['address'] if supplier['address'] != 'Unknown' else 'Not provided'}")
        st.write(f"**City:** {supplier['city']}")
        st.write(f"**Country:** {supplier['country']}")
        st.write(f"**Postal Code:** {supplier['postal_code'] if supplier['postal_code'] else 'Not provided'}")
    
    with col2:
        st.write(f"**Category:** {supplier['category']}")
        st.write(f"**Employees:** {supplier['employees'] if supplier['employees'] > 0 else 'Not provided'}")
        st.write(f"**Production Capacity:** {supplier['production_capacity']}")
        st.write(f"**Certification Score:** {supplier['certification_score']}/5.0")
    
    st.markdown("---")
    
    # Certifications
    st.subheader("Certifications & Expiry Dates")
    cert_cols = ['grs_expiry', 'zdhc_expiry', 'gots_expiry', 'rwas_expiry', 'wrap_expiry']
    cert_names = {'grs_expiry': 'GRS', 'zdhc_expiry': 'ZDHC', 'gots_expiry': 'GOTS', 'rwas_expiry': 'RWS', 'wrap_expiry': 'WRAP GOLD'}
    
    cert_data = []
    for col in cert_cols:
        if pd.notna(supplier[col]):
            expiry_date = pd.Timestamp(supplier[col])
            days_left = (expiry_date - pd.Timestamp.now()).days
            status = '✅' if days_left > 30 else ('🟠' if days_left > 0 else '🔴')
            cert_data.append({
                'Certification': cert_names[col],
                'Expiry Date': expiry_date.strftime('%Y-%m-%d'),
                'Days Left': days_left,
                'Status': status
            })
    
    if cert_data:
        cert_df = pd.DataFrame(cert_data)
        st.dataframe(cert_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No certifications recorded")
    st.markdown("---")
    
    # Audit history
    st.subheader("Audit History")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        audit_badge = {'Passed': '✅', 'Failed': '🔴', 'Pending': '🟠'}
        st.write(f"**Last Audit:** {pd.Timestamp(supplier['last_audit_date']).strftime('%Y-%m-%d')}")
        st.write(f"{audit_badge.get(supplier['audit_status'])} **Status:** {supplier['audit_status']}")
    
    with col2:
        st.write(f"**Next Audit:** {pd.Timestamp(supplier['next_audit_date']).strftime('%Y-%m-%d')}")
        days_until_audit = (pd.Timestamp(supplier['next_audit_date']) - pd.Timestamp.now()).days
        st.write(f"In {days_until_audit} days")
    
    with col3:
        st.write(f"**Incident History:** {'Yes' if supplier['has_incidents'] else 'No'}")
        if supplier['has_incidents']:
            st.write(f"**Type:** {supplier['incident_type']}")
    st.markdown("---")
    
    # Risk factors
    st.subheader("Risk Assessment")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Geopolitical Risk:** {supplier['geopolitical_risk']}")
        st.write(f"**Environmental Risk:** {supplier['environmental_risk']}")
    
    with col2:
        st.write(f"**Compliance Risk:** {supplier['compliance_risk']}")

# PAGE 4: CERTIFICATION TRACKER
elif page == "Certification Tracker":
    st.title("Certification Expiry Tracker")
    st.markdown("Monitor all certifications across your supplier network")
    tab1, tab2, tab3 = st.tabs(["Expiry Timeline", "Critical (< 30 days)", "Compliant"])
    
    # Collect all certification data
    cert_records = []
    for idx, row in df.iterrows():
        certs = {'GRS': row['grs_expiry'], 'ZDHC': row['zdhc_expiry'], 'GOTS': row['gots_expiry'], 'RWS': row['rwas_expiry'], 'WRAP': row['wrap_expiry']}
        for cert_name, expiry in certs.items():
            if pd.notna(expiry):
                days_left = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
                cert_records.append({
                    'Supplier': row['name'],
                    'Country': row['country'],
                    'Certification': cert_name,
                    'Expiry Date': pd.Timestamp(expiry).strftime('%Y-%m-%d'),
                    'Days Left': days_left,
                    'Status': 'Expired' if days_left < 0 else ('Critical' if days_left < 30 else ('Warning' if days_left < 90 else 'OK'))
                })
    cert_df = pd.DataFrame(cert_records)
    
    with tab1:
        st.subheader("Expiry Timeline (Next 180 days)")
        cert_df_sorted = cert_df.sort_values('Days Left')
        
        fig = px.bar(
            cert_df_sorted,
            x='Days Left',
            y='Supplier',
            color='Status',
            color_discrete_map={'OK': '#4caf50', 'Warning': '#ffb74d', 'Critical': '#ff9800', 'Expired': '#f44336'},
            orientation='h',
            labels={'Days Left': 'Days Until Expiry'}
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cert_df_sorted, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("CRITICAL: Expiring Within 30 Days")
        critical = cert_df[cert_df['Days Left'] < 30].sort_values('Days Left')
        if len(critical) > 0:
            for idx, row in critical.iterrows():
                if row['Days Left'] < 0:
                    st.error(f"🔴 {row['Supplier']} ({row['Country']}) - **{row['Certification']} EXPIRED {abs(row['Days Left'])} days ago**")
                else:
                    st.warning(f"🟠 {row['Supplier']} ({row['Country']}) - {row['Certification']} expires in {row['Days Left']} days")
            
            st.markdown("---")
            st.info("**Recommended Actions:**\n- Contact supplier immediately\n- Request certificate renewal\n- Schedule re-certification audit\n- Prepare alternate supplier if needed")
        else:
            st.success("No certifications expiring within 30 days")
    
    with tab3:
        st.subheader("Compliant: All OK")
        compliant = cert_df[cert_df['Days Left'] >= 90]
        st.success(f"{len(compliant)} certifications are valid for 90+ days")
        st.dataframe(compliant, use_container_width=True, hide_index=True)

# PAGE 5: RISK ASSESSMENT 
elif page == "Risk Assessment":
    st.title("Risk Assessment & Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Score Distribution")
        fig = px.histogram(
            df,
            x='overall_risk_score',
            nbins=20,
            labels={'overall_risk_score': 'Risk Score', 'count': 'Number of Suppliers'},
            color_discrete_sequence=['#667eea']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Risk Factors Heatmap")
        risk_factors = df.groupby('risk_level').agg({
            'overall_risk_score': 'mean',
            'has_incidents': 'sum',
            'audit_status': lambda x: (x == 'Failed').sum()
        }).round(2)
        st.dataframe(risk_factors, use_container_width=True)
    
    st.markdown("---")
    
    # Risk breakdown by country
    st.subheader("Risk Profile by Country")
    country_risk = df.groupby('country').agg({
        'overall_risk_score': 'mean',
        'name': 'count',
        'geopolitical_risk': lambda x: (x == 'High').sum(),
        'environmental_risk': lambda x: (x == 'High').sum()
    }).round(2).sort_values('overall_risk_score', ascending=False)
    
    country_risk.columns = ['Avg Risk Score', 'Suppliers', 'High Geo Risk', 'High Env Risk']
    st.dataframe(country_risk, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed risk analysis for critical suppliers
    st.subheader("Critical Suppliers Detail")
    critical_suppliers = df[df['risk_level'] == 'Critical'][['name', 'country', 'overall_risk_score', 'audit_status', 'geopolitical_risk', 'environmental_risk', 'has_incidents']]
    
    if len(critical_suppliers) > 0:
        st.dataframe(critical_suppliers, use_container_width=True, hide_index=True)
    else:
        st.success("No critical risk suppliers at this time")

# PAGE 6: ANALYTICS 
elif page == "Analytics":
    st.title("Analytics & Reporting")
    
    st.subheader("Supplier Portfolio Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Suppliers", len(df))
        st.metric("Countries", df['country'].nunique())
    with col2:
        avg_risk = df['overall_risk_score'].mean()
        st.metric("Average Risk Score", f"{avg_risk:.2f}", "1.0-3.0 scale")
        st.metric("Certifications per Supplier", f"{df['certifications'].apply(lambda x: len(x.split(', '))).mean():.1f}")
    with col3:
        compliance_rate = (df['audit_status'] == 'Passed').sum() / len(df) * 100
        st.metric("Audit Compliance Rate", f"{compliance_rate:.1f}%", f"{int((df['audit_status'] == 'Passed').sum())} passed")
    st.markdown("---")
    
    # Category distribution
    st.subheader("Supplier Distribution by Category")
    category_counts = df['category'].value_counts()
    fig = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        labels={'x': 'Number of Suppliers', 'y': 'Category'},
        color=category_counts.values,
        color_continuous_scale='blues'
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    
    # Risk vs Employees
    st.subheader("Risk Score vs Supplier Size")
    employees_filtered = df[df['employees'] > 0]
    fig = px.scatter(
        employees_filtered,
        x='employees',
        y='overall_risk_score',
        size='overall_risk_score',
        color='risk_level',
        hover_name='name',
        labels={'employees': 'Number of Employees', 'overall_risk_score': 'Risk Score'},
        color_discrete_map={'Critical': '#ff4444', 'High': '#ff9800', 'Medium': '#ffb74d', 'Low': '#4caf50'}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    
    # Export data
    st.subheader("Export Data")
    if st.button("Download Supplier Report (CSV)"):
        csv = df[['name', 'country', 'category', 'certifications', 'risk_level', 'overall_risk_score', 'audit_status', 'days_to_expiry']].to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"lvmh_supplier_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


