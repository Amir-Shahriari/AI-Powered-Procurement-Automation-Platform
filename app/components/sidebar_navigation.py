"""
Google AI Studio-style sidebar navigation component
"""
import streamlit as st
from typing import Dict, List, Optional
from app.core.navigation import _nav_set

def render_sidebar():
    """Render the Google AI Studio-style sidebar"""
    
    # Sidebar styling
    st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    .sidebar-section {
        margin-bottom: 1.5rem;
    }
    
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        padding: 0.5rem 0;
    }
    
    .sidebar-item {
        display: flex;
        align-items: center;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem 0;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.2s;
        font-size: 0.9rem;
        color: #5f6368;
    }
    
    .sidebar-item:hover {
        background-color: #e8f0fe;
    }
    
    .sidebar-item.active {
        background-color: #e8f0fe;
        color: #1a73e8;
        font-weight: 500;
    }
    
    .sidebar-item-icon {
        margin-right: 0.75rem;
        font-size: 1rem;
    }
    
    .sidebar-chevron {
        margin-left: auto;
        font-size: 0.8rem;
        transition: transform 0.2s;
    }
    
    .sidebar-chevron.expanded {
        transform: rotate(90deg);
    }
    
    .sidebar-button {
        background: #1a73e8;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .sidebar-button:hover {
        background: #1557b0;
    }
    
    .sidebar-user {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        margin-top: auto;
        border-top: 1px solid #e0e0e0;
    }
    
    .sidebar-user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #1a73e8;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        margin-right: 0.75rem;
    }
    
    .sidebar-user-name {
        font-size: 0.9rem;
        color: #5f6368;
        font-weight: 500;
    }
    
    /* Fixed Dashboard Button Styling */
    .fixed-dashboard-container {
        position: sticky;
        top: 0;
        z-index: 100;
        background: white;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    .fixed-dashboard-btn {
        background: linear-gradient(135deg, #1a73e8, #1557b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
        margin: 0.5rem 0 !important;
    }
    
    .fixed-dashboard-btn:hover {
        background: linear-gradient(135deg, #1557b0, #0d47a1) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # App Title
        st.markdown("""
        <div style="padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 1.5rem;">
            <h1 style="font-size: 1.3rem; font-weight: 700; color: #1a1a1a; margin: 0;">
                NSW Procurement Platform
            </h1>
            <p style="font-size: 0.85rem; color: #5f6368; margin: 0.25rem 0 0 0;">
                AI-Powered Procurement
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Fixed Dashboard Button - Always visible
        st.markdown("""
        <div class="fixed-dashboard-container">
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <div style="font-size: 1.1rem; font-weight: 600; color: #1a1a1a; margin-bottom: 0.25rem;">🏠 Quick Access</div>
                <div style="font-size: 0.85rem; color: #5f6368;">Return to Main Dashboard</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏠 **Go to Dashboard**", key="fixed_dashboard_btn", use_container_width=True, type="primary"):
            # Clear any interface flags to return to main dashboard
            if "show_rag_upload" in st.session_state:
                st.session_state["show_rag_upload"] = False
            if "show_quote_interface" in st.session_state:
                st.session_state["show_quote_interface"] = False
            if "show_content_viewer" in st.session_state:
                st.session_state["show_content_viewer"] = False
            _nav_set("main_dashboard")
            st.rerun()
        
        st.markdown("---")
        
        # Studio section removed
        # Dashboard section removed
        # Quick Actions section removed
        
        # Core Features Section - Dropdown
        with st.expander("🎯 **Core Features**", expanded=False):
            if st.button("🏠 Dashboard", key="sidebar_dashboard", use_container_width=True):
                _nav_set("main_dashboard")
                st.rerun()
            
            if st.button("🤖 AI Tender Generator", key="sidebar_tender", use_container_width=True):
                _nav_set("tender_creation")
                st.rerun()
            
            if st.button("🤖 AI-Enhanced TEPP", key="sidebar_tepp", use_container_width=True):
                _nav_set("tender_creation")
                st.rerun()
            
            if st.button("🔍 Contract Review", key="sidebar_contract", use_container_width=True):
                _nav_set("contract_review")
                st.rerun()
            
            if st.button("📚 RAG & Documents", key="sidebar_rag", use_container_width=True):
                st.session_state["show_rag_upload"] = True
                _nav_set("main_dashboard")
                st.rerun()
            
            if st.button("🛡️ Compliance Dashboard", key="sidebar_compliance", use_container_width=True):
                _nav_set("compliance_dashboard")
                st.rerun()
            
            if st.button("📊 Progress Dashboard", key="sidebar_progress", use_container_width=True):
                _nav_set("progress_dashboard")
                st.rerun()
            
            if st.button("🔍 Historical Matching", key="sidebar_historical", use_container_width=True):
                _nav_set("historical_matching")
                st.rerun()
            
            if st.button("💰 AI Quote Generator", key="sidebar_quote", use_container_width=True):
                st.session_state["show_quote_interface"] = True
                _nav_set("main_dashboard")
                st.rerun()
            
            if st.button("🔍 Unified Evaluation", key="sidebar_unified_evaluation", use_container_width=True):
                _nav_set("unified_evaluation")
                st.rerun()
        
        # Test Examples Section
        with st.expander("🧪 Test Examples", expanded=False):
            if st.button("🚛 Fleet Test Examples", key="sidebar_fleet_examples", use_container_width=True):
                st.session_state["show_test_examples"] = True
                st.session_state["test_example_type"] = "fleet"
                _nav_set("main_dashboard")
                st.rerun()
            
            if st.button("🏗️ Construction Test Examples", key="sidebar_construction_examples", use_container_width=True):
                st.info("🏗️ Construction Test Examples - Coming soon")
            
            if st.button("💼 Services Test Examples", key="sidebar_services_examples", use_container_width=True):
                st.session_state["show_test_examples"] = True
                st.session_state["test_example_type"] = "services"
                _nav_set("main_dashboard")
                st.rerun()
        
        # Advanced Features Section
        with st.expander("🔧 Advanced Features", expanded=False):
            if st.button("📊 Results & Analytics", key="sidebar_results", use_container_width=True):
                st.info("📊 Results & Analytics - Coming soon")
            
            if st.button("📚 Historical Projects", key="sidebar_historical_projects", use_container_width=True):
                st.info("📚 Historical Projects - Coming soon")
            
            if st.button("📈 Evaluation Tools", key="sidebar_evaluation", use_container_width=True):
                st.info("📈 Evaluation Tools - Coming soon")
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            if st.button("🔑 API Configuration", key="sidebar_api_config", use_container_width=True):
                _nav_set("ai_usage_monitor")
                st.rerun()
            
            if st.button("🔧 System Settings", key="sidebar_system_settings", use_container_width=True):
                st.info("🔧 System Settings - Coming soon")
            
            if st.button("👤 User Preferences", key="sidebar_user_prefs", use_container_width=True):
                st.info("👤 User Preferences - Coming soon")
            
            if st.button("🔒 Security Settings", key="sidebar_security", use_container_width=True):
                st.info("🔒 Security Settings - Coming soon")
        
        # User Profile Section
        st.markdown("""
        <div class="sidebar-user">
            <div class="sidebar-user-avatar">M</div>
            <div class="sidebar-user-name">mohsenmou2024...</div>
        </div>
        """, unsafe_allow_html=True)

def get_current_page_icon(page: str) -> str:
    """Get the appropriate icon for the current page"""
    icons = {
        "login": "🏠",
        "home": "🏠", 
        "tender_creation": "📋",
        "quote_creation": "💰",
        "contract_review": "🔍",
        "enhanced_tepp": "🤖",
        "ai_usage_monitor": "📊",
        "rag_monitor": "⚙️",
        "compliance": "🔍",
        "results": "📊",
        "evaluation": "📈",
        "historical_projects": "📚"
    }
    return icons.get(page, "📄")

def highlight_current_page(page: str):
    """Highlight the current page in the sidebar"""
    current_page = st.session_state.get("current_page", "login")
    return current_page == page
