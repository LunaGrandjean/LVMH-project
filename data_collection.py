import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

# Page configuration
st.set_page_config(
    page_title="LVMH - Data Collection",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Data Collection & Management Portal")
st.markdown("Update supplier certifications, audit dates, and incident information")

# Sidebar tabs
collection_mode = st.sidebar.radio(
    "Select Mode",
    ["Certification Updates", "Audit Scheduling", "Incident Reporting", "Bulk Upload", "Data History"]
)

# MODE 1: CERTIFICATION UPDATES 
if collection_mode == "Certification Updates":
    st.header("Update Certification Expiry Dates")
    st.markdown("Manually enter or update certification expiry dates for suppliers")
    
    # Load current data
    df = pd.read_csv('suppliers_full_data.csv')
    
    col1, col2 = st.columns(2)
    
    with col1:
        supplier = st.selectbox(
            "Select Supplier",
            sorted(df['name'].unique()),
            key="cert_supplier"
        )
        
        cert_type = st.selectbox(
            "Certification Type",
            ["GRS", "ZDHC", "GOTS", "RWS", "WRAP GOLD"],
            key="cert_type"
        )
    
    with col2:
        expiry_date = st.date_input(
            "Expiry Date",
            value=date.today(),
            key="cert_expiry"
        )
        
        issue_date = st.date_input(
            "Issue Date (Optional)",
            value=None,
            key="cert_issue"
        )
    
    # Notes
    notes = st.text_area(
        "Notes (e.g., certification number, issuing body)",
        placeholder="Enter any additional information about this certification",
        height=80
    )
    
    # File upload for certificate
    cert_file = st.file_uploader(
        "Upload Certificate (PDF/Image)",
        type=["pdf", "jpg", "jpeg", "png"],
        key="cert_file"
    )
    
    # Map cert_type to column name
    cert_col_map = {
        "GRS": "grs_expiry",
        "ZDHC": "zdhc_expiry",
        "GOTS": "gots_expiry",
        "RWS": "rwas_expiry",
        "WRAP GOLD": "wrap_expiry"
    }
    
    if st.button("Save Certification", key="save_cert"):
        # Update the CSV
        supplier_idx = df[df['name'] == supplier].index[0]
        df.at[supplier_idx, cert_col_map[cert_type]] = str(expiry_date)
        df.to_csv('suppliers_full_data.csv', index=False)
        
        # Log the update
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "certification_update",
            "supplier": supplier,
            "cert_type": cert_type,
            "expiry_date": str(expiry_date),
            "issue_date": str(issue_date) if issue_date else None,
            "notes": notes,
            "file_uploaded": cert_file is not None
        }
        
        # Append to activity log
        if os.path.exists('data_log.jsonl'):
            with open('data_log.jsonl', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        else:
            with open('data_log.jsonl', 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        st.success(f"Certification updated for {supplier} ({cert_type})")
        st.balloons()
    
    # Display current certifications
    st.markdown("---")
    st.subheader("Current Certifications")
    supplier_data = df[df['name'] == supplier].iloc[0]
    
    cert_data = []
    for cert_name, col_name in cert_col_map.items():
        if pd.notna(supplier_data[col_name]):
            expiry = pd.Timestamp(supplier_data[col_name])
            days_left = (expiry - pd.Timestamp.now()).days
            status = 'Valid' if days_left > 30 else ('Expiring Soon' if days_left > 0 else 'Expired')
            cert_data.append({
                'Type': cert_name,
                'Expiry': expiry.strftime('%Y-%m-%d'),
                'Days Left': days_left,
                'Status': status
            })
    
    if cert_data:
        st.dataframe(pd.DataFrame(cert_data), use_container_width=True, hide_index=True)
    else:
        st.info("No certifications recorded for this supplier")


# MODE 2: AUDIT SCHEDULING 
elif collection_mode == "Audit Scheduling":
    st.header("Schedule & Update Audits")
    st.markdown("Record audit dates, results, and schedule future audits")
    
    df = pd.read_csv('suppliers_full_data.csv')
    
    col1, col2 = st.columns(2)
    
    with col1:
        supplier = st.selectbox(
            "Select Supplier",
            sorted(df['name'].unique()),
            key="audit_supplier"
        )
        
        audit_type = st.selectbox(
            "Audit Type",
            ["Certification Audit", "Quality Audit", "Compliance Audit", "Re-Audit", "Surprise Audit"],
            key="audit_type"
        )
    
    with col2:
        audit_date = st.date_input(
            "Audit Date",
            value=date.today(),
            key="audit_date"
        )
        
        audit_status = st.selectbox(
            "Audit Result",
            ["Passed", "Pending", "Failed"],
            key="audit_status"
        )
    
    # Audit details
    col1, col2 = st.columns(2)
    
    with col1:
        auditor = st.text_input(
            "Auditor Name/Organization",
            placeholder="e.g., ZDHC Auditor, Internal Team",
            key="auditor"
        )
        
        next_audit_date = st.date_input(
            "Scheduled Next Audit",
            value=None,
            key="next_audit"
        )
    
    with col2:
        if audit_status == "Failed":
            corrective_action = st.text_area(
                "Corrective Action Required",
                placeholder="Describe the corrective actions needed",
                height=100,
                key="corrective"
            )
        else:
            corrective_action = None
    
    # Findings
    findings = st.text_area(
        "Audit Findings/Notes",
        placeholder="Key findings, strengths, areas for improvement",
        height=100,
        key="findings"
    )
    
    if st.button("Save Audit Record", key="save_audit"):
        supplier_idx = df[df['name'] == supplier].index[0]
        df.at[supplier_idx, 'last_audit_date'] = str(audit_date)
        df.at[supplier_idx, 'audit_status'] = audit_status
        if next_audit_date:
            df.at[supplier_idx, 'next_audit_date'] = str(next_audit_date)
        df.to_csv('suppliers_full_data.csv', index=False)
        
        # Log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "audit_update",
            "supplier": supplier,
            "audit_type": audit_type,
            "audit_date": str(audit_date),
            "status": audit_status,
            "auditor": auditor,
            "next_audit": str(next_audit_date) if next_audit_date else None,
            "corrective_action": corrective_action,
            "findings": findings
        }
        
        if os.path.exists('data_log.jsonl'):
            with open('data_log.jsonl', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        else:
            with open('data_log.jsonl', 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        st.success(f"Audit record saved for {supplier}")
        st.balloons()
    
    # Display audit history
    st.markdown("---")
    st.subheader("Supplier Audit Timeline")
    supplier_data = df[df['name'] == supplier].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Last Audit", pd.Timestamp(supplier_data['last_audit_date']).strftime('%Y-%m-%d'))
    with col2:
        st.metric("Status", supplier_data['audit_status'])
    with col3:
        if pd.notna(supplier_data['next_audit_date']):
            days_until = (pd.Timestamp(supplier_data['next_audit_date']) - pd.Timestamp.now()).days
            st.metric("Next Audit in", f"{days_until} days")


# MODE 3: INCIDENT REPORTING
elif collection_mode == "Incident Reporting":
    st.header("Report & Track Incidents")
    st.markdown("Document supplier-related incidents, controversies, and issues")
    
    df = pd.read_csv('suppliers_full_data.csv')
    
    col1, col2 = st.columns(2)
    
    with col1:
        supplier = st.selectbox(
            "Select Supplier",
            sorted(df['name'].unique()),
            key="incident_supplier"
        )
        
        incident_date = st.date_input(
            "Incident Date",
            value=date.today(),
            key="incident_date"
        )
    
    with col2:
        incident_type = st.selectbox(
            "Incident Type",
            [
                "Labor Violation",
                "Environmental Breach",
                "Quality Issue",
                "Safety Incident",
                "Sanction/Blacklist",
                "Bankruptcy/Financial",
                "Media Coverage",
                "Regulatory Fine",
                "Other"
            ],
            key="incident_type"
        )
        
        severity = st.selectbox(
            "Severity Level",
            ["Low", "Medium", "High", "Critical"],
            key="severity"
        )
    
    # Incident details
    description = st.text_area(
        "Incident Description",
        placeholder="Detailed description of the incident, what happened, and when",
        height=120,
        key="incident_desc"
    )
    
    # Source
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.selectbox(
            "Source of Information",
            ["Internal Report", "News Article", "Government Authority", "Audit Finding", "Supplier Disclosure", "Other"],
            key="source"
        )
    
    with col2:
        source_url = st.text_input(
            "Source URL (if applicable)",
            placeholder="https://...",
            key="source_url"
        )
    
    # Resolution
    status = st.selectbox(
        "Incident Status",
        ["Open", "Under Investigation", "Resolved", "Monitoring"],
        key="incident_status"
    )
    
    resolution = st.text_area(
        "Resolution/Action Taken",
        placeholder="What actions have been taken or planned",
        height=100,
        key="resolution"
    ) if status != "Open" else None
    
    if st.button("Report Incident", key="save_incident"):
        # Update supplier
        supplier_idx = df[df['name'] == supplier].index[0]
        df.at[supplier_idx, 'has_incidents'] = True
        df.at[supplier_idx, 'incident_type'] = incident_type
        df.to_csv('suppliers_full_data.csv', index=False)
        
        # Log incident
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "incident_report",
            "supplier": supplier,
            "incident_date": str(incident_date),
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "source": source,
            "source_url": source_url,
            "status": status,
            "resolution": resolution
        }
        
        if os.path.exists('data_log.jsonl'):
            with open('data_log.jsonl', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        else:
            with open('data_log.jsonl', 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        st.success(f"Incident reported for {supplier}")
        st.balloons()
    
    # Show current status
    st.markdown("---")
    st.subheader("Current Incident Status")
    supplier_data = df[df['name'] == supplier].iloc[0]
    
    if supplier_data['has_incidents']:
        col1, col2 = st.columns(2)
        with col1:
            st.warning(f"Incidents: YES")
            st.info(f"Type: {supplier_data['incident_type']}")
        with col2:
            st.markdown("*Mark this supplier as incident-free by clicking the button below*")
            if st.button("Clear Incident Flag", key="clear_incident"):
                df.at[supplier_idx, 'has_incidents'] = False
                df.at[supplier_idx, 'incident_type'] = None
                df.to_csv('suppliers_full_data.csv', index=False)
                st.success("Incident flag cleared")
                st.rerun()
    else:
        st.success("No incidents recorded for this supplier")


# MODE 4: BULK UPLOAD 
elif collection_mode == "Bulk Upload":
    st.header("Bulk Data Upload")
    st.markdown("Upload a CSV file to update multiple suppliers at once")
    
    st.info("""
    **Upload Format:**
    Your CSV should have these columns:
    - supplier_name (required)
    - cert_type (GRS, ZDHC, GOTS, RWS, WRAP GOLD)
    - expiry_date (YYYY-MM-DD)
    - audit_date (optional, YYYY-MM-DD)
    - audit_status (optional, Passed/Pending/Failed)
    - next_audit_date (optional, YYYY-MM-DD)
    - incident_flag (optional, True/False)
    - incident_type (optional)
    
    **Example:**
    | supplier_name | cert_type | expiry_date | audit_date | audit_status |
    |---|---|---|---|---|
    | Paolo tessitura | GOTS | 2025-08-23 | 2024-08-22 | Passed |
    | Confection Soleil | GOTS | 2025-06-15 | 2024-11-10 | Passed |
    """)
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file is not None:
        # Read uploaded file
        upload_df = pd.read_csv(uploaded_file)
        
        # Preview
        st.subheader("Preview (First 5 rows)")
        st.dataframe(upload_df.head(), use_container_width=True)
        
        # Validation
        st.subheader("Validation")
        
        errors = []
        current_df = pd.read_csv('suppliers_full_data.csv')
        
        for idx, row in upload_df.iterrows():
            supplier = row.get('supplier_name')
            if supplier not in current_df['name'].values:
                errors.append(f"Row {idx+2}: Supplier '{supplier}' not found in database")
        
        if errors:
            st.error(f"Found {len(errors)} validation errors:")
            for error in errors:
                st.write(f"- {error}")
        else:
            st.success("All suppliers found in database!")
            
            # Process upload
            if st.button("Process Upload", key="process_bulk"):
                cert_col_map = {
                    "GRS": "grs_expiry",
                    "ZDHC": "zdhc_expiry",
                    "GOTS": "gots_expiry",
                    "RWS": "rwas_expiry",
                    "WRAP GOLD": "wrap_expiry"
                }
                
                for idx, row in upload_df.iterrows():
                    supplier = row['supplier_name']
                    supplier_idx = current_df[current_df['name'] == supplier].index[0]
                    
                    # Update certification
                    if 'cert_type' in row and pd.notna(row['cert_type']):
                        cert_type = row['cert_type']
                        if cert_type in cert_col_map and pd.notna(row['expiry_date']):
                            current_df.at[supplier_idx, cert_col_map[cert_type]] = str(row['expiry_date'])
                    
                    # Update audit
                    if 'audit_date' in row and pd.notna(row['audit_date']):
                        current_df.at[supplier_idx, 'last_audit_date'] = str(row['audit_date'])
                    
                    if 'audit_status' in row and pd.notna(row['audit_status']):
                        current_df.at[supplier_idx, 'audit_status'] = row['audit_status']
                    
                    if 'next_audit_date' in row and pd.notna(row['next_audit_date']):
                        current_df.at[supplier_idx, 'next_audit_date'] = str(row['next_audit_date'])
                    
                    # Update incidents
                    if 'incident_flag' in row and pd.notna(row['incident_flag']):
                        current_df.at[supplier_idx, 'has_incidents'] = row['incident_flag']
                    
                    if 'incident_type' in row and pd.notna(row['incident_type']):
                        current_df.at[supplier_idx, 'incident_type'] = row['incident_type']
                    
                    # Log
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "action": "bulk_upload",
                        "supplier": supplier,
                        "data": row.to_dict()
                    }
                    
                    if os.path.exists('data_log.jsonl'):
                        with open('data_log.jsonl', 'a') as f:
                            f.write(json.dumps(log_entry) + '\n')
                    else:
                        with open('data_log.jsonl', 'w') as f:
                            f.write(json.dumps(log_entry) + '\n')
                
                current_df.to_csv('suppliers_full_data.csv', index=False)
                st.success(f"Successfully processed {len(upload_df)} records!")
                st.balloons()


# MODE 5: DATA HISTORY
elif collection_mode == "Data History":
    st.header("Data Update History")
    st.markdown("View all changes made to supplier data")
    
    if os.path.exists('data_log.jsonl'):
        # Load activity log
        activities = []
        with open('data_log.jsonl', 'r') as f:
            for line in f:
                activities.append(json.loads(line))
        
        # Reverse to show latest first
        activities.reverse()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            action_filter = st.selectbox(
                "Filter by Action",
                ["All", "certification_update", "audit_update", "incident_report", "bulk_upload"],
                key="action_filter"
            )
        
        with col2:
            supplier_filter = st.selectbox(
                "Filter by Supplier",
                ["All"] + sorted(list(set([a.get('supplier', 'N/A') for a in activities]))),
                key="supplier_filter"
            )
        
        with col3:
            days_back = st.slider("Days Back", 1, 365, 30)
        
        # Apply filters
        filtered = activities
        
        if action_filter != "All":
            filtered = [a for a in filtered if a.get('action') == action_filter]
        
        if supplier_filter != "All":
            filtered = [a for a in filtered if a.get('supplier') == supplier_filter]
        
        cutoff_date = datetime.now().timestamp() - (days_back * 86400)
        filtered = [a for a in filtered if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff_date]
        
        st.info(f"Showing {len(filtered)} updates")
        
        # Display
        for activity in filtered[:50]:  # Show latest 50
            timestamp = datetime.fromisoformat(activity['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            action = activity['action'].replace('_', ' ').title()
            supplier = activity.get('supplier', 'N/A')
            
            with st.expander(f"{timestamp} - {action} - {supplier}"):
                # Show relevant details based on action type
                if activity['action'] == 'certification_update':
                    st.write(f"**Certification:** {activity['cert_type']}")
                    st.write(f"**Expiry Date:** {activity['expiry_date']}")
                    if activity.get('notes'):
                        st.write(f"**Notes:** {activity['notes']}")
                
                elif activity['action'] == 'audit_update':
                    st.write(f"**Type:** {activity['audit_type']}")
                    st.write(f"**Date:** {activity['audit_date']}")
                    st.write(f"**Status:** {activity['status']}")
                    if activity.get('findings'):
                        st.write(f"**Findings:** {activity['findings']}")
                
                elif activity['action'] == 'incident_report':
                    st.write(f"**Type:** {activity['incident_type']}")
                    st.write(f"**Severity:** {activity['severity']}")
                    st.write(f"**Status:** {activity['status']}")
                    st.write(f"**Description:** {activity['description']}")
                
                elif activity['action'] == 'bulk_upload':
                    st.write(f"**Data:** {activity['data']}")
    else:
        st.info("No data updates recorded yet. Start by updating certifications, audits, or incidents!")
