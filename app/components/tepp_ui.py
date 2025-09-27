"""
TEPP (Tender Evaluation and Probity Plan) UI Component

This component provides the user interface for generating, editing, and managing
TEPP documents within the intelligent tender system.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from ..services.tepp_generator import TEPPGenerator, TEPPConfiguration
from ..services.project_manager import Project
from ..services.three_tier_rag_system import ThreeTierRAGSystem

def show_tepp_generator(selected_project: Project) -> Optional[Dict[str, Any]]:
    """Show the TEPP generator interface with AI-powered content analysis"""
    
    st.markdown("### 📋 TEPP Generation")
    st.markdown("Generate a comprehensive Tender Evaluation and Probity Plan based on your project specifications.")
    
    # Initialize TEPP generator
    tepp_generator = TEPPGenerator()
    
    # Create configuration from selected project
    config = create_tepp_config_from_project(selected_project)
    
    # Specification Input Section
    st.markdown("#### 📝 Project Specification Input")
    st.markdown("Provide your technical specification using one of the methods below. AI will analyze the content to generate appropriate TEPP details.")
    
    # Spec intake UI
    intake_mode = st.radio(
        "Choose input method:",
        ["Upload a file", "Paste raw text", "Write manually"],
        horizontal=True,
        disabled=False
    )

    uploaded_file = None
    pasted_text = None
    manual_text = None

    if intake_mode == "Upload a file":
        uploaded_file = st.file_uploader(
            "Upload Technical Specification",
            type=["pdf", "docx", "txt", "doc"],
            help="Upload your technical specification file. AI will extract key information to generate TEPP details."
        )
    elif intake_mode == "Paste raw text":
        pasted_text = st.text_area(
            "Technical specification",
            height=300,
            placeholder="Paste your technical specification text here. AI will analyze the content to generate appropriate TEPP details..."
        )
    else:  # Write manually
        manual_text = st.text_area(
            "Write specification manually",
            height=300,
            placeholder="Write your technical specification here. Be as detailed as possible for better AI analysis..."
        )

    # Get specification content
    spec_content = None
    if uploaded_file is not None:
        # For now, we'll use the file name as content - in a real implementation, you'd extract text
        spec_content = f"Uploaded file: {uploaded_file.name}"
    elif pasted_text and pasted_text.strip():
        spec_content = pasted_text.strip()
    elif manual_text and manual_text.strip():
        spec_content = manual_text.strip()

    # AI Analysis Section
    if spec_content:
        st.markdown("#### 🤖 AI Analysis")
        
        with st.spinner("AI is analyzing your specification..."):
            # AI-powered analysis of specification content
            ai_analysis = analyze_specification_with_ai(spec_content, config)
            
            # Display AI analysis results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 AI-Generated Project Details:**")
                st.info(f"""
                - **Suggested Title**: {ai_analysis['suggested_title']}
                - **Project Type**: {ai_analysis['project_type']}
                - **Complexity**: {ai_analysis['complexity_level']}
                - **Estimated Duration**: {ai_analysis['estimated_duration']} years
                """)
            
            with col2:
                st.markdown("**🎯 AI-Identified Key Requirements:**")
                for i, req in enumerate(ai_analysis['key_requirements'][:5], 1):
                    st.write(f"{i}. {req}")
                
                if len(ai_analysis['key_requirements']) > 5:
                    st.write(f"... and {len(ai_analysis['key_requirements']) - 5} more")
        
        # Update configuration with AI analysis
        config = update_config_with_ai_analysis(config, ai_analysis)
        
        # Show updated configuration
        with st.expander("⚙️ AI-Enhanced TEPP Configuration", expanded=True):
            config = show_tepp_configuration_form(config)
    
    else:
        # Show basic configuration if no specification provided
        with st.expander("⚙️ TEPP Configuration", expanded=True):
            config = show_tepp_configuration_form(config)

    # Generate TEPP button
    if st.button("🚀 Generate AI-Enhanced TEPP", type="primary", use_container_width=True, disabled=not spec_content):
        with st.spinner("Generating AI-enhanced TEPP document..."):
            try:
                tepp_data = tepp_generator.generate_tepp(config)
                
                # Add AI analysis metadata
                if spec_content:
                    tepp_data["ai_analysis"] = ai_analysis
                    tepp_data["specification_source"] = intake_mode
                    tepp_data["specification_content"] = spec_content[:500] + "..." if len(spec_content) > 500 else spec_content
                
                # Store in session state
                st.session_state["generated_tepp"] = tepp_data
                
                st.success("✅ AI-enhanced TEPP generated successfully!")
                return tepp_data
                
            except Exception as e:
                st.error(f"❌ Error generating TEPP: {str(e)}")
                return None
    
    return None

def create_tepp_config_from_project(project: Project) -> TEPPConfiguration:
    """Create TEPP configuration from selected project"""
    
    # Determine technical requirements based on project type
    technical_requirements = get_default_technical_requirements(project.category.value)
    
    # Determine desired outcomes based on project type
    desired_outcomes = get_default_desired_outcomes(project.category.value)
    
    # Set critical dates
    start_date = datetime.now() + timedelta(days=30)
    critical_dates = {
        "Contract commencement": start_date.strftime("%B %Y"),
        "Site access required": (start_date + timedelta(days=7)).strftime("%d/%m/%Y"),
        "Project completion": (start_date + timedelta(days=365)).strftime("%d/%m/%Y")
    }
    
    return TEPPConfiguration(
        project_title=project.title,
        project_description=project.description,
        contract_value=project.contract_value,
        contract_duration=2,  # Default 2 years
        extension_options=2,
        project_type=project.category.value,
        council_name=project.council,
        tender_number=f"T{datetime.now().year}-{datetime.now().strftime('%m%d')}-{project.category.value.upper()[:3]}",
        technical_requirements=technical_requirements,
        desired_outcomes=desired_outcomes,
        critical_dates=critical_dates,
        local_preference_applicable=True,
        interviews_required=project.contract_value > 500000,
        presentations_required=project.contract_value > 1000000
    )

def get_default_technical_requirements(project_type: str) -> List[str]:
    """Get default technical requirements based on project type"""
    
    requirements_map = {
        "construction": [
            "Compliance with Australian Building Codes and Standards",
            "WHS Management System certification",
            "Public Liability Insurance minimum $20M",
            "Professional Indemnity Insurance minimum $5M",
            "Relevant trade qualifications and licenses",
            "Environmental management plan",
            "Quality assurance procedures"
        ],
        "fleet": [
            "Vehicle compliance with Australian Design Rules",
            "Comprehensive insurance coverage",
            "Regular maintenance and servicing records",
            "Driver qualification requirements",
            "Fuel efficiency standards",
            "Safety equipment compliance",
            "GPS tracking and monitoring systems"
        ],
        "hvac": [
            "Refrigeration and Air Conditioning license",
            "Electrical license for HVAC work",
            "Compliance with Australian Standards AS/NZS 1668",
            "Energy efficiency ratings",
            "Maintenance and service agreements",
            "Warranty and support provisions",
            "Environmental compliance (refrigerant handling)"
        ],
        "services": [
            "Relevant professional qualifications",
            "Industry experience and references",
            "Quality management system",
            "Insurance coverage appropriate to service type",
            "Compliance with relevant regulations",
            "Performance monitoring and reporting",
            "Customer service standards"
        ],
        "it": [
            "Relevant IT certifications and qualifications",
            "Cybersecurity compliance",
            "Data protection and privacy measures",
            "System integration capabilities",
            "24/7 support and maintenance",
            "Backup and disaster recovery procedures",
            "Compliance with government IT standards"
        ],
        "consulting": [
            "Relevant professional qualifications",
            "Industry experience and track record",
            "Methodology and approach documentation",
            "Confidentiality and conflict of interest policies",
            "Professional indemnity insurance",
            "Quality assurance processes",
            "Deliverable specifications and timelines"
        ]
    }
    
    return requirements_map.get(project_type.lower(), requirements_map["services"])

def get_default_desired_outcomes(project_type: str) -> List[str]:
    """Get default desired outcomes based on project type"""
    
    outcomes_map = {
        "construction": [
            "High quality construction delivery",
            "Timely project completion",
            "Compliance with safety standards",
            "Environmental sustainability",
            "Cost-effective solutions",
            "Minimal disruption to community",
            "Long-term durability and maintenance"
        ],
        "fleet": [
            "Reliable vehicle performance",
            "Cost-effective fleet management",
            "Fuel efficiency and environmental compliance",
            "Minimal downtime and maintenance",
            "Driver safety and satisfaction",
            "Comprehensive service coverage",
            "Modern and well-maintained vehicles"
        ],
        "hvac": [
            "Optimal climate control",
            "Energy efficiency and cost savings",
            "Reliable system performance",
            "Minimal maintenance requirements",
            "Comfort and air quality",
            "Environmental compliance",
            "Long-term system reliability"
        ],
        "services": [
            "High quality service delivery",
            "Timely response and completion",
            "Cost-effective solutions",
            "Customer satisfaction",
            "Compliance with standards",
            "Continuous improvement",
            "Reliable and consistent service"
        ],
        "it": [
            "Secure and reliable IT systems",
            "Improved operational efficiency",
            "Data protection and privacy",
            "User-friendly interfaces",
            "Scalable and maintainable solutions",
            "24/7 system availability",
            "Future-proof technology"
        ],
        "consulting": [
            "Expert advice and recommendations",
            "Strategic insights and analysis",
            "Implementation support",
            "Knowledge transfer and training",
            "Measurable outcomes and results",
            "Independent and objective advice",
            "Value for money solutions"
        ]
    }
    
    return outcomes_map.get(project_type.lower(), outcomes_map["services"])

def show_tepp_configuration_form(config: TEPPConfiguration) -> TEPPConfiguration:
    """Show the TEPP configuration form"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        config.project_title = st.text_input(
            "Project Title",
            value=config.project_title,
            help="The official title of the project"
        )
        
        config.contract_duration = st.number_input(
            "Contract Duration (years)",
            min_value=1,
            max_value=10,
            value=config.contract_duration,
            help="Initial contract duration in years"
        )
        
        config.extension_options = st.number_input(
            "Extension Options",
            min_value=0,
            max_value=5,
            value=config.extension_options,
            help="Number of optional extension periods"
        )
        
        config.tender_number = st.text_input(
            "Tender Number",
            value=config.tender_number,
            help="Official tender reference number"
        )
    
    with col2:
        config.council_name = st.text_input(
            "Council/Organization",
            value=config.council_name,
            help="Name of the contracting organization"
        )
        
        config.local_preference_applicable = st.checkbox(
            "Apply Local Preference Policy",
            value=config.local_preference_applicable,
            help="Whether local preference discounts apply"
        )
        
        config.interviews_required = st.checkbox(
            "Interviews Required",
            value=config.interviews_required,
            help="Whether tenderer interviews are required"
        )
        
        config.presentations_required = st.checkbox(
            "Presentations Required",
            value=config.presentations_required,
            help="Whether tenderer presentations are required"
        )
    
    # Technical Requirements
    st.markdown("#### Technical Requirements")
    technical_requirements = st.text_area(
        "Technical Requirements (one per line)",
        value="\n".join(config.technical_requirements),
        height=150,
        help="List the technical requirements for this project"
    )
    config.technical_requirements = [req.strip() for req in technical_requirements.split("\n") if req.strip()]
    
    # Desired Outcomes
    st.markdown("#### Desired Outcomes")
    desired_outcomes = st.text_area(
        "Desired Outcomes (one per line)",
        value="\n".join(config.desired_outcomes),
        height=150,
        help="List the desired outcomes for this project"
    )
    config.desired_outcomes = [outcome.strip() for outcome in desired_outcomes.split("\n") if outcome.strip()]
    
    # Evaluation Criteria Weights
    st.markdown("#### Evaluation Criteria Weights")
    st.markdown("Adjust the weighting for each evaluation criterion (total must equal 100%):")
    
    criteria_weights = {}
    total_weight = 0
    
    col1, col2, col3 = st.columns(3)
    
    for i, (criterion, weight) in enumerate(config.evaluation_criteria_weights.items()):
        col = [col1, col2, col3][i % 3]
        with col:
            new_weight = st.number_input(
                criterion.replace("_", " ").title(),
                min_value=0.0,
                max_value=100.0,
                value=weight,
                step=1.0,
                key=f"weight_{criterion}"
            )
            criteria_weights[criterion] = new_weight
            total_weight += new_weight
    
    # Normalize weights if total doesn't equal 100%
    if total_weight != 100.0:
        if total_weight > 0:
            for criterion in criteria_weights:
                criteria_weights[criterion] = (criteria_weights[criterion] / total_weight) * 100
        else:
            # Reset to default if all weights are 0
            criteria_weights = config.evaluation_criteria_weights
    
    config.evaluation_criteria_weights = criteria_weights
    
    # Show total weight
    st.info(f"Total Weight: {sum(criteria_weights.values()):.1f}%")
    
    return config

