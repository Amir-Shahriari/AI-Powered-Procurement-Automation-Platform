#!/usr/bin/env python3
"""
Project Selector UI Component
Provides user interface for selecting historical projects, ongoing projects, or creating new tenders/RFQs
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from ..services.project_manager import ProjectManager, Project, ProjectStatus, ProjectCategory

def show_project_selector():
    """Show the main project selector interface"""
    
    st.markdown("## 🤖 AI-Guided Document Creation")
    st.markdown("Choose from historical projects, ongoing projects, or create new tender/RFQ documents")
    
    # Initialize project manager
    if 'project_manager' not in st.session_state:
        from pathlib import Path
        st.session_state.project_manager = ProjectManager(Path("data"))
    
    project_manager = st.session_state.project_manager
    
    # Project selection tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Project Overview", 
        "📚 Historical Projects", 
        "🔄 Ongoing Projects", 
        "➕ New Tender/RFQ"
    ])
    
    with tab1:
        show_project_overview(project_manager)
    
    with tab2:
        show_historical_projects(project_manager)
    
    with tab3:
        show_ongoing_projects(project_manager)
    
    with tab4:
        show_new_tender_rfq(project_manager)

def show_project_overview(project_manager: ProjectManager):
    """Show project overview with statistics"""
    
    st.markdown("### 📊 Project Overview")
    
    # Get project statistics
    stats = project_manager.get_project_statistics()
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Projects", stats["total_projects"])
    
    with col2:
        st.metric("Completed", stats["completed"])
    
    with col3:
        st.metric("Ongoing", stats["ongoing"])
    
    with col4:
        st.metric("New Tenders", stats["new_tenders"])
    
    with col5:
        st.metric("New RFQs", stats["new_rfqs"])
    
    # Total value
    st.metric("Total Contract Value", f"${stats['total_value']:,.0f}")
    
    # Recent projects
    st.markdown("#### 🕒 Recent Projects")
    recent_projects = project_manager.get_recent_projects(5)
    
    for project in recent_projects:
        with st.expander(f"{project.title} - {project.status.value.title()}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Category:** {project.category.value.title()}")
                st.write(f"**Value:** ${project.contract_value:,.0f}")
                st.write(f"**Council:** {project.council}")
            
            with col2:
                st.write(f"**Status:** {project.status.value.title()}")
                st.write(f"**Manager:** {project.project_manager}")
                st.write(f"**Created:** {project.created_date[:10]}")
            
            if st.button(f"📄 Open {project.title}", key=f"open_{project.project_id}"):
                st.session_state["selected_project"] = project
                st.session_state["current_page"] = "upload"
                st.rerun()

def show_historical_projects(project_manager: ProjectManager):
    """Show historical projects with search and filter capabilities"""
    
    st.markdown("### 📚 Historical Projects")
    st.markdown("Browse and select from completed projects to create similar tenders")
    
    # Search and filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input(
            "🔍 Search Projects",
            placeholder="Enter keywords, project name, or description...",
            key="historical_search"
        )
    
    with col2:
        category_filter = st.selectbox(
            "📂 Filter by Category",
            ["all", "construction", "fleet", "hvac", "services", "it", "consulting", "general"],
            key="historical_category"
        )
    
    with col3:
        sort_option = st.selectbox(
            "🔄 Sort by",
            ["Most Recent", "Project Name", "Contract Value", "Completion Date"],
            key="historical_sort"
        )
    
    # Get filtered projects
    if search_query:
        projects = project_manager.search_projects(search_query, category_filter, "completed")
    else:
        projects = project_manager.get_projects_by_status("completed")
        if category_filter != "all":
            projects = [p for p in projects if p.category.value == category_filter]
    
    # Sort projects
    if sort_option == "Most Recent":
        projects.sort(key=lambda p: p.last_modified, reverse=True)
    elif sort_option == "Project Name":
        projects.sort(key=lambda p: p.title)
    elif sort_option == "Contract Value":
        projects.sort(key=lambda p: p.contract_value, reverse=True)
    elif sort_option == "Completion Date":
        projects.sort(key=lambda p: p.completion_date or "", reverse=True)
    
    # Display projects
    if not projects:
        st.info("No historical projects found matching your criteria.")
        return
    
    st.markdown(f"#### Found {len(projects)} Historical Projects")
    
    # Display project cards
    for i, project in enumerate(projects):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{project.title}**")
                st.write(project.description[:200] + "..." if len(project.description) > 200 else project.description)
                
                # Tags
                if project.tags:
                    tag_cols = st.columns(len(project.tags))
                    for j, tag in enumerate(project.tags[:5]):  # Show max 5 tags
                        with tag_cols[j]:
                            st.markdown(f"`{tag}`")
            
            with col2:
                st.metric("Value", f"${project.contract_value:,.0f}")
                st.write(f"**Category:** {project.category.value.title()}")
                st.write(f"**Completed:** {project.completion_date[:10] if project.completion_date else 'N/A'}")
            
            with col3:
                if st.button("📄 Use as Template", key=f"use_template_{project.project_id}"):
                    st.session_state["selected_project"] = project
                    st.session_state["use_as_template"] = True
                    st.session_state["current_page"] = "upload"
                    st.rerun()
                
                if st.button("👁️ View Details", key=f"view_details_{project.project_id}"):
                    show_project_details(project)

def show_ongoing_projects(project_manager: ProjectManager):
    """Show ongoing projects with search and filter capabilities"""
    
    st.markdown("### 🔄 Ongoing Projects")
    st.markdown("View and manage projects currently in progress")
    
    # Search and filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input(
            "🔍 Search Projects",
            placeholder="Enter keywords, project name, or description...",
            key="ongoing_search"
        )
    
    with col2:
        category_filter = st.selectbox(
            "📂 Filter by Category",
            ["all", "construction", "fleet", "hvac", "services", "it", "consulting", "general"],
            key="ongoing_category"
        )
    
    with col3:
        sort_option = st.selectbox(
            "🔄 Sort by",
            ["Most Recent", "Project Name", "Contract Value", "Start Date"],
            key="ongoing_sort"
        )
    
    # Get filtered projects
    if search_query:
        projects = project_manager.search_projects(search_query, category_filter, "ongoing")
    else:
        projects = project_manager.get_projects_by_status("ongoing")
        if category_filter != "all":
            projects = [p for p in projects if p.category.value == category_filter]
    
    # Sort projects
    if sort_option == "Most Recent":
        projects.sort(key=lambda p: p.last_modified, reverse=True)
    elif sort_option == "Project Name":
        projects.sort(key=lambda p: p.title)
    elif sort_option == "Contract Value":
        projects.sort(key=lambda p: p.contract_value, reverse=True)
    elif sort_option == "Start Date":
        projects.sort(key=lambda p: p.created_date, reverse=True)
    
    # Display projects
    if not projects:
        st.info("No ongoing projects found matching your criteria.")
        return
    
    st.markdown(f"#### Found {len(projects)} Ongoing Projects")
    
    # Display project cards
    for i, project in enumerate(projects):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{project.title}**")
                st.write(project.description[:200] + "..." if len(project.description) > 200 else project.description)
                
                # Progress indicator (simplified)
                progress = st.progress(0.6)  # Placeholder progress
                st.caption("Project Progress: 60%")
                
                # Tags
                if project.tags:
                    tag_cols = st.columns(len(project.tags))
                    for j, tag in enumerate(project.tags[:5]):  # Show max 5 tags
                        with tag_cols[j]:
                            st.markdown(f"`{tag}`")
            
            with col2:
                st.metric("Value", f"${project.contract_value:,.0f}")
                st.write(f"**Category:** {project.category.value.title()}")
                st.write(f"**Manager:** {project.project_manager}")
            
            with col3:
                if st.button("📄 Open Project", key=f"open_ongoing_{project.project_id}"):
                    st.session_state["selected_project"] = project
                    st.session_state["current_page"] = "upload"
                    st.rerun()
                
                if st.button("👁️ View Details", key=f"view_ongoing_{project.project_id}"):
                    show_project_details(project)

def show_new_tender_rfq(project_manager: ProjectManager):
    """Show interface for creating new tender/RFQ"""
    
    st.markdown("### ➕ Create New Tender/RFQ")
    st.markdown("Start a new tender or RFQ from scratch with AI guidance")
    
    # Document type selection
    col1, col2 = st.columns(2)
    
    with col1:
        document_type = st.radio(
            "📄 Document Type",
            ["Tender", "RFQ (Request for Quotation)"],
            help="Select the type of procurement document to create"
        )
    
    with col2:
        council = st.selectbox(
            "🏛️ Council",
            ["Blacktown City Council", "Western Sydney Council", "Other NSW Council"],
            help="Select the council for this procurement"
        )
    
    # Project details form
    with st.form("new_tender_form"):
        st.markdown("#### 📝 Project Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            project_title = st.text_input(
                "Project Title",
                placeholder="Enter a descriptive project title...",
                help="Clear, descriptive title for the project"
            )
            
            project_category = st.selectbox(
                "Project Category",
                ["construction", "fleet", "hvac", "services", "it", "consulting", "general"],
                help="Select the project category"
            )
        
        with col2:
            contract_value = st.number_input(
                "Contract Value ($)",
                min_value=0.0,
                value=100000.0,
                step=1000.0,
                help="Estimated contract value"
            )
            
            project_manager_name = st.text_input(
                "Project Manager",
                placeholder="Enter project manager name...",
                help="Name of the project manager"
            )
        
        project_description = st.text_area(
            "Project Description",
            placeholder="Provide a detailed description of the project requirements...",
            help="Detailed description of what needs to be procured"
        )
        
        # Submit button
        if st.form_submit_button("🚀 Create New Tender/RFQ", type="primary"):
            if project_title and project_description:
                try:
                    # Create new project
                    new_project = project_manager.create_new_project(
                        title=project_title,
                        description=project_description,
                        category=ProjectCategory(project_category),
                        contract_value=contract_value,
                        council=council,
                        tender_type=document_type.lower().replace(" ", "_"),
                        project_manager=project_manager_name
                    )
                    
                    st.success(f"✅ Created new {document_type}: {project_title}")
                    
                    # Set as selected project and navigate to upload
                    st.session_state["selected_project"] = new_project
                    st.session_state["current_page"] = "upload"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating project: {str(e)}")
            else:
                st.error("Please fill in all required fields.")

def show_project_details(project: Project):
    """Show detailed project information in a modal-like interface"""
    
    st.markdown("#### 📋 Project Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Project ID:** {project.project_id}")
        st.write(f"**Title:** {project.title}")
        st.write(f"**Category:** {project.category.value.title()}")
        st.write(f"**Status:** {project.status.value.title()}")
        st.write(f"**Contract Value:** ${project.contract_value:,.0f}")
    
    with col2:
        st.write(f"**Council:** {project.council}")
        st.write(f"**Project Manager:** {project.project_manager}")
        st.write(f"**Created:** {project.created_date[:10]}")
        st.write(f"**Last Modified:** {project.last_modified[:10]}")
        if project.completion_date:
            st.write(f"**Completed:** {project.completion_date[:10]}")
    
    st.write(f"**Description:** {project.description}")
    
    if project.tags:
        st.write("**Tags:**")
        tag_cols = st.columns(len(project.tags))
        for i, tag in enumerate(project.tags):
            with tag_cols[i]:
                st.markdown(f"`{tag}`")
    
    if project.keywords:
        st.write("**Keywords:**")
        st.write(", ".join(project.keywords))
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Use as Template", key=f"detail_template_{project.project_id}"):
            st.session_state["selected_project"] = project
            st.session_state["use_as_template"] = True
            st.session_state["current_page"] = "upload"
            st.rerun()
    
    with col2:
        if st.button("📝 Edit Project", key=f"edit_{project.project_id}"):
            st.info("Project editing feature coming soon!")
    
    with col3:
        if st.button("📊 View Reports", key=f"reports_{project.project_id}"):
            st.info("Project reports feature coming soon!")
