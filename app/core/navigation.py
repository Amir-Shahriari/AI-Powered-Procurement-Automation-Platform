"""
Navigation system for the NSW Procurement Platform
"""
import streamlit as st
from typing import Optional, Dict, Any


def _nav_set(view: str, extra: Optional[Dict[str, str]] = None):
    """Set current page using session state instead of query parameters."""
    st.session_state["current_page"] = view
    if extra:
        st.session_state["page_params"] = extra.copy()
    else:
        st.session_state["page_params"] = {}


def _nav_init():
    """Initialize navigation system."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "login"
    if "page_params" not in st.session_state:
        st.session_state["page_params"] = {}


def _nav_snapshot_current():
    """Take a snapshot of current page for back navigation."""
    if "nav_history" not in st.session_state:
        st.session_state["nav_history"] = []
    
    current = {
        "page": st.session_state["current_page"],
        "params": st.session_state["page_params"].copy()
    }
    st.session_state["nav_history"].append(current)


def _nav_push_current():
    """Push current page to history before navigating."""
    _nav_snapshot_current()


def _nav_back():
    """Navigate back to previous page."""
    if "nav_history" in st.session_state and st.session_state["nav_history"]:
        previous = st.session_state["nav_history"].pop()
        st.session_state["current_page"] = previous["page"]
        st.session_state["page_params"] = previous["params"]
        st.rerun()


def _get_current_page():
    """Get current page from session state."""
    return st.session_state.get("current_page", "login")


def _get_page_params():
    """Get current page parameters from session state."""
    return st.session_state.get("page_params", {})
