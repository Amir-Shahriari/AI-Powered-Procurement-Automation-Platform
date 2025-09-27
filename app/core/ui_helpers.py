"""
UI helper functions and utilities
"""
import os
import streamlit as st
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


def _inject_css():
    """Inject custom CSS for the application."""
    default_path = Path(__file__).parent.parent / "ui" / "theme.css"
    css_path_str = os.getenv("APP_THEME_CSS", str(default_path))
    css_path = Path(css_path_str)
    
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # ULTRA-AGGRESSIVE SOLUTION TO COMPLETELY DISABLE STREAMLIT NAVIGATION
    st.markdown("""
    <style>
    /* NUCLEAR OPTION: HIDE EVERYTHING IN SIDEBAR EXCEPT OUR CUSTOM ELEMENTS */
    
    /* Hide ALL elements in sidebar by default */
    .stSidebar > * {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Only show our custom sidebar elements */
    .stSidebar .fixed-dashboard-container,
    .stSidebar .sidebar-section,
    .stSidebar .sidebar-item,
    .stSidebar .sidebar-user,
    .stSidebar .fixed-dashboard-btn,
    .stSidebar .stExpander,
    .stSidebar .stButton {
        display: block !important;
        visibility: visible !important;
        height: auto !important;
        width: auto !important;
        overflow: visible !important;
        padding: initial !important;
        margin: initial !important;
        border: initial !important;
    }
    
    /* Hide any Streamlit automatic navigation completely */
    .stSidebar [data-testid="stSidebarNav"],
    .stSidebar .stSelectbox,
    .stSidebar .stRadio,
    .stSidebar div[role="navigation"],
    .stSidebar nav,
    .stSidebar .navigation,
    .stSidebar .page-navigation,
    .stSidebar li,
    .stSidebar ul,
    .stSidebar ol,
    .stSidebar a,
    .stSidebar button:not(.fixed-dashboard-btn):not([data-testid="baseButton-secondary"]):not([data-testid="baseButton-primary"]) {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Hide any element containing specific page names */
    .stSidebar *:contains("main"),
    .stSidebar *:contains("compliance dashboard"),
    .stSidebar *:contains("historical matching dashboard"),
    .stSidebar *:contains("main dashboard"),
    .stSidebar *:contains("progress dashboard"),
    .stSidebar *:contains("signin page"),
    .stSidebar *:contains("unified evaluation dashboard"),
    .stSidebar *:contains("ai generation pages"),
    .stSidebar *:contains("auth pages"),
    .stSidebar *:contains("blacktown rag dashboard"),
    .stSidebar *:contains("contract review page"),
    .stSidebar *:contains("smart procurement flow"),
    .stSidebar *:contains("rag dashboard"),
    .stSidebar *:contains("collaborative evaluation dashboard"),
    .stSidebar *:contains("comprehensive evaluation dashbo") {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Hide any element with page-related attributes */
    .stSidebar *[aria-label*="page"],
    .stSidebar *[aria-label*="Page"],
    .stSidebar *[aria-label*="select"],
    .stSidebar *[aria-label*="Select"],
    .stSidebar *[title*="page"],
    .stSidebar *[title*="Page"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Hide all Streamlit CSS classes that might be page navigation */
    .stSidebar .css-1d391kg,
    .stSidebar .css-1cypcdb,
    .stSidebar .css-1v0mbdj,
    .stSidebar .css-1oe5cao,
    .stSidebar .css-1y4p8pa,
    .stSidebar .css-1d391kg > div,
    .stSidebar .css-1cypcdb > div,
    .stSidebar .css-1v0mbdj > div,
    .stSidebar .css-1oe5cao > div,
    .stSidebar .css-1y4p8pa > div {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Hide any element that might be a page selector */
    .stSidebar div[role="combobox"],
    .stSidebar div[role="listbox"],
    .stSidebar div[aria-expanded],
    .stSidebar div[aria-haspopup] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* Hide the entire first container in sidebar (page navigation) */
    .stSidebar .element-container:first-child {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    </style>
    
    <script>
    // ULTRA-AGGRESSIVE JAVASCRIPT TO HIDE ALL PAGE NAVIGATION
    function hideAllPageNavigation() {
        const sidebar = document.querySelector('.stSidebar');
        if (sidebar) {
            // Hide ALL elements in sidebar by default
            const allElements = sidebar.querySelectorAll('*');
            allElements.forEach(el => {
                // Skip our custom elements
                if (el.classList.contains('fixed-dashboard-container') ||
                    el.classList.contains('sidebar-section') ||
                    el.classList.contains('sidebar-item') ||
                    el.classList.contains('sidebar-user') ||
                    el.classList.contains('fixed-dashboard-btn') ||
                    el.classList.contains('stExpander') ||
                    el.tagName === 'BUTTON' ||
                    el.closest('.stExpander') ||
                    el.closest('.fixed-dashboard-container')) {
                    return; // Keep our custom elements visible
                }
                
                // Hide everything else
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.height = '0';
                el.style.width = '0';
                el.style.overflow = 'hidden';
                el.style.padding = '0';
                el.style.margin = '0';
                el.style.border = 'none';
            });
            
            // Specifically hide any element containing page names
            const pageNames = ['main', 'compliance dashboard', 'historical matching dashboard', 
                             'main dashboard', 'progress dashboard', 'signin page', 
                             'unified evaluation dashboard', 'ai generation pages', 'auth pages', 
                             'blacktown rag dashboard', 'contract review page', 'smart procurement flow', 
                             'rag dashboard', 'collaborative evaluation dashboard', 'comprehensive evaluation dashbo'];
            
            pageNames.forEach(pageName => {
                const elements = sidebar.querySelectorAll('*');
                elements.forEach(el => {
                    if (el.textContent && el.textContent.includes(pageName)) {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.height = '0';
                        el.style.width = '0';
                        el.style.overflow = 'hidden';
                        el.style.padding = '0';
                        el.style.margin = '0';
                        el.style.border = 'none';
                    }
                });
            });
            
            // Hide any element with page-related attributes
            const pageElements = sidebar.querySelectorAll('[aria-label*="page"], [aria-label*="Page"], [aria-label*="select"], [aria-label*="Select"], [title*="page"], [title*="Page"]');
            pageElements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.height = '0';
                el.style.width = '0';
                el.style.overflow = 'hidden';
                el.style.padding = '0';
                el.style.margin = '0';
                el.style.border = 'none';
            });
            
            // Hide all navigation elements
            const navElements = sidebar.querySelectorAll('[role="navigation"], nav, .navigation, .page-navigation, [data-testid="stSidebarNav"]');
            navElements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.height = '0';
                el.style.width = '0';
                el.style.overflow = 'hidden';
                el.style.padding = '0';
                el.style.margin = '0';
                el.style.border = 'none';
            });
            
            // Hide all selectbox and radio elements
            const formElements = sidebar.querySelectorAll('.stSelectbox, .stRadio, div[role="combobox"], div[role="listbox"]');
            formElements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.height = '0';
                el.style.width = '0';
                el.style.overflow = 'hidden';
                el.style.padding = '0';
                el.style.margin = '0';
                el.style.border = 'none';
            });
        }
    }
    
    // Run immediately and on DOM changes
    hideAllPageNavigation();
    setTimeout(hideAllPageNavigation, 100);
    setTimeout(hideAllPageNavigation, 500);
    setTimeout(hideAllPageNavigation, 1000);
    setTimeout(hideAllPageNavigation, 2000);
    setTimeout(hideAllPageNavigation, 5000);
    
    // Also run when the page loads
    document.addEventListener('DOMContentLoaded', hideAllPageNavigation);
    window.addEventListener('load', hideAllPageNavigation);
    
    // Run on any DOM changes with more aggressive monitoring
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' || mutation.type === 'attributes') {
                hideAllPageNavigation();
            }
        });
    });
    observer.observe(document.body, { 
        childList: true, 
        subtree: true, 
        attributes: true,
        attributeFilter: ['style', 'class', 'data-testid']
    });
    
    // Additional aggressive hiding every 100ms for the first 10 seconds
    let aggressiveHiding = 0;
    const aggressiveInterval = setInterval(() => {
        hideAllPageNavigation();
        aggressiveHiding++;
        if (aggressiveHiding > 100) { // Stop after 10 seconds
            clearInterval(aggressiveInterval);
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)


def _fmt_ts(mtime: float) -> str:
    """Format timestamp for display."""
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")


def _resolve_logo_paths():
    """Resolve logo file paths from environment variables or defaults."""
    here = Path(__file__)
    l1_env = os.getenv("APP_LOGO1")
    l2_env = os.getenv("APP_LOGO2")
    
    default_dir = here.parent.parent / "ui" / "assets"
    
    logo1 = Path(l1_env) if l1_env else (default_dir / "lgp-logo-retina.png")
    logo2 = Path(l2_env) if l2_env else (default_dir / "BlacktownCityCouncil_2019.png")
    
    return logo1, logo2


def _render_logos(height: int = 42):
    """Render logos in the top bar."""
    logo1, logo2 = _resolve_logo_paths()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if logo1.exists():
            st.image(str(logo1), height=height)
    
    with col2:
        st.markdown("### NSW Procurement Platform")
    
    with col3:
        if logo2.exists():
            st.image(str(logo2), height=height)


def _topbar():
    """Render the top navigation bar."""
    _render_logos()
    st.divider()


def _footer():
    """Render the footer."""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>© 2024 NSW Government | AI-Powered Procurement Platform</p>
    </div>
    """, unsafe_allow_html=True)


