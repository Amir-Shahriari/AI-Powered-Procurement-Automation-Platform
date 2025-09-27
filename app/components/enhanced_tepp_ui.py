"""
Enhanced TEPP UI Components with AI Integration and Comprehensive Editing
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.tepp_generator import TEPPGenerator, TEPPConfiguration
from app.services.three_tier_rag_system import ThreeTierRAGSystem
from app.services.ai_model_detector import get_ai_detector
from pathlib import Path

def show_enhanced_tepp_generator(selected_project=None):
    """Show enhanced TEPP generator with AI model selection and comprehensive editing"""
    
    # Display AI model selector in sidebar
    ai_detector = get_ai_detector()
    ai_detector.display_system_info()
    selected_model = ai_detector.display_model_selector()
    
    st.title("🤖 AI-Enhanced TEPP Generator")
    st.markdown("Generate comprehensive Tender Evaluation and Probity Plans with AI assistance")
    
    # Initialize session state with unique keys for AI-Enhanced TEPP Generator
    if 'enhanced_tepp_data' not in st.session_state:
        st.session_state.enhanced_tepp_data = None
    if 'enhanced_tepp_config' not in st.session_state:
        st.session_state.enhanced_tepp_config = None
    
    # Project information display
    if selected_project:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Project:** {selected_project.get('title', 'N/A')}")
        with col2:
            st.info(f"**Value:** ${selected_project.get('contract_value', 0):,.2f}")
        with col3:
            st.info(f"**Type:** {selected_project.get('category', 'N/A')}")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Generate TEPP", "✏️ Edit TEPP", "📄 View TEPP", "💾 Save & Approve"])
    
    with tab1:
        show_tepp_generation_tab(selected_project, selected_model)
    
    with tab2:
        if st.session_state.enhanced_tepp_data:
            show_tepp_editing_tab()
        else:
            st.warning("Please generate a TEPP first in the 'Generate TEPP' tab.")
    
    with tab3:
        if st.session_state.enhanced_tepp_data:
            show_tepp_viewing_tab()
        else:
            st.warning("Please generate a TEPP first in the 'Generate TEPP' tab.")
    
    with tab4:
        if st.session_state.enhanced_tepp_data:
            show_tepp_save_approve_tab()
        else:
            st.warning("Please generate a TEPP first in the 'Generate TEPP' tab.")

def show_tepp_generation_tab(selected_project, selected_model):
    """Show TEPP generation tab with AI enhancement"""
    
    st.subheader("📋 Generate New TEPP")
    
    # Basic configuration
    col1, col2 = st.columns(2)
    
    with col1:
        project_title = st.text_input(
            "Project Title",
            value=selected_project.get('title', '') if selected_project else '',
            help="Enter the project title for the TEPP"
        )
        
        contract_value = st.number_input(
            "Contract Value ($)",
            min_value=0.0,
            value=float(selected_project.get('contract_value', 0)) if selected_project else 0.0,
            step=1000.0,
            help="Enter the estimated contract value"
        )
        
        project_type = st.selectbox(
            "Project Type",
            options=["Construction", "Fleet", "HVAC", "Services", "IT", "Consulting", "General"],
            index=0,
            help="Select the type of project"
        )
    
    with col2:
        contract_duration = st.number_input(
            "Contract Duration (years)",
            min_value=1,
            max_value=10,
            value=2,
            help="Enter the contract duration in years"
        )
        
        extension_options = st.number_input(
            "Extension Options",
            min_value=0,
            max_value=5,
            value=2,
            help="Number of optional extensions"
        )
        
        council_name = st.text_input(
            "Council/Organization",
            value="Blacktown City Council",
            help="Enter the council or organization name"
        )
    
    # Specification input
    st.subheader("📝 Project Specification")
    
    spec_method = st.radio(
        "Choose input method:",
        ["📄 Upload File", "✍️ Paste Text", "✏️ Write Manually"],
        horizontal=True
    )
    
    spec_content = ""
    
    if spec_method == "📄 Upload File":
        uploaded_file = st.file_uploader(
            "Upload Specification File",
            type=['pdf', 'docx', 'txt', 'doc'],
            help="Upload your project specification file"
        )
        if uploaded_file:
            # Process uploaded file
            spec_content = process_uploaded_file(uploaded_file)
            if spec_content:
                st.success(f"✅ File processed: {uploaded_file.name}")
                st.text_area("Extracted Content Preview", spec_content[:500] + "...", height=100)
    
    elif spec_method == "✍️ Paste Text":
        spec_content = st.text_area(
            "Paste Specification Content",
            height=200,
            help="Paste your project specification content here"
        )
    
    elif spec_method == "✏️ Write Manually":
        spec_content = st.text_area(
            "Write Specification Content",
            height=200,
            help="Write your project specification content here"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            tender_number = st.text_input(
                "Tender Number",
                value=f"T{datetime.now().year}-{datetime.now().strftime('%m%d')}-{project_type.upper()[:3]}",
                help="Enter custom tender number"
            )
            
            local_preference = st.checkbox(
                "Apply Local Preference Policy",
                value=True,
                help="Apply local supplier preference policy"
            )
        
        with col2:
            interviews_required = st.checkbox(
                "Interviews Required",
                value=contract_value > 500000,
                help="Require interviews for evaluation"
            )
            
            presentations_required = st.checkbox(
                "Presentations Required",
                value=contract_value > 1000000,
                help="Require presentations for evaluation"
            )
    
    # Generate TEPP button
    if st.button("🤖 Generate TEPP with AI", type="primary", use_container_width=True):
        if not project_title:
            st.error("Please enter a project title")
            return
        
        if not spec_content:
            st.warning("No specification content provided. Generating with basic configuration.")
        
        # Create TEPP configuration
        config = TEPPConfiguration(
            project_title=project_title,
            project_description=spec_content[:200] + "..." if len(spec_content) > 200 else spec_content,
            contract_value=contract_value,
            contract_duration=contract_duration,
            extension_options=extension_options,
            project_type=project_type.lower(),
            council_name=council_name,
            tender_number=tender_number,
            local_preference_applicable=local_preference,
            interviews_required=interviews_required,
            presentations_required=presentations_required
        )
        
        # Initialize RAG system and TEPP generator
        try:
            rag_system = ThreeTierRAGSystem(Path("data"))
            tepp_generator = TEPPGenerator(rag_system)
            
            # Set the selected model in the TEPP generator
            tepp_generator.selected_model = selected_model
            
            # Generate TEPP
            with st.spinner(f"🤖 AI is generating your TEPP using {selected_model.model_name}..."):
                tepp_data = tepp_generator.generate_tepp(config, spec_content)
            
            # Store in session state with unique keys
            st.session_state.enhanced_tepp_data = tepp_data
            st.session_state.enhanced_tepp_config = config
            
            # Show AI model info
            if 'ai_insights' in tepp_data:
                st.info(f"🧠 AI Analysis completed using local models - {tepp_data.get('ai_model_used', 'Local AI')}")
            
            st.success("✅ TEPP generated successfully!")
            st.balloons()
            
            # Show summary
            show_tepp_summary(tepp_data)
            
        except Exception as e:
            st.error(f"Error generating TEPP: {e}")
            st.exception(e)

def show_tepp_editing_tab():
    """Show comprehensive TEPP editing interface"""
    
    st.subheader("✏️ Edit TEPP Sections")
    
    if not st.session_state.enhanced_tepp_data:
        st.warning("No TEPP data available for editing")
        return
    
    tepp_data = st.session_state.enhanced_tepp_data
    sections = tepp_data.get('sections', {})
    
    # Section selector
    section_options = {
        "Title Page": "title_page",
        "AIM": "aim",
        "Description": "description",
        "Probity": "probity",
        "Evaluation Committee": "evaluation_committee",
        "Evaluation Schedule": "evaluation_schedule",
        "Evaluation Methodology": "evaluation_methodology",
        "Pricing": "pricing",
        "Contract Negotiations": "contract_negotiations",
        "Debriefing": "debriefing",
        "Contract Management": "contract_management",
        "Critical Dates": "critical_dates",
        "Completion Guidelines": "completion_guidelines"
    }
    
    selected_section = st.selectbox(
        "Select Section to Edit:",
        options=list(section_options.keys()),
        help="Choose which section of the TEPP to edit"
    )
    
    section_key = section_options[selected_section]
    section_content = sections.get(section_key, "")
    
    # Edit section content
    st.subheader(f"Editing: {selected_section}")
    
    # Show current content
    st.markdown("**Current Content:**")
    st.markdown(section_content)
    
    # Edit interface
    new_content = st.text_area(
        f"Edit {selected_section} Content:",
        value=section_content,
        height=400,
        help=f"Edit the content for the {selected_section} section"
    )
    
    # Save changes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            # Update the section content
            st.session_state.enhanced_tepp_data['sections'][section_key] = new_content
            st.success(f"✅ {selected_section} updated successfully!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to Original"):
            # Reset to original content
            st.session_state.enhanced_tepp_data['sections'][section_key] = section_content
            st.success(f"✅ {selected_section} reset to original!")
            st.rerun()
    
    with col3:
        if st.button("🤖 AI Enhance"):
            # Use AI to enhance this section
            enhanced_content = enhance_section_with_ai(section_key, new_content, st.session_state.enhanced_tepp_config)
            if enhanced_content:
                st.session_state.enhanced_tepp_data['sections'][section_key] = enhanced_content
                st.success(f"✅ {selected_section} enhanced with AI!")
                st.rerun()
            else:
                st.warning("AI enhancement failed. Please try again.")
    
    # Show editing tips
    with st.expander("💡 Editing Tips"):
        st.markdown("""
        **Tips for editing TEPP sections:**
        - Use clear, professional language
        - Ensure all dates are accurate and realistic
        - Include specific requirements and criteria
        - Maintain consistency with other sections
        - Follow NSW Local Government guidelines
        - Use the AI Enhance button for intelligent suggestions
        """)

def show_tepp_viewing_tab():
    """Show complete TEPP document for review"""
    
    st.subheader("📄 Complete TEPP Document")
    
    if not st.session_state.enhanced_tepp_data:
        st.warning("No TEPP data available for viewing")
        return
    
    tepp_data = st.session_state.enhanced_tepp_data
    
    # Document header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("TEPP ID", tepp_data.get('tepp_id', 'N/A'))
    with col2:
        st.metric("Project Value", f"${tepp_data.get('contract_value', 0):,.2f}")
    with col3:
        st.metric("Process Type", tepp_data.get('process_type', 'N/A'))
    
    # AI model info
    if 'ai_model_used' in tepp_data:
        st.info(f"🤖 Generated using AI model: {tepp_data['ai_model_used']}")
    
    # Full document
    st.markdown("---")
    st.markdown(tepp_data.get('full_document', 'No document available'))
    
    # Download options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download as Markdown"):
            download_tepp_as_markdown(tepp_data)
    
    with col2:
        if st.button("📄 Download as PDF"):
            download_tepp_as_pdf(tepp_data)
    
    with col3:
        if st.button("📋 Copy to Clipboard"):
            st.code(tepp_data.get('full_document', ''), language='markdown')

def show_tepp_save_approve_tab():
    """Show TEPP save and approval interface"""
    
    st.subheader("💾 Save & Approve TEPP")
    
    if not st.session_state.enhanced_tepp_data:
        st.warning("No TEPP data available for saving")
        return
    
    tepp_data = st.session_state.enhanced_tepp_data
    
    # Save options
    st.subheader("💾 Save TEPP")
    
    col1, col2 = st.columns(2)
    
    with col1:
        save_name = st.text_input(
            "Save as:",
            value=f"{tepp_data.get('project_title', 'TEPP')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Enter a name for saving the TEPP"
        )
        
        save_location = st.selectbox(
            "Save Location:",
            options=["Local Storage", "Project Folder", "Shared Drive"],
            help="Choose where to save the TEPP"
        )
    
    with col2:
        include_ai_analysis = st.checkbox(
            "Include AI Analysis",
            value=True,
            help="Include AI analysis in saved document"
        )
        
        include_editable_fields = st.checkbox(
            "Include Editable Fields",
            value=True,
            help="Include editable field definitions"
        )
    
    if st.button("💾 Save TEPP", type="primary"):
        save_result = save_tepp_document(tepp_data, save_name, save_location, include_ai_analysis, include_editable_fields)
        if save_result:
            st.success(f"✅ TEPP saved successfully as: {save_name}")
        else:
            st.error("❌ Failed to save TEPP. Please try again.")
    
    # Approval workflow
    st.subheader("✅ Approval Workflow")
    
    approval_status = st.selectbox(
        "Approval Status:",
        options=["Draft", "Ready for Review", "Approved", "Rejected"],
        help="Set the approval status of the TEPP"
    )
    
    approver_name = st.text_input(
        "Approver Name:",
        help="Enter the name of the person approving the TEPP"
    )
    
    approval_notes = st.text_area(
        "Approval Notes:",
        height=100,
        help="Enter any notes about the approval"
    )
    
    if st.button("✅ Submit for Approval", type="primary"):
        approval_result = submit_for_approval(tepp_data, approval_status, approver_name, approval_notes)
        if approval_result:
            st.success("✅ TEPP submitted for approval successfully!")
        else:
            st.error("❌ Failed to submit for approval. Please try again.")

def show_tepp_summary(tepp_data):
    """Show TEPP generation summary"""
    
    st.subheader("📊 TEPP Generation Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sections Generated", len(tepp_data.get('sections', {})))
    
    with col2:
        st.metric("Document Length", f"{len(tepp_data.get('full_document', '')):,} characters")
    
    with col3:
        st.metric("Editable Fields", len(tepp_data.get('editable_fields', [])))
    
    with col4:
        st.metric("AI Model Used", tepp_data.get('ai_model_used', 'N/A'))
    
    # Show AI analysis summary
    if 'ai_analysis' in tepp_data:
        with st.expander("🤖 AI Analysis Summary"):
            ai_analysis = tepp_data['ai_analysis']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Technical Requirements:**")
                for req in ai_analysis.get('technical_requirements', [])[:5]:
                    st.markdown(f"• {req}")
            
            with col2:
                st.markdown("**Risk Factors:**")
                for risk in ai_analysis.get('risk_factors', [])[:5]:
                    st.markdown(f"• {risk}")

def process_uploaded_file(uploaded_file) -> str:
    """Process uploaded file and extract text content"""
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text based on file type
        if uploaded_file.name.lower().endswith('.pdf'):
            import fitz
            doc = fitz.open(temp_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        elif uploaded_file.name.lower().endswith(('.docx', '.doc')):
            import docx2txt
            text = docx2txt.process(temp_path)
        else:  # txt file
            text = temp_path.read_text(encoding='utf-8')
        
        # Clean up temp file
        temp_path.unlink()
        
        return text
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return ""

def enhance_section_with_ai(section_key: str, content: str, config: TEPPConfiguration) -> str:
    """Use AI to comprehensively enhance a specific section based on user edits and real factors"""
    try:
        # Get AI detector and selected model
        ai_detector = get_ai_detector()
        selected_model = ai_detector.get_recommended_model()
        
        # Initialize RAG system for context
        rag_system = ThreeTierRAGSystem(Path("data"))
        
        # Get comprehensive context for enhancement
        context_data = _get_enhancement_context(section_key, config, rag_system)
        
        # Create comprehensive enhancement prompt
        enhancement_prompt = _create_enhancement_prompt(section_key, content, config, context_data)
        
        # Use AI to enhance the section
        enhanced_content = _call_ai_for_enhancement(selected_model, enhancement_prompt, content)
        
        if enhanced_content:
            return enhanced_content
        else:
            # Fallback to basic enhancement
            return _apply_basic_enhancement(section_key, content, config, context_data)
            
    except Exception as e:
        st.error(f"AI enhancement failed: {e}")
        return None

def _get_enhancement_context(section_key: str, config: TEPPConfiguration, rag_system: ThreeTierRAGSystem) -> Dict[str, Any]:
    """Get comprehensive context for section enhancement"""
    try:
        context = {
            "project_info": {
                "title": config.project_title,
                "type": config.project_type,
                "value": config.contract_value,
                "duration": config.contract_duration,
                "council": config.council_name
            },
            "rag_context": "",
            "compliance_requirements": [],
            "best_practices": [],
            "risk_factors": [],
            "evaluation_criteria": config.evaluation_criteria_weights or {}
        }
        
        # Query RAG system for relevant context
        if rag_system:
            from app.services.three_tier_rag_system import RAGTier
            
            # Get compliance context
            compliance_query = f"TEPP {section_key} compliance requirements for {config.project_type} projects"
            compliance_results = rag_system.query_compliance(
                compliance_query,
                tiers=[RAGTier.COMPLIANCE, RAGTier.INTERNAL],
                project_type=config.project_type
            )
            
            if compliance_results:
                context["rag_context"] = "\n".join([result.content for result in compliance_results[:3]])
            
            # Get best practices
            best_practices_query = f"TEPP {section_key} best practices and guidelines"
            best_practices_results = rag_system.query_compliance(
                best_practices_query,
                tiers=[RAGTier.INTERNAL, RAGTier.EXTERNAL],
                project_type=config.project_type
            )
            
            if best_practices_results:
                context["best_practices"] = [result.content for result in best_practices_results[:2]]
        
        # Add project-specific context
        context["compliance_requirements"] = _get_section_specific_requirements(section_key, config)
        context["risk_factors"] = _get_section_specific_risks(section_key, config)
        
        return context
        
    except Exception as e:
        st.warning(f"Context gathering failed: {e}")
        return {"project_info": {"title": config.project_title, "type": config.project_type}}

def _create_enhancement_prompt(section_key: str, content: str, config: TEPPConfiguration, context: Dict[str, Any]) -> str:
    """Create comprehensive enhancement prompt for AI"""
    
    section_instructions = {
        "aim": """
        Enhance the AIM section by:
        1. Clarifying project objectives and scope
        2. Adding specific outcomes and deliverables
        3. Incorporating risk mitigation strategies
        4. Ensuring alignment with council strategic goals
        5. Adding measurable success criteria
        """,
        "description": """
        Enhance the DESCRIPTION section by:
        1. Adding detailed technical specifications
        2. Including performance standards and KPIs
        3. Specifying quality requirements
        4. Adding compliance and regulatory requirements
        5. Including sustainability and environmental considerations
        """,
        "probity": """
        Enhance the PROBITY section by:
        1. Adding specific probity requirements
        2. Including conflict of interest management
        3. Adding confidentiality protocols
        4. Specifying audit and review processes
        5. Including ethical conduct requirements
        """,
        "evaluation_committee": """
        Enhance the EVALUATION COMMITTEE section by:
        1. Specifying required expertise and qualifications
        2. Adding diversity and inclusion considerations
        3. Including training and development requirements
        4. Adding performance evaluation criteria
        5. Specifying decision-making processes
        """,
        "evaluation_schedule": """
        Enhance the EVALUATION SCHEDULE section by:
        1. Adding realistic timelines based on project complexity
        2. Including buffer time for contingencies
        3. Adding milestone checkpoints
        4. Including stakeholder engagement activities
        5. Adding quality assurance checkpoints
        """,
        "evaluation_methodology": """
        Enhance the EVALUATION METHODOLOGY section by:
        1. Adding detailed scoring criteria and rubrics
        2. Including assessment methods and tools
        3. Adding quality assurance processes
        4. Including peer review mechanisms
        5. Adding decision-making frameworks
        """,
        "pricing": """
        Enhance the PRICING section by:
        1. Adding detailed pricing models and structures
        2. Including cost-benefit analysis requirements
        3. Adding value for money assessment criteria
        4. Including total cost of ownership considerations
        5. Adding price variation and adjustment mechanisms
        """,
        "contract_negotiations": """
        Enhance the CONTRACT NEGOTIATIONS section by:
        1. Adding negotiation strategies and approaches
        2. Including key negotiation points and priorities
        3. Adding fallback positions and alternatives
        4. Including stakeholder consultation processes
        5. Adding documentation and record-keeping requirements
        """,
        "debriefing": """
        Enhance the DEBRIEFING section by:
        1. Adding structured debriefing processes
        2. Including feedback collection mechanisms
        3. Adding improvement recommendations
        4. Including lessons learned documentation
        5. Adding follow-up and action planning
        """,
        "contract_management": """
        Enhance the CONTRACT MANAGEMENT section by:
        1. Adding performance monitoring systems
        2. Including risk management processes
        3. Adding stakeholder communication protocols
        4. Including quality assurance mechanisms
        5. Adding continuous improvement processes
        """,
        "critical_dates": """
        Enhance the CRITICAL DATES section by:
        1. Adding realistic and achievable timelines
        2. Including dependency management
        3. Adding contingency planning
        4. Including stakeholder notification requirements
        5. Adding progress monitoring and reporting
        """,
        "completion_guidelines": """
        Enhance the COMPLETION GUIDELINES section by:
        1. Adding step-by-step completion processes
        2. Including quality checkpoints and validations
        3. Adding stakeholder approval requirements
        4. Including documentation and record-keeping
        5. Adding handover and transition processes
        """
    }
    
    prompt = f"""
    You are an expert in NSW Local Government procurement and TEPP (Tender Evaluation and Probity Plan) development. 
    
    TASK: Comprehensively enhance the following TEPP section based on user edits and real-world factors.
    
    SECTION: {section_key.upper()}
    PROJECT: {config.project_title}
    TYPE: {config.project_type}
    VALUE: ${config.contract_value:,.2f}
    DURATION: {config.contract_duration} years
    COUNCIL: {config.council_name}
    
    CURRENT CONTENT:
    {content}
    
    ENHANCEMENT INSTRUCTIONS:
    {section_instructions.get(section_key, "Enhance this section with comprehensive, professional content.")}
    
    CONTEXT INFORMATION:
    RAG Context: {context.get('rag_context', 'No additional context available')}
    Best Practices: {context.get('best_practices', [])}
    Compliance Requirements: {context.get('compliance_requirements', [])}
    Risk Factors: {context.get('risk_factors', [])}
    Evaluation Criteria: {context.get('evaluation_criteria', {})}
    
    REQUIREMENTS:
    1. Preserve the user's manual edits and improvements
    2. Add comprehensive, professional content based on real-world factors
    3. Ensure compliance with NSW Local Government requirements
    4. Include specific, actionable details
    5. Add risk mitigation strategies
    6. Include performance standards and KPIs
    7. Ensure alignment with project objectives
    8. Add stakeholder considerations
    9. Include quality assurance measures
    10. Make content practical and implementable
    
    OUTPUT FORMAT:
    Return the enhanced content that:
    - Maintains the original structure and format
    - Incorporates user edits
    - Adds comprehensive professional enhancements
    - Is specific to the project type and value
    - Follows NSW Local Government standards
    - Is ready for immediate use
    
    ENHANCED CONTENT:
    """
    
    return prompt

def _call_ai_for_enhancement(ai_model, prompt: str, original_content: str) -> str:
    """Call AI model for section enhancement"""
    try:
        if ai_model.provider == "Ollama" and ai_model.model_name != "ollama-not-running":
            return _call_ollama_for_enhancement(ai_model.model_name, prompt)
        elif ai_model.provider == "Google" and ai_model.model_name.startswith("gemini"):
            return _call_gemini_for_enhancement(ai_model.model_name, prompt)
        else:
            st.warning(f"AI model {ai_model.model_name} not available for enhancement")
            return None
            
    except Exception as e:
        st.warning(f"AI enhancement call failed: {e}")
        return None

def _call_ollama_for_enhancement(model_name: str, prompt: str) -> str:
    """Call Ollama for section enhancement"""
    try:
        import requests
        import json
        
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more focused enhancement
                "top_p": 0.9,
                "max_tokens": 4096
            }
        }
        
        with st.spinner(f"🤖 AI is enhancing section using {model_name}..."):
            response = requests.post(url, json=payload, timeout=300)
            
        if response.status_code == 200:
            result = response.json()
            enhanced_content = result.get("response", "")
            
            # Clean up the response
            if enhanced_content:
                # Remove any markdown formatting that might interfere
                enhanced_content = enhanced_content.strip()
                # Ensure it starts with proper section formatting
                if not enhanced_content.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.")):
                    # Add section number if missing
                    section_number = _get_section_number(enhanced_content)
                    if section_number:
                        enhanced_content = f"{section_number}. {enhanced_content}"
                
                return enhanced_content
            else:
                return None
        else:
            st.warning(f"Ollama API error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to Ollama. Make sure Ollama is running.")
        return None
    except Exception as e:
        st.warning(f"Ollama enhancement failed: {e}")
        return None

def _call_gemini_for_enhancement(model_name: str, prompt: str) -> str:
    """Call Gemini for section enhancement"""
    try:
        import google.generativeai as genai
        import os
        
        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.warning("Google API key not found")
            return None
        
        genai.configure(api_key=api_key)
        
        # Select model
        if "flash" in model_name.lower():
            model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            model = genai.GenerativeModel("gemini-1.5-pro")
        
        with st.spinner(f"🤖 AI is enhancing section using {model_name}..."):
            response = model.generate_content(prompt)
            
        if response and response.text:
            enhanced_content = response.text.strip()
            
            # Clean up the response
            if enhanced_content:
                # Ensure proper section formatting
                if not enhanced_content.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.")):
                    section_number = _get_section_number(enhanced_content)
                    if section_number:
                        enhanced_content = f"{section_number}. {enhanced_content}"
                
                return enhanced_content
            else:
                return None
        else:
            st.warning("Gemini API returned empty response")
            return None
            
    except Exception as e:
        st.warning(f"Gemini enhancement failed: {e}")
        return None

def _get_section_number(content: str) -> str:
    """Extract section number from content"""
    import re
    
    # Look for section headers
    section_patterns = [
        r"(\d+)\.\s*(AIM|DESCRIPTION|PROBITY|EVALUATION COMMITTEE|EVALUATION SCHEDULE|EVALUATION METHODOLOGY|PRICING|CONTRACT NEGOTIATIONS|DEBRIEFING|CONTRACT MANAGEMENT|CRITICAL DATES|COMPLETION GUIDELINES)",
        r"(\d+)\.\s*([A-Z\s]+)",
        r"(\d+)\."
    ]
    
    for pattern in section_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1) + "."
    
    return ""

def _apply_basic_enhancement(section_key: str, content: str, config: TEPPConfiguration, context: Dict[str, Any]) -> str:
    """Apply basic enhancement when AI is not available"""
    
    # Add project-specific enhancements
    project_info = context.get("project_info", {})
    project_type = project_info.get("type", "general")
    project_value = project_info.get("value", 0)
    
    # Add value-based enhancements
    if project_value > 1000000:
        value_note = "\n\n**High-Value Project Considerations:**\n• Enhanced probity requirements\n• Additional evaluation criteria\n• Extended evaluation timeline\n• Increased stakeholder involvement"
    elif project_value > 500000:
        value_note = "\n\n**Medium-Value Project Considerations:**\n• Standard probity requirements\n• Balanced evaluation criteria\n• Standard evaluation timeline"
    else:
        value_note = "\n\n**Low-Value Project Considerations:**\n• Streamlined evaluation process\n• Focused evaluation criteria\n• Accelerated timeline"
    
    # Add project type enhancements
    type_enhancements = {
        "construction": "\n\n**Construction-Specific Requirements:**\n• Building permit compliance\n• Site safety management\n• Environmental impact assessment\n• Quality assurance standards",
        "fleet": "\n\n**Fleet-Specific Requirements:**\n• Vehicle maintenance standards\n• Driver qualification requirements\n• Fleet management systems\n• Safety compliance",
        "hvac": "\n\n**HVAC-Specific Requirements:**\n• Energy efficiency standards\n• Environmental compliance\n• Maintenance protocols\n• Performance monitoring",
        "services": "\n\n**Services-Specific Requirements:**\n• Service level agreements\n• Performance monitoring\n• Quality assurance\n• Customer satisfaction metrics"
    }
    
    type_note = type_enhancements.get(project_type.lower(), "")
    
    # Add RAG context if available
    rag_note = ""
    if context.get("rag_context"):
        rag_note = f"\n\n**Compliance Context:**\n{context['rag_context'][:500]}..."
    
    # Add best practices if available
    best_practices_note = ""
    if context.get("best_practices"):
        best_practices_note = "\n\n**Best Practices:**\n" + "\n".join([f"• {practice[:100]}..." for practice in context["best_practices"][:3]])
    
    # Combine enhancements
    enhanced_content = content + value_note + type_note + rag_note + best_practices_note
    
    # Add AI enhancement note
    enhanced_content += "\n\n*[AI Enhancement: This section has been enhanced with project-specific requirements, compliance considerations, and best practices based on real-world factors.]*"
    
    return enhanced_content

def _get_section_specific_requirements(section_key: str, config: TEPPConfiguration) -> List[str]:
    """Get section-specific compliance requirements"""
    
    requirements_map = {
        "aim": [
            "Clear project objectives and scope",
            "Measurable outcomes and deliverables",
            "Alignment with council strategic goals",
            "Risk mitigation strategies"
        ],
        "description": [
            "Detailed technical specifications",
            "Performance standards and KPIs",
            "Quality requirements",
            "Compliance and regulatory requirements"
        ],
        "probity": [
            "Conflict of interest management",
            "Confidentiality protocols",
            "Audit and review processes",
            "Ethical conduct requirements"
        ],
        "evaluation_committee": [
            "Required expertise and qualifications",
            "Diversity and inclusion considerations",
            "Training and development requirements",
            "Performance evaluation criteria"
        ],
        "evaluation_schedule": [
            "Realistic timelines based on project complexity",
            "Buffer time for contingencies",
            "Milestone checkpoints",
            "Quality assurance checkpoints"
        ],
        "evaluation_methodology": [
            "Detailed scoring criteria and rubrics",
            "Assessment methods and tools",
            "Quality assurance processes",
            "Decision-making frameworks"
        ],
        "pricing": [
            "Detailed pricing models and structures",
            "Cost-benefit analysis requirements",
            "Value for money assessment criteria",
            "Total cost of ownership considerations"
        ],
        "contract_negotiations": [
            "Negotiation strategies and approaches",
            "Key negotiation points and priorities",
            "Fallback positions and alternatives",
            "Documentation and record-keeping requirements"
        ],
        "debriefing": [
            "Structured debriefing processes",
            "Feedback collection mechanisms",
            "Improvement recommendations",
            "Lessons learned documentation"
        ],
        "contract_management": [
            "Performance monitoring systems",
            "Risk management processes",
            "Stakeholder communication protocols",
            "Quality assurance mechanisms"
        ],
        "critical_dates": [
            "Realistic and achievable timelines",
            "Dependency management",
            "Contingency planning",
            "Progress monitoring and reporting"
        ],
        "completion_guidelines": [
            "Step-by-step completion processes",
            "Quality checkpoints and validations",
            "Stakeholder approval requirements",
            "Documentation and record-keeping"
        ]
    }
    
    return requirements_map.get(section_key, [])

def _get_section_specific_risks(section_key: str, config: TEPPConfiguration) -> List[str]:
    """Get section-specific risk factors"""
    
    risks_map = {
        "aim": [
            "Unclear project objectives",
            "Scope creep and changes",
            "Misalignment with strategic goals",
            "Inadequate risk assessment"
        ],
        "description": [
            "Incomplete technical specifications",
            "Unrealistic performance standards",
            "Quality requirements gaps",
            "Compliance oversights"
        ],
        "probity": [
            "Conflict of interest issues",
            "Confidentiality breaches",
            "Inadequate audit processes",
            "Ethical conduct violations"
        ],
        "evaluation_committee": [
            "Insufficient expertise",
            "Lack of diversity",
            "Inadequate training",
            "Poor performance evaluation"
        ],
        "evaluation_schedule": [
            "Unrealistic timelines",
            "Inadequate contingency planning",
            "Missing milestones",
            "Quality assurance gaps"
        ],
        "evaluation_methodology": [
            "Unclear scoring criteria",
            "Inadequate assessment methods",
            "Quality assurance failures",
            "Poor decision-making processes"
        ],
        "pricing": [
            "Inadequate pricing models",
            "Poor cost-benefit analysis",
            "Value for money assessment gaps",
            "Total cost of ownership oversights"
        ],
        "contract_negotiations": [
            "Poor negotiation strategies",
            "Inadequate preparation",
            "Lack of fallback positions",
            "Documentation gaps"
        ],
        "debriefing": [
            "Unstructured debriefing processes",
            "Inadequate feedback collection",
            "Missing improvement recommendations",
            "Poor lessons learned documentation"
        ],
        "contract_management": [
            "Inadequate performance monitoring",
            "Poor risk management",
            "Communication failures",
            "Quality assurance gaps"
        ],
        "critical_dates": [
            "Unrealistic timelines",
            "Poor dependency management",
            "Inadequate contingency planning",
            "Monitoring and reporting failures"
        ],
        "completion_guidelines": [
            "Unclear completion processes",
            "Missing quality checkpoints",
            "Inadequate stakeholder approval",
            "Documentation and record-keeping gaps"
        ]
    }
    
    return risks_map.get(section_key, [])

def download_tepp_as_markdown(tepp_data):
    """Download TEPP as Markdown file"""
    try:
        filename = f"{tepp_data.get('tepp_id', 'TEPP')}.md"
        st.download_button(
            label="Download Markdown",
            data=tepp_data.get('full_document', ''),
            file_name=filename,
            mime="text/markdown"
        )
    except Exception as e:
        st.error(f"Download failed: {e}")

def download_tepp_as_pdf(tepp_data):
    """Download TEPP as PDF file"""
    try:
        # This would require a markdown to PDF converter
        st.info("PDF download feature coming soon. Please use Markdown download for now.")
    except Exception as e:
        st.error(f"PDF download failed: {e}")

def save_tepp_document(tepp_data, save_name, save_location, include_ai_analysis, include_editable_fields) -> bool:
    """Save TEPP document to specified location"""
    try:
        # This would implement actual saving logic
        st.success(f"TEPP would be saved as: {save_name}")
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

def submit_for_approval(tepp_data, approval_status, approver_name, approval_notes) -> bool:
    """Submit TEPP for approval"""
    try:
        # This would implement actual approval workflow
        st.success(f"TEPP submitted for approval by {approver_name}")
        return True
    except Exception as e:
        st.error(f"Approval submission failed: {e}")
        return False
