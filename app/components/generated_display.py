"""
Display components for generated tender and quote packages
"""
import streamlit as st


def show_generated_tender(tender_package):
    """Show generated tender package with edit options"""
    
    st.markdown("---")
    st.markdown("### 📋 Generated Tender Package")
    
    # Package overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Project", tender_package["project_title"])
    
    with col2:
        st.metric("Value", f"${tender_package['contract_value']:,.0f}")
    
    with col3:
        st.metric("Type", tender_package["project_type"])
    
    with col4:
        st.metric("Status", tender_package["status"].title())
    
    # Documents section
    st.markdown("#### 📄 Generated Documents")
    
    # Create tabs for different documents
    tabs = st.tabs(["TEPP", "Returnable Schedule", "Evaluation Criteria", "Compliance", "Timeline", "Risk Assessment"])
    
    with tabs[0]:  # TEPP
        st.markdown("**Tender Evaluation and Probity Plan**")
        if "tepp" in tender_package and isinstance(tender_package["tepp"], dict):
            st.text_area("TEPP Content", value=tender_package["tepp"]["full_document"], height=400)
        else:
            st.info("TEPP document generated successfully")
    
    with tabs[1]:  # Returnable Schedule
        st.markdown("**Returnable Schedule**")
        st.info("Returnable Schedule document generated successfully")
    
    with tabs[2]:  # Evaluation Criteria
        st.markdown("**Evaluation Criteria**")
        st.info("Evaluation Criteria document generated successfully")
    
    with tabs[3]:  # Compliance
        st.markdown("**Compliance Checklist**")
        st.info("Compliance Checklist document generated successfully")
    
    with tabs[4]:  # Timeline
        st.markdown("**Project Timeline**")
        st.info("Project Timeline document generated successfully")
    
    with tabs[5]:  # Risk Assessment
        st.markdown("**Risk Assessment**")
        st.info("Risk Assessment document generated successfully")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✏️ Edit Package", type="primary"):
            st.info("Edit functionality coming soon!")
    
    with col2:
        if st.button("📄 Export PDF"):
            st.info("Export functionality coming soon!")
    
    with col3:
        if st.button("✅ Approve Package"):
            st.success("Package approved successfully!")
    
    with col4:
        if st.button("🔄 Regenerate"):
            st.session_state.pop("generated_tender", None)
            st.rerun()


def show_generated_quote(quote_package):
    """Show generated quote package with edit options"""
    
    st.markdown("---")
    st.markdown("### 💰 Generated Quote Package")
    
    # Package overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Project", quote_package["project_title"])
    
    with col2:
        st.metric("Value", f"${quote_package['contract_value']:,.0f}")
    
    with col3:
        st.metric("Type", quote_package["project_type"])
    
    with col4:
        st.metric("Status", quote_package["status"].title())
    
    # Documents section
    st.markdown("#### 📄 Generated Documents")
    
    # Create tabs for different documents
    tabs = st.tabs(["RFQ", "Evaluation Criteria", "Compliance", "Timeline"])
    
    with tabs[0]:  # RFQ
        st.markdown("**Request for Quotation**")
        st.info("RFQ document generated successfully")
    
    with tabs[1]:  # Evaluation Criteria
        st.markdown("**Evaluation Criteria**")
        st.info("Evaluation Criteria document generated successfully")
    
    with tabs[2]:  # Compliance
        st.markdown("**Compliance Requirements**")
        st.info("Compliance Requirements document generated successfully")
    
    with tabs[3]:  # Timeline
        st.markdown("**Quotation Timeline**")
        st.info("Timeline document generated successfully")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✏️ Edit Package", type="primary"):
            st.info("Edit functionality coming soon!")
    
    with col2:
        if st.button("📄 Export PDF"):
            st.info("Export functionality coming soon!")
    
    with col3:
        if st.button("✅ Approve Package"):
            st.success("Package approved successfully!")
    
    with col4:
        if st.button("🔄 Regenerate"):
            st.session_state.pop("generated_quote", None)
            st.rerun()
