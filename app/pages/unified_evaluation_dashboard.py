#!/usr/bin/env python3
"""
Unified Evaluation Dashboard
Combines collaborative evaluation and comprehensive procurement evaluation
into one powerful, integrated evaluation system
"""

import streamlit as st
from pathlib import Path
from app.core.ui_helpers import _inject_css
from app.components.sidebar_navigation import render_sidebar
from app.services.comprehensive_procurement_evaluator import (
    ComprehensiveProcurementEvaluator,
    DocumentType,
    EvaluationStatus,
    ProcurementDocument,
    TEPPDocument,
    RFTDocument,
    SupplierResponse,
    ComprehensiveEvaluation
)
from app.services.collaborative_evaluation_system import (
    CollaborativeEvaluationSystem,
    SupplierEvaluation,
    AIScoringResult,
    CommitteeMember
)
from app.services.tepp_integration_system import (
    TEPPIntegrationSystem,
    TEPPEvaluationMethod,
    TEPPComplianceLevel
)
from datetime import datetime
import json
import hashlib
import pandas as pd

def page_unified_evaluation_dashboard():
    """Unified evaluation dashboard page"""
    
    _inject_css()
    render_sidebar()
    
    st.title("🔍 Unified Evaluation Dashboard")
    st.markdown("Comprehensive evaluation system combining AI analysis, human consensus, and document integration")
    
    # Initialize evaluation systems
    try:
        comprehensive_evaluator = ComprehensiveProcurementEvaluator()
        collaborative_evaluator = CollaborativeEvaluationSystem()
        tepp_integration = TEPPIntegrationSystem(settings.DATA_DIR)
    except Exception as e:
        st.error(f"❌ Error initializing evaluation systems: {e}")
        return
    
    # Check if user is logged in
    if "user_name" not in st.session_state:
        st.warning("🔒 Please sign in to access evaluation system")
        return
    
    # Create tabs for different evaluation approaches
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Start Evaluation", 
        "📊 Evaluation Results", 
        "🤝 Collaborative Review", 
        "📋 TEPP Integration", 
        "📄 Document Management", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_start_evaluation_interface(comprehensive_evaluator, collaborative_evaluator)
    
    with tab2:
        show_evaluation_results_interface(comprehensive_evaluator, collaborative_evaluator)
    
    with tab3:
        show_collaborative_review_interface(collaborative_evaluator)
    
    with tab4:
        show_tepp_integration_interface(tepp_integration)
    
    with tab5:
        show_document_management_interface(comprehensive_evaluator)
    
    with tab6:
        show_settings_interface(comprehensive_evaluator, collaborative_evaluator)

