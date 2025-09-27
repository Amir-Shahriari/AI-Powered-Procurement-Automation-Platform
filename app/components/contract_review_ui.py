"""
AI-Powered Contract Review UI Component
Comprehensive contract analysis interface with risk, compliance, and governance review
"""

import streamlit as st
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.services.contract_reviewer import ContractReviewer, ContractReviewResult
from app.services.ai_model_detector import get_ai_detector
from app.core.navigation import _nav_set


def show_contract_reviewer():
    """Display the AI-powered contract review interface"""
    
    st.title("🔍 AI-Powered Contract Review")
    st.markdown("**Comprehensive Risk, Compliance & Governance Analysis**")
    
    # Initialize services
    if 'contract_reviewer' not in st.session_state:
        st.session_state.contract_reviewer = ContractReviewer()
    
    # Sidebar for AI model selection
    with st.sidebar:
        st.header("🤖 AI Configuration")
        
        # Get AI detector and display system info
        ai_detector = get_ai_detector()
        ai_detector.display_system_info()
        
        # AI Model Selection
        selected_model = ai_detector.display_model_selector()
        
        if selected_model:
            st.success(f"✅ Model: {selected_model.model_name}")
            st.caption(f"Provider: {selected_model.provider}")
            st.caption(f"Type: {selected_model.model_type}")
            st.caption(f"Cost: {selected_model.cost_per_token}")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📄 Contract Upload & Configuration")
        
        # Contract type selection
        contract_types = [
            "Construction & Infrastructure",
            "Professional Services", 
            "Supply & Procurement",
            "IT & Technology",
            "Consulting",
            "Maintenance & Operations",
            "Environmental Services",
            "General"
        ]
        
        contract_type = st.selectbox(
            "🏷️ Contract Type",
            contract_types,
            help="Select the type of contract for targeted analysis"
        )
        
        # Contract input method
        input_method = st.radio(
            "📝 Contract Input Method",
            ["📄 Upload File", "📋 Paste Text", "✏️ Write Manually"],
            horizontal=True
        )
        
        contract_content = ""
        
        if input_method == "📄 Upload File":
            uploaded_file = st.file_uploader(
                "Upload Contract Document",
                type=['pdf', 'docx', 'doc', 'txt'],
                help="Upload contract documents for AI analysis"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.type == "text/plain":
                        contract_content = str(uploaded_file.read(), "utf-8")
                    elif uploaded_file.type == "application/pdf":
                        st.warning("PDF processing not yet implemented. Please use TXT or DOCX files.")
                    else:
                        st.warning("File type not supported yet. Please use TXT files.")
                    
                    if contract_content:
                        st.success(f"✅ File processed: {uploaded_file.name}")
                        st.caption(f"Content length: {len(contract_content)} characters")
                        
                        # Show preview
                        with st.expander("📖 Content Preview", expanded=False):
                            st.text(contract_content[:1000] + "..." if len(contract_content) > 1000 else contract_content)
                
                except Exception as e:
                    st.error(f"Error processing file: {e}")
        
        elif input_method == "📋 Paste Text":
            contract_content = st.text_area(
                "Paste Contract Content",
                height=300,
                placeholder="Paste your contract text here...",
                help="Copy and paste contract content for analysis"
            )
        
        else:  # Write Manually
            contract_content = st.text_area(
                "Write Contract Content",
                height=300,
                placeholder="Write or type your contract content here...",
                help="Manually enter contract content for analysis"
            )
    
    with col2:
        st.header("⚙️ Review Configuration")
        
        # Analysis scope
        st.subheader("🎯 Analysis Scope")
        risk_analysis = st.checkbox("Risk Assessment", value=True, help="Analyze financial, operational, and legal risks")
        compliance_check = st.checkbox("Compliance Review", value=True, help="Check against regulations and standards")
        governance_review = st.checkbox("Governance Analysis", value=True, help="Assess governance and accountability")
        
        # Priority settings
        st.subheader("⚡ Priority Settings")
        urgency = st.selectbox(
            "Urgency Level",
            ["Standard", "High Priority", "Critical"],
            help="Higher priority contracts get more detailed analysis"
        )
        
        # Review depth
        review_depth = st.selectbox(
            "Review Depth",
            ["Standard", "Comprehensive", "Thorough"],
            help="Depth of analysis - thorough takes longer but provides more detail"
        )
        
        # Additional options
        st.subheader("🔧 Additional Options")
        include_benchmarking = st.checkbox("Industry Benchmarking", help="Compare against industry standards")
        generate_report = st.checkbox("Generate Detailed Report", value=True, help="Create comprehensive report")
        save_results = st.checkbox("Save Review Results", value=True, help="Save results for future reference")
    
    # Analysis button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 START AI CONTRACT REVIEW", type="primary", use_container_width=True):
            if not contract_content.strip():
                st.error("❌ Please provide contract content for analysis")
            elif not selected_model:
                st.error("❌ Please select an AI model for analysis")
            else:
                # Start the review process
                with st.spinner(f"🤖 AI is analyzing your {contract_type.lower()} contract using {selected_model.model_name}..."):
                    try:
                        # Set the selected model
                        st.session_state.contract_reviewer.selected_model = selected_model
                        
                        # Perform contract review
                        review_result = st.session_state.contract_reviewer.review_contract(
                            contract_content=contract_content,
                            contract_type=contract_type,
                            ai_model=selected_model
                        )
                        
                        # Store result in session state
                        st.session_state.contract_review_result = review_result
                        st.session_state.show_review_results = True
                        
                        st.success("✅ Contract review completed successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Contract review failed: {e}")
    
    # Display results if available
    if st.session_state.get('show_review_results') and st.session_state.get('contract_review_result'):
        display_contract_review_results(st.session_state.contract_review_result)


def display_contract_review_results(result: ContractReviewResult):
    """Display comprehensive contract review results"""
    
    st.markdown("---")
    st.header("📊 CONTRACT REVIEW RESULTS")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_color = {
            'Low': '🟢',
            'Medium': '🟡',
            'High': '🟠', 
            'Critical': '🔴'
        }.get(result.overall_risk_score, '⚪')
        st.metric("Risk Score", f"{risk_color} {result.overall_risk_score}")
    
    with col2:
        compliance_color = {
            'Compliant': '✅',
            'Non-Compliant': '❌',
            'Requires Review': '⚠️'
        }.get(result.compliance_score, '❓')
        st.metric("Compliance", f"{compliance_color} {result.compliance_score}")
    
    with col3:
        governance_color = {
            'Good': '✅',
            'Adequate': '⚠️',
            'Poor': '❌',
            'Requires Review': '❓'
        }.get(result.governance_score, '❓')
        st.metric("Governance", f"{governance_color} {result.governance_score}")
    
    with col4:
        st.metric("AI Model", result.ai_model_used)
    
    # Note about auto-save behavior
    st.info("💡 **Note:** Results are not automatically saved. Use the '💾 Save Results' button below to save this analysis.")
    
    # Executive Summary
    st.subheader("📋 Executive Summary")
    st.info(result.executive_summary)
    
    # Critical Issues (if any)
    if result.critical_issues:
        st.subheader("🚨 Critical Issues")
        for issue in result.critical_issues:
            st.error(f"• {issue}")
    
    # Tabs for detailed analysis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Risk Analysis", 
        "✅ Compliance Review", 
        "🏛️ Governance Analysis",
        "📝 Recommendations",
        "📄 Full Report"
    ])
    
    with tab1:
        display_risk_analysis(result.risks)
    
    with tab2:
        display_compliance_review(result.compliance_checks)
    
    with tab3:
        display_governance_analysis(result.governance_analysis)
    
    with tab4:
        display_recommendations(result)
    
    with tab5:
        display_full_report(result)
    
    # Action buttons
    st.markdown("---")
    
    # Action buttons with regenerate AI option
    st.subheader("🎯 Actions")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🤖 Regenerate AI Analysis", use_container_width=True, type="primary"):
            # Clear current results and trigger new analysis
            st.session_state.show_review_results = False
            st.session_state.contract_review_result = None
            st.success("🔄 Regenerating AI analysis...")
            st.rerun()
    
    with col2:
        if st.button("💾 Save Results", use_container_width=True):
            save_review_results(result)
    
    with col3:
        if st.button("📤 Export Report", use_container_width=True):
            export_review_report(result)
    
    with col4:
        if st.button("🔄 Review Another", use_container_width=True):
            st.session_state.show_review_results = False
            st.session_state.contract_review_result = None
            st.rerun()
    
    with col5:
        if st.button("📊 Dashboard", use_container_width=True):
            _nav_set("contract_review")
            st.rerun()


