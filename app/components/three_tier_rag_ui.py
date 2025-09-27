#!/usr/bin/env python3
"""
Three-Tier RAG System UI Components
Provides user interface for managing and uploading documents to the three-tier RAG system
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..services.three_tier_rag_system import ThreeTierRAGSystem, RAGTier, DocumentCategory

def show_three_tier_rag_upload():
    """Show the three-tier RAG upload interface"""
    
    st.markdown("## 🌐 Three-Tier RAG Document Management")
    st.markdown("Upload and manage compliance documents across all three tiers for comprehensive procurement alignment")
    
    # Initialize the three-tier RAG system
    if 'three_tier_rag' not in st.session_state:
        st.session_state.three_tier_rag = ThreeTierRAGSystem(Path("data"))
    
    rag_system = st.session_state.three_tier_rag
    
    # Create tabs for each tier
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌍 Global RAG", 
        "🏛️ Internal RAG", 
        "📋 Project RAG", 
        "📊 Compliance Overview"
    ])
    
    with tab1:
        show_global_rag_interface(rag_system)
    
    with tab2:
        show_internal_rag_interface(rag_system)
    
    with tab3:
        show_project_rag_interface(rag_system)
    
    with tab4:
        show_compliance_overview(rag_system)

def show_global_rag_interface(rag_system: ThreeTierRAGSystem):
    """Show Global RAG (Tier 1) interface"""
    
    st.markdown("### 🌍 Global RAG - NSW Local Government Standards")
    st.markdown("Upload external NSW Local Government rules, regulations, and standards that apply to all councils")
    
    # Document categories for Global RAG
    global_categories = {
        "NSW Legislation": DocumentCategory.NSW_LEGISLATION,
        "Local Government Act": DocumentCategory.LOCAL_GOVT_ACT,
        "Procurement Guidelines": DocumentCategory.PROCUREMENT_GUIDELINES,
        "Tendering Standards": DocumentCategory.TENDERING_STANDARDS,
        "Evaluation Criteria": DocumentCategory.EVALUATION_CRITERIA
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📤 Upload Global Documents")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload NSW Local Government Documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Upload NSW legislation, Local Government Act, procurement guidelines, etc."
        )
        
        if uploaded_files:
            # Document details form
            with st.form("global_document_form"):
                st.markdown("**Document Details**")
                
                col_title, col_category = st.columns(2)
                with col_title:
                    document_title = st.text_input("Document Title", key="global_title")
                with col_category:
                    selected_category = st.selectbox(
                        "Document Category",
                        list(global_categories.keys()),
                        key="global_category"
                    )
                
                if st.form_submit_button("📤 Upload to Global RAG", type="primary"):
                    if document_title and uploaded_files:
                        upload_global_documents(
                            rag_system, uploaded_files, document_title, 
                            global_categories[selected_category]
                        )
                    else:
                        st.error("Please provide document title and select files")
    
    with col2:
        st.markdown("#### 📋 Global RAG Status")
        
        # Show current global documents
        global_summary = rag_system.get_compliance_summary()
        global_info = global_summary["global_compliance"]
        
        st.metric("Documents", global_info["documents_count"])
        st.metric("Categories", len(global_info["categories_covered"]))
        
        if global_info["categories_covered"]:
            st.markdown("**Covered Categories:**")
            for category in global_info["categories_covered"]:
                st.write(f"• {category.replace('_', ' ').title()}")

def show_internal_rag_interface(rag_system: ThreeTierRAGSystem):
    """Show Internal RAG (Tier 2) interface"""
    
    st.markdown("### 🏛️ Internal RAG - Council-Specific Standards")
    st.markdown("Upload internal council rules, regulations, and policies that follow global standards")
    
    # Document categories for Internal RAG
    internal_categories = {
        "Council Policies": DocumentCategory.COUNCIL_POLICIES,
        "Internal Procedures": DocumentCategory.INTERNAL_PROCEDURES,
        "Council Standards": DocumentCategory.COUNCIL_STANDARDS,
        "Local Preference": DocumentCategory.LOCAL_PREFERENCE,
        "Social Procurement": DocumentCategory.SOCIAL_PROCUREMENT
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📤 Upload Internal Documents")
        
        # Council selection
        council = st.selectbox(
            "Select Council",
            ["Blacktown City Council", "Western Sydney Council", "Other NSW Council"],
            key="internal_council"
        )
        
        # File upload
        uploaded_files = st.file_uploader(
            f"Upload {council} Internal Documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Upload council policies, internal procedures, local preference policies, etc."
        )
        
        if uploaded_files:
            # Document details form
            with st.form("internal_document_form"):
                st.markdown("**Document Details**")
                
                col_title, col_category = st.columns(2)
                with col_title:
                    document_title = st.text_input("Document Title", key="internal_title")
                with col_category:
                    selected_category = st.selectbox(
                        "Document Category",
                        list(internal_categories.keys()),
                        key="internal_category"
                    )
                
                if st.form_submit_button("📤 Upload to Internal RAG", type="primary"):
                    if document_title and uploaded_files:
                        upload_internal_documents(
                            rag_system, uploaded_files, document_title, 
                            internal_categories[selected_category], council
                        )
                    else:
                        st.error("Please provide document title and select files")
    
    with col2:
        st.markdown("#### 📋 Internal RAG Status")
        
        # Show current internal documents
        internal_summary = rag_system.get_compliance_summary(council=council)
        internal_info = internal_summary["internal_compliance"]
        
        st.metric("Documents", internal_info["documents_count"])
        st.metric("Categories", len(internal_info["categories_covered"]))
        st.metric("Council", internal_info["council"] or "Not specified")
        
        if internal_info["categories_covered"]:
            st.markdown("**Covered Categories:**")
            for category in internal_info["categories_covered"]:
                st.write(f"• {category.replace('_', ' ').title()}")

def show_project_rag_interface(rag_system: ThreeTierRAGSystem):
    """Show Project RAG (Tier 3) interface"""
    
    st.markdown("### 📋 Project RAG - Project-Specific Compliance")
    st.markdown("Upload project-specific compliance documents (WHS, ADR, ISO, environmental, etc.)")
    
    # Document categories for Project RAG
    project_categories = {
        "WHS Compliance": DocumentCategory.WHS_COMPLIANCE,
        "ADR Standards": DocumentCategory.ADR_STANDARDS,
        "ISO Standards": DocumentCategory.ISO_STANDARDS,
        "Environmental": DocumentCategory.ENVIRONMENTAL,
        "EEO & Fair Employment": DocumentCategory.EEO_FAIR_EMPLOYMENT,
        "Safety Standards": DocumentCategory.SAFETY_STANDARDS,
        "Quality Management": DocumentCategory.QUALITY_MANAGEMENT
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📤 Upload Project Documents")
        
        # Project type selection
        project_type = st.selectbox(
            "Project Type",
            ["Construction", "Fleet", "HVAC", "Services", "IT", "Consulting", "General"],
            key="project_type"
        )
        
        # File upload
        uploaded_files = st.file_uploader(
            f"Upload {project_type} Project Compliance Documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="Upload WHS plans, ADR compliance, ISO certificates, environmental assessments, etc."
        )
        
        if uploaded_files:
            # Document details form
            with st.form("project_document_form"):
                st.markdown("**Document Details**")
                
                col_title, col_category = st.columns(2)
                with col_title:
                    document_title = st.text_input("Document Title", key="project_title")
                with col_category:
                    selected_category = st.selectbox(
                        "Document Category",
                        list(project_categories.keys()),
                        key="project_category"
                    )
                
                if st.form_submit_button("📤 Upload to Project RAG", type="primary"):
                    if document_title and uploaded_files:
                        upload_project_documents(
                            rag_system, uploaded_files, document_title, 
                            project_categories[selected_category], project_type
                        )
                    else:
                        st.error("Please provide document title and select files")
    
    with col2:
        st.markdown("#### 📋 Project RAG Status")
        
        # Show current project documents
        project_summary = rag_system.get_compliance_summary(project_type=project_type)
        project_info = project_summary["project_compliance"]
        
        st.metric("Documents", project_info["documents_count"])
        st.metric("Categories", len(project_info["categories_covered"]))
        st.metric("Project Type", project_info["project_type"] or "Not specified")
        
        if project_info["categories_covered"]:
            st.markdown("**Covered Categories:**")
            for category in project_info["categories_covered"]:
                st.write(f"• {category.replace('_', ' ').title()}")

def show_compliance_overview(rag_system: ThreeTierRAGSystem):
    """Show comprehensive compliance overview"""
    
    st.markdown("### 📊 Three-Tier Compliance Overview")
    st.markdown("Comprehensive view of all compliance documents and their alignment")
    
    # Get comprehensive summary
    summary = rag_system.get_compliance_summary()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Global Documents", 
            summary["global_compliance"]["documents_count"],
            help="NSW Local Government external standards"
        )
    
    with col2:
        st.metric(
            "Internal Documents", 
            summary["internal_compliance"]["documents_count"],
            help="Council-specific internal rules and policies"
        )
    
    with col3:
        st.metric(
            "Project Documents", 
            summary["project_compliance"]["documents_count"],
            help="Project-specific compliance (WHS, ADR, ISO, etc.)"
        )
    
    with col4:
        total_queries = summary["query_stats"]["total_queries"]
        st.metric(
            "Total Queries", 
            total_queries,
            help="Total compliance queries processed"
        )
    
    # Document alignment validation
    st.markdown("#### 🔍 Document Alignment Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        document_type = st.selectbox(
            "Document Type to Validate",
            ["TEPP", "Returnable_Schedule", "RFT", "RFQ"],
            help="Select document type to validate against all three tiers"
        )
    
    with col2:
        if st.button("🔍 Validate Alignment", type="primary"):
            # This would validate a sample document or user-provided content
            st.info("Document alignment validation feature coming soon!")
    
    # Query interface
    st.markdown("#### 🔍 Cross-Tier Compliance Query")
    
    query = st.text_input(
        "Search across all compliance tiers",
        placeholder="e.g., 'evaluation criteria for construction projects'",
        help="Search for compliance requirements across all three tiers"
    )
    
    if query:
        if st.button("🔍 Search Compliance", type="primary"):
            with st.spinner("Searching across all compliance tiers..."):
                results = rag_system.query_compliance(query)
                
                if results:
                    st.success(f"Found {len(results)} relevant compliance requirements")
                    
                    for i, result in enumerate(results[:10]):  # Show top 10 results
                        with st.expander(f"Tier {result.tier.value.title()}: {result.title}"):
                            st.write(f"**Category:** {result.category.value.replace('_', ' ').title()}")
                            st.write(f"**Relevance:** {result.relevance_score:.2f}")
                            st.write(f"**Content:** {result.content}")
                            
                            if result.compliance_requirements:
                                st.write("**Compliance Requirements:**")
                                for req in result.compliance_requirements:
                                    st.write(f"• {req}")
                else:
                    st.warning("No relevant compliance requirements found")

def upload_global_documents(rag_system: ThreeTierRAGSystem, 
                          uploaded_files: List, 
                          title: str, 
                          category: DocumentCategory):
    """Upload documents to Global RAG"""
    
    try:
        for uploaded_file in uploaded_files:
            # Save uploaded file temporarily
            temp_path = Path(f"temp_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Upload to RAG system
            doc_id = rag_system.upload_document(
                file_path=temp_path,
                title=f"{title} - {uploaded_file.name}",
                tier=RAGTier.GLOBAL,
                category=category
            )
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
        
        st.success(f"✅ Successfully uploaded {len(uploaded_files)} document(s) to Global RAG")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error uploading documents: {str(e)}")

def upload_internal_documents(rag_system: ThreeTierRAGSystem, 
                            uploaded_files: List, 
                            title: str, 
                            category: DocumentCategory,
                            council: str):
    """Upload documents to Internal RAG"""
    
    try:
        for uploaded_file in uploaded_files:
            # Save uploaded file temporarily
            temp_path = Path(f"temp_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Upload to RAG system
            doc_id = rag_system.upload_document(
                file_path=temp_path,
                title=f"{title} - {uploaded_file.name}",
                tier=RAGTier.INTERNAL,
                category=category,
                council=council
            )
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
        
        st.success(f"✅ Successfully uploaded {len(uploaded_files)} document(s) to Internal RAG for {council}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error uploading documents: {str(e)}")

def upload_project_documents(rag_system: ThreeTierRAGSystem, 
                          uploaded_files: List, 
                          title: str, 
                          category: DocumentCategory,
                          project_type: str):
    """Upload documents to Project RAG"""
    
    try:
        for uploaded_file in uploaded_files:
            # Save uploaded file temporarily
            temp_path = Path(f"temp_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Upload to RAG system
            doc_id = rag_system.upload_document(
                file_path=temp_path,
                title=f"{title} - {uploaded_file.name}",
                tier=RAGTier.PROJECT,
                category=category,
                project_type=project_type
            )
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
        
        st.success(f"✅ Successfully uploaded {len(uploaded_files)} document(s) to Project RAG for {project_type}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error uploading documents: {str(e)}")

def show_rag_alignment_status():
    """Show RAG alignment status for current project"""
    
    st.markdown("#### 🎯 RAG Alignment Status")
    
    # This would show the current project's alignment with all three RAG tiers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 Global RAG**")
        st.success("✅ Aligned")
        st.caption("NSW Local Government standards")
    
    with col2:
        st.markdown("**🏛️ Internal RAG**")
        st.success("✅ Aligned")
        st.caption("Council-specific policies")
    
    with col3:
        st.markdown("**📋 Project RAG**")
        st.warning("⚠️ Partial")
        st.caption("Project-specific compliance")
    
    # Show recommendations
    st.markdown("#### 💡 Recommendations")
    st.info("""
    **To improve compliance alignment:**
    - Upload additional WHS compliance documents for construction projects
    - Add ISO 14001 environmental management standards
    - Include ADR compliance requirements for fleet projects
    """)