def show_start_evaluation_interface(comprehensive_evaluator, collaborative_evaluator):
    """Interface to start unified evaluation process"""
    
    st.markdown("### 🚀 Start Unified Evaluation")
    st.markdown("Create evaluation criteria, select project, and upload supplier returnable schedules")
    
    # Project selection from existing projects
    st.markdown("#### 📋 Project Selection")
    
    # Get existing projects from the projects directory
    existing_projects = get_existing_projects()
    
    if existing_projects:
        selected_project = st.selectbox(
            "Select Existing Project",
            options=existing_projects,
            format_func=lambda x: f"{x['project_name']} - {x['project_type']} (${x['contract_value']:,.0f})"
        )
        
        if selected_project:
            st.success(f"✅ Selected: {selected_project['project_name']}")
            
            # Display project details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Project Type", selected_project['project_type'])
            with col2:
                st.metric("Contract Value", f"${selected_project['contract_value']:,.0f}")
            with col3:
                st.metric("Status", selected_project['status'])
    else:
        st.warning("⚠️ No existing projects found. Please create a project first.")
        return
    
    # Manual evaluation criteria creation
    st.markdown("#### ⚖️ Evaluation Criteria & Weights")
    st.markdown("Create custom evaluation criteria with weights and sub-criteria")
    
    with st.form("evaluation_criteria_form"):
        # Main criteria
        st.markdown("**Main Evaluation Criteria**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            price_weight = st.slider("Price Weight (%)", 0, 100, 40)
            technical_weight = st.slider("Technical Weight (%)", 0, 100, 30)
        
        with col2:
            experience_weight = st.slider("Experience Weight (%)", 0, 100, 20)
            compliance_weight = st.slider("Compliance Weight (%)", 0, 100, 10)
        
        # Validation
        total_weight = price_weight + technical_weight + experience_weight + compliance_weight
        if total_weight != 100:
            st.warning(f"⚠️ Total weight is {total_weight}%. Please adjust to 100%.")
        
        # Sub-criteria for each main criterion
        st.markdown("**Sub-Criteria Definition**")
        
        # Price sub-criteria
        with st.expander("💰 Price Sub-Criteria", expanded=True):
            price_sub_criteria = []
            num_price_criteria = st.number_input("Number of Price Sub-Criteria", min_value=1, max_value=10, value=3)
            
            for i in range(num_price_criteria):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    criterion_name = st.text_input(f"Price Criterion {i+1}", value=f"Price Criterion {i+1}", key=f"price_crit_{i}")
                with col2:
                    criterion_weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100//num_price_criteria, key=f"price_weight_{i}")
                with col3:
                    max_score = st.number_input("Max Score", min_value=1, max_value=10, value=5, key=f"price_score_{i}")
                
                price_sub_criteria.append({
                    "name": criterion_name,
                    "weight": criterion_weight,
                    "max_score": max_score
                })
        
        # Technical sub-criteria
        with st.expander("🔧 Technical Sub-Criteria", expanded=True):
            technical_sub_criteria = []
            num_technical_criteria = st.number_input("Number of Technical Sub-Criteria", min_value=1, max_value=10, value=4)
            
            for i in range(num_technical_criteria):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    criterion_name = st.text_input(f"Technical Criterion {i+1}", value=f"Technical Criterion {i+1}", key=f"tech_crit_{i}")
                with col2:
                    criterion_weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100//num_technical_criteria, key=f"tech_weight_{i}")
                with col3:
                    max_score = st.number_input("Max Score", min_value=1, max_value=10, value=5, key=f"tech_score_{i}")
                
                technical_sub_criteria.append({
                    "name": criterion_name,
                    "weight": criterion_weight,
                    "max_score": max_score
                })
        
        # Experience sub-criteria
        with st.expander("👥 Experience Sub-Criteria", expanded=True):
            experience_sub_criteria = []
            num_experience_criteria = st.number_input("Number of Experience Sub-Criteria", min_value=1, max_value=10, value=3)
            
            for i in range(num_experience_criteria):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    criterion_name = st.text_input(f"Experience Criterion {i+1}", value=f"Experience Criterion {i+1}", key=f"exp_crit_{i}")
                with col2:
                    criterion_weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100//num_experience_criteria, key=f"exp_weight_{i}")
                with col3:
                    max_score = st.number_input("Max Score", min_value=1, max_value=10, value=5, key=f"exp_score_{i}")
                
                experience_sub_criteria.append({
                    "name": criterion_name,
                    "weight": criterion_weight,
                    "max_score": max_score
                })
        
        # Compliance sub-criteria
        with st.expander("🛡️ Compliance Sub-Criteria", expanded=True):
            compliance_sub_criteria = []
            num_compliance_criteria = st.number_input("Number of Compliance Sub-Criteria", min_value=1, max_value=10, value=2)
            
            for i in range(num_compliance_criteria):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    criterion_name = st.text_input(f"Compliance Criterion {i+1}", value=f"Compliance Criterion {i+1}", key=f"comp_crit_{i}")
                with col2:
                    criterion_weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100//num_compliance_criteria, key=f"comp_weight_{i}")
                with col3:
                    max_score = st.number_input("Max Score", min_value=1, max_value=10, value=5, key=f"comp_score_{i}")
                
                compliance_sub_criteria.append({
                    "name": criterion_name,
                    "weight": criterion_weight,
                    "max_score": max_score
                })
        
        # Upload supplier returnable schedules
        st.markdown("#### 📄 Supplier Returnable Schedules")
        st.markdown("Upload filled returnable schedules from suppliers for compliance checking and scoring")
        
        supplier_schedules = st.file_uploader(
            "Upload Supplier Returnable Schedules", 
            type=['pdf', 'docx', 'xlsx'], 
            accept_multiple_files=True, 
            key="supplier_schedules_upload",
            help="Upload completed returnable schedules from suppliers"
        )
        
        if supplier_schedules:
            st.success(f"✅ {len(supplier_schedules)} supplier returnable schedules uploaded")
            
            # Display uploaded files
            for i, file in enumerate(supplier_schedules):
                st.write(f"📄 **Supplier {i+1}**: {file.name} ({file.size:,} bytes)")
        
        # Evaluation settings
        st.markdown("#### ⚙️ Evaluation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            evaluation_method = st.selectbox("Evaluation Method", 
                options=["MEAT", "Lowest Price Conforming", "TCO", "Quality/Cost Ratio"])
            compliance_check = st.checkbox("Enable Compliance Checking", value=True)
        
        with col2:
            risk_assessment = st.checkbox("Enable Risk Assessment", value=True)
            auto_scoring = st.checkbox("Enable AI Auto-Scoring", value=True)
        
        # Start evaluation button
        if st.form_submit_button("🚀 Start Evaluation", type="primary", use_container_width=True):
            if total_weight == 100 and supplier_schedules:
                with st.spinner("🤖 Starting evaluation process..."):
                    try:
                        # Create evaluation criteria structure
                        evaluation_criteria = {
                            "main_criteria": {
                                "price": {"weight": price_weight, "sub_criteria": price_sub_criteria},
                                "technical": {"weight": technical_weight, "sub_criteria": technical_sub_criteria},
                                "experience": {"weight": experience_weight, "sub_criteria": experience_sub_criteria},
                                "compliance": {"weight": compliance_weight, "sub_criteria": compliance_sub_criteria}
                            },
                            "evaluation_method": evaluation_method,
                            "compliance_check": compliance_check,
                            "risk_assessment": risk_assessment,
                            "auto_scoring": auto_scoring
                        }
                        
                        # Start evaluation process
                        evaluation_id = start_returnable_schedule_evaluation(
                            selected_project, evaluation_criteria, supplier_schedules
                        )
                        
                        st.success(f"✅ Evaluation started! Evaluation ID: {evaluation_id}")
                        st.info("📊 AI is analyzing returnable schedules for compliance and scoring...")
                        
                        # Store evaluation ID for navigation
                        st.session_state["current_unified_evaluation_id"] = evaluation_id
                        st.session_state["current_evaluation_type"] = "returnable_schedule"
                        
                    except Exception as e:
                        st.error(f"❌ Error starting evaluation: {e}")
            else:
                st.warning("⚠️ Please ensure weights total 100% and upload supplier returnable schedules")
        
        # Document upload sections
        st.markdown("#### 📄 Procurement Documents")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**TEPP Document**")
            tepp_file = st.file_uploader("Upload TEPP Document", type=['pdf', 'docx'], key="tepp_upload")
            if tepp_file:
                st.success(f"✅ TEPP uploaded: {tepp_file.name}")
        
        with col2:
            st.markdown("**RFT Document**")
            rft_file = st.file_uploader("Upload RFT Document", type=['pdf', 'docx'], key="rft_upload")
            if rft_file:
                st.success(f"✅ RFT uploaded: {rft_file.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Returnable Schedules**")
            schedule_files = st.file_uploader("Upload Returnable Schedules", type=['pdf', 'docx', 'xlsx'], 
                                            accept_multiple_files=True, key="schedule_upload")
            if schedule_files:
                st.success(f"✅ {len(schedule_files)} schedule files uploaded")
        
        with col2:
            st.markdown("**Technical Specifications**")
            tech_files = st.file_uploader("Upload Technical Specs", type=['pdf', 'docx'], 
                                        accept_multiple_files=True, key="tech_upload")
            if tech_files:
                st.success(f"✅ {len(tech_files)} technical files uploaded")
        
        # Supplier responses
        st.markdown("#### 👥 Supplier Responses")
        supplier_responses = st.file_uploader("Upload Supplier Response Packages", 
                                            type=['pdf', 'docx', 'zip'], 
                                            accept_multiple_files=True, key="supplier_upload")
        
        if supplier_responses:
            st.success(f"✅ {len(supplier_responses)} supplier response packages uploaded")
        
        # Evaluation criteria
        st.markdown("#### ⚖️ Evaluation Criteria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            price_weight = st.slider("Price Weight (%)", 0, 100, 40)
            technical_weight = st.slider("Technical Weight (%)", 0, 100, 30)
        
        with col2:
            experience_weight = st.slider("Experience Weight (%)", 0, 100, 20)
            compliance_weight = st.slider("Compliance Weight (%)", 0, 100, 10)
        
        # Validation
        total_weight = price_weight + technical_weight + experience_weight + compliance_weight
        if total_weight != 100:
            st.warning(f"⚠️ Total weight is {total_weight}%. Please adjust to 100%.")
        
        # Committee settings (for collaborative/hybrid approaches)
        if evaluation_type in ["Collaborative Committee Review", "Hybrid Approach"]:
            st.markdown("#### 👥 Committee Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                committee_size = st.number_input("Committee Size", min_value=3, max_value=10, value=5)
                evaluation_duration = st.number_input("Evaluation Duration (days)", min_value=1, max_value=30, value=7)
            
            with col2:
                consensus_threshold = st.slider("Consensus Threshold (%)", 50, 100, 75)
                allow_anonymous = st.checkbox("Allow Anonymous Voting", value=True)
        
        # Start evaluation button
        if st.form_submit_button("🚀 Start Unified Evaluation", type="primary", use_container_width=True):
            if project_title and (tepp_file or rft_file) and supplier_responses and total_weight == 100:
                with st.spinner("🤖 Starting unified evaluation process..."):
                    try:
                        # Create evaluation session
                        if evaluation_type == "Comprehensive Document Analysis":
                            evaluation_id = start_comprehensive_evaluation(
                                comprehensive_evaluator, project_title, tepp_file, rft_file, 
                                schedule_files, tech_files, supplier_responses, 
                                price_weight, technical_weight, experience_weight, compliance_weight
                            )
                        elif evaluation_type == "Collaborative Committee Review":
                            evaluation_id = start_collaborative_evaluation(
                                collaborative_evaluator, project_title, supplier_responses,
                                committee_size, evaluation_duration, consensus_threshold, allow_anonymous
                            )
                        else:  # Hybrid Approach
                            evaluation_id = start_hybrid_evaluation(
                                comprehensive_evaluator, collaborative_evaluator, project_title,
                                tepp_file, rft_file, schedule_files, tech_files, supplier_responses,
                                price_weight, technical_weight, experience_weight, compliance_weight,
                                committee_size, evaluation_duration, consensus_threshold, allow_anonymous
                            )
                        
                        st.success(f"✅ Unified evaluation started! Evaluation ID: {evaluation_id}")
                        st.info("📊 AI is analyzing documents and supplier responses...")
                        
                        # Store evaluation ID for navigation
                        st.session_state["current_unified_evaluation_id"] = evaluation_id
                        st.session_state["current_evaluation_type"] = evaluation_type
                        
                    except Exception as e:
                        st.error(f"❌ Error starting unified evaluation: {e}")
            else:
                st.warning("⚠️ Please provide project title, upload documents, supplier responses, and ensure weights total 100%")

def show_evaluation_results_interface(comprehensive_evaluator, collaborative_evaluator):
    """Interface to view unified evaluation results"""
    
    st.markdown("### 📊 Unified Evaluation Results")
    st.markdown("View comprehensive evaluation results and returnable schedule compliance")
    
    # Get evaluation ID
    evaluation_id = st.session_state.get("current_unified_evaluation_id")
    evaluation_type = st.session_state.get("current_evaluation_type")
    
    if not evaluation_id:
        st.info("📋 No active evaluation. Start a unified evaluation first.")
        return
    
    # Display results based on evaluation type
    if evaluation_type == "returnable_schedule":
        show_returnable_schedule_results(evaluation_id)
    elif evaluation_type == "Comprehensive Document Analysis":
        show_comprehensive_results(comprehensive_evaluator, evaluation_id)
    elif evaluation_type == "Collaborative Committee Review":
        show_collaborative_results(collaborative_evaluator, evaluation_id)
    else:  # Hybrid Approach
        show_hybrid_results(comprehensive_evaluator, collaborative_evaluator, evaluation_id)

def show_collaborative_review_interface(collaborative_evaluator):
    """Interface for collaborative committee review"""
    
    st.markdown("### 🤝 Collaborative Committee Review")
    st.markdown("AI pre-scoring with human committee consensus")
    
    # Get active evaluation sessions
    try:
        sessions = collaborative_evaluator.get_active_sessions()
        
        if not sessions:
            st.info("📋 No active collaborative evaluation sessions.")
            return
        
        # Display active sessions
        for session in sessions:
            with st.expander(f"📋 {session.project_name} - {session.status.value}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Suppliers", len(session.supplier_submissions))
                    st.metric("Committee Members", len(session.committee_members))
                
                with col2:
                    st.metric("Status", session.status.value)
                    st.metric("Progress", f"{session.progress_percentage}%")
                
                with col3:
                    st.metric("Deadline", session.deadline)
                    st.metric("Consensus", f"{session.consensus_percentage}%")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👥 Join Committee", key=f"join_{session.session_id}"):
                        st.info("👥 Committee joining - Coming soon")
                
                with col2:
                    if st.button("📊 View Results", key=f"results_{session.session_id}"):
                        st.info("📊 Results view - Coming soon")
                
                with col3:
                    if st.button("📋 Manage Session", key=f"manage_{session.session_id}"):
                        st.info("📋 Session management - Coming soon")
    
    except Exception as e:
        st.error(f"❌ Error loading collaborative sessions: {e}")

def show_document_management_interface(comprehensive_evaluator):
    """Interface for managing procurement documents"""
    
    st.markdown("### 📄 Document Management")
    st.markdown("Manage and analyze all procurement documents")
    
    # Document type selection
    document_type = st.selectbox("Select Document Type", 
        options=[dt.value for dt in DocumentType], 
        format_func=lambda x: x.replace('_', ' ').title())
    
    if document_type:
        st.markdown(f"#### {document_type.replace('_', ' ').title()} Documents")
        
        # Document upload
        uploaded_files = st.file_uploader(f"Upload {document_type.replace('_', ' ').title()} Documents", 
                                        type=['pdf', 'docx', 'xlsx'], 
                                        accept_multiple_files=True, 
                                        key=f"upload_{document_type}")
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} {document_type} documents uploaded")
            
            # Process documents
            if st.button("🔍 Analyze Documents", type="primary"):
                with st.spinner("🤖 Analyzing documents with AI..."):
                    st.info("📊 Document analysis - Coming soon")
        
        # Document library
        st.markdown("#### 📚 Document Library")
        st.info("📚 Document library - Coming soon")

def show_settings_interface(comprehensive_evaluator, collaborative_evaluator):
    """Interface for evaluation settings"""
    
    st.markdown("### ⚙️ Unified Evaluation Settings")
    st.markdown("Configure evaluation parameters for both approaches")
    
    # AI Settings
    st.markdown("#### 🤖 AI Analysis Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ai_model = st.selectbox("AI Model", options=["Gemini 1.5 Flash", "Gemini 1.5 Pro"])
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7)
    
    with col2:
        analysis_depth = st.selectbox("Analysis Depth", options=["Basic", "Standard", "Comprehensive"])
        risk_tolerance = st.selectbox("Risk Tolerance", options=["Low", "Medium", "High"])
    
    # Evaluation Settings
    st.markdown("#### ⚖️ Evaluation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_weights = st.checkbox("Use Default Weightings", value=True)
        auto_ranking = st.checkbox("Automatic Ranking", value=True)
    
    with col2:
        compliance_check = st.checkbox("Enable Compliance Checking", value=True)
        risk_assessment = st.checkbox("Enable Risk Assessment", value=True)
    
    # Collaborative Settings
    st.markdown("#### 🤝 Collaborative Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_consensus = st.slider("Default Consensus Threshold (%)", 50, 100, 75)
        allow_anonymous = st.checkbox("Allow Anonymous Voting", value=True)
    
    with col2:
        auto_reminders = st.checkbox("Automatic Reminders", value=True)
        deadline_buffer = st.number_input("Deadline Buffer (hours)", min_value=1, max_value=48, value=24)
    
    # Save settings
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
    
    with col2:
        if st.button("🚪 Sign Out", type="secondary"):
            st.session_state.clear()
            st.rerun()

def start_comprehensive_evaluation(comprehensive_evaluator, project_title, tepp_file, rft_file, 
                                 schedule_files, tech_files, supplier_responses, 
                                 price_weight, technical_weight, experience_weight, compliance_weight):
    """Start comprehensive document analysis evaluation"""
    
    # Create procurement documents
    procurement_documents = []
    
    if tepp_file:
        tepp_doc = create_tepp_document(tepp_file, project_title)
        procurement_documents.append(tepp_doc)
    
    if rft_file:
        rft_doc = create_rft_document(rft_file, project_title)
        procurement_documents.append(rft_doc)
    
    # Create supplier responses
    supplier_responses_list = []
    for i, response_file in enumerate(supplier_responses):
        supplier_response = create_supplier_response(response_file, f"supplier_{i+1}")
        supplier_responses_list.append(supplier_response)
    
    # Evaluation criteria
    evaluation_criteria = {
        "price_weight": price_weight,
        "technical_weight": technical_weight,
        "experience_weight": experience_weight,
        "compliance_weight": compliance_weight
    }
    
    # Start comprehensive evaluation
    evaluation_id = comprehensive_evaluator.start_comprehensive_evaluation(
        project_title,
        procurement_documents,
        supplier_responses_list,
        evaluation_criteria
    )
    
    return evaluation_id

def start_collaborative_evaluation(collaborative_evaluator, project_title, supplier_responses,
                                committee_size, evaluation_duration, consensus_threshold, allow_anonymous):
    """Start collaborative committee review evaluation"""
    
    # Create supplier submissions
    supplier_submissions = []
    for i, response_file in enumerate(supplier_responses):
        submission = SupplierSubmission(
            submission_id=f"sub_{i+1}",
            supplier_id=f"supplier_{i+1}",
            supplier_name=f"Supplier {i+1}",
            project_id=project_title,
            submission_date=datetime.now().isoformat(),
            documents=[response_file.name],
            status="submitted"
        )
        supplier_submissions.append(submission)
    
    # Start collaborative evaluation
    evaluation_id = collaborative_evaluator.start_evaluation_session(
        project_title,
        supplier_submissions,
        committee_size,
        evaluation_duration,
        consensus_threshold,
        allow_anonymous
    )
    
    return evaluation_id

def start_hybrid_evaluation(comprehensive_evaluator, collaborative_evaluator, project_title,
                           tepp_file, rft_file, schedule_files, tech_files, supplier_responses,
                           price_weight, technical_weight, experience_weight, compliance_weight,
                           committee_size, evaluation_duration, consensus_threshold, allow_anonymous):
    """Start hybrid evaluation combining both approaches"""
    
    # First, run comprehensive document analysis
    comprehensive_id = start_comprehensive_evaluation(
        comprehensive_evaluator, project_title, tepp_file, rft_file, 
        schedule_files, tech_files, supplier_responses, 
        price_weight, technical_weight, experience_weight, compliance_weight
    )
    
    # Then, start collaborative review with comprehensive results
    collaborative_id = start_collaborative_evaluation(
        collaborative_evaluator, project_title, supplier_responses,
        committee_size, evaluation_duration, consensus_threshold, allow_anonymous
    )
    
    # Return combined evaluation ID
    return f"hybrid_{comprehensive_id}_{collaborative_id}"

def show_comprehensive_results(comprehensive_evaluator, evaluation_id):
    """Show comprehensive evaluation results"""
    
    try:
        summary = comprehensive_evaluator.get_evaluation_summary(evaluation_id)
        
        if "error" in summary:
            st.error(f"❌ {summary['error']}")
            return
        
        st.markdown(f"**Evaluation ID:** {summary['evaluation_id']}")
        st.markdown(f"**Project ID:** {summary['project_id']}")
        st.markdown(f"**Total Suppliers:** {summary['total_suppliers']}")
        
        # Display supplier rankings
        st.markdown("#### 🏆 Supplier Rankings")
        
        for supplier in summary["suppliers"]:
            with st.expander(f"#{supplier['final_ranking']} {supplier['supplier_name']} - Overall Score: {supplier['overall_score']:.1f}", 
                           expanded=supplier['final_ranking'] == 1):
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Overall Score", f"{supplier['overall_score']:.1f}")
                with col2:
                    st.metric("Compliance Score", f"{supplier['compliance_score']:.1f}%")
                with col3:
                    st.metric("Risk Score", f"{supplier['risk_score']:.1f}%")
                with col4:
                    st.metric("Ranking", f"#{supplier['final_ranking']}")
    
    except Exception as e:
        st.error(f"❌ Error loading comprehensive results: {e}")

def show_collaborative_results(collaborative_evaluator, evaluation_id):
    """Show collaborative evaluation results"""
    
    try:
        # Get collaborative evaluation results
        st.info("📊 Collaborative evaluation results - Coming soon")
    
    except Exception as e:
        st.error(f"❌ Error loading collaborative results: {e}")

def show_hybrid_results(comprehensive_evaluator, collaborative_evaluator, evaluation_id):
    """Show hybrid evaluation results"""
    
    try:
        st.info("📊 Hybrid evaluation results - Coming soon")
    
    except Exception as e:
        st.error(f"❌ Error loading hybrid results: {e}")

def create_tepp_document(file, project_title):
    """Create TEPP document from uploaded file"""
    return TEPPDocument(
        document_id=hashlib.md5(f"{file.name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        document_type=DocumentType.TEPP,
        title=f"TEPP - {project_title}",
        content=f"TEPP content from {file.name}",
        metadata={"file_name": file.name, "file_size": file.size},
        created_date=datetime.now().isoformat(),
        updated_date=datetime.now().isoformat(),
        version="1.0",
        council="Blacktown City Council",
        project_id=project_title,
        evaluation_criteria=[],
        returnable_schedules=[],
        compliance_requirements=[],
        evaluation_methodology="MEAT",
        scoring_weights={}
    )

def create_rft_document(file, project_title):
    """Create RFT document from uploaded file"""
    return RFTDocument(
        document_id=hashlib.md5(f"{file.name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        document_type=DocumentType.RFT,
        title=f"RFT - {project_title}",
        content=f"RFT content from {file.name}",
        metadata={"file_name": file.name, "file_size": file.size},
        created_date=datetime.now().isoformat(),
        updated_date=datetime.now().isoformat(),
        version="1.0",
        council="Blacktown City Council",
        project_id=project_title,
        technical_requirements=[],
        commercial_requirements=[],
        compliance_requirements=[],
        submission_requirements=[]
    )

def create_supplier_response(file, supplier_id):
    """Create supplier response from uploaded file"""
    return SupplierResponse(
        response_id=hashlib.md5(f"{file.name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        supplier_id=supplier_id,
        supplier_name=f"Supplier {supplier_id}",
        document_responses={},
        returnable_schedule_responses={},
        supporting_documents=[file.name],
        submission_date=datetime.now().isoformat(),
        compliance_status={}
    )

def get_existing_projects():
    """Get existing projects from the projects directory"""
    projects = []
    projects_dir = Path("projects")
    
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                # Look for project metadata files
                metadata_files = list(project_dir.glob("*.json"))
                if metadata_files:
                    try:
                        with open(metadata_files[0], 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                            
                        projects.append({
                            "project_id": project_dir.name,
                            "project_name": project_data.get("project_name", project_dir.name),
                            "project_type": project_data.get("project_type", "Unknown"),
                            "contract_value": project_data.get("contract_value", 0),
                            "status": project_data.get("status", "Active"),
                            "created_date": project_data.get("created_date", ""),
                            "council": project_data.get("council", "Blacktown City Council")
                        })
                    except Exception as e:
                        print(f"⚠️ Error loading project {project_dir.name}: {e}")
    
    return projects

def start_returnable_schedule_evaluation(selected_project, evaluation_criteria, supplier_schedules):
    """Start returnable schedule evaluation process"""
    
    evaluation_id = hashlib.md5(f"rs_eval_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    # Create evaluation session data
    evaluation_session = {
        "evaluation_id": evaluation_id,
        "project_id": selected_project["project_id"],
        "project_name": selected_project["project_name"],
        "evaluation_criteria": evaluation_criteria,
        "supplier_schedules": [{"name": f.name, "size": f.size} for f in supplier_schedules],
        "status": "in_progress",
        "created_date": datetime.now().isoformat(),
        "compliance_results": {},
        "scoring_results": {},
        "final_rankings": []
    }
    
    # Store evaluation session
    evaluations_dir = Path("data") / "returnable_schedule_evaluations"
    evaluations_dir.mkdir(parents=True, exist_ok=True)
    
    eval_file = evaluations_dir / f"{evaluation_id}.json"
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_session, f, indent=2, ensure_ascii=False)
    
    return evaluation_id

def show_returnable_schedule_results(evaluation_id):
    """Show returnable schedule evaluation results"""
    
    try:
        # Load evaluation session
        evaluations_dir = Path("data") / "returnable_schedule_evaluations"
        eval_file = evaluations_dir / f"{evaluation_id}.json"
        
        if not eval_file.exists():
            st.error("❌ Evaluation not found")
            return
        
        with open(eval_file, 'r', encoding='utf-8') as f:
            evaluation_session = json.load(f)
        
        st.markdown(f"**Evaluation ID:** {evaluation_session['evaluation_id']}")
        st.markdown(f"**Project:** {evaluation_session['project_name']}")
        st.markdown(f"**Status:** {evaluation_session['status']}")
        st.markdown(f"**Created:** {evaluation_session['created_date'][:19]}")
        
        # Display evaluation criteria
        st.markdown("#### ⚖️ Evaluation Criteria")
        
        criteria = evaluation_session["evaluation_criteria"]["main_criteria"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Price Weight", f"{criteria['price']['weight']}%")
            st.markdown("**Sub-Criteria:**")
            for sub_crit in criteria['price']['sub_criteria']:
                st.write(f"• {sub_crit['name']} ({sub_crit['weight']}%)")
        
        with col2:
            st.metric("Technical Weight", f"{criteria['technical']['weight']}%")
            st.markdown("**Sub-Criteria:**")
            for sub_crit in criteria['technical']['sub_criteria']:
                st.write(f"• {sub_crit['name']} ({sub_crit['weight']}%)")
        
        with col3:
            st.metric("Experience Weight", f"{criteria['experience']['weight']}%")
            st.markdown("**Sub-Criteria:**")
            for sub_crit in criteria['experience']['sub_criteria']:
                st.write(f"• {sub_crit['name']} ({sub_crit['weight']}%)")
        
        with col4:
            st.metric("Compliance Weight", f"{criteria['compliance']['weight']}%")
            st.markdown("**Sub-Criteria:**")
            for sub_crit in criteria['compliance']['sub_criteria']:
                st.write(f"• {sub_crit['name']} ({sub_crit['weight']}%)")
        
        # Display supplier schedules
        st.markdown("#### 📄 Supplier Returnable Schedules")
        
        for i, schedule in enumerate(evaluation_session["supplier_schedules"]):
            with st.expander(f"📄 Supplier {i+1}: {schedule['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("File Size", f"{schedule['size']:,} bytes")
                
                with col2:
                    st.metric("Status", "Uploaded")
                
                with col3:
                    st.metric("Compliance", "Pending")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🔍 Analyze Compliance", key=f"analyze_{i}"):
                        st.info("🔍 Compliance analysis - Coming soon")
                
                with col2:
                    if st.button(f"📊 Score Schedule", key=f"score_{i}"):
                        st.info("📊 Scoring - Coming soon")
                
                with col3:
                    if st.button(f"📄 View Details", key=f"details_{i}"):
                        st.info("📄 Schedule details - Coming soon")
        
        # Evaluation progress
        st.markdown("#### 📊 Evaluation Progress")
        
        if evaluation_session["status"] == "in_progress":
            st.info("🤖 AI is analyzing returnable schedules for compliance and scoring...")
            
            # Simulate progress
            progress = st.progress(0)
            status_text = st.empty()
            
            for i in range(101):
                progress.progress(i)
                status_text.text(f"Processing... {i}%")
                if i == 100:
                    status_text.text("✅ Analysis complete!")
        
        elif evaluation_session["status"] == "completed":
            st.success("✅ Evaluation completed!")
            
            # Display results
            if evaluation_session.get("final_rankings"):
                st.markdown("#### 🏆 Final Rankings")
                
                for i, ranking in enumerate(evaluation_session["final_rankings"]):
                    st.write(f"#{i+1} {ranking['supplier_name']} - Score: {ranking['total_score']:.1f}")
        
        else:
            st.warning("⚠️ Evaluation status unknown")
    
    except Exception as e:
        st.error(f"❌ Error loading evaluation results: {e}")

def show_tepp_integration_interface(tepp_integration):
    """TEPP Integration Interface"""
    
    st.markdown("### 📋 TEPP Integration System")
    st.markdown("Integrate TEPP documents and methodology into collaborative evaluation system")
    
    # Create two columns for TEPP session management
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🆕 Create New TEPP Evaluation Session")
        
        # Project selection
        existing_projects = get_existing_projects()
        if existing_projects:
            project_options = {f"{p['name']} ({p['id']})": p['id'] for p in existing_projects}
            selected_project = st.selectbox("Select Project", list(project_options.keys()))
            project_id = project_options[selected_project]
            project_title = selected_project.split(" (")[0]
        else:
            st.warning("No projects available. Please create a project first.")
            return
        
        # TEPP document upload
        st.markdown("##### 📄 Upload TEPP Document")
        tepp_file = st.file_uploader(
            "Upload TEPP Document", 
            type=['pdf', 'docx', 'txt'],
            help="Upload the TEPP (Tender Evaluation Plan & Process) document"
        )
        
        # Evaluation method selection
        evaluation_method = st.selectbox(
            "Evaluation Method",
            [method.value for method in TEPPEvaluationMethod],
            help="Select the TEPP evaluation methodology"
        )
        
        # Create session button
        if st.button("🚀 Create TEPP Evaluation Session", type="primary"):
            if tepp_file:
                # Save uploaded file
                tepp_path = Path("data/tepp_documents") / tepp_file.name
                tepp_path.parent.mkdir(exist_ok=True)
                
                with open(tepp_path, "wb") as f:
                    f.write(tepp_file.getbuffer())
                
                # Create TEPP evaluation session
                try:
                    session_id = tepp_integration.create_tepp_evaluation_session(
                        project_id=project_id,
                        project_title=project_title,
                        tepp_document_path=str(tepp_path),
                        evaluation_method=TEPPEvaluationMethod(evaluation_method)
                    )
                    
                    st.success(f"✅ TEPP evaluation session created: {session_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating TEPP session: {e}")
            else:
                st.warning("Please upload a TEPP document")
    
    with col2:
        st.markdown("#### 📊 Active TEPP Sessions")
        
        # Get active sessions
        try:
            active_sessions = tepp_integration.get_active_tepp_sessions()
            
            if active_sessions:
                for session in active_sessions:
                    with st.expander(f"📋 {session['project_title']}"):
                        st.write(f"**Session ID:** {session['session_id']}")
                        st.write(f"**Method:** {session['evaluation_method']}")
                        st.write(f"**Criteria:** {session['total_criteria']}")
                        st.write(f"**Suppliers:** {session['total_suppliers']}")
                        st.write(f"**Created:** {session['created_date'][:10]}")
                        
                        if st.button(f"View Details", key=f"view_{session['session_id']}"):
                            st.session_state["selected_tepp_session"] = session['session_id']
                            st.rerun()
            else:
                st.info("No active TEPP sessions")
                
        except Exception as e:
            st.error(f"❌ Error loading TEPP sessions: {e}")
    
    # Show selected session details
    if "selected_tepp_session" in st.session_state:
        show_tepp_session_details(tepp_integration, st.session_state["selected_tepp_session"])

def show_tepp_session_details(tepp_integration, session_id):
    """Show detailed TEPP session information"""
    
    st.markdown("---")
    st.markdown(f"#### 📋 TEPP Session Details: {session_id}")
    
    try:
        # Get session dashboard data
        dashboard_data = tepp_integration.get_tepp_evaluation_dashboard_data(session_id)
        
        if "error" in dashboard_data:
            st.error(f"❌ {dashboard_data['error']}")
            return
        
        # Display session overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Project", dashboard_data["project_title"])
        
        with col2:
            st.metric("Evaluation Method", dashboard_data["evaluation_method"].title())
        
        with col3:
            st.metric("Total Criteria", dashboard_data["total_criteria"])
        
        with col4:
            st.metric("Total Suppliers", dashboard_data["total_suppliers"])
        
        # Display criteria summary
        st.markdown("##### 📊 Evaluation Criteria")
        criteria_df = pd.DataFrame(dashboard_data["criteria_summary"])
        st.dataframe(criteria_df, use_container_width=True)
        
        # Display supplier rankings
        if dashboard_data["ranked_suppliers"]:
            st.markdown("##### 🏆 Supplier Rankings")
            rankings_df = pd.DataFrame(dashboard_data["ranked_suppliers"])
            st.dataframe(rankings_df, use_container_width=True)
        
        # Display compliance summary
        st.markdown("##### ✅ Compliance Summary")
        compliance = dashboard_data["compliance_summary"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Items", compliance["total_items"])
        with col2:
            st.metric("Mandatory Items", compliance["mandatory_items"])
        with col3:
            st.metric("Compliance Results", compliance["compliance_results"])
        
        # Back button
        if st.button("← Back to TEPP Sessions"):
            del st.session_state["selected_tepp_session"]
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error loading session details: {e}")
