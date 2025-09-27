#!/usr/bin/env python3
"""
Historical Project Matching Dashboard
AI-powered matching of new projects with historical data
"""

import streamlit as st
from pathlib import Path
import os
from app.services.historical_matching import HistoricalMatchingService, ProjectCategory, MatchType
from app.core.ui_helpers import _inject_css
from app.components.sidebar_navigation import render_sidebar
from datetime import datetime

def page_historical_matching_dashboard():
    """Historical Project Matching Dashboard Page"""
    
    # Inject CSS and render sidebar
    _inject_css()
    render_sidebar()
    
    st.title("🔍 Historical Project Matching")
    st.markdown("AI-powered matching of new projects with historical data for improved planning and cost estimation")
    
    # Initialize historical matching service
    try:
        matching_service = HistoricalMatchingService()
        
        # Initialize sample data if no projects exist
        if not matching_service.historical_projects:
            with st.spinner("Initializing sample historical projects..."):
                matching_service.initialize_sample_data()
                st.success("✅ Sample historical projects loaded")
    except Exception as e:
        st.error(f"❌ Error initializing historical matching service: {e}")
        return
    
    # Get project statistics
    stats = matching_service.get_project_statistics()
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Historical Projects",
            value=stats['total_projects'],
            delta=f"${stats['total_value']:,.0f} total value"
        )
    
    with col2:
        st.metric(
            label="Average Project Cost",
            value=f"${stats['average_cost']:,.0f}",
            delta=f"{stats['average_duration']:.0f} days avg"
        )
    
    with col3:
        st.metric(
            label="Project Categories",
            value=len(stats['categories']),
            delta="Available for matching"
        )
    
    with col4:
        st.metric(
            label="Councils",
            value=len(stats['councils']),
            delta="Historical data"
        )
    
    # Main matching interface
    st.subheader("🎯 Find Matching Historical Projects")
    
    # Project input form
    with st.form("project_matching_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_title = st.text_input("Project Title", placeholder="Enter project title")
            project_description = st.text_area(
                "Project Description", 
                placeholder="Describe the project scope, requirements, and objectives",
                height=100
            )
            project_category = st.selectbox(
                "Project Category",
                options=[cat.value for cat in ProjectCategory],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            project_budget = st.number_input(
                "Estimated Budget ($)", 
                min_value=0.0, 
                value=0.0,
                help="Optional: Enter estimated budget for cost comparison"
            )
            project_timeline = st.number_input(
                "Estimated Timeline (days)", 
                min_value=1, 
                value=90,
                help="Optional: Enter estimated project duration"
            )
            council = st.selectbox(
                "Council",
                options=["Blacktown City Council", "Other NSW Council"],
                index=0
            )
        
        submitted = st.form_submit_button("🔍 Find Matching Projects", use_container_width=True)
    
    # Process matching request
    if submitted and project_description:
        with st.spinner("🔍 Analyzing historical projects..."):
            try:
                # Find matching projects
                matches = matching_service.find_matching_projects(
                    new_project_description=project_description,
                    new_project_category=ProjectCategory(project_category),
                    new_project_budget=project_budget if project_budget > 0 else None,
                    new_project_timeline=project_timeline,
                    council=council
                )
                
                if matches:
                    st.success(f"✅ Found {len(matches)} matching historical projects")
                    
                    # Display matches
                    for i, match in enumerate(matches, 1):
                        with st.expander(f"📋 Match {i}: {match.historical_project.title} (Score: {match.similarity_score:.2f})", expanded=i==1):
                            
                            # Match overview
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Similarity Score", f"{match.similarity_score:.1%}")
                                st.metric("Match Type", match.match_type.value.title())
                            
                            with col2:
                                st.metric("Historical Cost", f"${match.historical_project.total_cost:,.0f}")
                                st.metric("Historical Duration", f"{matching_service._calculate_duration(match.historical_project)} days")
                            
                            with col3:
                                cost_range = match.cost_estimate_range
                                timeline_range = match.timeline_estimate
                                st.metric("Estimated Cost Range", f"${cost_range[0]:,.0f} - ${cost_range[1]:,.0f}")
                                st.metric("Estimated Timeline", f"{timeline_range[0]} - {timeline_range[1]} days")
                            
                            # Project details
                            st.markdown("### 📄 Historical Project Details")
                            st.write(f"**Description:** {match.historical_project.description}")
                            st.write(f"**Category:** {match.historical_project.category.value.replace('_', ' ').title()}")
                            st.write(f"**Council:** {match.historical_project.council}")
                            st.write(f"**Project Type:** {match.historical_project.project_type}")
                            
                            # Key specifications
                            if match.historical_project.key_specifications:
                                st.markdown("**Key Specifications:**")
                                for spec in match.historical_project.key_specifications:
                                    st.markdown(f"• {spec}")
                            
                            # Matching factors
                            if match.matching_factors:
                                st.markdown("**Matching Factors:**")
                                for factor in match.matching_factors:
                                    st.markdown(f"• {factor}")
                            
                            # AI recommendations
                            if match.recommendations:
                                st.markdown("### 🤖 AI Recommendations")
                                for rec in match.recommendations:
                                    st.info(f"💡 {rec}")
                            
                            # Risk factors
                            if match.risk_factors:
                                st.markdown("### ⚠️ Risk Factors")
                                for risk in match.risk_factors:
                                    st.warning(f"⚠️ {risk}")
                            
                            # Historical performance
                            if match.historical_project.contractor_performance:
                                st.markdown("### 📊 Historical Contractor Performance")
                                perf = match.historical_project.contractor_performance
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Quality", f"{perf.get('quality', 0):.1f}/5.0")
                                with col2:
                                    st.metric("Timeliness", f"{perf.get('timeliness', 0):.1f}/5.0")
                                with col3:
                                    st.metric("Communication", f"{perf.get('communication', 0):.1f}/5.0")
                            
                            # Lessons learned
                            if match.historical_project.lessons_learned:
                                st.markdown("### 📚 Lessons Learned")
                                for lesson in match.historical_project.lessons_learned:
                                    st.success(f"✅ {lesson}")
                            
                            # Compliance issues
                            if match.historical_project.compliance_issues:
                                st.markdown("### 🛡️ Historical Compliance Issues")
                                for issue in match.historical_project.compliance_issues:
                                    st.error(f"❌ {issue}")
                
                else:
                    st.warning("⚠️ No matching historical projects found. Try adjusting your search criteria.")
                    
            except Exception as e:
                st.error(f"❌ Error finding matches: {e}")
    
    # Historical projects overview
    st.subheader("📚 Historical Projects Overview")
    
    # Category breakdown
    if stats['categories']:
        st.markdown("### 📊 Projects by Category")
        for category, count in stats['categories'].items():
            st.write(f"• **{category.replace('_', ' ').title()}**: {count} projects")
    
    # Recent projects
    if matching_service.historical_projects:
        st.markdown("### 📋 Recent Historical Projects")
        
        # Show last 5 projects
        recent_projects = sorted(
            matching_service.historical_projects, 
            key=lambda x: x.created_date, 
            reverse=True
        )[:5]
        
        for project in recent_projects:
            with st.expander(f"📄 {project.title} - ${project.total_cost:,.0f}"):
                st.write(f"**Description:** {project.description}")
                st.write(f"**Category:** {project.category.value.replace('_', ' ').title()}")
                st.write(f"**Duration:** {matching_service._calculate_duration(project)} days")
                st.write(f"**Council:** {project.council}")
                
                if project.success_factors:
                    st.markdown("**Success Factors:**")
                    for factor in project.success_factors:
                        st.markdown(f"• {factor}")
    
    # Add new historical project
    st.subheader("➕ Add New Historical Project")
    
    with st.expander("📝 Add Historical Project", expanded=False):
        with st.form("add_historical_project_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input("Project Title")
                new_description = st.text_area("Project Description", height=100)
                new_category = st.selectbox(
                    "Project Category",
                    options=[cat.value for cat in ProjectCategory],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                new_start_date = st.date_input("Start Date")
                new_end_date = st.date_input("End Date")
            
            with col2:
                new_cost = st.number_input("Total Cost ($)", min_value=0.0)
                new_council = st.text_input("Council", value="Blacktown City Council")
                new_project_type = st.text_input("Project Type")
                new_specifications = st.text_area("Key Specifications (one per line)", height=100)
                new_success_factors = st.text_area("Success Factors (one per line)", height=100)
            
            if st.form_submit_button("➕ Add Historical Project"):
                if new_title and new_description and new_cost > 0:
                    try:
                        # Process specifications and success factors
                        specifications = [s.strip() for s in new_specifications.split('\n') if s.strip()]
                        success_factors = [s.strip() for s in new_success_factors.split('\n') if s.strip()]
                        
                        project_id = matching_service.add_historical_project(
                            title=new_title,
                            description=new_description,
                            category=ProjectCategory(new_category),
                            start_date=new_start_date.strftime("%Y-%m-%d"),
                            end_date=new_end_date.strftime("%Y-%m-%d"),
                            total_cost=new_cost,
                            council=new_council,
                            project_type=new_project_type,
                            key_specifications=specifications,
                            success_factors=success_factors
                        )
                        
                        st.success(f"✅ Historical project added successfully! ID: {project_id}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error adding historical project: {e}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Footer
    st.markdown("---")
    st.markdown("**🔍 Historical Project Matching** - AI-Powered Project Planning and Cost Estimation")
    st.caption("Use historical project data to improve planning, cost estimation, and risk assessment for new projects")