def _sticky_expander(label: str, key: str, default_expanded: bool = False):
    """Create a sticky expander that remembers its state."""
    if key not in st.session_state:
        st.session_state[key] = default_expanded
    
    expanded = st.expander(label, expanded=st.session_state[key])
    
    if expanded:
        st.session_state[key] = True
    else:
        st.session_state[key] = False
    
    return expanded


def _slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a URL-friendly slug."""
    import re
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:max_len].strip('-')


def _get_project_dir(project_name: str, rec_id: str) -> Path:
    """Get the project directory path."""
    from app.core.config import DATA_DIR
    project_dir = DATA_DIR / "projects" / rec_id
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def _save_uploaded_file_to_project(uploaded_file, project_dir: Path) -> Path:
    """Save uploaded file to project directory."""
    uploads_dir = project_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    file_path = uploads_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path


def _save_text_spec_to_project(text: str, project_dir: Path) -> Path:
    """Save text specification to project directory."""
    uploads_dir = project_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    file_path = uploads_dir / "specification.txt"
    file_path.write_text(text)
    return file_path


def _save_json_to_project(data: dict, project_dir: Path, filename: str) -> Path:
    """Save JSON data to project directory."""
    import json
    file_path = project_dir / filename
    file_path.write_text(json.dumps(data, indent=2, default=str))
    return file_path


def _clean_company_from_filename(filename: str) -> str:
    """Clean company name from filename for display."""
    import re
    # Remove common company suffixes and clean up
    cleaned = re.sub(r'_(ltd|pty|inc|corp|llc|co)\.?', '', filename, flags=re.IGNORECASE)
    cleaned = re.sub(r'[_-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()
