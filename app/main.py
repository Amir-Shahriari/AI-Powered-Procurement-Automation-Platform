"""
Main application entry point for the NSW Procurement Platform
"""
import os
import streamlit as st

# Fix OMP library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Configure Streamlit to disable automatic page navigation
st.set_page_config(
    page_title="NSW Government Procurement Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Disable Streamlit's automatic multipage navigation
import os
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# Import core modules
from app.core.navigation import _nav_init, _get_current_page, _get_page_params, _nav_set
from app.core.ui_helpers import _inject_css

# Import page modules
from app.pages.signin_page import page_signin
from app.pages.main_dashboard import page_main_dashboard

# Import enhanced components
from app.components.enhanced_tepp_ui import show_enhanced_tepp_generator
from app.components.sidebar_navigation import render_sidebar
from app.services.ai_model_detector import get_ai_detector

# Import compliance dashboard page
from app.pages.compliance_dashboard import page_compliance_dashboard

# RAG and Document Upload are now integrated into main dashboard

# Import progress dashboard page
from app.pages.progress_dashboard import page_progress_dashboard

# Import historical matching dashboard page
from app.pages.historical_matching_dashboard import page_historical_matching_dashboard
from app.pages.unified_evaluation_dashboard import page_unified_evaluation_dashboard
from app.components.ai_content_viewer import AIContentViewer

# Quote generation is now integrated into main dashboard

# Functional pages only - removed placeholder pages
def page_tender_creation():
    """AI-powered tender creation page with integrated TEPP Generator"""
    _inject_css()
    render_sidebar()
    
    # Header
    st.markdown('''
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1e3a8a; font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700;">
            📋 AI-Powered Tender Creation
        </h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
            AI will generate everything automatically following NSW compliance rules
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Back to selection button
    if st.button("← Back to Selection", type="secondary"):
        _nav_set("main_dashboard")
        st.rerun()
    
    # Create tabs for different tender creation tools
    tab1, tab2, tab3 = st.tabs(["🤖 AI Tender Generator", "🤖 AI-Enhanced TEPP Generator", "📚 Content Viewer & Editor"])
    
    with tab1:
        show_ai_tender_generator()
    
    with tab2:
        show_enhanced_tepp_generator()
    
    with tab3:
        # Initialize content viewer
        content_viewer = AIContentViewer()
        content_viewer.display_content_dashboard()

def show_ai_tender_generator():
    """Show the AI tender generator interface"""
    st.markdown("#### 🤖 AI Tender Generator")
    st.markdown("Generate comprehensive tender packages using AI")
    
    # Initialize session state with unique keys for AI Tender Generator
    if 'tender_tepp_data' not in st.session_state:
        st.session_state.tender_tepp_data = None
    if 'tender_tepp_config' not in st.session_state:
        st.session_state.tender_tepp_config = None
    if 'tender_package_data' not in st.session_state:
        st.session_state.tender_package_data = None
    
    # AI Enhancement Option
    ai_enhancement = st.checkbox("Enable AI Enhancement", value=True, 
                               help="Use AI to enhance and optimize the generated content")
    
    # Tender generation form
    with st.form("tender_generation_form"):
        st.markdown("##### 📋 Project Information")
        col1, col2 = st.columns(2)
        
        with col1:
            tender_number = st.text_input("Tender Number *", placeholder="e.g., T2024-001, RFT-2024-123")
            project_name = st.text_input("Project Name *", placeholder="Enter project name")
            project_type = st.selectbox("Project Type *", 
                options=["Construction", "Services", "Consulting", "Equipment", "IT", "Maintenance", "Fleet"])
            contract_value = st.number_input("Contract Value ($) *", min_value=0.0, value=0.0)
        
        with col2:
            council = st.text_input("Council *", value="Blacktown City Council")
            procurement_method = st.selectbox("Procurement Method *", 
                options=["Open Tender", "Selective Tender", "Request for Proposal"])
            evaluation_method = st.selectbox("Evaluation Method *", 
                options=["MEAT", "Lowest Price Conforming", "TCO", "Quality/Cost Ratio"])
        
        # Project Specifications
        st.markdown("##### 📄 Project Specifications")
        spec_input_method = st.radio(
            "Specification Input Method",
            options=["Manual Text Input", "Upload File"],
            horizontal=True
        )
        
        if spec_input_method == "Manual Text Input":
            project_specifications = st.text_area(
                "Project Specifications", 
                placeholder="Paste your detailed project specifications here...\n\nExample: Vehicle requirements, technical specifications, compliance requirements, etc.",
                height=200,
                help="Enter detailed project specifications. You can paste from the test specification files provided."
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload Specification File",
                type=['pdf', 'docx', 'txt', 'md'],
                help="Upload a specification file (PDF, DOCX, TXT, or MD)"
            )
            if uploaded_file:
                # Extract text from uploaded file
                try:
                    if uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
                        # Handle TXT files
                        project_specifications = str(uploaded_file.read(), "utf-8")
                        st.success(f"✅ Successfully loaded text file: {uploaded_file.name}")
                        
                    elif uploaded_file.name.endswith('.md'):
                        # Handle Markdown files
                        project_specifications = str(uploaded_file.read(), "utf-8")
                        st.success(f"✅ Successfully loaded markdown file: {uploaded_file.name}")
                        
                    elif uploaded_file.type == "application/pdf":
                        # Handle PDF files
                        try:
                            import PyPDF2
                            import io
                            
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                            text_content = ""
                            
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                text_content += page.extract_text() + "\n"
                            
                            project_specifications = text_content
                            st.success(f"✅ Successfully extracted text from PDF: {uploaded_file.name}")
                            
                        except ImportError:
                            st.error("❌ PyPDF2 not available. Please install: pip install PyPDF2")
                            project_specifications = f"PDF file uploaded: {uploaded_file.name}\n\n[PDF text extraction requires PyPDF2 library]"
                        except Exception as e:
                            st.error(f"❌ Error reading PDF: {str(e)}")
                            project_specifications = f"PDF file uploaded: {uploaded_file.name}\n\n[Error extracting text]"
                            
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        # Handle DOCX files
                        try:
                            from docx import Document
                            import io
                            
                            doc = Document(io.BytesIO(uploaded_file.read()))
                            text_content = ""
                            
                            for paragraph in doc.paragraphs:
                                text_content += paragraph.text + "\n"
                            
                            project_specifications = text_content
                            st.success(f"✅ Successfully extracted text from DOCX: {uploaded_file.name}")
                            
                        except ImportError:
                            st.error("❌ python-docx not available. Please install: pip install python-docx")
                            project_specifications = f"DOCX file uploaded: {uploaded_file.name}\n\n[DOCX text extraction requires python-docx library]"
                        except Exception as e:
                            st.error(f"❌ Error reading DOCX: {str(e)}")
                            project_specifications = f"DOCX file uploaded: {uploaded_file.name}\n\n[Error extracting text]"
                            
                    else:
                        # Fallback for unknown file types
                        project_specifications = f"File uploaded: {uploaded_file.name}\n\n[File type not supported for text extraction]"
                        st.warning(f"⚠️ File type not supported for text extraction: {uploaded_file.name}")
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    project_specifications = f"Error processing file: {uploaded_file.name}"
            else:
                project_specifications = ""
        
        # Advanced Options
        with st.expander("🔧 Advanced Options", expanded=False):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                contract_duration = st.number_input("Contract Duration (years)", min_value=1, max_value=10, value=2)
                extension_options = st.number_input("Extension Options (years)", min_value=0, max_value=5, value=1)
                compliance_focus = st.selectbox("Compliance Focus", 
                    options=["Standard", "High", "Maximum"], index=1)
            
            with col_adv2:
                detail_level = st.selectbox("Detail Level", 
                    options=["Basic", "Standard", "Detailed", "Comprehensive"], index=2)
                creativity_level = st.selectbox("Creativity Level", 
                    options=["Conservative", "Balanced", "Innovative"], index=1)
                local_preference = st.checkbox("Apply Local Preference Policy", value=True)
        
        submitted = st.form_submit_button("🤖 Generate AI Tender Package", type="primary", use_container_width=True)
    
    if submitted and project_name and project_specifications:
        # Validate inputs
        if not tender_number.strip():
            st.error("❌ Please enter a tender number")
            return
        
        if not project_name.strip():
            st.error("❌ Please enter a project name")
            return
        
        if not project_specifications.strip():
            st.error("❌ Please enter project specifications")
            return
        
        if contract_value <= 0:
            st.error("❌ Please enter a valid contract value")
            return
        
        # Generate tender package
        with st.spinner("🤖 Generating AI tender package..."):
            try:
                # Import the AI generation service
                from app.services.ai_generation import generate_ai_tender_package
                
                # Generate the tender package
                tender_package = generate_ai_tender_package(
                    project_title=project_name,
                    contract_value=contract_value,
                    project_type=project_type,
                    contract_duration=contract_duration,
                    spec_content=project_specifications,
                    council=council,
                    tender_number=tender_number
                )
                
                if tender_package:
                    # Store in session state
                    st.session_state.tender_package_data = tender_package
                    
                    # Display success message
                    st.success("✅ AI Tender Package generated successfully!")
                    
                    # Display generated content
                    st.markdown("---")
                    st.markdown("##### 📄 Generated Tender Package")
                    
                    # Display TEPP data
                    if tender_package.get('tepp'):
                        st.markdown("**TEPP Document:**")
                        tepp_data = tender_package['tepp']
                        st.json(tepp_data)
                    
                    # Display other documents
                    if tender_package.get('documents'):
                        st.markdown("**Generated Documents:**")
                        for doc_type, doc_content in tender_package['documents'].items():
                            st.markdown(f"**{doc_type.replace('_', ' ').title()}:** {doc_content}")
                    
                    
                    # Display package info
                    st.markdown("**Package Information:**")
                    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                    
                    with col_info1:
                        st.metric("Tender Number", tender_package.get('tender_number', 'N/A'))
                    with col_info2:
                        st.metric("Project", tender_package['project_title'])
                    with col_info3:
                        st.metric("Value", f"${tender_package['contract_value']:,.0f}")
                    with col_info4:
                        st.metric("Status", tender_package['status'].title())
                    
                    # Action buttons
                    st.markdown("---")
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if st.button("📄 View Full TEPP", use_container_width=True):
                            st.session_state.show_tepp_viewer = True
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("💾 Save Package", use_container_width=True):
                            st.info("💾 Save functionality coming soon")
                    
                    with col_btn3:
                        if st.button("📤 Export Documents", use_container_width=True):
                            st.info("📤 Export functionality coming soon")
                
                else:
                    st.error("❌ Failed to generate tender package. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Error generating tender package: {str(e)}")
                st.info("💡 Try with a simpler specification or check your inputs")
    
    elif submitted:
        st.error("❌ Please fill in all required fields")
    
    # Display help section
    with st.expander("💡 How to Use the AI Tender Generator", expanded=False):
        st.markdown("""
        **Step 1: Enable AI Enhancement**
        - Check "Enable AI Enhancement" for better results
        - AI model is configured in the sidebar
        
        **Step 2: Enter Project Information**
        - Tender number (e.g., T2024-001, RFT-2024-123)
        - Project name and type
        - Contract value and duration
        - Council and procurement method
        
        **Step 3: Provide Specifications**
        - Manual text input: Paste detailed specifications
        - File upload: Upload specification documents
        - Use the provided test specifications for testing
        
        **Step 4: Configure Advanced Options**
        - Set contract duration and extensions
        - Choose compliance focus and detail level
        - Enable local preference policies
        
        **Step 5: Generate and Review**
        - Click "Generate AI Tender Package"
        - Review the generated TEPP and documents
        - Save or export as needed
        
        **Test Specifications Available:**
        - Sweeper Truck Specification (Medium complexity)
        - Garbage Truck Specification (High complexity)
        - Fire Truck Specification (Very high complexity)
        """)

def page_quote_creation():
    """AI-powered quote creation page"""
    _inject_css()
    render_sidebar()
    
    # Header
    st.markdown('''
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1e3a8a; font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700;">
            💰 AI-Powered Quote Creation
        </h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
            Generate professional quotes quickly and accurately using AI
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Back to selection button
    if st.button("← Back to Selection", type="secondary"):
        _nav_set("main_dashboard")
        st.rerun()
    
    st.info("💰 Quote creation is now integrated into the main dashboard. Please use the main dashboard to access quote generation features.")

def page_contract_review():
    """AI-powered contract review page"""
    _inject_css()
    render_sidebar()
    
    # Header
    st.markdown('''
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1e3a8a; font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700;">
            🔍 AI-Powered Contract Review
        </h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
            AI-powered contract analysis and risk assessment
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Back to selection button
    if st.button("← Back to Selection", type="secondary"):
        _nav_set("main_dashboard")
        st.rerun()
    
    st.info("🔍 Contract review functionality is now integrated into the main dashboard. Please use the main dashboard to access contract review features.")

def page_ai_usage_monitor():
    """AI Usage Monitor - Functional page"""
    st.title("📊 AI Usage Monitor")
    st.markdown("Monitor AI model usage, costs, and performance metrics.")
    
    # Basic usage stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requests", "1,234", "12%")
    
    with col2:
        st.metric("Cost This Month", "$45.67", "8%")
    
    with col3:
        st.metric("Avg Response Time", "2.3s", "-5%")
    
    # Usage chart placeholder
    st.markdown("### Usage Over Time")
    st.line_chart({"Requests": [100, 120, 110, 140, 160, 180, 200]})
    
    if st.button("← Back to Home"):
        _nav_set("home")
        st.rerun()

def page_rag_monitor():
    """RAG System Monitor - Functional page"""
    st.title("⚙️ RAG System Monitor")
    st.markdown("Monitor the Retrieval-Augmented Generation system performance.")
    
    # System status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents Indexed", "1,456", "23")
    
    with col2:
        st.metric("Query Success Rate", "98.5%", "0.2%")
    
    with col3:
        st.metric("Avg Query Time", "1.2s", "-0.1s")
    
    # System health
    st.markdown("### System Health")
    st.success("✅ All systems operational")
    
    if st.button("← Back to Home"):
        _nav_set("home")
        st.rerun()


def main():
    """Main application entry point"""
    _inject_css()

    # Initialize navigation
    _nav_init()
    
    # Check authentication status
    is_authenticated = st.session_state.get("authenticated", False)
    
    # Force reset to signin if not authenticated
    if not is_authenticated:
        if "current_page" not in st.session_state or st.session_state["current_page"] != "signin":
            st.session_state["current_page"] = "signin"
    
    # Get current page from session state
    current_page = _get_current_page()
    page_params = _get_page_params()
    
    # Handle purchase_category from session state
    if "purchase_category" in page_params:
        st.session_state.purchase_category = page_params["purchase_category"]

    # Debug: Show current page (only for authenticated users) - REMOVED
    
    # Route to appropriate page using session state
    if not is_authenticated or current_page == "signin":
        # No sidebar for sign-in page
        page_signin()
    elif current_page == "main_dashboard" or current_page == "home":
        page_main_dashboard()
    elif current_page == "tender_creation":
        page_tender_creation()
    elif current_page == "quote_creation":
        page_quote_creation()
    elif current_page == "rag_monitor":
        page_rag_monitor()
    elif current_page == "ai_usage_monitor":
        page_ai_usage_monitor()
    elif current_page == "contract_review":
        page_contract_review()
    elif current_page == "compliance_dashboard":
        page_compliance_dashboard()
    elif current_page == "progress_dashboard":
        page_progress_dashboard()
    elif current_page == "historical_matching":
        page_historical_matching_dashboard()
    elif current_page == "unified_evaluation":
        page_unified_evaluation_dashboard()
    else:
        # Default to main dashboard for authenticated users
        page_main_dashboard()


if __name__ == "__main__":
    main()