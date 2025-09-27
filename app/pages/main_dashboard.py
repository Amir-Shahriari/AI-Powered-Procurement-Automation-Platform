"""
Main dashboard page with procurement type selection only
"""
import streamlit as st
from app.core.navigation import _nav_set
from app.core.ui_helpers import _inject_css
from app.components.sidebar_navigation import render_sidebar
from app.services.quote_generator import AIQuoteGenerator, QuoteType, QuoteCategory, QuoteStatus
from app.services.three_tier_rag_system import ThreeTierRAGSystem, RAGTier, DocumentCategory, RAGDocument
from app.services.document_processor import OptimizedDocumentProcessor, ProcessedDocument
from app.components.ai_content_viewer import AIContentViewer
from app.config import settings
import hashlib
from datetime import datetime

def page_main_dashboard():
    """Main dashboard with procurement type selection and sidebar"""
    _inject_css()
    
    # Render sidebar
    render_sidebar()
    
    # Show quote interface if requested - clean interface without logos
    if st.session_state.get("show_quote_interface", False):
        show_quote_interface()
    elif st.session_state.get("show_rag_upload", False):
        show_rag_upload_interface()
    elif st.session_state.get("show_test_examples", False):
        show_test_examples_interface()
    else:
        # Header with logo
        st.markdown('''
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #1e3a8a; font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700;">
                🏛️ NSW Procurement Platform
            </h1>
            <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
                AI-Powered Compliant Procurement for NSW Local Government
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Display both logos side by side
        col_logo1, col_logo2 = st.columns(2)
        
        with col_logo1:
            try:
                st.image("app/ui/assets/lgp-logo-retina.png", width=120, caption="Local Government Procurement")
            except:
                # Fallback if logo not found
                st.markdown("### 🏛️ Local Government Procurement")
        
        with col_logo2:
            try:
                st.image("app/ui/assets/AI Government Procurement.png", width=120, caption="EmbryA AI Government Procurement")
            except:
                # Fallback if logo not found
                st.markdown("### 🤖 EmbryA AI Government Procurement")
        
        # Main content area
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Procurement type selection
            st.markdown("### Choose Procurement Type:")
            st.markdown("Select the type of procurement process you want to start.")
            
            # Create two main buttons for procurement types
            col_tender, col_quote = st.columns(2)
            
            with col_tender:
                if st.button("📋 **TENDER**\n\nFormal tender process\n$250k+ contracts\nFull evaluation", 
                           type="primary", use_container_width=True, key="btn_tender"):
                    st.session_state["procurement_type"] = "tender"
                    _nav_set("tender_creation")
                    st.rerun()
            
            with col_quote:
                if st.button("💰 **QUOTE**\n\nSimplified quotation\nUnder $250k\nQuick evaluation", 
                           type="secondary", use_container_width=True, key="btn_quote"):
                    st.session_state["procurement_type"] = "quote"
                    st.session_state["show_quote_interface"] = True
                    st.rerun()
            
            # User info display
            if "user_name" in st.session_state:
                st.markdown("---")
                st.info(f"👤 Welcome, **{st.session_state['user_name']}**")
                
                # Logout button
                if st.button("🚪 Sign Out", type="secondary"):
                    st.session_state.clear()
                    st.rerun()
            
            # Quick stats or recent activity
            st.markdown("---")
            st.markdown("### 📈 Quick Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Active Tenders", "12", "3")
            
            with col2:
                st.metric("Active Quotes", "8", "2")
            
            with col3:
                st.metric("Completed Projects", "45", "12")
            
            with col4:
                st.metric("Compliance Rate", "98.5%", "0.2%")
            


def show_quote_interface():
    """Show the comprehensive Quote interface similar to Tender interface"""
    
    # Clean interface - no logos, welcome messages, or sign out buttons
    st.markdown("### 💰 AI-Powered Quote Creation")
    st.markdown("Generate professional quotes quickly and accurately using AI-powered analysis")
    
    # Initialize quote generator service
    try:
        quote_generator = AIQuoteGenerator()
    except Exception as e:
        st.error(f"❌ Error initializing quote generator: {e}")
        return
    
    # Get quote statistics
    stats = quote_generator.get_quote_statistics()
    
    # Display quote statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quotes", stats['total_quotes'])
    
    with col2:
        st.metric("Total Value", f"${stats['total_value']:,.0f}")
    
    with col3:
        st.metric("Average Value", f"${stats['average_value']:,.0f}")
    
    with col4:
        st.metric("Draft Quotes", stats['status_breakdown'].get('draft', 0))
    
    # Create tabs for different quote functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 Generate Quote", 
        "📚 Quote Library", 
        "📊 Quote Analytics", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_quote_generation_interface(quote_generator)
    
    with tab2:
        show_quote_library_interface(quote_generator)
    
    with tab3:
        show_quote_analytics_interface(quote_generator)
    
    with tab4:
        show_quote_settings_interface()
    
    # Back button
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state["show_quote_interface"] = False
        st.rerun()


def show_quote_generation_interface(quote_generator):
    """Show the quote generation interface"""
    
    st.markdown("#### 🤖 Generate New Quote")
    st.markdown("Create professional quotes using AI-powered analysis")
    
    # Quote generation form
    with st.form("quote_generation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            quote_title = st.text_input("Quote Title", placeholder="Enter quote title")
            quote_description = st.text_area("Project Description", placeholder="Describe the project scope and requirements", height=100)
            quote_type = st.selectbox("Quote Type", options=[qt.value for qt in QuoteType], format_func=lambda x: x.replace('_', ' ').title())
        
        with col2:
            quote_category = st.selectbox("Quote Category", options=[qc.value for qc in QuoteCategory], format_func=lambda x: x.replace('_', ' ').title())
            client_name = st.text_input("Client Name", placeholder="Enter client name")
            client_email = st.text_input("Client Email", placeholder="client@example.com")
        
        # Advanced options
        with st.expander("🔧 Advanced Options", expanded=False):
            col3, col4 = st.columns(2)
            
            with col3:
                budget_min = st.number_input("Minimum Budget ($)", min_value=0.0, value=0.0)
                budget_max = st.number_input("Maximum Budget ($)", min_value=0.0, value=0.0)
            
            with col4:
                timeline_days = st.number_input("Timeline (days)", min_value=1, value=30)
                requirements = st.text_area("Special Requirements", placeholder="Enter any special requirements", height=80)
        
        submitted = st.form_submit_button("🤖 Generate AI Quote", type="primary", use_container_width=True)
    
    # Process quote generation
    if submitted and quote_title and quote_description and client_name and client_email:
        with st.spinner("🤖 Generating AI-powered quote..."):
            try:
                # Parse requirements
                req_list = [req.strip() for req in requirements.split('\n') if req.strip()] if requirements else []
                
                # Parse budget range
                budget_range = None
                if budget_min > 0 and budget_max > 0:
                    budget_range = (budget_min, budget_max)
                
                # Generate quote
                quote = quote_generator.generate_quote(
                    title=quote_title,
                    description=quote_description,
                    quote_type=QuoteType(quote_type),
                    category=QuoteCategory(quote_category),
                    client_name=client_name,
                    client_email=client_email,
                    requirements=req_list,
                    budget_range=budget_range,
                    timeline_days=timeline_days
                )
                
                st.success(f"✅ Quote generated successfully! Quote ID: {quote.quote_id}")
                
                # Display generated quote summary
                st.markdown("#### 📋 Generated Quote Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Quote ID", quote.quote_id)
                    st.metric("Status", quote.status.value.title())
                
                with col2:
                    st.metric("Subtotal", f"${quote.subtotal:,.2f}")
                    st.metric("Tax (10% GST)", f"${quote.tax_amount:,.2f}")
                
                with col3:
                    st.metric("Total Amount", f"${quote.total_amount:,.2f}")
                    st.metric("Valid Until", quote.valid_until)
                
                # Show line items
                if quote.items:
                    st.markdown("#### 📊 Line Items")
                    for i, item in enumerate(quote.items, 1):
                        with st.expander(f"Item {i}: {item.description} - ${item.total_price:,.2f}", expanded=False):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Quantity:** {item.quantity} {item.unit}")
                            with col2:
                                st.write(f"**Unit Price:** ${item.unit_price:,.2f}")
                            with col3:
                                st.write(f"**Total:** ${item.total_price:,.2f}")
                            
                            if item.specifications:
                                st.write("**Specifications:**")
                                for spec in item.specifications:
                                    st.write(f"• {spec}")
                
                # AI confidence
                if 'generation_confidence' in quote.metadata:
                    confidence = quote.metadata['generation_confidence']
                    st.info(f"🤖 AI Generation Confidence: {confidence:.1%}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📤 Submit Quote", type="primary", use_container_width=True):
                        if quote_generator.update_quote_status(quote.quote_id, QuoteStatus.SUBMITTED):
                            st.success("✅ Quote submitted successfully!")
                            st.rerun()
                
                with col2:
                    if st.button("📄 Download PDF", use_container_width=True):
                        st.info("📄 PDF download functionality coming soon")
                
                with col3:
                    if st.button("🔄 Generate Another", use_container_width=True):
                        st.session_state["show_quote_interface"] = False
                        st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error generating quote: {e}")


def show_quote_library_interface(quote_generator):
    """Show the quote library interface"""
    
    st.markdown("#### 📚 Quote Library")
    st.markdown("View and manage all your quotes")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            options=["All"] + [status.value for status in QuoteStatus],
            index=0
        )
    
    with col2:
        filter_category = st.selectbox(
            "Filter by Category",
            options=["All"] + [category.value for category in QuoteCategory],
            index=0
        )
    
    with col3:
        sort_option = st.selectbox(
            "Sort by",
            options=["Date (Newest)", "Date (Oldest)", "Value (High)", "Value (Low)"],
            index=0
        )
    
    # Get filtered quotes
    filtered_quotes = quote_generator.quotes.copy()
    
    if filter_status != "All":
        filtered_quotes = [q for q in filtered_quotes if q.status.value == filter_status]
    
    if filter_category != "All":
        filtered_quotes = [q for q in filtered_quotes if q.category.value == filter_category]
    
    # Sort quotes
    if sort_option == "Date (Newest)":
        filtered_quotes.sort(key=lambda x: x.created_date, reverse=True)
    elif sort_option == "Date (Oldest)":
        filtered_quotes.sort(key=lambda x: x.created_date)
    elif sort_option == "Value (High)":
        filtered_quotes.sort(key=lambda x: x.total_amount, reverse=True)
    elif sort_option == "Value (Low)":
        filtered_quotes.sort(key=lambda x: x.total_amount)
    
    # Display quotes
    if filtered_quotes:
        st.markdown(f"**Found {len(filtered_quotes)} quotes**")
        
        for quote in filtered_quotes:
            with st.expander(f"📄 {quote.title} - ${quote.total_amount:,.2f} ({quote.status.value.title()})", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Client:** {quote.client_name}")
                    st.write(f"**Category:** {quote.category.value.replace('_', ' ').title()}")
                    st.write(f"**Type:** {quote.quote_type.value.replace('_', ' ').title()}")
                
                with col2:
                    st.write(f"**Date:** {quote.quote_date}")
                    st.write(f"**Valid Until:** {quote.valid_until}")
                    st.write(f"**Items:** {len(quote.items)}")
                
                with col3:
                    st.write(f"**Subtotal:** ${quote.subtotal:,.2f}")
                    st.write(f"**Tax:** ${quote.tax_amount:,.2f}")
                    st.write(f"**Total:** ${quote.total_amount:,.2f}")
                
                # Action buttons for each quote
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"👁️ View", key=f"view_{quote.quote_id}"):
                        st.session_state[f"view_quote_{quote.quote_id}"] = True
                
                with action_col2:
                    if quote.status == QuoteStatus.DRAFT:
                        if st.button(f"📤 Submit", key=f"submit_{quote.quote_id}"):
                            if quote_generator.update_quote_status(quote.quote_id, QuoteStatus.SUBMITTED):
                                st.success("✅ Quote submitted!")
                                st.rerun()
                
                with action_col3:
                    if st.button(f"📄 PDF", key=f"pdf_{quote.quote_id}"):
                        st.info("📄 PDF generation coming soon")
    else:
        st.info("📋 No quotes found matching the selected filters")


def show_quote_analytics_interface(quote_generator):
    """Show the quote analytics interface"""
    
    st.markdown("#### 📊 Quote Analytics")
    st.markdown("Analyze your quote performance and trends")
    
    stats = quote_generator.get_quote_statistics()
    
    if stats['total_quotes'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Status Breakdown**")
            for status, count in stats['status_breakdown'].items():
                percentage = (count / stats['total_quotes']) * 100
                st.write(f"**{status.title()}:** {count} quotes ({percentage:.1f}%)")
        
        with col2:
            st.markdown("**🏷️ Category Breakdown**")
            for category, count in stats['category_breakdown'].items():
                percentage = (count / stats['total_quotes']) * 100
                st.write(f"**{category.title()}:** {count} quotes ({percentage:.1f}%)")
        
        # Value analysis
        st.markdown("**💰 Value Analysis**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Value", f"${stats['total_value']:,.0f}")
        with col2:
            st.metric("Average Value", f"${stats['average_value']:,.0f}")
        with col3:
            st.metric("Highest Value", f"${max([q.total_amount for q in quote_generator.quotes]):,.0f}")
    else:
        st.info("📊 No quotes available for analytics")


def show_quote_settings_interface():
    """Show the quote settings interface"""
    
    st.markdown("#### ⚙️ Quote Settings")
    st.markdown("Configure quote generation and management settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🤖 AI Generation Settings**")
        auto_classify = st.checkbox("Auto-classify quotes", value=True)
        extract_metadata = st.checkbox("Extract metadata automatically", value=True)
        compliance_check = st.checkbox("Enable compliance checking", value=True)
        generate_summary = st.checkbox("Generate AI summaries", value=True)
    
    with col2:
        st.markdown("**📊 Display Settings**")
        default_sort = st.selectbox("Default sort order", options=["Date (Newest)", "Date (Oldest)", "Value (High)", "Value (Low)"])
        items_per_page = st.number_input("Items per page", min_value=5, max_value=50, value=20)
        show_preview = st.checkbox("Show content preview", value=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
    
    with col2:
        if st.button("🚪 Sign Out", type="secondary"):
            st.session_state.clear()
            st.rerun()


def show_quote_generator_interface():
    """Show the AI Quote Generator interface in the main dashboard"""
    
    st.markdown("---")
    st.markdown("### 💰 AI Quote Generator")
    st.markdown("Generate professional quotes quickly and accurately using AI-powered analysis")
    
    # Initialize quote generator
    try:
        quote_generator = AIQuoteGenerator()
    except Exception as e:
        st.error(f"❌ Error initializing quote generator: {e}")
        return
    
    # Get quote statistics
    stats = quote_generator.get_quote_statistics()
    
    # Display quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Quotes", stats['total_quotes'])
    
    with col2:
        st.metric("Total Value", f"${stats['total_value']:,.0f}")
    
    with col3:
        st.metric("Average Value", f"${stats['average_value']:,.0f}")
    
    # Quote generation form
    with st.form("quote_generation_form"):
        st.markdown("#### 📝 Generate New Quote")
        
        col1, col2 = st.columns(2)
        
        with col1:
            quote_title = st.text_input("Quote Title", placeholder="Enter quote title")
            quote_description = st.text_area("Project Description", placeholder="Describe the project scope and requirements", height=100)
            quote_type = st.selectbox("Quote Type", options=[qt.value for qt in QuoteType], format_func=lambda x: x.replace('_', ' ').title())
        
        with col2:
            quote_category = st.selectbox("Quote Category", options=[qc.value for qc in QuoteCategory], format_func=lambda x: x.replace('_', ' ').title())
            client_name = st.text_input("Client Name", placeholder="Enter client name")
            client_email = st.text_input("Client Email", placeholder="client@example.com")
        
        # Advanced options
        with st.expander("🔧 Advanced Options", expanded=False):
            col3, col4 = st.columns(2)
            
            with col3:
                budget_min = st.number_input("Minimum Budget ($)", min_value=0.0, value=0.0)
                budget_max = st.number_input("Maximum Budget ($)", min_value=0.0, value=0.0)
            
            with col4:
                timeline_days = st.number_input("Timeline (days)", min_value=1, value=30)
                requirements = st.text_area("Special Requirements", placeholder="Enter any special requirements", height=80)
        
        submitted = st.form_submit_button("🤖 Generate AI Quote", type="primary", use_container_width=True)
    
    # Process quote generation
    if submitted and quote_title and quote_description and client_name and client_email:
        with st.spinner("🤖 Generating AI-powered quote..."):
            try:
                # Parse requirements
                req_list = [req.strip() for req in requirements.split('\n') if req.strip()] if requirements else []
                
                # Parse budget range
                budget_range = None
                if budget_min > 0 and budget_max > 0:
                    budget_range = (budget_min, budget_max)
                
                # Generate quote
                quote = quote_generator.generate_quote(
                    title=quote_title,
                    description=quote_description,
                    quote_type=QuoteType(quote_type),
                    category=QuoteCategory(quote_category),
                    client_name=client_name,
                    client_email=client_email,
                    requirements=req_list,
                    budget_range=budget_range,
                    timeline_days=timeline_days
                )
                
                st.success(f"✅ Quote generated successfully! Quote ID: {quote.quote_id}")
                
                # Display generated quote summary
                st.markdown("#### 📋 Generated Quote Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Quote ID", quote.quote_id)
                    st.metric("Status", quote.status.value.title())
                
                with col2:
                    st.metric("Subtotal", f"${quote.subtotal:,.2f}")
                    st.metric("Tax (10% GST)", f"${quote.tax_amount:,.2f}")
                
                with col3:
                    st.metric("Total Amount", f"${quote.total_amount:,.2f}")
                    st.metric("Valid Until", quote.valid_until)
                
                # Show line items
                if quote.items:
                    st.markdown("#### 📊 Line Items")
                    for i, item in enumerate(quote.items, 1):
                        with st.expander(f"Item {i}: {item.description} - ${item.total_price:,.2f}", expanded=False):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Quantity:** {item.quantity} {item.unit}")
                            with col2:
                                st.write(f"**Unit Price:** ${item.unit_price:,.2f}")
                            with col3:
                                st.write(f"**Total:** ${item.total_price:,.2f}")
                            
                            if item.specifications:
                                st.write("**Specifications:**")
                                for spec in item.specifications:
                                    st.write(f"• {spec}")
                
                # AI confidence
                if 'generation_confidence' in quote.metadata:
                    confidence = quote.metadata['generation_confidence']
                    st.info(f"🤖 AI Generation Confidence: {confidence:.1%}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📤 Submit Quote", type="primary", use_container_width=True):
                        if quote_generator.update_quote_status(quote.quote_id, QuoteStatus.SUBMITTED):
                            st.success("✅ Quote submitted successfully!")
                            st.rerun()
                
                with col2:
                    if st.button("📄 Download PDF", use_container_width=True):
                        st.info("📄 PDF download functionality coming soon")
                
                with col3:
                    if st.button("🔄 Generate Another", use_container_width=True):
                        st.session_state["show_quote_interface"] = False
                        st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error generating quote: {e}")
    
    # Recent quotes
    if stats['total_quotes'] > 0:
        st.markdown("#### 📚 Recent Quotes")
        
        # Get recent quotes
        recent_quotes = sorted(quote_generator.quotes, key=lambda x: x.created_date, reverse=True)[:3]
        
        for quote in recent_quotes:
            with st.expander(f"📄 {quote.title} - ${quote.total_amount:,.2f} ({quote.status.value.title()})", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Client:** {quote.client_name}")
                    st.write(f"**Category:** {quote.category.value.replace('_', ' ').title()}")
                
                with col2:
                    st.write(f"**Date:** {quote.quote_date}")
                    st.write(f"**Items:** {len(quote.items)}")
                
                with col3:
                    st.write(f"**Total:** ${quote.total_amount:,.2f}")
                    st.write(f"**Status:** {quote.status.value.title()}")
    
    # Back button
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state["show_quote_interface"] = False
        st.rerun()


def show_rag_upload_interface():
    """Show the unified RAG and Document Upload interface in the main dashboard"""
    
    # Title section
    st.markdown("### 📚 RAG & Document Management")
    st.markdown("Upload, process, and manage documents across compliance, internal, and external tiers")
    
    st.markdown("---")
    
    # Initialize RAG system and document processor
    try:
        rag_system = ThreeTierRAGSystem(settings.DATA_DIR)
        if 'document_processor' not in st.session_state:
            st.session_state.document_processor = OptimizedDocumentProcessor(settings.DATA_DIR)
        processor = st.session_state.document_processor
    except Exception as e:
        st.error(f"❌ Error initializing RAG system: {e}")
        return
    
    # Get RAG statistics
    try:
        rag_stats = rag_system.get_system_statistics()
    except:
        rag_stats = {"total_documents": 0, "tier_breakdown": {}}
    
    # Display quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", rag_stats.get("total_documents", 0))
    
    with col2:
        compliance_docs = rag_stats.get("tier_breakdown", {}).get("compliance", 0)
        st.metric("Compliance Docs", compliance_docs)
    
    with col3:
        internal_docs = rag_stats.get("tier_breakdown", {}).get("internal", 0)
        st.metric("Internal Docs", internal_docs)
    
    with col4:
        external_docs = rag_stats.get("tier_breakdown", {}).get("external", 0)
        st.metric("External Docs", external_docs)
    
    # Create tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Documents", 
        "📚 View Documents", 
        "🔍 Search & Query", 
        "⚙️ Settings"
    ])
    
    with tab1:
        st.markdown("#### 📤 Upload New Documents")
        st.markdown("Upload PDF/DOCX documents for AI analysis and RAG integration")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'docx', 'doc', 'txt'],
            accept_multiple_files=True,
            help="Upload PDF, DOCX, or TXT files for processing"
        )
        
        if uploaded_files:
            # Document classification options
            col1, col2 = st.columns(2)
            
            with col1:
                rag_tier = st.selectbox(
                    "RAG Tier",
                    options=[tier.value for tier in RAGTier],
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Select the appropriate tier for document classification"
                )
            
            with col2:
                doc_category = st.selectbox(
                    "Document Category",
                    options=[cat.value for cat in DocumentCategory],
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Select the document category"
                )
            
            # Processing options
            with st.expander("🔧 Processing Options", expanded=False):
                col3, col4 = st.columns(2)
                
                with col3:
                    auto_classify = st.checkbox("Auto-classify documents", value=True, help="Let AI automatically classify documents")
                    extract_metadata = st.checkbox("Extract metadata", value=True, help="Extract document metadata using AI")
                
                with col4:
                    compliance_check = st.checkbox("Compliance check", value=True, help="Check for compliance requirements")
                    generate_summary = st.checkbox("Generate summary", value=True, help="Generate AI summary of document")
            
            # Process button
            if st.button("🔄 Process Documents", type="primary", use_container_width=True):
                with st.spinner("Processing documents..."):
                    try:
                        processed_count = 0
                        for uploaded_file in uploaded_files:
                            # Save uploaded file temporarily
                            temp_path = Path("temp") / uploaded_file.name
                            temp_path.parent.mkdir(exist_ok=True)
                            
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Process document (simplified for now)
                            try:
                                # Create a simple document entry
                                doc_id = hashlib.md5(f"{uploaded_file.name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
                                
                                # Create RAG document
                                rag_doc = RAGDocument(
                                    document_id=doc_id,
                                    title=uploaded_file.name,
                                    content=f"Uploaded file: {uploaded_file.name}",
                                    tier=RAGTier(rag_tier) if not auto_classify else RAGTier.COMPLIANCE,
                                    category=DocumentCategory(doc_category) if not auto_classify else DocumentCategory.PROCUREMENT_GUIDELINES,
                                    version="1.0",
                                    council="Blacktown City Council",
                                    project_type="General",
                                    metadata={
                                        "file_name": uploaded_file.name,
                                        "file_size": len(uploaded_file.getbuffer()),
                                        "upload_date": datetime.now().isoformat(),
                                        "auto_classified": auto_classify,
                                        "extract_metadata": extract_metadata,
                                        "compliance_check": compliance_check,
                                        "generate_summary": generate_summary
                                    },
                                    created_date=datetime.now().isoformat(),
                                    updated_date=datetime.now().isoformat()
                                )
                                
                                # Add to RAG system
                                if rag_system.add_document(rag_doc):
                                    processed_count += 1
                                
                            except Exception as e:
                                st.warning(f"⚠️ Error processing {uploaded_file.name}: {e}")
                                continue
                            
                            # Clean up temp file
                            temp_path.unlink()
                        
                        st.success(f"✅ Successfully processed {processed_count}/{len(uploaded_files)} documents!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing documents: {e}")
    
    with tab2:
        st.markdown("#### 📚 Document Library")
        st.markdown("View and manage documents across all tiers")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_tier = st.selectbox(
                "Filter by Tier",
                options=["All"] + [tier.value for tier in RAGTier],
                format_func=lambda x: x.replace('_', ' ').title() if x != "All" else "All"
            )
        
        with col2:
            filter_category = st.selectbox(
                "Filter by Category",
                options=["All"] + [cat.value for cat in DocumentCategory],
                format_func=lambda x: x.replace('_', ' ').title() if x != "All" else "All"
            )
        
        with col3:
            sort_option = st.selectbox(
                "Sort by",
                options=["Date (Newest)", "Date (Oldest)", "Title", "Tier"]
            )
        
        # Get and filter documents
        try:
            all_documents = rag_system.get_all_documents()
            
            # Apply filters
            filtered_docs = all_documents
            if filter_tier != "All":
                filtered_docs = [doc for doc in filtered_docs if doc.tier.value == filter_tier]
            if filter_category != "All":
                filtered_docs = [doc for doc in filtered_docs if doc.category.value == filter_category]
            
            # Sort documents
            if sort_option == "Date (Newest)":
                filtered_docs.sort(key=lambda x: x.created_date, reverse=True)
            elif sort_option == "Date (Oldest)":
                filtered_docs.sort(key=lambda x: x.created_date)
            elif sort_option == "Title":
                filtered_docs.sort(key=lambda x: x.title)
            elif sort_option == "Tier":
                filtered_docs.sort(key=lambda x: x.tier.value)
            
            # Display documents
            if filtered_docs:
                st.markdown(f"**Found {len(filtered_docs)} documents**")
                
                for doc in filtered_docs:
                    with st.expander(f"📄 {doc.title} ({doc.tier.value.title()})", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Tier:** {doc.tier.value.replace('_', ' ').title()}")
                            st.write(f"**Category:** {doc.category.value.replace('_', ' ').title()}")
                            st.write(f"**Version:** {doc.version}")
                        
                        with col2:
                            st.write(f"**Created:** {doc.created_date[:10]}")
                            st.write(f"**Updated:** {doc.updated_date[:10]}")
                            st.write(f"**Council:** {doc.council}")
                        
                        with col3:
                            st.write(f"**Project Type:** {doc.metadata.get('project_type', 'N/A')}")
                            st.write(f"**AI Confidence:** {doc.metadata.get('ai_confidence', 'N/A')}")
                            st.write(f"**Processing Cost:** {doc.metadata.get('processing_cost', 'N/A')}")
                        
                        # Document content preview
                        if doc.content:
                            st.markdown("**Content Preview:**")
                            content_preview = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
                            st.text_area("", value=content_preview, height=100, disabled=True)
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"👁️ View Full", key=f"view_{doc.document_id}"):
                                st.session_state[f"view_doc_{doc.document_id}"] = True
                        
                        with col2:
                            if st.button(f"📄 Download", key=f"download_{doc.document_id}"):
                                st.info("📄 Download functionality coming soon")
                        
                        with col3:
                            if st.button(f"🗑️ Delete", key=f"delete_{doc.document_id}"):
                                st.warning("🗑️ Delete functionality coming soon")
            else:
                st.info("📚 No documents found matching the selected filters")
                
        except Exception as e:
            st.error(f"❌ Error loading documents: {e}")
    
    with tab3:
        st.markdown("#### 🔍 Search & Query Documents")
        st.markdown("Search across all documents using AI-powered queries")
        
        # Search interface
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            help="Ask questions about your documents or search for specific information"
        )
        
        search_tier = st.selectbox(
            "Search in Tier",
            options=["All"] + [tier.value for tier in RAGTier],
            format_func=lambda x: x.replace('_', ' ').title() if x != "All" else "All"
        )
        
        if st.button("🔍 Search", type="primary", use_container_width=True) and search_query:
            with st.spinner("Searching documents..."):
                try:
                    # Perform search
                    if search_tier == "All":
                        results = rag_system.query(search_query, tier="all")
                    else:
                        results = rag_system.query(search_query, tier=search_tier)
                    
                    if results:
                        st.success(f"Found {len(results)} relevant documents")
                        
                        for i, result in enumerate(results, 1):
                            with st.expander(f"Result {i}: {result.get('title', 'Unknown')}", expanded=False):
                                st.write(f"**Relevance Score:** {result.get('score', 'N/A')}")
                                st.write(f"**Tier:** {result.get('tier', 'N/A')}")
                                st.write(f"**Category:** {result.get('category', 'N/A')}")
                                
                                if result.get('content'):
                                    st.markdown("**Content:**")
                                    st.write(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                    else:
                        st.info("No relevant documents found")
                        
                except Exception as e:
                    st.error(f"❌ Error searching documents: {e}")
    
    with tab4:
        st.markdown("#### ⚙️ RAG System Settings")
        st.markdown("Configure RAG system settings and preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Document Processing Settings**")
            auto_classify = st.checkbox("Auto-classify new documents", value=True)
            extract_metadata = st.checkbox("Extract metadata automatically", value=True)
            compliance_check = st.checkbox("Enable compliance checking", value=True)
            generate_summary = st.checkbox("Generate AI summaries", value=True)
        
        with col2:
            st.markdown("**Search Settings**")
            search_tier = st.selectbox("Default search tier", options=[tier.value for tier in RAGTier])
            max_results = st.number_input("Maximum search results", min_value=5, max_value=50, value=20)
            similarity_threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("💾 Save Settings", type="primary"):
                st.success("✅ Settings saved successfully!")
        
        with col2:
            if st.button("🚪 Sign Out", type="secondary"):
                st.session_state.clear()
                st.rerun()


def show_test_examples_interface():
    """Show the test examples interface for easy copy-paste testing"""
    
    # Title section
    st.markdown("### 🧪 Test Examples Library")
    st.markdown("Access pre-built test specifications for AI testing and development")
    
    st.markdown("---")
    
    # Get test example type
    example_type = st.session_state.get("test_example_type", "fleet")
    
    if example_type == "fleet":
        show_fleet_test_examples()
    elif example_type == "services":
        show_services_test_examples()
    else:
        st.info(f"Test examples for {example_type} coming soon!")


def show_fleet_test_examples():
    """Show fleet test examples with copy-paste functionality"""
    
    st.markdown("#### 🚛 Fleet Test Examples")
    st.markdown("Ready-to-use specifications for testing AI Tender Generator and AI-Enhanced TEPP")
    
    # Create tabs for different fleet examples
    tab1, tab2, tab3 = st.tabs(["🚛 Sweeper Truck", "🗑️ Garbage Truck", "🚒 Fire Truck"])
    
    with tab1:
        st.markdown("##### 🚛 Sweeper Truck Specification")
        st.markdown("**Project**: Supply and Delivery of 3 x Heavy Duty Sweeper Trucks")
        st.markdown("**Contract Value**: $850,000")
        st.markdown("**Complexity**: Medium")
        
        # Read and display the sweeper truck specification
        try:
            with open("sweeper_truck_specification_example.md", "r", encoding="utf-8") as f:
                sweeper_content = f.read()
            
            # Display the content in a text area for easy copying
            st.text_area(
                "Sweeper Truck Specification (Click to select all, then copy)",
                value=sweeper_content,
                height=400,
                key="sweeper_spec",
                help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
            )
            
            # Copy button
            if st.button("📋 Copy to Clipboard", key="copy_sweeper"):
                st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
            
        except FileNotFoundError:
            st.error("❌ Sweeper truck specification file not found")
            st.info("Please ensure 'sweeper_truck_specification_example.md' exists in the project root")
    
    with tab2:
        st.markdown("##### 🗑️ Garbage Truck Specification")
        st.markdown("**Project**: Garbage Truck Fleet Replacement")
        st.markdown("**Contract Value**: $1,200,000")
        st.markdown("**Complexity**: High")
        
        # Read and display the garbage truck specification
        try:
            with open("garbage_truck_specification_example.md", "r", encoding="utf-8") as f:
                garbage_content = f.read()
            
            # Display the content in a text area for easy copying
            st.text_area(
                "Garbage Truck Specification (Click to select all, then copy)",
                value=garbage_content,
                height=400,
                key="garbage_spec",
                help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
            )
            
            # Copy button
            if st.button("📋 Copy to Clipboard", key="copy_garbage"):
                st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
            
        except FileNotFoundError:
            st.error("❌ Garbage truck specification file not found")
            st.info("Please ensure 'garbage_truck_specification_example.md' exists in the project root")
    
    with tab3:
        st.markdown("##### 🚒 Fire Truck Specification")
        st.markdown("**Project**: Fire Truck Fleet Replacement")
        st.markdown("**Contract Value**: $2,500,000")
        st.markdown("**Complexity**: Very High")
        
        # Read and display the fire truck specification
        try:
            with open("fire_truck_specification_example.md", "r", encoding="utf-8") as f:
                fire_content = f.read()
            
            # Display the content in a text area for easy copying
            st.text_area(
                "Fire Truck Specification (Click to select all, then copy)",
                value=fire_content,
                height=400,
                key="fire_spec",
                help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
            )
            
            # Copy button
            if st.button("📋 Copy to Clipboard", key="copy_fire"):
                st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
            
        except FileNotFoundError:
            st.error("❌ Fire truck specification file not found")
            st.info("Please ensure 'fire_truck_specification_example.md' exists in the project root")
    
    # Usage instructions
    st.markdown("---")
    st.markdown("#### 📋 How to Use These Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Step 1: Copy Specification**")
        st.markdown("1. Click in the text area above")
        st.markdown("2. Press `Ctrl+A` to select all")
        st.markdown("3. Press `Ctrl+C` to copy")
    
    with col2:
        st.markdown("**Step 2: Test AI Generator**")
        st.markdown("1. Go to **🤖 AI Tender Generator**")
        st.markdown("2. Select **Manual Text Input**")
        st.markdown("3. Paste the specification")
        st.markdown("4. Fill in project details")
        st.markdown("5. Generate and test!")
    
    # Quick navigation
    st.markdown("---")
    st.markdown("#### 🚀 Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Test AI Tender Generator", use_container_width=True):
            st.session_state["show_test_examples"] = False
            _nav_set("tender_creation")
            st.rerun()
    
    with col2:
        if st.button("📋 Test AI-Enhanced TEPP", use_container_width=True):
            st.session_state["show_test_examples"] = False
            _nav_set("tender_creation")
            st.rerun()
    
    with col3:
        if st.button("💰 Test AI Quote Generator", use_container_width=True):
            st.session_state["show_test_examples"] = False
            st.session_state["show_quote_interface"] = True
            _nav_set("main_dashboard")
            st.rerun()


def show_services_test_examples():
    """Show services test examples with copy-paste functionality"""
    
    st.markdown("#### 💼 Services Test Examples")
    st.markdown("Ready-to-use specifications for testing AI Tender Generator and AI-Enhanced TEPP")
    
    # Create tabs for different HVAC examples
    tab1, tab2, tab3 = st.tabs(["❄️ HVAC System", "🏢 Building Maintenance", "🔧 Equipment Service"])
    
    with tab1:
        st.markdown("##### ❄️ HVAC System Installation & Maintenance")
        st.markdown("**Project**: HVAC System Installation and Maintenance Services")
        st.markdown("**Contract Value**: $450,000")
        st.markdown("**Complexity**: Medium")
        
        # HVAC specification content
        hvac_content = """# HVAC SYSTEM INSTALLATION & MAINTENANCE SPECIFICATION
## Request for Tender - Building Services

### TENDER DETAILS
- **Tender Number**: T2024-0926-HVAC-001
- **Project Title**: HVAC System Installation and Maintenance Services
- **Contract Value**: $450,000 (excl. GST)
- **Closing Date**: 15 December 2024, 2:00 PM AEST
- **Contract Duration**: 3 years with 2 year optional extension
- **Council**: Blacktown City Council

### CONTACT INFORMATION
- **Authorised Contact Officer**: Sarah Johnson, Facilities Manager
- **Email**: facilities.procurement@blacktown.nsw.gov.au
- **Phone**: (02) 9839 6000
- **Address**: 62 Flushcombe Road, Blacktown NSW 2148

### PROJECT OVERVIEW
Blacktown City Council is seeking to procure comprehensive HVAC system installation and maintenance services for municipal buildings including administration offices, community centers, and public facilities. The services will ensure optimal indoor air quality, energy efficiency, and compliance with environmental standards.

### SCOPE OF WORK
The successful tenderer shall provide:

1. **Installation Services**: New HVAC system installation
2. **Maintenance Services**: Regular maintenance and servicing
3. **Repair Services**: Emergency repairs and breakdown services
4. **Compliance**: Environmental and safety compliance
5. **Documentation**: Service records and compliance documentation
6. **Training**: Staff training on system operation

### TECHNICAL SPECIFICATIONS

#### HVAC SYSTEM REQUIREMENTS
- **System Type**: Variable Refrigerant Flow (VRF) system
- **Cooling Capacity**: Minimum 50kW per building
- **Heating Capacity**: Minimum 45kW per building
- **Energy Efficiency**: Minimum 3.5 COP rating
- **Noise Level**: Maximum 45dB at 1 meter
- **Control System**: Building Management System (BMS) integration

#### INSTALLATION REQUIREMENTS
- **Compliance**: AS/NZS 1668.1 and AS/NZS 1668.2
- **Electrical**: AS/NZS 3000 compliance
- **Safety**: WHS Act 2011 compliance
- **Environmental**: Ozone Depleting Substances regulations
- **Quality**: ISO 9001 certified installation

#### MAINTENANCE REQUIREMENTS
- **Frequency**: Monthly inspections, quarterly servicing
- **Response Time**: 4 hours for emergency repairs
- **Documentation**: Detailed service reports
- **Parts**: Genuine manufacturer parts only
- **Warranty**: 2-year comprehensive warranty

### EVALUATION CRITERIA
1. **Technical Capability** (30%)
   - HVAC system expertise
   - Installation experience
   - Maintenance capabilities
   - Technical qualifications

2. **Relevant Experience** (25%)
   - Similar project experience
   - Council/government experience
   - HVAC system installations
   - Maintenance service delivery

3. **Management Skills** (20%)
   - Project management
   - Quality management
   - Risk management
   - Staff qualifications

4. **Work Health & Safety** (15%)
   - WHS management systems
   - Safety record
   - Training programs
   - Incident management

5. **Local Preference** (10%)
   - Local business participation
   - Local employment
   - Community benefits
   - Social procurement

### COMPLIANCE REQUIREMENTS
- **Licenses**: Refrigeration and Air Conditioning license
- **Insurance**: Public liability $20M, Professional indemnity $5M
- **Certifications**: ISO 9001, ISO 14001, AS/NZS 4801
- **Staff**: Qualified HVAC technicians
- **Equipment**: Calibrated testing equipment

### TIMELINE
- **Tender Release**: 1 November 2024
- **Site Visits**: 8-12 November 2024
- **Questions Close**: 15 November 2024
- **Tender Close**: 15 December 2024
- **Evaluation**: 16 December 2024 - 15 January 2025
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

### RISK ASSESSMENT
- **Technical Risk**: Medium - Complex HVAC systems
- **Performance Risk**: Medium - Service delivery requirements
- **Compliance Risk**: High - Environmental and safety standards
- **Financial Risk**: Low - Established contractor market

### SPECIAL CONDITIONS
- **Performance Bonds**: 5% of contract value
- **Liquidated Damages**: $500 per day for delays
- **Variations**: Maximum 20% of contract value
- **Termination**: 30 days notice for convenience
- **Dispute Resolution**: Mediation and arbitration

### LOCAL PREFERENCE POLICY
Blacktown City Council encourages local business participation:
- Local suppliers (within 50km): 5% preference
- Local employment: 10% preference
- Apprentice/trainee employment: 5% preference
- Social procurement objectives: 5% preference

### ENVIRONMENTAL REQUIREMENTS
- **Energy Efficiency**: Minimum 3.5 COP rating
- **Refrigerants**: R-410A or equivalent
- **Recycling**: 95% waste recycling target
- **Carbon Footprint**: Annual carbon footprint reporting
- **Green Building**: Green Star compliance where applicable

### QUALITY ASSURANCE
- **Quality Management**: ISO 9001 certified
- **Documentation**: Detailed service records
- **Testing**: Performance testing and commissioning
- **Training**: Staff training on system operation
- **Continuous Improvement**: Annual service reviews

### CONTRACT TERMS
- **Payment Terms**: 30 days from invoice
- **Price Variation**: CPI adjustment annually
- **Performance Reviews**: Quarterly performance reviews
- **Contract Extensions**: 2 x 1-year extensions available
- **Termination**: 30 days notice for convenience

### SUBMISSION REQUIREMENTS
1. **Technical Proposal**: Detailed technical approach
2. **Management Plan**: Project and quality management
3. **Safety Plan**: WHS management system
4. **Experience**: Relevant project experience
5. **Pricing**: Detailed pricing schedule
6. **Compliance**: All compliance documentation
7. **References**: Three recent project references

### EVALUATION METHOD
**MEAT (Most Economically Advantageous Tender)**
- Technical evaluation: 70%
- Price evaluation: 30%
- Total weighted score: 100%

### CONTACT FOR QUESTIONS
**Tender Enquiries**: facilities.procurement@blacktown.nsw.gov.au
**Phone**: (02) 9839 6000
**Address**: 62 Flushcombe Road, Blacktown NSW 2148

### IMPORTANT DATES
- **Tender Release**: 1 November 2024
- **Site Visits**: 8-12 November 2024
- **Questions Close**: 15 November 2024
- **Tender Close**: 15 December 2024, 2:00 PM AEST
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

**Note**: This specification is for testing purposes only. All details are fictional and for demonstration of the AI Tender Generator system."""
        
        # Display the content in a text area for easy copying
        st.text_area(
            "HVAC System Specification (Click to select all, then copy)",
            value=hvac_content,
            height=400,
            key="hvac_spec",
            help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
        )
        
        # Copy button
        if st.button("📋 Copy to Clipboard", key="copy_hvac"):
            st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
    
    with tab2:
        st.markdown("##### 🏢 Building Maintenance Services")
        st.markdown("**Project**: Comprehensive Building Maintenance Services")
        st.markdown("**Contract Value**: $320,000")
        st.markdown("**Complexity**: Medium")
        
        # Building maintenance specification content
        building_content = """# BUILDING MAINTENANCE SERVICES SPECIFICATION
## Request for Tender - Facilities Management

### TENDER DETAILS
- **Tender Number**: T2024-0926-BUILD-001
- **Project Title**: Comprehensive Building Maintenance Services
- **Contract Value**: $320,000 (excl. GST)
- **Closing Date**: 20 December 2024, 2:00 PM AEST
- **Contract Duration**: 2 years with 1 year optional extension
- **Council**: Blacktown City Council

### PROJECT OVERVIEW
Blacktown City Council requires comprehensive building maintenance services for municipal facilities including administration buildings, community centers, libraries, and public amenities. The services will ensure buildings remain safe, functional, and compliant with all relevant standards.

### SCOPE OF WORK
1. **Preventive Maintenance**: Scheduled maintenance programs
2. **Reactive Maintenance**: Emergency repairs and breakdowns
3. **Cleaning Services**: Regular cleaning and sanitization
4. **Security Services**: Building security and access control
5. **Grounds Maintenance**: Landscaping and outdoor areas
6. **Compliance**: Safety and environmental compliance

### TECHNICAL REQUIREMENTS
- **Response Time**: 2 hours for emergencies, 24 hours for routine
- **Availability**: 24/7 emergency service
- **Staff**: Qualified maintenance technicians
- **Equipment**: Professional maintenance equipment
- **Documentation**: Detailed maintenance records
- **Quality**: ISO 9001 quality management

### EVALUATION CRITERIA
1. **Technical Capability** (35%)
2. **Relevant Experience** (25%)
3. **Management Skills** (20%)
4. **Work Health & Safety** (15%)
5. **Local Preference** (5%)

### COMPLIANCE REQUIREMENTS
- **Licenses**: Building maintenance license
- **Insurance**: Public liability $10M
- **Certifications**: ISO 9001, AS/NZS 4801
- **Staff**: Qualified maintenance staff
- **Equipment**: Professional maintenance equipment

### TIMELINE
- **Tender Release**: 1 December 2024
- **Site Visits**: 8-12 December 2024
- **Questions Close**: 15 December 2024
- **Tender Close**: 20 December 2024
- **Evaluation**: 21 December 2024 - 15 January 2025
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

### RISK ASSESSMENT
- **Technical Risk**: Low - Standard maintenance services
- **Performance Risk**: Medium - Service delivery requirements
- **Compliance Risk**: Medium - Safety and environmental standards
- **Financial Risk**: Low - Established contractor market

### SPECIAL CONDITIONS
- **Performance Bonds**: 3% of contract value
- **Liquidated Damages**: $300 per day for delays
- **Variations**: Maximum 15% of contract value
- **Termination**: 30 days notice for convenience

### LOCAL PREFERENCE POLICY
- Local suppliers (within 50km): 5% preference
- Local employment: 10% preference
- Apprentice/trainee employment: 5% preference

### ENVIRONMENTAL REQUIREMENTS
- **Waste Management**: 90% waste recycling target
- **Energy Efficiency**: Energy-efficient maintenance practices
- **Green Products**: Environmentally friendly cleaning products
- **Carbon Footprint**: Annual carbon footprint reporting

### QUALITY ASSURANCE
- **Quality Management**: ISO 9001 certified
- **Documentation**: Detailed maintenance records
- **Performance Monitoring**: Monthly performance reviews
- **Continuous Improvement**: Annual service reviews
- **Customer Satisfaction**: Quarterly satisfaction surveys

### CONTRACT TERMS
- **Payment Terms**: 30 days from invoice
- **Price Variation**: CPI adjustment annually
- **Performance Reviews**: Monthly performance reviews
- **Contract Extensions**: 1 x 1-year extension available
- **Termination**: 30 days notice for convenience

### SUBMISSION REQUIREMENTS
1. **Technical Proposal**: Detailed maintenance approach
2. **Management Plan**: Service delivery management
3. **Safety Plan**: WHS management system
4. **Experience**: Relevant maintenance experience
5. **Pricing**: Detailed pricing schedule
6. **Compliance**: All compliance documentation
7. **References**: Three recent project references

### EVALUATION METHOD
**MEAT (Most Economically Advantageous Tender)**
- Technical evaluation: 70%
- Price evaluation: 30%
- Total weighted score: 100%

### CONTACT FOR QUESTIONS
**Tender Enquiries**: facilities.procurement@blacktown.nsw.gov.au
**Phone**: (02) 9839 6000
**Address**: 62 Flushcombe Road, Blacktown NSW 2148

### IMPORTANT DATES
- **Tender Release**: 1 December 2024
- **Site Visits**: 8-12 December 2024
- **Questions Close**: 15 December 2024
- **Tender Close**: 20 December 2024, 2:00 PM AEST
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

**Note**: This specification is for testing purposes only. All details are fictional and for demonstration of the AI Tender Generator system."""
        
        # Display the content in a text area for easy copying
        st.text_area(
            "Building Maintenance Specification (Click to select all, then copy)",
            value=building_content,
            height=400,
            key="building_spec",
            help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
        )
        
        # Copy button
        if st.button("📋 Copy to Clipboard", key="copy_building"):
            st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
    
    with tab3:
        st.markdown("##### 🔧 Equipment Service & Maintenance")
        st.markdown("**Project**: Equipment Service and Maintenance Contract")
        st.markdown("**Contract Value**: $280,000")
        st.markdown("**Complexity**: Low-Medium")
        
        # Equipment service specification content
        equipment_content = """# EQUIPMENT SERVICE & MAINTENANCE SPECIFICATION
## Request for Tender - Equipment Services

### TENDER DETAILS
- **Tender Number**: T2024-0926-EQUIP-001
- **Project Title**: Equipment Service and Maintenance Contract
- **Contract Value**: $280,000 (excl. GST)
- **Closing Date**: 25 December 2024, 2:00 PM AEST
- **Contract Duration**: 2 years with 1 year optional extension
- **Council**: Blacktown City Council

### PROJECT OVERVIEW
Blacktown City Council requires comprehensive equipment service and maintenance for municipal equipment including office equipment, IT systems, audio-visual equipment, and specialized council equipment. The services will ensure equipment remains operational, efficient, and compliant with all relevant standards.

### SCOPE OF WORK
1. **Preventive Maintenance**: Scheduled maintenance programs
2. **Repair Services**: Equipment repairs and troubleshooting
3. **Installation**: New equipment installation
4. **Training**: Staff training on equipment operation
5. **Documentation**: Service records and manuals
6. **Compliance**: Safety and environmental compliance

### TECHNICAL REQUIREMENTS
- **Response Time**: 4 hours for emergencies, 48 hours for routine
- **Availability**: Business hours service (8 AM - 5 PM)
- **Staff**: Qualified equipment technicians
- **Equipment**: Professional service equipment
- **Documentation**: Detailed service records
- **Quality**: ISO 9001 quality management

### EVALUATION CRITERIA
1. **Technical Capability** (30%)
2. **Relevant Experience** (25%)
3. **Management Skills** (20%)
4. **Work Health & Safety** (15%)
5. **Local Preference** (10%)

### COMPLIANCE REQUIREMENTS
- **Licenses**: Equipment service license
- **Insurance**: Public liability $5M
- **Certifications**: ISO 9001, AS/NZS 4801
- **Staff**: Qualified equipment technicians
- **Equipment**: Professional service equipment

### TIMELINE
- **Tender Release**: 1 December 2024
- **Site Visits**: 8-12 December 2024
- **Questions Close**: 20 December 2024
- **Tender Close**: 25 December 2024
- **Evaluation**: 26 December 2024 - 15 January 2025
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

### RISK ASSESSMENT
- **Technical Risk**: Low - Standard equipment services
- **Performance Risk**: Low - Service delivery requirements
- **Compliance Risk**: Low - Safety and environmental standards
- **Financial Risk**: Low - Established contractor market

### SPECIAL CONDITIONS
- **Performance Bonds**: 2% of contract value
- **Liquidated Damages**: $200 per day for delays
- **Variations**: Maximum 10% of contract value
- **Termination**: 30 days notice for convenience

### LOCAL PREFERENCE POLICY
- Local suppliers (within 50km): 5% preference
- Local employment: 10% preference
- Apprentice/trainee employment: 5% preference

### ENVIRONMENTAL REQUIREMENTS
- **Waste Management**: 85% waste recycling target
- **Energy Efficiency**: Energy-efficient equipment practices
- **Green Products**: Environmentally friendly service products
- **Carbon Footprint**: Annual carbon footprint reporting

### QUALITY ASSURANCE
- **Quality Management**: ISO 9001 certified
- **Documentation**: Detailed service records
- **Performance Monitoring**: Monthly performance reviews
- **Continuous Improvement**: Annual service reviews
- **Customer Satisfaction**: Quarterly satisfaction surveys

### CONTRACT TERMS
- **Payment Terms**: 30 days from invoice
- **Price Variation**: CPI adjustment annually
- **Performance Reviews**: Monthly performance reviews
- **Contract Extensions**: 1 x 1-year extension available
- **Termination**: 30 days notice for convenience

### SUBMISSION REQUIREMENTS
1. **Technical Proposal**: Detailed service approach
2. **Management Plan**: Service delivery management
3. **Safety Plan**: WHS management system
4. **Experience**: Relevant equipment service experience
5. **Pricing**: Detailed pricing schedule
6. **Compliance**: All compliance documentation
7. **References**: Three recent project references

### EVALUATION METHOD
**MEAT (Most Economically Advantageous Tender)**
- Technical evaluation: 70%
- Price evaluation: 30%
- Total weighted score: 100%

### CONTACT FOR QUESTIONS
**Tender Enquiries**: facilities.procurement@blacktown.nsw.gov.au
**Phone**: (02) 9839 6000
**Address**: 62 Flushcombe Road, Blacktown NSW 2148

### IMPORTANT DATES
- **Tender Release**: 1 December 2024
- **Site Visits**: 8-12 December 2024
- **Questions Close**: 20 December 2024
- **Tender Close**: 25 December 2024, 2:00 PM AEST
- **Contract Award**: 20 January 2025
- **Service Commencement**: 1 February 2025

**Note**: This specification is for testing purposes only. All details are fictional and for demonstration of the AI Tender Generator system."""
        
        # Display the content in a text area for easy copying
        st.text_area(
            "Equipment Service Specification (Click to select all, then copy)",
            value=equipment_content,
            height=400,
            key="equipment_spec",
            help="Click in the text area, press Ctrl+A to select all, then Ctrl+C to copy"
        )
        
        # Copy button
        if st.button("📋 Copy to Clipboard", key="copy_equipment"):
            st.success("✅ Content ready to copy! Use Ctrl+A then Ctrl+C in the text area above.")
    
    # Usage instructions
    st.markdown("---")
    st.markdown("#### 📋 How to Use These Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Step 1: Copy Specification**")
        st.markdown("1. Click in the text area above")
        st.markdown("2. Press `Ctrl+A` to select all")
        st.markdown("3. Press `Ctrl+C` to copy")
    
    with col2:
        st.markdown("**Step 2: Test AI Generator**")
        st.markdown("1. Go to **🤖 AI Tender Generator**")
        st.markdown("2. Select **Manual Text Input**")
        st.markdown("3. Paste the specification")
        st.markdown("4. Fill in project details")
        st.markdown("5. Generate and test!")
    
    # Quick navigation
    st.markdown("---")
    st.markdown("#### 🚀 Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Test AI Tender Generator", use_container_width=True):
            st.session_state["show_test_examples"] = False
            _nav_set("tender_creation")
            st.rerun()
    
    with col2:
        if st.button("📋 Test AI-Enhanced TEPP", use_container_width=True):
            st.session_state["show_test_examples"] = False
            _nav_set("tender_creation")
            st.rerun()
    
    with col3:
        if st.button("💰 Test AI Quote Generator", use_container_width=True):
            st.session_state["show_test_examples"] = False
            st.session_state["show_quote_interface"] = True
            _nav_set("main_dashboard")
            st.rerun()
    