def show_tepp_editor(tepp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Show the TEPP editor interface"""
    
    st.markdown("### ✏️ Edit TEPP Document")
    st.markdown("Review and edit the generated TEPP document before approval.")
    
    # Create tabs for different sections
    tabs = st.tabs([
        "📄 Overview",
        "📋 Description",
        "👥 Evaluation Committee",
        "📊 Evaluation Criteria",
        "💰 Pricing",
        "📅 Schedule",
        "📝 Full Document"
    ])
    
    with tabs[0]:  # Overview
        show_tepp_overview(tepp_data)
    
    with tabs[1]:  # Description
        show_tepp_description_editor(tepp_data)
    
    with tabs[2]:  # Evaluation Committee
        show_evaluation_committee_editor(tepp_data)
    
    with tabs[3]:  # Evaluation Criteria
        show_evaluation_criteria_editor(tepp_data)
    
    with tabs[4]:  # Pricing
        show_pricing_editor(tepp_data)
    
    with tabs[5]:  # Schedule
        show_schedule_editor(tepp_data)
    
    with tabs[6]:  # Full Document
        show_full_document_editor(tepp_data)
    
    # Save changes button
    if st.button("💾 Save Changes", type="primary"):
        st.session_state["generated_tepp"] = tepp_data
        st.success("✅ Changes saved successfully!")
    
    return tepp_data

def show_tepp_overview(tepp_data: Dict[str, Any]):
    """Show TEPP overview information"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("TEPP ID", tepp_data["tepp_id"])
    
    with col2:
        st.metric("Project", tepp_data["project_title"])
    
    with col3:
        st.metric("Contract Value", f"${tepp_data['contract_value']:,.0f}")
    
    with col4:
        st.metric("Process Type", tepp_data["process_type"])
    
    st.markdown("#### Document Information")
    st.info(f"""
    - **Generated**: {tepp_data['generated_date']}
    - **Tender Number**: {tepp_data['tender_number']}
    - **Status**: Draft
    - **Sections**: {len(tepp_data['sections'])} sections completed
    """)

def show_tepp_description_editor(tepp_data: Dict[str, Any]):
    """Show description section editor"""
    
    st.markdown("#### Project Description")
    
    # This would be implemented to edit the description section
    st.text_area(
        "Project Description",
        value=tepp_data["sections"]["description"],
        height=300,
        help="Edit the project description and requirements"
    )

def show_evaluation_committee_editor(tepp_data: Dict[str, Any]):
    """Show evaluation committee editor"""
    
    st.markdown("#### Evaluation Committee")
    
    # This would be implemented to edit the evaluation committee
    st.text_area(
        "Evaluation Committee",
        value=tepp_data["sections"]["evaluation_committee"],
        height=200,
        help="Edit the evaluation committee members"
    )

def show_evaluation_criteria_editor(tepp_data: Dict[str, Any]):
    """Show evaluation criteria editor"""
    
    st.markdown("#### Evaluation Criteria")
    
    # This would be implemented to edit the evaluation criteria
    st.text_area(
        "Evaluation Criteria",
        value=tepp_data["sections"]["evaluation_methodology"],
        height=300,
        help="Edit the evaluation criteria and weights"
    )

def show_pricing_editor(tepp_data: Dict[str, Any]):
    """Show pricing section editor"""
    
    st.markdown("#### Pricing Information")
    
    # This would be implemented to edit the pricing section
    st.text_area(
        "Pricing Model",
        value=tepp_data["sections"]["pricing"],
        height=300,
        help="Edit the pricing model and local preference policy"
    )

def show_schedule_editor(tepp_data: Dict[str, Any]):
    """Show schedule editor"""
    
    st.markdown("#### Evaluation Schedule")
    
    # This would be implemented to edit the schedule
    st.text_area(
        "Schedule",
        value=tepp_data["sections"]["evaluation_schedule"],
        height=300,
        help="Edit the evaluation schedule and critical dates"
    )

def show_full_document_editor(tepp_data: Dict[str, Any]):
    """Show full document editor"""
    
    st.markdown("#### Full TEPP Document")
    
    # Show the full document for editing
    edited_document = st.text_area(
        "TEPP Document",
        value=tepp_data["full_document"],
        height=600,
        help="Edit the complete TEPP document"
    )
    
    # Update the full document if changed
    if edited_document != tepp_data["full_document"]:
        tepp_data["full_document"] = edited_document

def show_tepp_approval(tepp_data: Dict[str, Any]) -> bool:
    """Show TEPP approval interface"""
    
    st.markdown("### ✅ TEPP Approval")
    st.markdown("Review the final TEPP document and approve for use.")
    
    # Show summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Document Summary")
        st.info(f"""
        - **TEPP ID**: {tepp_data['tepp_id']}
        - **Project**: {tepp_data['project_title']}
        - **Value**: ${tepp_data['contract_value']:,.0f}
        - **Process**: {tepp_data['process_type']}
        - **Generated**: {tepp_data['generated_date']}
        """)
    
    with col2:
        st.markdown("#### Approval Actions")
        
        if st.button("✅ Approve TEPP", type="primary"):
            tepp_data["status"] = "approved"
            tepp_data["approved_date"] = datetime.now().isoformat()
            st.session_state["generated_tepp"] = tepp_data
            st.success("✅ TEPP approved successfully!")
            return True
        
        if st.button("❌ Reject TEPP", type="secondary"):
            tepp_data["status"] = "rejected"
            st.session_state["generated_tepp"] = tepp_data
            st.error("❌ TEPP rejected. Please review and regenerate.")
            return False
    
    return False

def export_tepp(tepp_data: Dict[str, Any], format: str = "markdown") -> str:
    """Export TEPP in specified format"""
    
    if format == "markdown":
        return tepp_data["full_document"]
    elif format == "json":
        return json.dumps(tepp_data, indent=2, default=str)
    else:
        return tepp_data["full_document"]

def analyze_specification_with_ai(spec_content: str, config: TEPPConfiguration) -> Dict[str, Any]:
    """Analyze specification content using AI and RAG system"""
    
    try:
        # Initialize RAG system
        rag_system = ThreeTierRAGSystem(Path("data"))
        
        # Create analysis query
        analysis_query = f"""
        Analyze the following technical specification and provide detailed insights for TEPP generation:
        
        Specification Content:
        {spec_content}
        
        Current Project Context:
        - Project Type: {config.project_type}
        - Contract Value: ${config.contract_value:,.0f}
        - Council: {config.council_name}
        
        Please provide:
        1. A professional project title based on the specification
        2. Refined project type classification
        3. Complexity level assessment (Low/Medium/High)
        4. Estimated project duration in years
        5. Key technical requirements extracted from the specification
        6. Specific desired outcomes for this project
        7. Recommended evaluation criteria weights
        8. Risk factors and mitigation strategies
        9. Compliance requirements specific to this project
        10. Local preference applicability assessment
        """
        
        # Query the RAG system
        rag_response = rag_system.query(analysis_query, tier="internal")
        
        # Parse AI response and create structured analysis
        ai_analysis = parse_ai_analysis_response(rag_response, spec_content, config)
        
        return ai_analysis
        
    except Exception as e:
        # Fallback to basic analysis if RAG fails
        return create_basic_ai_analysis(spec_content, config)

def parse_ai_analysis_response(rag_response: str, spec_content: str, config: TEPPConfiguration) -> Dict[str, Any]:
    """Parse AI response into structured analysis"""
    
    # Extract information from RAG response
    lines = rag_response.split('\n')
    
    # Initialize analysis with defaults
    analysis = {
        "suggested_title": config.project_title,
        "project_type": config.project_type,
        "complexity_level": "Medium",
        "estimated_duration": config.contract_duration,
        "key_requirements": config.technical_requirements.copy(),
        "desired_outcomes": config.desired_outcomes.copy(),
        "evaluation_weights": config.evaluation_criteria_weights.copy(),
        "risk_factors": [],
        "compliance_requirements": [],
        "local_preference_applicable": config.local_preference_applicable,
        "ai_confidence": 0.8
    }
    
    # Parse AI response for specific information
    for line in lines:
        line = line.strip()
        
        if "title:" in line.lower() or "project title:" in line.lower():
            title = line.split(":", 1)[1].strip()
            if title and len(title) > 5:
                analysis["suggested_title"] = title
        
        elif "complexity:" in line.lower():
            complexity = line.split(":", 1)[1].strip().lower()
            if "high" in complexity:
                analysis["complexity_level"] = "High"
            elif "low" in complexity:
                analysis["complexity_level"] = "Low"
            else:
                analysis["complexity_level"] = "Medium"
        
        elif "duration:" in line.lower() or "years:" in line.lower():
            try:
                duration = float(line.split(":", 1)[1].strip().split()[0])
                if 0.5 <= duration <= 10:
                    analysis["estimated_duration"] = int(duration)
            except:
                pass
        
        elif "requirements:" in line.lower() or "requirement:" in line.lower():
            req = line.split(":", 1)[1].strip()
            if req and len(req) > 10:
                analysis["key_requirements"].append(req)
        
        elif "outcome:" in line.lower() or "outcomes:" in line.lower():
            outcome = line.split(":", 1)[1].strip()
            if outcome and len(outcome) > 10:
                analysis["desired_outcomes"].append(outcome)
    
    # Enhance requirements based on specification content
    analysis["key_requirements"].extend(extract_requirements_from_content(spec_content))
    analysis["desired_outcomes"].extend(extract_outcomes_from_content(spec_content))
    
    # Remove duplicates and limit length
    analysis["key_requirements"] = list(set(analysis["key_requirements"]))[:10]
    analysis["desired_outcomes"] = list(set(analysis["desired_outcomes"]))[:8]
    
    return analysis

def create_basic_ai_analysis(spec_content: str, config: TEPPConfiguration) -> Dict[str, Any]:
    """Create basic AI analysis when RAG system is not available"""
    
    # Extract key information from specification content
    content_lower = spec_content.lower()
    
    # Determine complexity based on content length and keywords
    complexity_keywords = ["complex", "sophisticated", "advanced", "technical", "specialized"]
    complexity_score = sum(1 for keyword in complexity_keywords if keyword in content_lower)
    
    if complexity_score >= 3:
        complexity_level = "High"
    elif complexity_score >= 1:
        complexity_level = "Medium"
    else:
        complexity_level = "Low"
    
    # Estimate duration based on content and project type
    if config.contract_value > 1000000:
        estimated_duration = 3
    elif config.contract_value > 500000:
        estimated_duration = 2
    else:
        estimated_duration = 1
    
    # Extract requirements from content
    requirements = extract_requirements_from_content(spec_content)
    outcomes = extract_outcomes_from_content(spec_content)
    
    return {
        "suggested_title": config.project_title,
        "project_type": config.project_type,
        "complexity_level": complexity_level,
        "estimated_duration": estimated_duration,
        "key_requirements": requirements[:10],
        "desired_outcomes": outcomes[:8],
        "evaluation_weights": config.evaluation_criteria_weights.copy(),
        "risk_factors": [],
        "compliance_requirements": [],
        "local_preference_applicable": config.local_preference_applicable,
        "ai_confidence": 0.6
    }

def extract_requirements_from_content(content: str) -> List[str]:
    """Extract technical requirements from specification content"""
    
    requirements = []
    content_lower = content.lower()
    
    # Common requirement patterns
    requirement_patterns = [
        "must", "shall", "required", "compliance", "standard", "certification",
        "insurance", "qualification", "license", "warranty", "guarantee"
    ]
    
    sentences = content.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if any(pattern in sentence.lower() for pattern in requirement_patterns):
            if len(sentence) > 20 and len(sentence) < 200:
                requirements.append(sentence)
    
    return requirements

def extract_outcomes_from_content(content: str) -> List[str]:
    """Extract desired outcomes from specification content"""
    
    outcomes = []
    content_lower = content.lower()
    
    # Common outcome patterns
    outcome_patterns = [
        "achieve", "deliver", "provide", "ensure", "maintain", "improve",
        "enhance", "optimize", "maximize", "minimize", "reduce", "increase"
    ]
    
    sentences = content.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if any(pattern in sentence.lower() for pattern in outcome_patterns):
            if len(sentence) > 20 and len(sentence) < 200:
                outcomes.append(sentence)
    
    return outcomes

def update_config_with_ai_analysis(config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> TEPPConfiguration:
    """Update TEPP configuration with AI analysis results"""
    
    # Update project title if AI suggested a better one
    if ai_analysis.get("suggested_title") and ai_analysis["suggested_title"] != config.project_title:
        config.project_title = ai_analysis["suggested_title"]
    
    # Update project type if AI suggested a different classification
    if ai_analysis.get("project_type") and ai_analysis["project_type"] != config.project_type:
        config.project_type = ai_analysis["project_type"]
    
    # Update duration if AI suggested different duration
    if ai_analysis.get("estimated_duration") and ai_analysis["estimated_duration"] != config.contract_duration:
        config.contract_duration = ai_analysis["estimated_duration"]
    
    # Update technical requirements with AI-extracted requirements
    if ai_analysis.get("key_requirements"):
        # Merge AI requirements with existing ones
        all_requirements = config.technical_requirements + ai_analysis["key_requirements"]
        config.technical_requirements = list(set(all_requirements))[:15]  # Limit to 15 requirements
    
    # Update desired outcomes with AI-extracted outcomes
    if ai_analysis.get("desired_outcomes"):
        # Merge AI outcomes with existing ones
        all_outcomes = config.desired_outcomes + ai_analysis["desired_outcomes"]
        config.desired_outcomes = list(set(all_outcomes))[:10]  # Limit to 10 outcomes
    
    # Update evaluation weights if AI suggested different weights
    if ai_analysis.get("evaluation_weights"):
        config.evaluation_criteria_weights = ai_analysis["evaluation_weights"]
    
    # Update local preference applicability
    if "local_preference_applicable" in ai_analysis:
        config.local_preference_applicable = ai_analysis["local_preference_applicable"]
    
    return config