def display_risk_analysis(risks: List):
    """Display risk analysis results"""
    
    if not risks:
        st.info("No specific risks identified in the analysis.")
        return
    
    for i, risk in enumerate(risks, 1):
        severity_color = {
            'Low': '🟢',
            'Medium': '🟡',
            'High': '🟠',
            'Critical': '🔴'
        }.get(risk.severity, '⚪')
        
        with st.expander(f"{severity_color} {risk.risk_type} - {risk.severity}", expanded=risk.severity in ['High', 'Critical']):
            st.markdown(f"**Description:** {risk.description}")
            st.markdown(f"**Recommendation:** {risk.recommendation}")
            st.markdown(f"**Compliance Impact:** {risk.compliance_impact}")


def display_compliance_review(compliance_checks: List):
    """Display compliance review results"""
    
    if not compliance_checks:
        st.info("No compliance checks performed.")
        return
    
    for check in compliance_checks:
        status_color = {
            'Compliant': '✅',
            'Non-Compliant': '❌',
            'Requires Review': '⚠️'
        }.get(check.status, '❓')
        
        with st.expander(f"{status_color} {check.category} - {check.status}", expanded=check.status == 'Non-Compliant'):
            st.markdown(f"**Description:** {check.description}")
            st.markdown(f"**Evidence:** {check.evidence}")
            st.markdown(f"**Remediation:** {check.remediation}")


