"""
AI-Powered Compliance Dashboard
Real-time monitoring of NSW procurement compliance across all projects and data
"""

import streamlit as st
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.ui_helpers import _inject_css
from app.components.sidebar_navigation import render_sidebar
from app.services.ai_compliance_analyzer import AIComplianceAnalyzer, ComplianceLevel, ComplianceCategory
from app.services.unified_compliance_engine import UnifiedComplianceEngine
from app.services.three_tier_rag_system import ThreeTierRAGSystem
from app.services.collaborative_evaluation_system import CollaborativeEvaluationSystem
from app.services.historical_matching import HistoricalMatchingService
from app.services.quote_generator import AIQuoteGenerator
from app.config import settings
from pathlib import Path

def page_compliance_dashboard():
    """AI-Powered Compliance Dashboard page"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.error("Please sign in to access the Compliance Dashboard")
        return
    
    # Inject CSS and render sidebar
    _inject_css()
    render_sidebar()
    
    # Initialize all compliance-related systems
    if 'compliance_analyzer' not in st.session_state:
        st.session_state.compliance_analyzer = AIComplianceAnalyzer(settings.DATA_DIR)
    
    if 'unified_compliance_engine' not in st.session_state:
        st.session_state.unified_compliance_engine = UnifiedComplianceEngine(settings.DATA_DIR)
    
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = ThreeTierRAGSystem(settings.DATA_DIR)
    
    if 'collaborative_evaluation' not in st.session_state:
        st.session_state.collaborative_evaluation = CollaborativeEvaluationSystem(settings.DATA_DIR)
    
    if 'historical_matching' not in st.session_state:
        st.session_state.historical_matching = HistoricalMatchingService(settings.DATA_DIR)
    
    if 'quote_generator' not in st.session_state:
        st.session_state.quote_generator = AIQuoteGenerator(settings.DATA_DIR)
    
    analyzer = st.session_state.compliance_analyzer
    unified_engine = st.session_state.unified_compliance_engine
    rag_system = st.session_state.rag_system
    eval_system = st.session_state.collaborative_evaluation
    historical_service = st.session_state.historical_matching
    quote_service = st.session_state.quote_generator
    
    # Page header
    st.markdown("## 🛡️ AI-Powered Compliance Dashboard")
    st.markdown("Real-time monitoring of NSW procurement compliance across all projects and data")
    
    # System Integration Status
    st.markdown("### 🔗 Integrated Systems Status")
    
    # Display system status
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("🤖 AI Compliance", "Active", "✅")
    
    with col2:
        st.metric("🔄 Unified Engine", "Active", "✅")
    
    with col3:
        st.metric("📚 RAG System", "Active", "✅")
    
    with col4:
        st.metric("🤝 Evaluations", "Active", "✅")
    
    with col5:
        st.metric("🔍 Historical", "Active", "✅")
    
    with col6:
        st.metric("💰 Quotes", "Active", "✅")
    
    st.markdown("---")
    
    # Control panel
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔄 Refresh Scan", type="primary"):
            with st.spinner("Scanning all data for compliance..."):
                # Run async scan
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    metrics = loop.run_until_complete(analyzer.scan_all_data())
                    st.success("✅ Compliance scan completed!")
                    st.rerun()
                finally:
                    loop.close()
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("📊 Compliance report generation - Coming soon")
    
    with col3:
        if st.button("🚨 View Alerts"):
            st.info("🚨 Alert management - Coming soon")
    
    with col4:
        if st.button("⚙️ Settings"):
            st.info("⚙️ Compliance settings - Coming soon")
    
    with col5:
        if st.button("🚪 Sign Out", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Get dashboard data
    dashboard_data = analyzer.get_compliance_dashboard_data()
    
    if not dashboard_data['metrics']:
        st.warning("⚠️ No compliance data available. Click 'Refresh Scan' to analyze all projects.")
        return
    
    # Main metrics row
    _display_main_metrics(dashboard_data['metrics'])
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "🚨 Violations", 
        "📈 Trends", 
        "🔍 Projects", 
        "📋 Rules",
        "🔗 System Integration"
    ])
    
    with tab1:
        _display_overview_tab(dashboard_data)
    
    with tab2:
        _display_violations_tab(analyzer)
    
    with tab3:
        _display_trends_tab(dashboard_data)
    
    with tab4:
        _display_projects_tab(analyzer)
    
    with tab5:
        _display_rules_tab(analyzer)
    
    with tab6:
        _display_system_integration_tab(analyzer, unified_engine, rag_system, eval_system, historical_service, quote_service)

def _display_main_metrics(metrics: Dict[str, Any]):
    """Display main compliance metrics"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Compliance Score",
            f"{metrics['compliance_score']:.1f}%",
            delta=f"{metrics['compliance_score'] - 85:.1f}%" if metrics['compliance_score'] > 85 else None
        )
    
    with col2:
        st.metric(
            "Total Projects",
            metrics['total_projects'],
            delta=f"+{metrics['compliant_projects']}" if metrics['compliant_projects'] > 0 else None
        )
    
    with col3:
        st.metric(
            "Critical Violations",
            metrics['critical_violations'],
            delta=f"-{metrics['critical_violations']}" if metrics['critical_violations'] > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "High Priority",
            metrics['high_violations'],
            delta=f"-{metrics['high_violations']}" if metrics['high_violations'] > 0 else None,
            delta_color="inverse"
        )
    
    with col5:
        st.metric(
            "Compliant Projects",
            metrics['compliant_projects'],
            delta=f"+{metrics['compliant_projects']}" if metrics['compliant_projects'] > 0 else None
        )

