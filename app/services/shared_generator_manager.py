#!/usr/bin/env python3
"""
Shared Generator Manager
Manages shared resources and configuration between AI Tender Generator and AI-Enhanced TEPP Generator
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
from app.services.three_tier_rag_system import ThreeTierRAGSystem
from app.services.ai_model_detector import get_ai_detector, AIModelConfig
from app.services.tepp_generator import TEPPGenerator, TEPPConfiguration

class SharedGeneratorManager:
    """Manages shared resources between generators"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._init_shared_resources()
    
    def _init_shared_resources(self):
        """Initialize shared resources"""
        # Initialize shared RAG system
        if 'shared_rag_system' not in st.session_state:
            st.session_state.shared_rag_system = ThreeTierRAGSystem(self.data_dir)
        
        # Initialize AI detector
        if 'shared_ai_detector' not in st.session_state:
            st.session_state.shared_ai_detector = get_ai_detector()
        
        # Initialize generator status tracking
        if 'active_generator' not in st.session_state:
            st.session_state.active_generator = None
        
        # Initialize data migration tracking
        if 'generator_data_migration' not in st.session_state:
            st.session_state.generator_data_migration = {
                'tender_to_enhanced': None,
                'enhanced_to_tender': None
            }
    
    def get_shared_rag_system(self) -> ThreeTierRAGSystem:
        """Get shared RAG system instance"""
        return st.session_state.shared_rag_system
    
    def get_shared_ai_detector(self):
        """Get shared AI detector instance"""
        return st.session_state.shared_ai_detector
    
    def set_active_generator(self, generator_type: str):
        """Set the currently active generator"""
        st.session_state.active_generator = generator_type
    
    def get_active_generator(self) -> Optional[str]:
        """Get the currently active generator"""
        return st.session_state.active_generator
    
    def migrate_data_between_generators(self, from_generator: str, to_generator: str) -> bool:
        """Migrate data between generators"""
        try:
            if from_generator == "tender" and to_generator == "enhanced":
                # Migrate from AI Tender Generator to AI-Enhanced TEPP Generator
                if st.session_state.get('tender_tepp_data'):
                    st.session_state.enhanced_tepp_data = st.session_state.tender_tepp_data
                    st.session_state.enhanced_tepp_config = st.session_state.tender_tepp_config
                    st.session_state.generator_data_migration['tender_to_enhanced'] = True
                    return True
            
            elif from_generator == "enhanced" and to_generator == "tender":
                # Migrate from AI-Enhanced TEPP Generator to AI Tender Generator
                if st.session_state.get('enhanced_tepp_data'):
                    st.session_state.tender_tepp_data = st.session_state.enhanced_tepp_data
                    st.session_state.tender_tepp_config = st.session_state.enhanced_tepp_config
                    st.session_state.generator_data_migration['enhanced_to_tender'] = True
                    return True
            
            return False
        except Exception as e:
            st.error(f"Error migrating data: {e}")
            return False
    
    def get_generator_status(self) -> Dict[str, Any]:
        """Get status of both generators"""
        return {
            'active_generator': st.session_state.get('active_generator'),
            'tender_has_data': bool(st.session_state.get('tender_tepp_data')),
            'enhanced_has_data': bool(st.session_state.get('enhanced_tepp_data')),
            'tender_package_has_data': bool(st.session_state.get('tender_package_data')),
            'data_migration': st.session_state.get('generator_data_migration', {})
        }
    
    def create_tepp_generator(self) -> TEPPGenerator:
        """Create TEPP generator with shared resources"""
        return TEPPGenerator(self.get_shared_rag_system())
    
    def display_generator_status(self):
        """Display current generator status"""
        status = self.get_generator_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status['active_generator'] == 'tender':
                st.success("🤖 AI Tender Generator - Active")
            elif status['active_generator'] == 'enhanced':
                st.success("🤖 AI-Enhanced TEPP Generator - Active")
            else:
                st.info("No generator active")
        
        with col2:
            if status['tender_has_data']:
                st.info("📋 Tender TEPP Data Available")
            else:
                st.warning("📋 No Tender TEPP Data")
        
        with col3:
            if status['enhanced_has_data']:
                st.info("📋 Enhanced TEPP Data Available")
            else:
                st.warning("📋 No Enhanced TEPP Data")
    
    def display_data_migration_options(self):
        """Display data migration options"""
        status = self.get_generator_status()
        
        if status['tender_has_data'] and not status['enhanced_has_data']:
            st.info("💡 You have TEPP data from AI Tender Generator. You can migrate it to AI-Enhanced TEPP Generator for advanced editing.")
            if st.button("🔄 Migrate to Enhanced TEPP Generator", type="secondary"):
                if self.migrate_data_between_generators("tender", "enhanced"):
                    st.success("✅ Data migrated successfully!")
                    st.rerun()
        
        elif status['enhanced_has_data'] and not status['tender_has_data']:
            st.info("💡 You have TEPP data from AI-Enhanced TEPP Generator. You can migrate it to AI Tender Generator.")
            if st.button("🔄 Migrate to Tender Generator", type="secondary"):
                if self.migrate_data_between_generators("enhanced", "tender"):
                    st.success("✅ Data migrated successfully!")
                    st.rerun()
        
        elif status['tender_has_data'] and status['enhanced_has_data']:
            st.warning("⚠️ You have data in both generators. Please choose which one to keep.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Use Enhanced TEPP Data", type="primary"):
                    if self.migrate_data_between_generators("enhanced", "tender"):
                        st.success("✅ Using Enhanced TEPP data!")
                        st.rerun()
            
            with col2:
                if st.button("🔄 Use Tender TEPP Data", type="secondary"):
                    if self.migrate_data_between_generators("tender", "enhanced"):
                        st.success("✅ Using Tender TEPP data!")
                        st.rerun()
    
    def clear_all_generator_data(self):
        """Clear all generator data"""
        keys_to_clear = [
            'tender_tepp_data', 'tender_tepp_config', 'tender_package_data',
            'enhanced_tepp_data', 'enhanced_tepp_config',
            'active_generator', 'generator_data_migration'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("✅ All generator data cleared!")
        st.rerun()
