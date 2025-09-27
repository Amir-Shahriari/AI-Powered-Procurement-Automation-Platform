#!/usr/bin/env python3
"""
Project Type and Procurement Process Selector Component
Provides UI for selecting project types and procurement processes
"""

import streamlit as st
from typing import Optional, Tuple
from ..services.project_type_manager import (
    ProjectTypeManager, ProjectType, ProcurementProcess, 
    get_project_type_manager
)
from ..config import settings

def show_project_type_selector(data_dir, key_prefix: str = "") -> Tuple[Optional[ProjectType], Optional[ProcurementProcess], str]:
    """
    Show project type and procurement process selector
    
    Returns:
        Tuple of (project_type, procurement_process, council_name)
    """
    
    # Initialize project type manager
    manager = get_project_type_manager(data_dir)
    
    st.markdown("### 🏗️ Project Configuration")
    
    # Council selection
    col1, col2 = st.columns(2)
    
    with col1:
        council_name = st.selectbox(
            "🏛️ Council/Organization",
            options=[
                "Blacktown City Council",
                "Parramatta City Council", 
                "Liverpool City Council",
                "Penrith City Council",
                "Campbelltown City Council",
                "Other Council",
                "LGP (Local Government Procurement)",
                "Other Organization"
            ],
            key=f"{key_prefix}_council",
            help="Select your council or organization for tailored processes"
        )
    
    with col2:
        # Contract value input
        contract_value = st.number_input(
            "💰 Estimated Contract Value ($)",
            min_value=0,
            value=100000,
            step=10000,
            key=f"{key_prefix}_value",
            help="Estimated contract value to determine procurement process"
        )
    
    # Project type selection
    st.markdown("#### 📋 Project Type")
    
    project_types = manager.get_project_types()
    project_type_options = {f"{pt.name} - {pt.description}": pt.type for pt in project_types}
    
    selected_project_type_name = st.selectbox(
        "Select Project Type",
        options=list(project_type_options.keys()),
        key=f"{key_prefix}_project_type",
        help="Choose the type of project you're procuring"
    )
    
    selected_project_type = project_type_options[selected_project_type_name]
    selected_project_type_config = manager.get_project_type_config(selected_project_type)
    
    # Show project type details
    with st.expander(f"ℹ️ {selected_project_type_config.name} Details", expanded=False):
        st.markdown(f"**Description:** {selected_project_type_config.description}")
        st.markdown(f"**Typical Value Range:** {selected_project_type_config.typical_value_range}")
        st.markdown(f"**Default Process:** {selected_project_type_config.default_process.value.replace('_', ' ').title()}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Required Documents:**")
            for doc in selected_project_type_config.required_documents:
                st.markdown(f"• {doc}")
        
        with col2:
            st.markdown("**Evaluation Criteria:**")
            for criteria in selected_project_type_config.evaluation_criteria:
                st.markdown(f"• {criteria}")
    
    # Procurement process selection
    st.markdown("#### ⚖️ Procurement Process")
    
    # Get recommended process based on value
    recommended_process = manager.recommend_process_for_value(contract_value)
    
    procurement_processes = manager.get_procurement_processes()
    process_options = {f"{pp.name} - {pp.description}": pp.process for pp in procurement_processes}
    
    # Highlight recommended process
    recommended_process_config = manager.get_procurement_process_config(recommended_process)
    recommended_process_name = f"{recommended_process_config.name} - {recommended_process_config.description}"
    
    selected_process_name = st.selectbox(
        "Select Procurement Process",
        options=list(process_options.keys()),
        index=list(process_options.keys()).index(recommended_process_name) if recommended_process_name in process_options else 0,
        key=f"{key_prefix}_process",
        help=f"Recommended: {recommended_process_name} (based on contract value)"
    )
    
    selected_process = process_options[selected_process_name]
    selected_process_config = manager.get_procurement_process_config(selected_process)
    
    # Show process details
    with st.expander(f"ℹ️ {selected_process_config.name} Details", expanded=False):
        st.markdown(f"**Description:** {selected_process_config.description}")
        st.markdown(f"**Value Threshold:** {selected_process_config.value_threshold}")
        st.markdown(f"**Timeline:** {selected_process_config.timeline}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Required Steps:**")
            for step in selected_process_config.required_steps:
                st.markdown(f"• {step}")
        
        with col2:
            st.markdown("**Mandatory Documents:**")
            for doc in selected_process_config.mandatory_documents:
                st.markdown(f"• {doc}")
    
    # Show combined requirements
    st.markdown("#### 📄 Project Requirements Summary")
    
    # Get evaluation criteria for this combination
    evaluation_criteria = manager.get_evaluation_criteria_for_project(selected_project_type, selected_process)
    required_documents = manager.get_required_documents_for_project(selected_project_type, selected_process)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Evaluation Criteria:**")
        for criteria in evaluation_criteria:
            st.markdown(f"• {criteria['criterion']} ({criteria['weight']}%)")
    
    with col2:
        st.markdown("**Required Documents:**")
        for doc in required_documents:
            st.markdown(f"• {doc}")
    
    # Show compliance requirements
    if selected_project_type_config.compliance_requirements:
        st.markdown("#### 🛡️ Compliance Requirements")
        for req in selected_project_type_config.compliance_requirements:
            st.markdown(f"• {req}")
    
    # Show special considerations
    if selected_project_type_config.special_considerations:
        st.markdown("#### ⚠️ Special Considerations")
        for consideration in selected_project_type_config.special_considerations:
            st.markdown(f"• {consideration}")
    
    return selected_project_type, selected_process, council_name

def show_project_type_summary(project_type: ProjectType, process: ProcurementProcess, 
                            council_name: str, contract_value: float):
    """Show a summary of the selected project configuration"""
    
    st.markdown("### ✅ Project Configuration Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Council", council_name)
    
    with col2:
        st.metric("Project Type", project_type.value.replace('_', ' ').title())
    
    with col3:
        st.metric("Process", process.value.replace('_', ' ').title())
    
    with col4:
        st.metric("Contract Value", f"${contract_value:,.0f}")
    
    # Show next steps
    st.markdown("#### 🚀 Next Steps")
    st.info("""
    1. **Upload your specification** - Provide detailed technical requirements
    2. **AI will analyze** - Extract key information and requirements
    3. **Generate documents** - Create TEPP and Returnable Schedules
    4. **Review and edit** - Customize generated documents as needed
    5. **Publish tender** - Distribute to suppliers
    """)

def get_project_configuration_data(project_type: ProjectType, process: ProcurementProcess, 
                                 council_name: str, contract_value: float) -> dict:
    """Get configuration data for the selected project"""
    
    manager = get_project_type_manager(settings.DATA_DIR)
    
    return {
        "project_type": project_type.value,
        "project_type_name": project_type.name,
        "procurement_process": process.value,
        "procurement_process_name": process.name,
        "council_name": council_name,
        "contract_value": contract_value,
        "evaluation_criteria": manager.get_evaluation_criteria_for_project(project_type, process),
        "required_documents": manager.get_required_documents_for_project(project_type, process),
        "compliance_requirements": manager.get_project_type_config(project_type).compliance_requirements if manager.get_project_type_config(project_type) else [],
        "special_considerations": manager.get_project_type_config(project_type).special_considerations if manager.get_project_type_config(project_type) else []
    }