def display_governance_analysis(governance_analysis: List):
    """Display governance analysis results"""
    
    if not governance_analysis:
        st.info("No governance analysis performed.")
        return
    
    for gov in governance_analysis:
        with st.expander(f"🏛️ {gov.aspect} - {gov.assessment}"):
            st.markdown(f"**Findings:** {gov.findings}")
            st.markdown(f"**Recommendations:** {gov.recommendations}")


def display_recommendations(result: ContractReviewResult):
    """Display recommendations and next steps"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(result.recommendations, 1):
            st.markdown(f"{i}. {rec}")
    
    with col2:
        st.subheader("📋 Next Steps")
        for i, step in enumerate(result.next_steps, 1):
            st.markdown(f"{i}. {step}")


def display_full_report(result: ContractReviewResult):
    """Display the complete review report"""
    
    report = st.session_state.contract_reviewer.generate_review_report(result)
    
    st.markdown(report)
    
    # Download button
    st.download_button(
        label="📥 Download Full Report",
        data=report,
        file_name=f"contract_review_{result.contract_id}.md",
        mime="text/markdown"
    )


def save_review_results(result: ContractReviewResult):
    """Save review results to session state and local storage"""
    
    try:
        # Convert result to dictionary for storage
        result_dict = {
            'contract_id': result.contract_id,
            'review_date': result.review_date,
            'ai_model_used': result.ai_model_used,
            'overall_risk_score': result.overall_risk_score,
            'compliance_score': result.compliance_score,
            'governance_score': result.governance_score,
            'executive_summary': result.executive_summary,
            'critical_issues': result.critical_issues,
            'recommendations': result.recommendations,
            'next_steps': result.next_steps
        }
        
        # Save to session state
        if 'saved_reviews' not in st.session_state:
            st.session_state.saved_reviews = []
        
        st.session_state.saved_reviews.append(result_dict)
        
        st.success("✅ Review results saved successfully!")
        
    except Exception as e:
        st.error(f"❌ Failed to save results: {e}")


def export_review_report(result: ContractReviewResult):
    """Export review report in various formats"""
    
    try:
        report = st.session_state.contract_reviewer.generate_review_report(result)
        
        # JSON export
        json_data = {
            'contract_id': result.contract_id,
            'review_date': result.review_date,
            'ai_model_used': result.ai_model_used,
            'overall_risk_score': result.overall_risk_score,
            'compliance_score': result.compliance_score,
            'governance_score': result.governance_score,
            'executive_summary': result.executive_summary,
            'critical_issues': result.critical_issues,
            'recommendations': result.recommendations,
            'next_steps': result.next_steps,
            'risks': [
                {
                    'risk_type': risk.risk_type,
                    'severity': risk.severity,
                    'description': risk.description,
                    'recommendation': risk.recommendation,
                    'compliance_impact': risk.compliance_impact
                } for risk in result.risks
            ],
            'compliance_checks': [
                {
                    'category': check.category,
                    'status': check.status,
                    'description': check.description,
                    'evidence': check.evidence,
                    'remediation': check.remediation
                } for check in result.compliance_checks
            ],
            'governance_analysis': [
                {
                    'aspect': gov.aspect,
                    'assessment': gov.assessment,
                    'findings': gov.findings,
                    'recommendations': gov.recommendations
                } for gov in result.governance_analysis
            ]
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📄 Download Markdown Report",
                data=report,
                file_name=f"contract_review_{result.contract_id}.md",
                mime="text/markdown"
            )
        
        with col2:
            st.download_button(
                label="📊 Download JSON Data",
                data=json.dumps(json_data, indent=2),
                file_name=f"contract_review_{result.contract_id}.json",
                mime="application/json"
            )
        
        st.success("✅ Export options ready!")
        
    except Exception as e:
        st.error(f"❌ Failed to export report: {e}")


def show_contract_review_dashboard():
    """Display dashboard of saved contract reviews"""
    
    st.title("📊 Contract Review Dashboard")
    st.markdown("**Historical Contract Reviews & Analytics**")
    
    if 'saved_reviews' not in st.session_state or not st.session_state.saved_reviews:
        st.info("No saved contract reviews found. Complete a contract review to see analytics here.")
        return
    
    reviews = st.session_state.saved_reviews
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reviews", len(reviews))
    
    with col2:
        high_risk = len([r for r in reviews if r['overall_risk_score'] in ['High', 'Critical']])
        st.metric("High Risk Contracts", high_risk)
    
    with col3:
        non_compliant = len([r for r in reviews if r['compliance_score'] == 'Non-Compliant'])
        st.metric("Non-Compliant", non_compliant)
    
    with col4:
        avg_reviews = len(reviews) / 30 if len(reviews) > 0 else 0  # Assuming monthly view
        st.metric("Avg Reviews/Month", f"{avg_reviews:.1f}")
    
    # Recent reviews table
    st.subheader("📋 Recent Reviews")
    
    for review in reviews[-5:]:  # Show last 5 reviews
        with st.expander(f"Contract {review['contract_id']} - {review['review_date']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Risk", review['overall_risk_score'])
            
            with col2:
                st.metric("Compliance", review['compliance_score'])
            
            with col3:
                st.metric("Governance", review['governance_score'])
            
            st.markdown(f"**Summary:** {review['executive_summary']}")
            
            if review['critical_issues']:
                st.warning("Critical Issues Found:")
                for issue in review['critical_issues']:
                    st.markdown(f"• {issue}")
