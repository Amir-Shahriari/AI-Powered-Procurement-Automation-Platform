#!/usr/bin/env python3
"""
AI Content Viewer and Editor
Comprehensive viewing, editing, and interaction capabilities for all AI-generated content
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import base64
from io import BytesIO

class AIContentViewer:
    """Comprehensive viewer and editor for AI-generated content"""
    
    def __init__(self):
        self.content_types = {
            'tepp_document': 'TEPP Document',
            'tender_package': 'Tender Package',
            'quote_package': 'Quote Package',
            'evaluation_results': 'Evaluation Results',
            'compliance_analysis': 'Compliance Analysis',
            'rag_documents': 'RAG Documents',
            'ai_analysis': 'AI Analysis',
            'generated_reports': 'Generated Reports'
        }
    
    def display_content_dashboard(self):
        """Display comprehensive content dashboard"""
        st.title("📚 AI Content Dashboard")
        st.markdown("View, edit, and interact with all AI-generated content")
        
        # Content overview
        self._display_content_overview()
        
        # Content explorer
        self._display_content_explorer()
        
        # Recent activity
        self._display_recent_activity()
    
    def _display_content_overview(self):
        """Display overview of all available content"""
        st.markdown("### 📊 Content Overview")
        
        # Get all available content
        content_summary = self._get_content_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", content_summary['total_documents'])
        
        with col2:
            st.metric("TEPP Documents", content_summary['tepp_documents'])
        
        with col3:
            st.metric("Tender Packages", content_summary['tender_packages'])
        
        with col4:
            st.metric("AI Analyses", content_summary['ai_analyses'])
    
    def _get_content_summary(self) -> Dict[str, int]:
        """Get summary of all available content"""
        summary = {
            'total_documents': 0,
            'tepp_documents': 0,
            'tender_packages': 0,
            'ai_analyses': 0,
            'evaluation_results': 0,
            'compliance_analyses': 0
        }
        
        # Count session state content
        if st.session_state.get('enhanced_tepp_data'):
            summary['tepp_documents'] += 1
            summary['total_documents'] += 1
        
        if st.session_state.get('tender_tepp_data'):
            summary['tepp_documents'] += 1
            summary['total_documents'] += 1
        
        if st.session_state.get('tender_package_data'):
            summary['tender_packages'] += 1
            summary['total_documents'] += 1
        
        if st.session_state.get('generated_quote'):
            summary['tender_packages'] += 1
            summary['total_documents'] += 1
        
        # Count evaluation results
        if st.session_state.get('current_unified_evaluation_id'):
            summary['evaluation_results'] += 1
            summary['total_documents'] += 1
        
        return summary
    
    def _display_content_explorer(self):
        """Display content explorer with filtering and search"""
        st.markdown("### 🔍 Content Explorer")
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search content", placeholder="Search by title, type, or content...")
        
        with col2:
            content_type_filter = st.selectbox("Filter by type", ["All"] + list(self.content_types.values()))
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Date Created", "Type", "Title", "Size"])
        
        # Display content cards
        self._display_content_cards(search_term, content_type_filter, sort_by)
    
    def _display_content_cards(self, search_term: str, content_type_filter: str, sort_by: str):
        """Display content as interactive cards"""
        
        # Get all content
        all_content = self._get_all_content()
        
        # Filter content
        filtered_content = self._filter_content(all_content, search_term, content_type_filter)
        
        # Sort content
        sorted_content = self._sort_content(filtered_content, sort_by)
        
        # Display cards
        if not sorted_content:
            st.info("No content found. Generate some content first!")
            return
        
        for i, content in enumerate(sorted_content):
            with st.expander(f"📄 {content['title']} - {content['type']}", expanded=False):
                self._display_content_card(content)
    
    def _get_all_content(self) -> List[Dict[str, Any]]:
        """Get all available content from session state"""
        content = []
        
        # Enhanced TEPP data
        if st.session_state.get('enhanced_tepp_data'):
            content.append({
                'id': 'enhanced_tepp',
                'title': 'AI-Enhanced TEPP Document',
                'type': 'TEPP Document',
                'data': st.session_state['enhanced_tepp_data'],
                'config': st.session_state.get('enhanced_tepp_config'),
                'created_date': datetime.now().isoformat(),
                'size': len(str(st.session_state['enhanced_tepp_data'])),
                'source': 'AI-Enhanced TEPP Generator'
            })
        
        # Tender TEPP data
        if st.session_state.get('tender_tepp_data'):
            content.append({
                'id': 'tender_tepp',
                'title': 'AI Tender TEPP Document',
                'type': 'TEPP Document',
                'data': st.session_state['tender_tepp_data'],
                'config': st.session_state.get('tender_tepp_config'),
                'created_date': datetime.now().isoformat(),
                'size': len(str(st.session_state['tender_tepp_data'])),
                'source': 'AI Tender Generator'
            })
        
        # Tender package data
        if st.session_state.get('tender_package_data'):
            content.append({
                'id': 'tender_package',
                'title': 'AI Tender Package',
                'type': 'Tender Package',
                'data': st.session_state['tender_package_data'],
                'created_date': datetime.now().isoformat(),
                'size': len(str(st.session_state['tender_package_data'])),
                'source': 'AI Tender Generator'
            })
        
        # Quote data
        if st.session_state.get('generated_quote'):
            content.append({
                'id': 'generated_quote',
                'title': 'AI Generated Quote',
                'type': 'Quote Package',
                'data': st.session_state['generated_quote'],
                'created_date': datetime.now().isoformat(),
                'size': len(str(st.session_state['generated_quote'])),
                'source': 'AI Quote Generator'
            })
        
        return content
    
    def _filter_content(self, content: List[Dict[str, Any]], search_term: str, content_type_filter: str) -> List[Dict[str, Any]]:
        """Filter content based on search term and type"""
        filtered = content
        
        if search_term:
            filtered = [c for c in filtered if search_term.lower() in c['title'].lower() or 
                      search_term.lower() in str(c['data']).lower()]
        
        if content_type_filter != "All":
            filtered = [c for c in filtered if c['type'] == content_type_filter]
        
        return filtered
    
    def _sort_content(self, content: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort content based on criteria"""
        if sort_by == "Date Created":
            return sorted(content, key=lambda x: x['created_date'], reverse=True)
        elif sort_by == "Type":
            return sorted(content, key=lambda x: x['type'])
        elif sort_by == "Title":
            return sorted(content, key=lambda x: x['title'])
        elif sort_by == "Size":
            return sorted(content, key=lambda x: x['size'], reverse=True)
        else:
            return content
    
    def _display_content_card(self, content: Dict[str, Any]):
        """Display individual content card with viewing and editing options"""
        
        # Content metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Type:** {content['type']}")
            st.write(f"**Source:** {content['source']}")
        
        with col2:
            st.write(f"**Size:** {content['size']:,} characters")
            st.write(f"**Created:** {content['created_date'][:10]}")
        
        with col3:
            st.write(f"**ID:** {content['id']}")
        
        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("👁️ View", key=f"view_{content['id']}"):
                st.session_state[f"viewing_content_{content['id']}"] = True
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_{content['id']}"):
                st.session_state[f"editing_content_{content['id']}"] = True
        
        with col3:
            if st.button("📋 Copy", key=f"copy_{content['id']}"):
                st.session_state[f"copying_content_{content['id']}"] = True
        
        with col4:
            if st.button("💾 Export", key=f"export_{content['id']}"):
                st.session_state[f"exporting_content_{content['id']}"] = True
        
        with col5:
            if st.button("🗑️ Delete", key=f"delete_{content['id']}"):
                st.session_state[f"deleting_content_{content['id']}"] = True
        
        # Handle actions
        self._handle_content_actions(content)
    
    def _handle_content_actions(self, content: Dict[str, Any]):
        """Handle content actions (view, edit, copy, export, delete)"""
        content_id = content['id']
        
        # View content
        if st.session_state.get(f"viewing_content_{content_id}"):
            self._view_content(content)
        
        # Edit content
        if st.session_state.get(f"editing_content_{content_id}"):
            self._edit_content(content)
        
        # Copy content
        if st.session_state.get(f"copying_content_{content_id}"):
            self._copy_content(content)
        
        # Export content
        if st.session_state.get(f"exporting_content_{content_id}"):
            self._export_content(content)
        
        # Delete content
        if st.session_state.get(f"deleting_content_{content_id}"):
            self._delete_content(content)
    
    def _view_content(self, content: Dict[str, Any]):
        """View content in detail"""
        st.markdown("---")
        st.markdown(f"### 👁️ Viewing: {content['title']}")
        
        # Content type specific viewing
        if content['type'] == 'TEPP Document':
            self._view_tepp_document(content)
        elif content['type'] == 'Tender Package':
            self._view_tender_package(content)
        elif content['type'] == 'Quote Package':
            self._view_quote_package(content)
        else:
            self._view_generic_content(content)
        
        # Close button
        if st.button("❌ Close", key=f"close_view_{content['id']}"):
            st.session_state[f"viewing_content_{content['id']}"] = False
            st.rerun()
    
    def _view_tepp_document(self, content: Dict[str, Any]):
        """View TEPP document in detail"""
        tepp_data = content['data']
        
        # TEPP sections
        if isinstance(tepp_data, dict):
            for section_name, section_content in tepp_data.items():
                if isinstance(section_content, dict):
                    with st.expander(f"📋 {section_name.replace('_', ' ').title()}", expanded=False):
                        for key, value in section_content.items():
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    with st.expander(f"📋 {section_name.replace('_', ' ').title()}", expanded=False):
                        st.write(section_content)
        else:
            st.write(tepp_data)
    
    def _view_tender_package(self, content: Dict[str, Any]):
        """View tender package in detail"""
        package_data = content['data']
        
        if isinstance(package_data, dict):
            for key, value in package_data.items():
                with st.expander(f"📄 {key.replace('_', ' ').title()}", expanded=False):
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            st.write(f"**{sub_key.replace('_', ' ').title()}:** {sub_value}")
                    else:
                        st.write(value)
        else:
            st.write(package_data)
    
    def _view_quote_package(self, content: Dict[str, Any]):
        """View quote package in detail"""
        quote_data = content['data']
        
        if isinstance(quote_data, dict):
            for key, value in quote_data.items():
                with st.expander(f"💰 {key.replace('_', ' ').title()}", expanded=False):
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            st.write(f"**{sub_key.replace('_', ' ').title()}:** {sub_value}")
                    else:
                        st.write(value)
        else:
            st.write(quote_data)
    
    def _view_generic_content(self, content: Dict[str, Any]):
        """View generic content"""
        st.json(content['data'])
    
    def _edit_content(self, content: Dict[str, Any]):
        """Edit content interactively"""
        st.markdown("---")
        st.markdown(f"### ✏️ Editing: {content['title']}")
        
        # Content type specific editing
        if content['type'] == 'TEPP Document':
            self._edit_tepp_document(content)
        elif content['type'] == 'Tender Package':
            self._edit_tender_package(content)
        elif content['type'] == 'Quote Package':
            self._edit_quote_package(content)
        else:
            self._edit_generic_content(content)
        
        # Save and cancel buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", key=f"save_{content['id']}"):
                self._save_content_changes(content)
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_{content['id']}"):
                st.session_state[f"editing_content_{content['id']}"] = False
                st.rerun()
    
    def _edit_tepp_document(self, content: Dict[str, Any]):
        """Edit TEPP document interactively"""
        tepp_data = content['data']
        
        if isinstance(tepp_data, dict):
            for section_name, section_content in tepp_data.items():
                with st.expander(f"✏️ {section_name.replace('_', ' ').title()}", expanded=True):
                    if isinstance(section_content, dict):
                        for key, value in section_content.items():
                            new_value = st.text_area(
                                f"{key.replace('_', ' ').title()}:",
                                value=str(value),
                                key=f"edit_{content['id']}_{section_name}_{key}",
                                height=100
                            )
                            # Update the content
                            if new_value != value:
                                tepp_data[section_name][key] = new_value
                    else:
                        new_content = st.text_area(
                            f"{section_name.replace('_', ' ').title()}:",
                            value=str(section_content),
                            key=f"edit_{content['id']}_{section_name}",
                            height=200
                        )
                        # Update the content
                        if new_content != section_content:
                            tepp_data[section_name] = new_content
        else:
            new_content = st.text_area(
                "Content:",
                value=str(tepp_data),
                key=f"edit_{content['id']}_content",
                height=300
            )
            # Update the content
            if new_content != tepp_data:
                content['data'] = new_content
    
    def _edit_tender_package(self, content: Dict[str, Any]):
        """Edit tender package interactively"""
        package_data = content['data']
        
        if isinstance(package_data, dict):
            for key, value in package_data.items():
                with st.expander(f"✏️ {key.replace('_', ' ').title()}", expanded=True):
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            new_value = st.text_area(
                                f"{sub_key.replace('_', ' ').title()}:",
                                value=str(sub_value),
                                key=f"edit_{content['id']}_{key}_{sub_key}",
                                height=100
                            )
                            # Update the content
                            if new_value != sub_value:
                                package_data[key][sub_key] = new_value
                    else:
                        new_value = st.text_area(
                            f"{key.replace('_', ' ').title()}:",
                            value=str(value),
                            key=f"edit_{content['id']}_{key}",
                            height=150
                        )
                        # Update the content
                        if new_value != value:
                            package_data[key] = new_value
        else:
            new_content = st.text_area(
                "Content:",
                value=str(package_data),
                key=f"edit_{content['id']}_content",
                height=300
            )
            # Update the content
            if new_content != package_data:
                content['data'] = new_content
    
    def _edit_quote_package(self, content: Dict[str, Any]):
        """Edit quote package interactively"""
        quote_data = content['data']
        
        if isinstance(quote_data, dict):
            for key, value in quote_data.items():
                with st.expander(f"✏️ {key.replace('_', ' ').title()}", expanded=True):
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            new_value = st.text_area(
                                f"{sub_key.replace('_', ' ').title()}:",
                                value=str(sub_value),
                                key=f"edit_{content['id']}_{key}_{sub_key}",
                                height=100
                            )
                            # Update the content
                            if new_value != sub_value:
                                quote_data[key][sub_key] = new_value
                    else:
                        new_value = st.text_area(
                            f"{key.replace('_', ' ').title()}:",
                            value=str(value),
                            key=f"edit_{content['id']}_{key}",
                            height=150
                        )
                        # Update the content
                        if new_value != value:
                            quote_data[key] = new_value
        else:
            new_content = st.text_area(
                "Content:",
                value=str(quote_data),
                key=f"edit_{content['id']}_content",
                height=300
            )
            # Update the content
            if new_content != quote_data:
                content['data'] = new_content
    
    def _edit_generic_content(self, content: Dict[str, Any]):
        """Edit generic content"""
        new_content = st.text_area(
            "Content:",
            value=str(content['data']),
            key=f"edit_{content['id']}_content",
            height=300
        )
        # Update the content
        if new_content != content['data']:
            content['data'] = new_content
    
    def _save_content_changes(self, content: Dict[str, Any]):
        """Save content changes to session state"""
        content_id = content['id']
        
        # Update session state based on content type
        if content_id == 'enhanced_tepp':
            st.session_state['enhanced_tepp_data'] = content['data']
        elif content_id == 'tender_tepp':
            st.session_state['tender_tepp_data'] = content['data']
        elif content_id == 'tender_package':
            st.session_state['tender_package_data'] = content['data']
        elif content_id == 'generated_quote':
            st.session_state['generated_quote'] = content['data']
        
        st.success("✅ Changes saved successfully!")
        st.session_state[f"editing_content_{content_id}"] = False
        st.rerun()
    
    def _copy_content(self, content: Dict[str, Any]):
        """Copy content to clipboard or create duplicate"""
        st.markdown("---")
        st.markdown(f"### 📋 Copying: {content['title']}")
        
        # Copy options
        copy_option = st.radio("Copy as:", ["JSON", "Text", "Markdown", "Duplicate"])
        
        if copy_option == "JSON":
            json_str = json.dumps(content['data'], indent=2)
            st.code(json_str, language='json')
            st.button("📋 Copy to Clipboard", key=f"copy_json_{content['id']}")
        
        elif copy_option == "Text":
            text_str = str(content['data'])
            st.text_area("Text content:", value=text_str, height=200)
            st.button("📋 Copy to Clipboard", key=f"copy_text_{content['id']}")
        
        elif copy_option == "Markdown":
            markdown_str = self._convert_to_markdown(content['data'])
            st.markdown(markdown_str)
            st.button("📋 Copy to Clipboard", key=f"copy_markdown_{content['id']}")
        
        elif copy_option == "Duplicate":
            new_id = f"{content['id']}_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.info(f"Duplicate will be created with ID: {new_id}")
            if st.button("🔄 Create Duplicate", key=f"duplicate_{content['id']}"):
                # Create duplicate in session state
                duplicate_content = content.copy()
                duplicate_content['id'] = new_id
                duplicate_content['title'] = f"{content['title']} (Copy)"
                st.session_state[f"content_{new_id}"] = duplicate_content
                st.success("✅ Duplicate created successfully!")
                st.rerun()
        
        # Close button
        if st.button("❌ Close", key=f"close_copy_{content['id']}"):
            st.session_state[f"copying_content_{content['id']}"] = False
            st.rerun()
    
    def _convert_to_markdown(self, data: Any) -> str:
        """Convert content to markdown format"""
        if isinstance(data, dict):
            markdown = "# Content\n\n"
            for key, value in data.items():
                markdown += f"## {key.replace('_', ' ').title()}\n\n"
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        markdown += f"### {sub_key.replace('_', ' ').title()}\n\n{sub_value}\n\n"
                else:
                    markdown += f"{value}\n\n"
            return markdown
        else:
            return f"# Content\n\n{str(data)}"
    
    def _export_content(self, content: Dict[str, Any]):
        """Export content to various formats"""
        st.markdown("---")
        st.markdown(f"### 💾 Exporting: {content['title']}")
        
        # Export options
        export_format = st.selectbox("Export format:", ["JSON", "TXT", "CSV", "PDF", "Word"])
        
        if export_format == "JSON":
            json_str = json.dumps(content['data'], indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"{content['id']}.json",
                mime="application/json"
            )
        
        elif export_format == "TXT":
            text_str = str(content['data'])
            st.download_button(
                label="📥 Download TXT",
                data=text_str,
                file_name=f"{content['id']}.txt",
                mime="text/plain"
            )
        
        elif export_format == "CSV":
            if isinstance(content['data'], dict):
                df = pd.DataFrame([content['data']])
                csv_str = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_str,
                    file_name=f"{content['id']}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("CSV export not available for this content type")
        
        # Close button
        if st.button("❌ Close", key=f"close_export_{content['id']}"):
            st.session_state[f"exporting_content_{content['id']}"] = False
            st.rerun()
    
    def _delete_content(self, content: Dict[str, Any]):
        """Delete content with confirmation"""
        st.markdown("---")
        st.markdown(f"### 🗑️ Delete: {content['title']}")
        
        st.warning("⚠️ Are you sure you want to delete this content? This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Yes, Delete", key=f"confirm_delete_{content['id']}", type="primary"):
                self._confirm_delete_content(content)
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_delete_{content['id']}"):
                st.session_state[f"deleting_content_{content['id']}"] = False
                st.rerun()
    
    def _confirm_delete_content(self, content: Dict[str, Any]):
        """Confirm and execute content deletion"""
        content_id = content['id']
        
        # Remove from session state
        if content_id == 'enhanced_tepp':
            st.session_state['enhanced_tepp_data'] = None
            st.session_state['enhanced_tepp_config'] = None
        elif content_id == 'tender_tepp':
            st.session_state['tender_tepp_data'] = None
            st.session_state['tender_tepp_config'] = None
        elif content_id == 'tender_package':
            st.session_state['tender_package_data'] = None
        elif content_id == 'generated_quote':
            st.session_state['generated_quote'] = None
        
        st.success("✅ Content deleted successfully!")
        st.session_state[f"deleting_content_{content_id}"] = False
        st.rerun()
    
    def _display_recent_activity(self):
        """Display recent activity and changes"""
        st.markdown("### 📈 Recent Activity")
        
        # Get recent activity from session state
        activity_log = st.session_state.get('content_activity_log', [])
        
        if not activity_log:
            st.info("No recent activity")
            return
        
        # Display activity items
        for activity in activity_log[-10:]:  # Show last 10 activities
            with st.expander(f"{activity['action']} - {activity['content_title']} ({activity['timestamp']})"):
                st.write(f"**Action:** {activity['action']}")
                st.write(f"**Content:** {activity['content_title']}")
                st.write(f"**Timestamp:** {activity['timestamp']}")
                if activity.get('details'):
                    st.write(f"**Details:** {activity['details']}")
    
    def log_activity(self, action: str, content_title: str, details: str = None):
        """Log activity for tracking"""
        if 'content_activity_log' not in st.session_state:
            st.session_state['content_activity_log'] = []
        
        activity = {
            'action': action,
            'content_title': content_title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': details
        }
        
        st.session_state['content_activity_log'].append(activity)
        
        # Keep only last 50 activities
        if len(st.session_state['content_activity_log']) > 50:
            st.session_state['content_activity_log'] = st.session_state['content_activity_log'][-50:]