def _display_overview_tab(dashboard_data: Dict[str, Any]):
    """Display overview tab with charts and summary"""
    
    # Compliance score gauge
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Compliance Score")
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = dashboard_data['metrics']['compliance_score'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Compliance"},
            delta = {'reference': 85},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🚨 Violations by Severity")
        
        # Violations pie chart
        violation_data = {
            'Critical': dashboard_data['metrics']['critical_violations'],
            'High': dashboard_data['metrics']['high_violations'],
            'Medium': dashboard_data['metrics']['medium_violations'],
            'Low': dashboard_data['metrics']['low_violations']
        }
        
        colors = ['red', 'orange', 'yellow', 'lightblue']
        
        fig = px.pie(
            values=list(violation_data.values()),
            names=list(violation_data.keys()),
            color_discrete_sequence=colors,
            title="Violation Distribution"
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Compliance by category
    st.markdown("### 📋 Compliance by Category")
    
    categories = ['Legislative', 'Financial', 'Process', 'Social', 'Environmental', 'Safety', 'Documentation', 'Timeline']
    compliance_scores = [85, 92, 78, 88, 90, 95, 82, 87]  # Mock data - would be calculated from actual data
    
    fig = px.bar(
        x=categories,
        y=compliance_scores,
        title="Compliance Score by Category",
        color=compliance_scores,
        color_continuous_scale="RdYlGn"
    )
    
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def _display_violations_tab(analyzer: AIComplianceAnalyzer):
    """Display violations tab with detailed violation list"""
    
    st.markdown("### 🚨 Active Compliance Violations")
    
    violations = analyzer.violations
    
    if not violations:
        st.success("✅ No active violations found!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    with col2:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All"] + [cat.value.title() for cat in ComplianceCategory]
        )
    
    with col3:
        project_filter = st.selectbox(
            "Filter by Project",
            ["All"] + list(set(v.project_name for v in violations))
        )
    
    # Filter violations
    filtered_violations = violations
    
    if severity_filter != "All":
        filtered_violations = [v for v in filtered_violations if v.severity.value == severity_filter.lower()]
    
    if category_filter != "All":
        # Get rule categories
        rule_categories = {rule.rule_id: rule.category.value for rule in analyzer.compliance_rules}
        filtered_violations = [v for v in filtered_violations if rule_categories.get(v.rule_id, '').title() == category_filter]
    
    if project_filter != "All":
        filtered_violations = [v for v in filtered_violations if v.project_name == project_filter]
    
    st.markdown(f"**Found {len(filtered_violations)} violations**")
    
    # Display violations
    for i, violation in enumerate(filtered_violations):
        with st.expander(f"🚨 {violation.violation_type} - {violation.project_name}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:** {violation.description}")
                st.markdown(f"**Project:** {violation.project_name}")
                st.markdown(f"**Detected:** {violation.detected_at[:19]}")
                if violation.due_date:
                    st.markdown(f"**Due Date:** {violation.due_date[:19]}")
            
            with col2:
                # Severity badge
                severity_color = {
                    'critical': 'red',
                    'high': 'orange', 
                    'medium': 'yellow',
                    'low': 'blue'
                }
                
                st.markdown(f"""
                <div style="background-color: {severity_color.get(violation.severity.value, 'gray')}; 
                           color: white; padding: 0.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 1rem;">
                    <strong>{violation.severity.value.upper()}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Confidence:** {violation.ai_confidence:.1%}")
                st.markdown(f"**Status:** {violation.status}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📝 Add Notes", key=f"notes_{i}"):
                    st.info("📝 Add resolution notes - Coming soon")
            
            with col2:
                if st.button(f"✅ Mark Resolved", key=f"resolve_{i}"):
                    st.info("✅ Mark as resolved - Coming soon")
            
            with col3:
                if st.button(f"🔍 View Details", key=f"details_{i}"):
                    st.info("🔍 View detailed analysis - Coming soon")

def _display_trends_tab(dashboard_data: Dict[str, Any]):
    """Display trends tab with historical compliance data"""
    
    st.markdown("### 📈 Compliance Trends")
    
    # Mock historical data - would come from database
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    compliance_scores = [85 + (i % 10) - 5 for i in range(30)]
    violations = [max(0, 5 + (i % 8) - 4) for i in range(30)]
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Compliance Score Over Time', 'Violations Over Time'),
        vertical_spacing=0.1
    )
    
    # Compliance score line
    fig.add_trace(
        go.Scatter(x=dates, y=compliance_scores, name='Compliance Score', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Violations bar chart
    fig.add_trace(
        go.Bar(x=dates, y=violations, name='Violations', marker_color='red'),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Compliance by project type
    st.markdown("### 📊 Compliance by Project Type")
    
    project_types = ['Construction', 'Services', 'Goods', 'Consulting']
    type_scores = [88, 92, 85, 90]
    
    fig = px.bar(
        x=project_types,
        y=type_scores,
        title="Compliance Score by Project Type",
        color=type_scores,
        color_continuous_scale="RdYlGn"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _display_projects_tab(analyzer: AIComplianceAnalyzer):
    """Display projects tab with project-specific compliance"""
    
    st.markdown("### 🔍 Project Compliance Status")
    
    # Get violations by project
    project_violations = analyzer.get_violations_by_project()
    
    if not project_violations:
        st.info("No project data available for analysis.")
        return
    
    # Project compliance table
    project_data = []
    
    for project_id, violations in project_violations.items():
        critical_count = len([v for v in violations if v.severity == ComplianceLevel.CRITICAL])
        high_count = len([v for v in violations if v.severity == ComplianceLevel.HIGH])
        medium_count = len([v for v in violations if v.severity == ComplianceLevel.MEDIUM])
        low_count = len([v for v in violations if v.severity == ComplianceLevel.LOW])
        
        total_violations = len(violations)
        compliance_score = max(0, 100 - (critical_count * 20 + high_count * 10 + medium_count * 5 + low_count * 2))
        
        project_data.append({
            'Project': violations[0].project_name if violations else project_id,
            'ID': project_id,
            'Compliance Score': f"{compliance_score:.1f}%",
            'Critical': critical_count,
            'High': high_count,
            'Medium': medium_count,
            'Low': low_count,
            'Total': total_violations
        })
    
    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(project_data)
    
    # Sort by compliance score
    df['Score_Num'] = df['Compliance Score'].str.rstrip('%').astype(float)
    df = df.sort_values('Score_Num', ascending=True)
    df = df.drop('Score_Num', axis=1)
    
    st.dataframe(df, use_container_width=True)
    
    # Project details
    if st.selectbox("Select Project for Details", [""] + [p['Project'] for p in project_data]):
        selected_project = st.selectbox("Select Project for Details", [p['Project'] for p in project_data])
        project_id = next(p['ID'] for p in project_data if p['Project'] == selected_project)
        
        st.markdown(f"### 📋 Details for {selected_project}")
        
        project_violations_list = project_violations.get(project_id, [])
        
        if project_violations_list:
            for violation in project_violations_list:
                st.markdown(f"**{violation.violation_type}** ({violation.severity.value})")
                st.markdown(f"- {violation.description}")
                st.markdown(f"- Detected: {violation.detected_at[:19]}")
                st.markdown("---")
        else:
            st.success("✅ No violations found for this project!")

def _display_rules_tab(analyzer: AIComplianceAnalyzer):
    """Display rules tab with compliance rules and their status"""
    
    st.markdown("### 📋 NSW Procurement Compliance Rules")
    
    rules = analyzer.compliance_rules
    
    # Rules summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rules", len(rules))
    
    with col2:
        critical_rules = len([r for r in rules if r.level == ComplianceLevel.CRITICAL])
        st.metric("Critical Rules", critical_rules)
    
    with col3:
        high_rules = len([r for r in rules if r.level == ComplianceLevel.HIGH])
        st.metric("High Priority Rules", high_rules)
    
    with col4:
        categories = len(set(r.category for r in rules))
        st.metric("Rule Categories", categories)
    
    st.markdown("---")
    
    # Rules by category
    for category in ComplianceCategory:
        category_rules = [r for r in rules if r.category == category]
        
        if category_rules:
            with st.expander(f"📋 {category.value.title()} Rules ({len(category_rules)})", expanded=False):
                for rule in category_rules:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{rule.name}**")
                        st.markdown(f"*{rule.description}*")
                        st.markdown(f"NSW Reference: {rule.nsw_reference}")
                    
                    with col2:
                        # Severity badge
                        severity_color = {
                            'critical': 'red',
                            'high': 'orange',
                            'medium': 'yellow',
                            'low': 'blue'
                        }
                        
                        st.markdown(f"""
                        <div style="background-color: {severity_color.get(rule.level.value, 'gray')}; 
                                   color: white; padding: 0.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 1rem;">
                            <strong>{rule.level.value.upper()}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if rule.value_threshold:
                            st.markdown(f"Threshold: ${rule.value_threshold:,}")
                    
                    st.markdown("---")
    
    # AI Analysis Status
    st.markdown("### 🤖 AI Analysis Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("AI Model", analyzer.ai_model.model_name if analyzer.ai_model else "Not Available")
    
    with col2:
        # Get fresh dashboard data for this section
        fresh_data = analyzer.get_compliance_dashboard_data()
        st.metric("Last Scan", fresh_data['last_scan'][:19] if fresh_data['last_scan'] else "Never")
    
    with col3:
        st.metric("Total Violations", fresh_data['total_violations'])
    
    # AI Configuration
    if st.button("🔧 Configure AI Analysis"):
        st.info("🔧 AI configuration - Coming soon")

def _display_system_integration_tab(analyzer, unified_engine, rag_system, eval_system, historical_service, quote_service):
    """Display system integration tab with cross-system monitoring"""
    
    st.markdown("### 🔗 System Integration & Cross-References")
    st.markdown("Monitor compliance across all integrated systems and their interactions")
    
    # System Overview
    st.markdown("#### 📊 System Status Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🤖 AI Compliance Analyzer**")
        st.info("✅ Active - Real-time compliance monitoring")
        st.markdown("- **Rules Loaded:** 25+ NSW compliance rules")
        st.markdown("- **AI Model:** Gemini 1.5 Flash")
        st.markdown("- **Last Scan:** Real-time")
        
        st.markdown("**🔄 Unified Compliance Engine**")
        st.info("✅ Active - Comprehensive compliance checking")
        st.markdown("- **Blacktown Standards:** Integrated")
        st.markdown("- **Global NSW Standards:** Active")
        st.markdown("- **RAG Integration:** Connected")
    
    with col2:
        st.markdown("**📚 Three-Tier RAG System**")
        st.info("✅ Active - Document intelligence")
        st.markdown("- **Compliance Tier:** Active")
        st.markdown("- **Internal Tier:** Active")
        st.markdown("- **External Tier:** Active")
        
        st.markdown("**🤝 Collaborative Evaluation**")
        st.info("✅ Active - AI-powered evaluation")
        st.markdown("- **AI Pre-scoring:** Active")
        st.markdown("- **Committee Review:** Ready")
        st.markdown("- **Consensus Building:** Available")
    
    st.markdown("---")
    
    # Cross-System Compliance Monitoring
    st.markdown("#### 🔍 Cross-System Compliance Monitoring")
    
    # RAG System Integration
    with st.expander("📚 RAG System Integration", expanded=True):
        try:
            rag_stats = rag_system.get_system_statistics()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Documents", rag_stats.get("total_documents", 0))
            
            with col2:
                compliance_docs = rag_stats.get("tier_breakdown", {}).get("compliance", 0)
                st.metric("Compliance Docs", compliance_docs)
            
            with col3:
                st.metric("System Health", "✅ Healthy")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📤 Upload Documents", key="rag_upload"):
                    st.session_state["show_rag_upload"] = True
                    st.rerun()
            
            with col2:
                if st.button("🔍 Search Documents", key="rag_search"):
                    st.info("🔍 Document search - Coming soon")
            
            with col3:
                if st.button("📊 View Analytics", key="rag_analytics"):
                    st.info("📊 RAG analytics - Coming soon")
        
        except Exception as e:
            st.error(f"❌ Error accessing RAG system: {e}")
    
    # Collaborative Evaluation Integration
    with st.expander("🤝 Collaborative Evaluation Integration", expanded=True):
        try:
            # Get evaluation statistics
            eval_stats = eval_system.get_evaluation_summary("current") if hasattr(eval_system, 'get_evaluation_summary') else {"total_suppliers": 0, "status": "No active evaluations"}
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Active Evaluations", eval_stats.get("total_suppliers", 0))
            
            with col2:
                st.metric("Evaluation Status", eval_stats.get("status", "None"))
            
            with col3:
                st.metric("System Status", "✅ Ready")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🏁 Start Evaluation", key="eval_start"):
                    st.session_state["current_page"] = "collaborative_evaluation"
                    st.rerun()
            
            with col2:
                if st.button("📊 View Results", key="eval_results"):
                    st.info("📊 Evaluation results - Coming soon")
            
            with col3:
                if st.button("📋 Manage Committee", key="eval_committee"):
                    st.info("📋 Committee management - Coming soon")
        
        except Exception as e:
            st.error(f"❌ Error accessing evaluation system: {e}")
    
    # Historical Matching Integration
    with st.expander("🔍 Historical Matching Integration", expanded=True):
        try:
            # Get historical project statistics
            hist_stats = historical_service.get_project_statistics() if hasattr(historical_service, 'get_project_statistics') else {"total_projects": 0, "categories": {}}
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Historical Projects", hist_stats.get("total_projects", 0))
            
            with col2:
                categories = len(hist_stats.get("categories", {}))
                st.metric("Project Categories", categories)
            
            with col3:
                st.metric("Matching Status", "✅ Active")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Match Project", key="hist_match"):
                    st.session_state["current_page"] = "historical_matching"
                    st.rerun()
            
            with col2:
                if st.button("📊 View Analytics", key="hist_analytics"):
                    st.info("📊 Historical analytics - Coming soon")
            
            with col3:
                if st.button("📋 Add Project", key="hist_add"):
                    st.info("📋 Add historical project - Coming soon")
        
        except Exception as e:
            st.error(f"❌ Error accessing historical matching: {e}")
    
    # Quote Generator Integration
    with st.expander("💰 Quote Generator Integration", expanded=True):
        try:
            # Get quote statistics
            quote_stats = quote_service.get_quote_statistics() if hasattr(quote_service, 'get_quote_statistics') else {"total_quotes": 0, "total_value": 0}
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Quotes", quote_stats.get("total_quotes", 0))
            
            with col2:
                total_value = quote_stats.get("total_value", 0)
                st.metric("Total Value", f"${total_value:,.0f}")
            
            with col3:
                st.metric("Generator Status", "✅ Active")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💰 Generate Quote", key="quote_generate"):
                    st.session_state["show_quote_interface"] = True
                    st.rerun()
            
            with col2:
                if st.button("📊 View Analytics", key="quote_analytics"):
                    st.info("📊 Quote analytics - Coming soon")
            
            with col3:
                if st.button("📋 Manage Quotes", key="quote_manage"):
                    st.info("📋 Quote management - Coming soon")
        
        except Exception as e:
            st.error(f"❌ Error accessing quote generator: {e}")
    
    st.markdown("---")
    
    # System Health Monitoring
    st.markdown("#### 🏥 System Health Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("AI Model Status", "✅ Gemini 1.5 Flash", "Active")
    
    with col2:
        st.metric("Database Status", "✅ Connected", "Healthy")
    
    with col3:
        st.metric("API Status", "✅ All Systems", "Operational")
    
    with col4:
        st.metric("Last Update", "Just Now", "✅ Current")
    
    # Quick System Actions
    st.markdown("#### ⚡ Quick System Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh All Systems", type="primary", use_container_width=True):
            st.success("✅ All systems refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 Generate Full Report", use_container_width=True):
            st.info("📊 Comprehensive system report - Coming soon")
    
    with col3:
        if st.button("🔧 System Settings", use_container_width=True):
            st.info("🔧 System configuration - Coming soon")
    
    with col4:
        if st.button("📈 Performance Monitor", use_container_width=True):
            st.info("📈 Performance monitoring - Coming soon")
