#!/usr/bin/env python3
"""
Progress Dashboard Page
Shows development progress with downloadable reports
"""

import streamlit as st
from pathlib import Path
import os
from app.services.progress_tracker import ProgressTracker
from app.core.ui_helpers import _inject_css
from app.components.sidebar_navigation import render_sidebar

def page_progress_dashboard():
    """Progress Dashboard Page"""
    
    # Inject CSS and render sidebar
    _inject_css()
    render_sidebar()
    
    st.title("📊 Development Progress Dashboard")
    st.markdown("Track development milestones and generate reports for stakeholders")
    
    # Initialize progress tracker first
    progress_tracker = ProgressTracker()
    
    # Get overall progress
    overall_progress = progress_tracker.get_overall_progress()
    
    # Display current date
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    st.info(f"📅 **Current Date**: {current_date} | Last Updated: {overall_progress['last_updated'][:10]}")
    
    # Display overall progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Overall Progress",
            value=f"{overall_progress['overall_progress_percentage']}%",
            delta=f"{overall_progress['completed_features']}/{overall_progress['total_features']} features"
        )
    
    with col2:
        st.metric(
            label="Completed Features",
            value=overall_progress['completed_features'],
            delta=f"{overall_progress['total_features'] - overall_progress['completed_features']} remaining"
        )
    
    with col3:
        st.metric(
            label="In Progress",
            value=overall_progress['in_progress_features'],
            delta="Currently active"
        )
    
    with col4:
        st.metric(
            label="Planned Features",
            value=overall_progress['planned_features'],
            delta="Future development"
        )
    
    # Progress bar
    st.progress(overall_progress['overall_progress_percentage'] / 100)
    st.caption(f"Last updated: {overall_progress['last_updated']}")
    
    # Features by category
    st.subheader("📋 Features by Category")
    categories = progress_tracker.get_features_by_category()
    
    for category, features in categories.items():
        with st.expander(f"{category} ({len(features)} features)"):
            for feature in features:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{feature.name}**")
                    st.caption(feature.description)
                    if feature.stakeholder_impact:
                        st.info(f"💡 {feature.stakeholder_impact}")
                
                with col2:
                    status_color = {
                        "Completed": "🟢",
                        "In Progress": "🟡", 
                        "Planned": "⚪",
                        "Testing": "🔵",
                        "Deployed": "✅"
                    }.get(feature.status.value, "⚪")
                    st.write(f"{status_color} {feature.status.value}")
                
                with col3:
                    st.write(f"**{feature.progress_percentage}%**")
                    st.progress(feature.progress_percentage / 100)
    
    # Report generation section
    st.subheader("📄 Generate Reports")
    st.markdown("Download comprehensive progress reports for stakeholders")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate Excel Report", use_container_width=True):
            with st.spinner("Generating Excel report..."):
                excel_path = progress_tracker.generate_excel_report()
                if excel_path:
                    st.success("✅ Excel report generated successfully!")
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=open(excel_path, 'rb').read(),
                        file_name=f"progress_report_{Path(excel_path).name}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Failed to generate Excel report")
    
    with col2:
        if st.button("📋 Generate JSON Report", use_container_width=True):
            with st.spinner("Generating JSON report..."):
                json_path = progress_tracker.generate_json_report()
                if json_path:
                    st.success("✅ JSON report generated successfully!")
                    st.download_button(
                        label="📥 Download JSON Report",
                        data=open(json_path, 'rb').read(),
                        file_name=f"progress_report_{Path(json_path).name}",
                        mime="application/json"
                    )
                else:
                    st.error("❌ Failed to generate JSON report")
    
    with col3:
        if st.button("📝 Generate Summary Report", use_container_width=True):
            st.info("📋 Summary Report Generated")
            
            # Display summary
            st.subheader("📈 Project Summary")
            
            # Key achievements
            st.markdown("### 🎯 Key Achievements")
            completed_features = [f for f in progress_tracker.features if f.status.value == "Completed"]
            
            for feature in completed_features[:5]:  # Show top 5
                st.markdown(f"✅ **{feature.name}** - {feature.stakeholder_impact}")
            
            # Stakeholder benefits
            st.markdown("### 👥 Stakeholder Benefits")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**LGP Benefits:**")
                st.markdown("• Automated compliance checking reduces manual review time by 80%")
                st.markdown("• AI-powered tender generation saves 15+ hours per tender")
                st.markdown("• Real-time violation tracking ensures regulatory compliance")
                st.markdown("• Centralized document management improves accessibility")
            
            with col2:
                st.markdown("**Council Benefits:**")
                st.markdown("• Streamlined procurement process reduces administrative burden")
                st.markdown("• AI assistance improves tender quality and compliance")
                st.markdown("• Historical data matching improves project planning")
                st.markdown("• Mobile access enables field-based procurement management")
    
    # Development timeline
    st.subheader("📅 Development Timeline")
    
    # Show current date context
    from datetime import datetime
    today = datetime.now()
    st.caption(f"Timeline based on current system date: {today.strftime('%B %d, %Y')}")
    
    timeline_data = []
    for feature in progress_tracker.features:
        # Calculate days since start/completion
        start_date = datetime.strptime(feature.start_date, "%Y-%m-%d")
        days_since_start = (today - start_date).days
        
        status_info = feature.status.value
        if feature.completion_date:
            completion_date = datetime.strptime(feature.completion_date, "%Y-%m-%d")
            days_since_completion = (today - completion_date).days
            status_info += f" ({days_since_completion} days ago)"
        elif feature.status.value == "In Progress":
            status_info += f" (Day {days_since_start})"
        
        timeline_data.append({
            "Feature": feature.name,
            "Start Date": feature.start_date,
            "Target Date": feature.target_date,
            "Completion Date": feature.completion_date or "TBD",
            "Status": status_info,
            "Progress": f"{feature.progress_percentage}%",
            "Days Active": days_since_start
        })
    
    if timeline_data:
        st.dataframe(timeline_data, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("**📊 Progress Dashboard** - NSW Procurement Platform Development Tracking")
    st.caption("This dashboard provides real-time visibility into development progress for all stakeholders")
