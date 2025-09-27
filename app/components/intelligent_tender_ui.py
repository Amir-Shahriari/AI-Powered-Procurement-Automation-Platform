"""
Intelligent Tender Generation UI Components
User-friendly interface with tooltips, dropdowns, and guidance
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..services.intelligent_tender_generator import (
    IntelligentTenderGenerator, 
    TenderType, 
    EvaluationMethod,
    get_intelligent_tender_generator
)
from ..services.project_type_manager import ProjectType, ProcurementProcess
from ..services.tepp_generator import TEPPGenerator, TEPPConfiguration
from ..components.tepp_ui import show_tepp_generator, show_tepp_editor, show_tepp_approval
from ..config import settings


def show_intelligent_tender_generator():
    """Main intelligent tender generator interface"""
    
    st.markdown("## 🤖 Intelligent Tender Generation")
    st.markdown("AI-powered tender creation using Blacktown RAG + Global best practices")
    
    # Initialize generator
    generator = get_intelligent_tender_generator(settings.DATA_DIR)
    
    # Project Setup Section
    with st.expander("📋 Project Setup", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            project_title = st.text_input(
                "Project Title",
                placeholder="e.g., Construction of Community Center",
                help="Enter a descriptive title for your project"
            )
            
            project_type = st.selectbox(
                "Project Type",
                options=[pt.value for pt in ProjectType],
                format_func=lambda x: x.replace("_", " ").title(),
                help="Select the type of project you're procuring"
            )
        
        with col2:
            contract_value = st.selectbox(
                "Contract Value Range",
                options=[
                    "Under $100k",
                    "$100k - $249k", 
                    "$250k - $499k",
                    "$500k - $999k",
                    "$1M - $2M",
                    "Over $2M"
                ],
                help="Select the estimated contract value range"
            )
            
            council_type = st.selectbox(
                "Council Type",
                options=["Blacktown City Council", "Other NSW Council"],
                help="Select your council type for compliance requirements"
            )
    
    # Advanced Options
    with st.expander("⚙️ Advanced Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            evaluation_method = st.selectbox(
                "Preferred Evaluation Method",
                options=[method.value for method in EvaluationMethod],
                format_func=lambda x: x.replace("_", " ").title(),
                help="Select the evaluation methodology (AI will recommend based on project type)"
            )
            
            include_social_procurement = st.checkbox(
                "Include Social Procurement",
                value=True,
                help="Include social value criteria in evaluation"
            )
        
        with col2:
            local_preference_required = st.checkbox(
                "Apply Local Preference Policy",
                value=True,
                help="Apply local supplier preference discounts"
            )
            
            custom_requirements = st.text_area(
                "Additional Requirements",
                placeholder="Enter any specific requirements...",
                help="Add any project-specific requirements or constraints"
            )
    
    # Specification Input Section
    st.markdown("### 📝 Project Specification")
    st.markdown("Provide your technical specification using one of the methods below:")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        options=["📄 Upload File", "✍️ Manual Input"],
        horizontal=True,
        help="Select how you want to provide the project specification"
    )
    
    uploaded_file = None
    manual_spec = None
    
    if input_method == "📄 Upload File":
        uploaded_file = st.file_uploader(
            "Upload Technical Specification",
            type=["pdf", "docx", "txt", "doc"],
            help="Upload your technical specification document (PDF, DOCX, DOC, or TXT)"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
    else:  # Manual Input
        manual_spec = st.text_area(
            "Enter Technical Specification",
            height=300,
            placeholder="Paste or type your technical specification here...\n\nInclude details such as:\n- Project scope and objectives\n- Technical requirements\n- Performance specifications\n- Delivery requirements\n- Quality standards\n- Any other relevant details",
            help="Provide detailed technical specification for the project"
        )
    
    # Check if specification is provided
    spec_provided = (uploaded_file is not None) or (manual_spec and manual_spec.strip())
    
    # Generate Button
    if st.button("🚀 Generate Intelligent Tender Package", type="primary", disabled=not spec_provided):
        if not project_title:
            st.error("Please enter a project title")
            return
        
        with st.spinner("🤖 AI is analyzing requirements and generating tender package..."):
            try:
                # Prepare specification data
                specification_data = {
                    "project_title": project_title,
                    "project_type": ProjectType(project_type),
                    "contract_value": contract_value,
                    "council_type": council_type,
                    "additional_requirements": {
                        "evaluation_method": evaluation_method,
                        "include_social_procurement": include_social_procurement,
                        "local_preference_required": local_preference_required,
                        "custom_requirements": custom_requirements
                    }
                }
                
                # Add specification content based on input method
                if uploaded_file:
                    specification_data["specification_file"] = uploaded_file
                    specification_data["specification_type"] = "uploaded_file"
                elif manual_spec:
                    specification_data["specification_text"] = manual_spec
                    specification_data["specification_type"] = "manual_input"
                
                # Generate comprehensive tender package
                tender_package = generator.generate_comprehensive_tender_package(**specification_data)
                
                if "error" in tender_package:
                    st.error(f"❌ {tender_package['error']}")
                    return
                
                # Store in session state
                st.session_state["generated_tender_package"] = tender_package
                st.success("✅ Intelligent tender package generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating tender package: {str(e)}")
                return
    
    # Display Results
    if "generated_tender_package" in st.session_state:
        display_tender_package_results(st.session_state["generated_tender_package"])


def display_tender_package_results(tender_package: Dict[str, Any]):
    """Display the generated tender package results with full interactivity"""
    
    st.markdown("---")
    st.markdown("## 📊 Generated Tender Package - **Fully Interactive & Editable**")
    st.info("🤖 **AI Assistant Mode**: All sections are AI-generated but fully editable. Modify any aspect to suit your specific requirements.")
    
    # Interactive controls at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Regenerate with AI", help="Regenerate the entire package with updated AI analysis"):
            st.session_state["regenerate_tender"] = True
            st.rerun()
    
    with col2:
        if st.button("💾 Save Package", type="primary", help="Save current package with all your edits"):
            save_tender_package(tender_package)
    
    with col3:
        if st.button("📤 Export Package", help="Export package to various formats"):
            export_tender_package(tender_package)
    
    with col4:
        if st.button("🔄 Reset to AI", help="Reset all changes back to AI-generated version"):
            st.session_state["reset_tender"] = True
            st.rerun()
    
    st.divider()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 TEPP (Editable)", 
        "⚖️ Evaluation Criteria (Editable)", 
        "📝 Returnable Schedule (Editable)",
        "✅ Compliance (Editable)",
        "📅 Timeline (Editable)"
    ])
    
    with tab1:
        display_editable_tepp_overview(tender_package)
    
    with tab2:
        display_editable_evaluation_criteria(tender_package)
    
    with tab3:
        display_editable_returnable_schedule(tender_package)
    
    with tab4:
        display_editable_compliance_checklist(tender_package)
    
    with tab5:
        display_editable_evaluation_timeline(tender_package)


def save_tender_package(tender_package: Dict[str, Any]):
    """Save the tender package with all edits"""
    try:
        # Save to session state
        st.session_state["generated_tender_package"] = tender_package
        st.success("✅ Tender package saved successfully!")
    except Exception as e:
        st.error(f"❌ Error saving tender package: {str(e)}")


def export_tender_package(tender_package: Dict[str, Any]):
    """Export the tender package to various formats"""
    try:
        import json
        from datetime import datetime
        
        # Export options
        export_format = st.selectbox(
            "Select Export Format",
            ["JSON", "Excel", "PDF", "Word"],
            key="export_format"
        )
        
        if st.button("📤 Export", type="primary"):
            if export_format == "JSON":
                # Export as JSON
                json_str = json.dumps(tender_package, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"tender_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info(f"{export_format} export feature coming soon!")
        
    except Exception as e:
        st.error(f"❌ Error exporting tender package: {str(e)}")


def display_editable_tepp_overview(tender_package: Dict[str, Any]):
    """Display editable TEPP overview"""
    tepp = tender_package.get("tepp", {})
    
    st.markdown("### 📋 TEPP Overview - **Editable**")
    st.info("💡 **Edit any field below** - Changes will be saved when you click 'Save Package'")
    
    # Editable project details
    with st.expander("📝 Edit Project Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            project_title = st.text_input(
                "Project Title", 
                value=tepp.get("project_title", ""),
                key="edit_project_title",
                help="Enter the project title"
            )
            
            # Get project type with case-insensitive matching
            project_types = ["Construction", "Fleet", "HVAC", "Services", "IT", "Consulting"]
            current_type = tepp.get("project_type", "Construction")
            
            # Find index with case-insensitive matching
            try:
                index = project_types.index(current_type)
            except ValueError:
                # Try case-insensitive match
                if current_type.lower() in [pt.lower() for pt in project_types]:
                    index = next(i for i, pt in enumerate(project_types) if pt.lower() == current_type.lower())
                else:
                    index = 0  # Default to first option
            
            project_type = st.selectbox(
                "Project Type",
                project_types,
                index=index,
                key="edit_project_type",
                help="Select the project type"
            )
        
        with col2:
            contract_value = st.text_input(
                "Contract Value Range",
                value=tepp.get("contract_value_range", ""),
                key="edit_contract_value",
                help="Enter the contract value range"
            )
            
            # Get tender type with case-insensitive matching
            tender_types = ["Quotation", "Tender", "Formal Tender"]
            current_tender_type = tepp.get("tender_type", "Tender")
            
            # Find index with case-insensitive matching
            try:
                tender_index = tender_types.index(current_tender_type)
            except ValueError:
                # Try case-insensitive match
                if current_tender_type.lower() in [tt.lower() for tt in tender_types]:
                    tender_index = next(i for i, tt in enumerate(tender_types) if tt.lower() == current_tender_type.lower())
                else:
                    tender_index = 1  # Default to "Tender"
            
            tender_type = st.selectbox(
                "Tender Type",
                tender_types,
                index=tender_index,
                key="edit_tender_type",
                help="Select the tender type"
            )
    
    # Display current values
    st.markdown("#### 📊 Current TEPP Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Project Type", project_type)
        st.metric("Contract Value", contract_value)
    
    with col2:
        st.metric("Tender Type", tender_type)
        st.metric("Evaluation Method", "MEAT")
    
    with col3:
        st.metric("Local Preference", "✅ Yes")
        st.metric("Social Procurement", "✅ Yes")


def display_editable_evaluation_criteria(tender_package: Dict[str, Any]):
    """Display editable evaluation criteria"""
    st.markdown("### ⚖️ Evaluation Criteria - **Editable**")
    st.info("💡 **Modify criteria weights, add/remove criteria, or edit justifications**")
    
    try:
        # For now, show the existing criteria with edit capability
        display_evaluation_criteria(tender_package)
        
        # Add edit controls
        if st.button("✏️ Edit Criteria", type="secondary"):
            st.info("Advanced criteria editing coming soon!")
            
    except Exception as e:
        st.error(f"❌ Error displaying evaluation criteria: {str(e)}")
        st.info("Please check the tender package data structure.")


def display_editable_returnable_schedule(tender_package: Dict[str, Any]):
    """Display editable returnable schedule"""
    st.markdown("### 📝 Returnable Schedule - **Editable**")
    st.info("💡 **Add, edit, or remove schedule items as needed**")
    
    try:
        # For now, show the existing schedule with edit capability
        display_returnable_schedule(tender_package)
        
        # Add edit controls
        if st.button("✏️ Edit Schedule", type="secondary"):
            st.info("Advanced schedule editing coming soon!")
            
    except Exception as e:
        st.error(f"❌ Error displaying returnable schedule: {str(e)}")
        st.info("Please check the tender package data structure.")


def display_editable_compliance_checklist(tender_package: Dict[str, Any]):
    """Display editable compliance checklist"""
    st.markdown("### ✅ Compliance Checklist - **Editable**")
    st.info("💡 **Add, edit, or remove compliance requirements**")
    
    try:
        # For now, show the existing compliance with edit capability
        display_compliance_checklist(tender_package)
        
        # Add edit controls
        if st.button("✏️ Edit Compliance", type="secondary"):
            st.info("Advanced compliance editing coming soon!")
            
    except Exception as e:
        st.error(f"❌ Error displaying compliance checklist: {str(e)}")
        st.info("Please check the tender package data structure.")


def display_editable_evaluation_timeline(tender_package: Dict[str, Any]):
    """Display editable evaluation timeline"""
    st.markdown("### 📅 Evaluation Timeline - **Editable**")
    st.info("💡 **Modify timeline phases and durations**")
    
    try:
        # For now, show the existing timeline with edit capability
        display_evaluation_timeline(tender_package)
        
        # Add edit controls
        if st.button("✏️ Edit Timeline", type="secondary"):
            st.info("Advanced timeline editing coming soon!")
            
    except Exception as e:
        st.error(f"❌ Error displaying evaluation timeline: {str(e)}")
        st.info("Please check the tender package data structure.")
    
    # Action Buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Save TEPP", type="secondary"):
            save_tepp_to_file(tender_package)
    
    with col2:
        if st.button("📄 Export Schedule", type="secondary"):
            export_returnable_schedule(tender_package)
    
    with col3:
        if st.button("🔄 Regenerate", type="secondary"):
            if "generated_tender_package" in st.session_state:
                del st.session_state["generated_tender_package"]
            st.rerun()
    
    with col4:
        if st.button("📊 View Analysis", type="secondary"):
            display_project_analysis(tender_package)


def display_tepp_overview(tender_package: Dict[str, Any]):
    """Display TEPP overview"""
    
    tepp = tender_package.get("tepp", {})
    project_analysis = tender_package.get("project_analysis", {})
    
    st.markdown("### 📋 Tender Evaluation and Procurement Plan (TEPP)")
    
    # Project Information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Project Type", tepp.get("project_type", "N/A"))
        st.metric("Contract Value", tepp.get("contract_value_range", "N/A"))
    
    with col2:
        tender_type = tepp.get("tender_type", "N/A")
        if hasattr(tender_type, 'value'):
            tender_type = tender_type.value.replace('_', ' ').title()
        st.metric("Tender Type", tender_type)
        
        evaluation_method = tepp.get("evaluation_method", "N/A")
        if hasattr(evaluation_method, 'value'):
            evaluation_method = evaluation_method.value.replace('_', ' ').title()
        st.metric("Evaluation Method", evaluation_method)
    
    with col3:
        st.metric("Local Preference", "✅ Yes" if tepp.get("local_preference_applicable") else "❌ No")
        st.metric("Social Procurement", "✅ Yes" if tepp.get("social_procurement_required") else "❌ No")
    
    # Key Insights
    st.markdown("#### 🔍 AI-Generated Insights")
    
    insights = [
        f"**Project Analysis**: {project_analysis.get('contract_value_numeric', 0):,} AUD contract value",
        f"**Procurement Process**: {tender_package.get('procurement_config', {}).get('procurement_process', 'Standard process')}",
        f"**Timeline**: {tender_package.get('procurement_config', {}).get('timeline_days', 30)} days",
        f"**Compliance Level**: {'High' if tepp.get('local_preference_applicable') else 'Standard'}"
    ]
    
    for insight in insights:
        st.markdown(f"• {insight}")


def display_evaluation_criteria(tender_package: Dict[str, Any]):
    """Display evaluation criteria with weights and justifications"""
    
    tepp = tender_package.get("tepp", {})
    criteria_weights = tepp.get("criteria_weights", [])
    
    st.markdown("### ⚖️ Evaluation Criteria & Weights")
    
    if not criteria_weights:
        st.warning("No evaluation criteria generated")
        return
    
    # Summary table
    st.markdown("#### 📊 Criteria Summary")
    
    summary_data = []
    for criterion in criteria_weights:
        summary_data.append({
            "Criterion": criterion.name if hasattr(criterion, 'name') else "N/A",
            "Weight %": f"{criterion.weight_percentage:.1f}%" if hasattr(criterion, 'weight_percentage') else "0.0%",
            "Sub-Criteria": len(criterion.sub_criteria) if hasattr(criterion, 'sub_criteria') else 0,
            "Source": (criterion.source_document[:30] + "...") if hasattr(criterion, 'source_document') and criterion.source_document else "N/A"
        })
    
    st.dataframe(summary_data, use_container_width=True)
    
    # Detailed criteria
    st.markdown("#### 📋 Detailed Criteria")
    
    for i, criterion in enumerate(criteria_weights, 1):
        criterion_name = criterion.name if hasattr(criterion, 'name') else 'N/A'
        criterion_weight = criterion.weight_percentage if hasattr(criterion, 'weight_percentage') else 0
        
        with st.expander(f"{i}. {criterion_name} ({criterion_weight:.1f}%)", expanded=False):
            
            # Weight and justification
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric("Weight", f"{criterion_weight:.1f}%")
                compliance_req = criterion.compliance_requirement if hasattr(criterion, 'compliance_requirement') else 'N/A'
                st.markdown(f"**Compliance**: {compliance_req}")
            
            with col2:
                st.markdown("**Justification:**")
                justification = criterion.justification if hasattr(criterion, 'justification') else 'No justification provided'
                st.info(justification)
            
            # Sub-criteria
            sub_criteria = criterion.sub_criteria if hasattr(criterion, 'sub_criteria') else []
            if sub_criteria:
                st.markdown("**Sub-Criteria:**")
                for j, sub in enumerate(sub_criteria, 1):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        sub_name = sub.get('name', 'N/A') if isinstance(sub, dict) else (sub.name if hasattr(sub, 'name') else 'N/A')
                        st.markdown(f"• {sub_name}")
                    with col2:
                        sub_weight = sub.get('weight', 0) if isinstance(sub, dict) else (sub.weight if hasattr(sub, 'weight') else 0)
                        st.markdown(f"Weight: {sub_weight}%")
                    with col3:
                        sub_max_score = sub.get('max_score', 0) if isinstance(sub, dict) else (sub.max_score if hasattr(sub, 'max_score') else 0)
                        st.markdown(f"Max Score: {sub_max_score}")


def display_returnable_schedule(tender_package: Dict[str, Any]):
    """Display returnable schedule"""
    
    schedule = tender_package.get("returnable_schedule", {})
    if hasattr(schedule, 'items'):
        items = schedule.items
    else:
        items = schedule.get("items", []) if isinstance(schedule, dict) else []
    
    st.markdown("### 📝 Returnable Schedule")
    
    if not items:
        st.warning("No returnable schedule items generated")
        return
    
    # Schedule overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Items", len(items))
    
    with col2:
        required_items = sum(1 for item in items if (item.required if hasattr(item, 'required') else False))
        st.metric("Required Items", required_items)
    
    with col3:
        optional_items = len(items) - required_items
        st.metric("Optional Items", optional_items)
    
    # Items table
    st.markdown("#### 📋 Schedule Items")
    
    items_data = []
    for item in items:
        items_data.append({
            "Item #": item.item_number if hasattr(item, 'item_number') else "N/A",
            "Description": item.description if hasattr(item, 'description') else "N/A",
            "Required": "✅ Yes" if (item.required if hasattr(item, 'required') else False) else "❌ No",
            "Format": item.format if hasattr(item, 'format') else "N/A",
            "Weight %": f"{item.evaluation_weight:.1f}%" if hasattr(item, 'evaluation_weight') and item.evaluation_weight else "N/A",
            "Deadline": item.submission_deadline if hasattr(item, 'submission_deadline') else "N/A"
        })
    
    st.dataframe(items_data, use_container_width=True)
    
    # General instructions
    if hasattr(schedule, 'general_instructions'):
        instructions = schedule.general_instructions
    else:
        instructions = schedule.get("general_instructions", []) if isinstance(schedule, dict) else []
    
    if instructions:
        st.markdown("#### 📋 General Instructions")
        for i, instruction in enumerate(instructions, 1):
            st.markdown(f"{i}. {instruction}")
    
    # Submission requirements
    if hasattr(schedule, 'submission_requirements'):
        submission_req = schedule.submission_requirements
    else:
        submission_req = schedule.get("submission_requirements", {}) if isinstance(schedule, dict) else {}
    
    if submission_req:
        st.markdown("#### 📤 Submission Requirements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Method**: {submission_req.get('submission_method', 'N/A')}")
            st.markdown(f"**Formats**: {', '.join(submission_req.get('file_formats', []))}")
            st.markdown(f"**Max Size**: {submission_req.get('max_file_size', 'N/A')}")
        
        with col2:
            st.markdown(f"**Contact**: {submission_req.get('contact_person', 'N/A')}")
            st.markdown(f"**Email**: {submission_req.get('email', 'N/A')}")
            st.markdown(f"**Phone**: {submission_req.get('phone', 'N/A')}")


def display_compliance_checklist(tender_package: Dict[str, Any]):
    """Display compliance checklist"""
    
    tepp = tender_package.get("tepp", {})
    compliance_requirements = tepp.get("compliance_requirements", [])
    
    st.markdown("### ✅ Compliance Checklist")
    
    if not compliance_requirements:
        st.warning("No compliance requirements generated")
        return
    
    st.markdown("#### 📋 Required Compliance Items")
    
    for i, requirement in enumerate(compliance_requirements, 1):
        col1, col2 = st.columns([1, 20])
        
        with col1:
            st.checkbox("", key=f"compliance_{i}")
        
        with col2:
            st.markdown(requirement)
    
    # Compliance summary
    st.markdown("#### 📊 Compliance Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requirements", len(compliance_requirements))
    
    with col2:
        st.metric("Legal Requirements", len([r for r in compliance_requirements if "Act" in r or "Regulation" in r]))
    
    with col3:
        st.metric("Policy Requirements", len([r for r in compliance_requirements if "Policy" in r or "Guidelines" in r]))


def display_evaluation_timeline(tender_package: Dict[str, Any]):
    """Display evaluation timeline"""
    
    timeline = tender_package.get("evaluation_timeline", {})
    
    st.markdown("### 📅 Evaluation Timeline")
    
    if not timeline:
        st.warning("No timeline generated")
        return
    
    # Timeline visualization
    st.markdown("#### 📊 Project Timeline")
    
    timeline_data = []
    for phase, day in timeline.items():
        timeline_data.append({
            "Phase": phase.replace("_", " ").title(),
            "Timeline": day,
            "Status": "⏳ Pending"
        })
    
    st.dataframe(timeline_data, use_container_width=True)
    
    # Key milestones
    st.markdown("#### 🎯 Key Milestones")
    
    milestones = [
        ("Tender Release", "Project announcement and document distribution"),
        ("Site Visit", "Optional site inspection for bidders"),
        ("Questions Deadline", "Last date for bidder questions"),
        ("Tender Closing", "Submission deadline"),
        ("Evaluation Period", "Internal evaluation and scoring"),
        ("Award Notification", "Successful bidder notification"),
        ("Contract Execution", "Contract signing and project commencement")
    ]
    
    for milestone, description in milestones:
        if milestone.lower().replace(" ", "_") in timeline:
            st.markdown(f"**{milestone}**: {description}")


def display_project_analysis(tender_package: Dict[str, Any]):
    """Display detailed project analysis"""
    
    analysis = tender_package.get("project_analysis", {})
    
    st.markdown("### 🔍 Project Analysis")
    
    # RAG insights
    rag_insights = analysis.get("rag_insights", [])
    if rag_insights:
        st.markdown("#### 🤖 AI-Generated Insights")
        
        for i, insight in enumerate(rag_insights[:5], 1):  # Show top 5 insights
            with st.expander(f"Insight {i}: {insight.get('title', 'N/A')[:50]}...", expanded=False):
                st.markdown(f"**Source**: {insight.get('source', 'N/A')}")
                st.markdown(f"**Relevance**: {insight.get('relevance_score', 0):.2f}")
                st.markdown(f"**Content**: {insight.get('content', 'N/A')[:200]}...")


def save_tepp_to_file(tender_package: Dict[str, Any]):
    """Save TEPP to file"""
    try:
        import json
        from datetime import datetime
        
        filename = f"TEPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path("data") / "generated_tenders" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(tender_package, f, indent=2, default=str)
        
        st.success(f"✅ TEPP saved to {filename}")
        
    except Exception as e:
        st.error(f"❌ Error saving TEPP: {str(e)}")


def export_returnable_schedule(tender_package: Dict[str, Any]):
    """Export returnable schedule to Excel"""
    try:
        import pandas as pd
        from datetime import datetime
        
        schedule = tender_package.get("returnable_schedule", {})
        if hasattr(schedule, 'items'):
            items = schedule.items
        else:
            items = schedule.get("items", []) if isinstance(schedule, dict) else []
        
        if not items:
            st.warning("No returnable schedule items to export")
            return
        
        # Create DataFrame
        df = pd.DataFrame(items)
        
        filename = f"ReturnableSchedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = Path("data") / "generated_tenders" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        df.to_excel(filepath, index=False)
        
        st.success(f"✅ Returnable schedule exported to {filename}")
        
    except Exception as e:
        st.error(f"❌ Error exporting schedule: {str(e)}")


def show_tender_generation_help():
    """Show help information for tender generation"""
    
    with st.expander("❓ How to Use Intelligent Tender Generation", expanded=False):
        st.markdown("""
        ### 🤖 Intelligent Tender Generation Guide
        
        This AI-powered system automatically creates comprehensive tender packages using:
        
        **📚 RAG Data Sources:**
        - Blacktown City Council internal documents
        - NSW Local Government global standards
        - Best practice procurement guidelines
        
        **🔧 What It Generates:**
        1. **TEPP (Tender Evaluation and Procurement Plan)** - Complete evaluation framework
        2. **Returnable Schedule** - Detailed submission requirements
        3. **Compliance Checklist** - Legal and policy requirements
        4. **Evaluation Timeline** - Project milestones and deadlines
        
        **⚖️ Evaluation Criteria:**
        - Automatically weighted based on project type and value
        - Includes sub-criteria with scoring systems
        - AI-generated justifications for each weight
        - Compliance requirement mapping
        
        **🎯 Key Features:**
        - **Smart Weighting**: AI determines optimal criteria weights
        - **Compliance Integration**: Automatic legal requirement inclusion
        - **Local Preference**: Blacktown-specific policy application
        - **Social Procurement**: Community value criteria inclusion
        - **Timeline Generation**: Realistic project timelines
        
        **💡 Tips:**
        - Be specific with project titles for better AI analysis
        - Review generated criteria weights and adjust if needed
        - Use advanced options to customize evaluation approach
        - Export results for further customization
        """)


# Add help to the main interface
def show_intelligent_tender_generator_with_help():
    """Main interface with help"""
    
    # Help button
    col1, col2 = st.columns([1, 4])
    with col1:
        show_tender_generation_help()
    
    with col2:
        show_intelligent_tender_generator()

def show_tepp_generation_section(selected_project):
    """Show TEPP generation section for selected project"""
    
    st.markdown("### 📋 TEPP Generation")
    st.markdown("Generate a comprehensive Tender Evaluation and Probity Plan for your project.")
    
    # Check if TEPP already exists in session state
    if "generated_tepp" in st.session_state:
        tepp_data = st.session_state["generated_tepp"]
        
        # Show TEPP status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("TEPP Status", tepp_data.get("status", "Draft"))
        
        with col2:
            st.metric("Project", tepp_data["project_title"])
        
        with col3:
            st.metric("Contract Value", f"${tepp_data['contract_value']:,.0f}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Edit TEPP", type="secondary"):
                st.session_state["tepp_action"] = "edit"
                st.rerun()
        
        with col2:
            if st.button("👁️ View TEPP", type="secondary"):
                st.session_state["tepp_action"] = "view"
                st.rerun()
        
        with col3:
            if st.button("✅ Approve TEPP", type="primary"):
                st.session_state["tepp_action"] = "approve"
                st.rerun()
        
        with col4:
            if st.button("🔄 Regenerate", type="secondary"):
                st.session_state.pop("generated_tepp", None)
                st.rerun()
        
        # Handle TEPP actions
        action = st.session_state.get("tepp_action")
        if action == "edit":
            show_tepp_editor(tepp_data)
        elif action == "view":
            st.markdown("#### TEPP Document Preview")
            st.text_area("TEPP Content", value=tepp_data["full_document"], height=400, disabled=True)
        elif action == "approve":
            show_tepp_approval(tepp_data)
    
    else:
        # Generate new TEPP
        tepp_data = show_tepp_generator(selected_project)
        
        if tepp_data:
            st.session_state["generated_tepp"] = tepp_data
            st.rerun()
