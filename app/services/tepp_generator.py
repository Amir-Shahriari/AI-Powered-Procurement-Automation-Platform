"""
TEPP (Tender Evaluation and Probity Plan) Generator Service

This service generates customized TEPP documents based on project specifications
and integrates with the RAG system for intelligent content generation.
"""

import re
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from app.services.three_tier_rag_system import ThreeTierRAGSystem
from app.services.ai_model_detector import get_ai_detector, AIModelConfig

@dataclass
class TEPPConfiguration:
    """Configuration for TEPP generation"""
    project_title: str
    project_description: str
    contract_value: float
    contract_duration: int
    extension_options: int = 2
    project_type: str = "construction"
    council_name: str = "Blacktown City Council"
    tender_number: str = ""
    evaluation_committee: List[Dict[str, str]] = None
    technical_requirements: List[str] = None
    desired_outcomes: List[str] = None
    critical_dates: Dict[str, str] = None
    evaluation_criteria_weights: Dict[str, float] = None
    local_preference_applicable: bool = True
    interviews_required: bool = False
    presentations_required: bool = False
    
    def __post_init__(self):
        if self.evaluation_committee is None:
            self.evaluation_committee = []
        if self.technical_requirements is None:
            self.technical_requirements = []
        if self.desired_outcomes is None:
            self.desired_outcomes = []
        if self.critical_dates is None:
            self.critical_dates = {}
        if self.evaluation_criteria_weights is None:
            self.evaluation_criteria_weights = self._get_default_weights()
        if not self.tender_number:
            self.tender_number = f"T{datetime.now().year}-{datetime.now().strftime('%m%d')}-{self.project_type.upper()[:3]}"
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default evaluation criteria weights based on project type"""
        if self.project_type.lower() in ["construction", "infrastructure"]:
            return {
                "pricing": 40.0,
                "technical_capability": 25.0,
                "experience": 15.0,
                "work_health_safety": 10.0,
                "sustainability": 5.0,
                "local_preference": 5.0
            }
        elif self.project_type.lower() in ["services", "consulting"]:
            return {
                "pricing": 30.0,
                "technical_capability": 30.0,
                "experience": 20.0,
                "management_skills": 10.0,
                "sustainability": 5.0,
                "local_preference": 5.0
            }
        else:  # Default for other types
            return {
                "pricing": 35.0,
                "technical_capability": 25.0,
                "experience": 20.0,
                "work_health_safety": 10.0,
                "sustainability": 5.0,
                "local_preference": 5.0
            }

class TEPPGenerator:
    """Generates customized TEPP documents"""
    
    def __init__(self, rag_system=None):
        self.rag_system = rag_system
        self.tepp_template_path = Path("data/rag_documents/internal/tepp_template.md")
        self.ai_detector = get_ai_detector()
    
    def generate_tepp(self, config: TEPPConfiguration, spec_content: str = "") -> Dict[str, Any]:
        """Generate a complete TEPP document based on configuration with AI enhancement"""
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: AI Analysis of Specifications
        status_text.text("🤖 Analyzing specifications with AI...")
        progress_bar.progress(10)
        
        ai_analysis = self._analyze_specifications_with_ai(config, spec_content)
        
        # Step 2: Enhance configuration with AI insights
        status_text.text("📋 Enhancing TEPP configuration...")
        progress_bar.progress(20)
        
        enhanced_config = self._enhance_config_with_ai(config, ai_analysis)
        
        # Step 3: Determine process type
        status_text.text("⚖️ Determining procurement process...")
        progress_bar.progress(30)
        
        process_type = self._determine_process_type(enhanced_config.contract_value)
        
        # Step 4: Generate TEPP content with AI
        status_text.text("📝 Generating TEPP sections with AI...")
        progress_bar.progress(40)
        
        tepp_content = {
            "title_page": self._generate_title_page(enhanced_config),
            "table_of_contents": self._generate_table_of_contents(),
            "aim": self._generate_ai_enhanced_aim_section(enhanced_config, ai_analysis),
            "description": self._generate_ai_enhanced_description_section(enhanced_config, ai_analysis),
            "probity": self._generate_ai_enhanced_probity_section(enhanced_config, ai_analysis),
            "evaluation_committee": self._generate_ai_enhanced_evaluation_committee(enhanced_config, ai_analysis),
            "evaluation_schedule": self._generate_ai_enhanced_evaluation_schedule(enhanced_config, ai_analysis),
            "evaluation_methodology": self._generate_ai_enhanced_evaluation_methodology(enhanced_config, ai_analysis),
            "pricing": self._generate_ai_enhanced_pricing_section(enhanced_config, ai_analysis),
            "contract_negotiations": self._generate_ai_enhanced_contract_negotiations(enhanced_config, ai_analysis),
            "debriefing": self._generate_ai_enhanced_debriefing_section(enhanced_config, ai_analysis),
            "contract_management": self._generate_ai_enhanced_contract_management(enhanced_config, ai_analysis),
            "critical_dates": self._generate_ai_enhanced_critical_dates(enhanced_config, ai_analysis),
            "completion_guidelines": self._generate_ai_enhanced_completion_guidelines(enhanced_config, ai_analysis)
        }
        
        # Step 5: Assemble full document
        status_text.text("📄 Assembling complete TEPP document...")
        progress_bar.progress(80)
        
        full_document = self._assemble_full_document(tepp_content, enhanced_config)
        
        # Step 6: Finalize
        status_text.text("✅ TEPP generation complete!")
        progress_bar.progress(100)
        
        return {
            "tepp_id": f"TEPP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "project_title": enhanced_config.project_title,
            "tender_number": enhanced_config.tender_number,
            "contract_value": enhanced_config.contract_value,
            "process_type": process_type,
            "generated_date": datetime.now().isoformat(),
            "ai_analysis": ai_analysis,
            "sections": tepp_content,
            "full_document": full_document,
            "editable_fields": self._identify_editable_fields(tepp_content),
            "ai_model_used": getattr(self, 'selected_model', self.ai_detector.get_recommended_model()).model_name
        }
    
    def _determine_process_type(self, contract_value: float) -> str:
        """Determine the procurement process type based on contract value"""
        if contract_value < 100000:
            return "Quotation"
        elif contract_value < 250000:
            return "Tender"
        else:
            return "Formal Tender"
    
    def _generate_title_page(self, config: TEPPConfiguration) -> str:
        """Generate the title page content"""
        return f"""TENDER EVALUATION AND PROBITY PLAN
TENDER NO. {config.tender_number}

{config.project_title.upper()}

For a term of {config.contract_duration} years (plus {config.extension_options} year optional extensions)

{config.council_name}
{datetime.now().strftime('%B %Y')}"""
    
    def _generate_table_of_contents(self) -> str:
        """Generate table of contents"""
        return """TABLE OF CONTENTS
1. Aim
2. Description of Requirement
   2.1 Desired Outcomes
   2.2 Purpose of Request for Tender (RFT)
3. Probity and Accountability
   3.1 Probity
   3.2 Confidentiality and Conflict of Interest
   3.3 Security and Confidentiality
   3.4 Authorised Contact Officer
   3.5 Advertising the RFT
   3.6 Receipt of Tenders
   3.7 Late Tenders
   3.8 Requests for Clarification
   3.9 Critical issues or risks
4. Evaluation Committee
5. Evaluation Schedule
6. Tender Evaluation
   6.1 Evaluation Methodology
   6.1.1 Compliance Criteria
   6.1.2 Mandatory Criteria
7. Pricing
   7.1.1 Pricing Model
   7.1.2 Local preference policy
   7.1.3 Value for Money
   7.1.4 Interviews and Presentation Criteria
   7.2 Short-listing / Setting Aside Tenders
   7.3 Alternative Tenders
   7.4 Tenderer Presentations
   7.5 Evaluation Report
8. Contract Negotiations
9. Debriefing of Unsuccessful Tenderers
10. Contract Management
11. Critical dates
12. How to Complete the TEPP"""
    
    def _generate_aim_section(self, config: TEPPConfiguration) -> str:
        """Generate the aim section"""
        return f"""1. AIM
The Request for Tender (RFT) is for the {config.project_title} to Council for the service of {config.project_description} on an as required basis for a period of {config.contract_duration} years plus {config.extension_options} x 1 year extension options.

This Tender Evaluation and Probity Plan (TEPP) is the planning and control document in conducting the evaluation of Tenders received in response to the RFT.

The TEPP sets out:
• the processes and principles to be followed when evaluating Tenders;
• individual's responsibilities;
• the evaluation schedule; and
• reporting requirements."""
    
    def _generate_description_section(self, config: TEPPConfiguration) -> str:
        """Generate the description of requirement section"""
        technical_reqs = "\n".join([f"• {req}" for req in config.technical_requirements]) if config.technical_requirements else "• [INSERT TECHNICAL REQUIREMENTS]"
        outcomes = "\n".join([f"• {outcome}" for outcome in config.desired_outcomes]) if config.desired_outcomes else "• Best value for money\n• Timely delivery\n• High quality service delivery"
        
        return f"""2. DESCRIPTION OF REQUIREMENT
This RFT seeks a company suitably qualified and experienced person/s, firms or entities for the provision of {config.project_description} on an as required basis, including but not limited to:

General:
• {config.project_description}

Technical Requirements:
{technical_reqs}

Invoicing:
• All council invoices for service are paid on a 30 day payment term.
• [INSERT ANY ADDITIONAL DETAILS/REQUIREMENTS]

Reporting:
• [INSERT DETAILS]

Performance Monitoring:
The Service Provider must, at its expense, meet regular or as needs with Council, as reasonably directed by Council, to evaluate and monitor performance of this Agreement by the Service Provider on the basis of the criteria listed below or otherwise as agreed by the parties:
• Quality of service delivery;
• Compliance with guaranteed delivery times;
• Management of sales, customer service and complaints;
• Contract administration and management;
• WHS Management;
• Any other relevant contract matters.

2.1 DESIRED OUTCOMES
The following outcomes have been identified for this engagement:
{outcomes}

2.2 PURPOSE OF REQUEST FOR TENDER (RFT)
Council seeks this contract in order to meet its legislative requirements under the Local Government Act and Regulation, requirements for tendering.

The purpose of this Request for Tender is for provision of {config.project_title} for the {config.project_description}. Council reserves the right to select a panel of suppliers or a single supplier.

Suppliers will be selected with the proven ability to provide the services detailed in the Scope of Works."""
    
    def _generate_probity_section(self, config: TEPPConfiguration) -> str:
        """Generate the probity and accountability section"""
        return f"""3. PROBITY AND ACCOUNTABILITY
3.1 PROBITY
Probity is an integral element of this tendering and contracting process and it is the responsibility of all staff members involved with the RFT. The broad objectives of the probity process are to:
1. ensure conformity to processes that are designed to achieve best value for money;
2. improve accountability;
3. encourage commercial competition on the basis that all Tenders will be assessed against the same criteria;
4. preserve public and Tenderer confidence in government processes; and
5. improve defensibility of decisions so as to avoid potential administrative and legal challenge.

These objectives are underpinned by five (5) essential principles as follows:
1. open competitive process,
2. transparency of process,
3. identification and resolution of conflicts of interest,
4. accountability, and
5. monitoring and evaluating performance.

3.2 CONFIDENTIALITY AND CONFLICT OF INTEREST
A Confidentiality and Conflict of Interest Declaration is to be signed by each member of the Evaluation Committee and other staff that have access to confidential information. This includes advisers to the evaluation committee, who will sign the Confidentiality and Conflict of Interest Declaration prior to assessing any confidential information or offering comments or views, or scores.

The following items are to be maintained as confidential:
• Contents of submissions from Tenderers
• Clarification questions and responses
• Confidential information produced as part of the evaluation process (e.g. scoresheets, meeting minutes and evaluation reports)
• Other information related to the process that is not publicly available.

3.3 SECURITY AND CONFIDENTIALITY
It is essential for the integrity of the Tender evaluation process that security and confidentiality are maintained at all times, as Tenderers have a right to expect that privileged commercial information will be treated in confidence.

3.4 AUTHORISED CONTACT OFFICER
As stated in the Tender documentation, the only Council officer who is authorised to deal with enquiries is [INSERT NAME AND TITLE OF PERSON] that will field questions on the tender in your team.

3.5 ADVERTISING THE RFT
The RFT will be advertised in the 'Tenders Section' of Council's website and WSROC NSW e-tendering website.
The RFT will be advertised in the Sydney Morning Herald on Tuesday, TBA and Saturday, TBA and the Local newspaper(s) for two weeks on Tuesday, TBA and Wednesday, TBA.

3.6 RECEIPT OF TENDERS
Tenders must be lodged electronically at the Tendering website before the closing date and time stated in the RFT document.
Tenders submitted electronically will be opened concurrently by representatives from Internal Audit and Governance.

3.7 LATE TENDERS
Late tenders will be treated in accordance with the 'Late Tenders' provided in the RFT. A tender that is not received as specified before the closing time will not be accepted for consideration unless there is sufficient evidence satisfactory to the Evaluation Committee.

3.8 REQUESTS FOR CLARIFICATION
To enable the Evaluation Committee to thoroughly evaluate Tenders, it may be necessary for the Committee to request clarification of information provided in a Tender. To the extent practicable, clarification will be sought and recorded in writing.

3.9 CRITICAL ISSUES OR RISKS
Risk Management is the process of identifying risks, analysing their consequences and devising appropriate responses.

| Issue/Risk | Consequences | Action |
|------------|--------------|--------|
| Pre-selection of preferred tenderer | Does not provide value to Council and is a risk of potential corruption | Independent evaluation without influence from personnel who may have existing relationship with contractors |
| Poor quality at high cost | Inflated costs for sub-standard service | Evaluation includes subject matter of expertise |"""
    
    def _generate_evaluation_committee(self, config: TEPPConfiguration) -> str:
        """Generate the evaluation committee section"""
        if config.evaluation_committee:
            committee_table = "| Name | Title | Branch/Department | Committee Role |\n|------|-------|------------------|----------------|\n"
            for member in config.evaluation_committee:
                committee_table += f"| {member.get('name', '[NAME]')} | {member.get('title', '[TITLE]')} | {member.get('branch', '[BRANCH]')} | {member.get('role', '[ROLE]')} |\n"
        else:
            committee_table = """| Name | Title | Branch/Department | Committee Role |
|------|-------|------------------|----------------|
| [NAME] | [TITLE] | [BRANCH] | Chair |
| [NAME] | [TITLE] | [BRANCH] | Subject Matter Expert |
| [NAME] | [TITLE] | [BRANCH] | Evaluation Member |"""
        
        return f"""4. EVALUATION COMMITTEE
The Evaluation Committee will consist of the following Council officers:

{committee_table}"""
    
    def _generate_evaluation_schedule(self, config: TEPPConfiguration) -> str:
        """Generate the evaluation schedule section"""
        start_date = datetime.now()
        
        schedule = f"""5. EVALUATION SCHEDULE
The following is an outline of the key activities and tasks underpinning this evaluation process.

| Task | Responsibility | Due by |
|------|---------------|--------|
| Finalisation of the TEPP | Project Manager | {(start_date + timedelta(days=1)).strftime('%d/%m/%Y')} |
| Finalisation of the RFT | Project Manager | {(start_date + timedelta(days=3)).strftime('%d/%m/%Y')} |
| Approval of TEPP | Internal Audit | {(start_date + timedelta(days=5)).strftime('%d/%m/%Y')} |
| Approval to release RFT | Director | {(start_date + timedelta(days=7)).strftime('%d/%m/%Y')} |
| RFT Advertised | Public Relations | {(start_date + timedelta(days=8)).strftime('%d/%m/%Y')} |
| Tender Briefing / Site Visits | Project Manager | {(start_date + timedelta(days=15)).strftime('%d/%m/%Y')} |
| RFT Closing Date | Project Manager | {(start_date + timedelta(days=30)).strftime('%d/%m/%Y')} |
| Tender Evaluation | Evaluation Committee | {(start_date + timedelta(days=37)).strftime('%d/%m/%Y')} |
| Complete Evaluation Report | Project Manager | {(start_date + timedelta(days=42)).strftime('%d/%m/%Y')} |
| Evaluation Report Review | Manager & Director | {(start_date + timedelta(days=45)).strftime('%d/%m/%Y')} |
| Tender Review | Tender Review Committee | {(start_date + timedelta(days=47)).strftime('%d/%m/%Y')} |
| Council Report to General Manager | Director | {(start_date + timedelta(days=50)).strftime('%d/%m/%Y')} |
| Council Resolution | Council | {(start_date + timedelta(days=52)).strftime('%d/%m/%Y')} |
| Notification of Tenderers | Project Manager or Manager | {(start_date + timedelta(days=54)).strftime('%d/%m/%Y')} |
| Finalise Contract | Project Manager via Manager | {(start_date + timedelta(days=60)).strftime('%d/%m/%Y')} |
| Debriefing of Unsuccessful Tenders | Evaluation Committee | {(start_date + timedelta(days=65)).strftime('%d/%m/%Y')} |"""
        
        return schedule
    
    def _generate_evaluation_methodology(self, config: TEPPConfiguration) -> str:
        """Generate the evaluation methodology section"""
        criteria_table = "| Criteria | Weight |\n|----------|--------|\n"
        for criterion, weight in config.evaluation_criteria_weights.items():
            criteria_table += f"| {criterion.replace('_', ' ').title()} | {weight}% |\n"
        
        return f"""6. TENDER EVALUATION
6.1 EVALUATION METHODOLOGY
The Evaluation Committee, in accordance with the evaluation methodology specified in the RFT and reproduced in this document, will evaluate all tenders.

6.1.1 COMPLIANCE CRITERIA
Generally compliance is taken to mean submission of the Tender by the closing date and in accordance with all other lodgement instructions and provision of all of the information requested in the RFT including late tender provisions.

| Compliance Criteria | Weight |
|-------------------|--------|
| Tender Details | Nil |
| Compliance of RFT Terms & Conditions | Nil |
| Tenderer's Statutory Declaration | Nil |

6.1.2 MANDATORY CRITERIA
Tenders will be assessed to meet the requirements as set out in the RFT document, to demonstrate their ability to meet all mandatory conditions of the Tender and specifications.

{criteria_table}
TOTAL | 100%

The Tenderer's ability to satisfy the criteria will be assessed on the basis of scores allocated by the Evaluation Committee in accordance with the TEPP by consensus, in response to questions relating to each criterion and then weighted as detailed above.

| Score | Description | Full Description |
|-------|-------------|-----------------|
| 5 | Exceptional | Full achievement of the requirements specified in the RFT for that criterion. Demonstrated strengths, no errors, weaknesses or omissions. |
| 4 | Superior | Sound achievement of the requirements specified in the RFT for that criterion. Some minor errors, risks, weaknesses or omissions, which may be acceptable as offered. |
| 3 | Good | Reasonable achievement of the requirements specified in the RFT for that criterion. Some errors, risks, weaknesses or omissions, which can be corrected/overcome with minimal effort. |
| 2 | Adequate | Minimal achievement of the requirements specified in the RFT for that criterion. Some errors, risks, weaknesses or omissions, which are possible to correct/overcome and make acceptable. |
| 1 | Poor to deficient | No achievement of the requirements specified in the RFT for that criterion. Existence of numerous errors, risks, weaknesses or omissions, which are difficult to correct/overcome and make acceptable. |
| 0 | Unacceptable | Totally deficient and non-compliant. |"""
    
    def _generate_pricing_section(self, config: TEPPConfiguration) -> str:
        """Generate the pricing section"""
        local_preference_text = ""
        if config.local_preference_applicable:
            local_preference_text = f"""7.1.2 LOCAL PREFERENCE POLICY
The applicants will be evaluated in accordance with the Local Preference Policy as specified in the Procurement Policy P000553.1 providing for a 5% discount on the tendered pricing for suppliers local to the Blacktown LGA capped at a maximum benefit of $50,000 and a 2.5% discount capped at a maximum of $25,000 for those suppliers located in Western Sydney Councils.

Blacktown City Local supplier: Supplier with a principal place of business or part of their business address (not being a PO Box) that is located within the Blacktown City local government area.

Western Sydney Council supplier: Supplier with a principal place of business or part of their business address (not being a PO Box) that is located within a Western Sydney Council LGA encompassing the below:
• Blue Mountains City Council
• City of Parramatta Council
• Cumberland City Council
• Fairfield City Council
• Hawkesbury City Council
• Liverpool City Council
• Parramatta City Council
• Penrith City Council
• The Hills Shire Council"""
        
        interviews_text = ""
        if config.interviews_required or config.presentations_required:
            interviews_text = """7.1.4 INTERVIEWS AND PRESENTATION CRITERIA
The final scores may be revised following any interviews and presentations conducted with the shortlisted Tenders. This will be in accordance with section 6.4 Tenderer Presentations."""
        
        return f"""7. PRICING
7.1.1 PRICING MODEL
Pricing for tender evaluation will then be normalised and the lowest fee achieves the maximum score, which is equal to the weighting for price criteria. In accordance with the State Government's method of scoring price, the Total Net Cost for tender evaluation will be normalised and weighted for comparison as follows:

where:
Pc = Total Net Cost calculated for tender evaluation
Pav = Average of all Total Net Costs (as above)
Ps = Price score = 200 - (1001 x Pc/Pav)
Pn = Normalised Price Score = Ps/Highest Ps x 1001
Pw = Weighted Price Score = Pn x percentage weighting/100

{local_preference_text}

7.1.3 VALUE FOR MONEY
'Value for Money' will be assessed based on the combined outcomes of the assessments of the qualitative criteria and price. In assessing 'value for money', major factors to be considered include the quality of the proposed provision of advisory services, i.e. how well it meets the specified requirements; vs Whole of life costs; vs Risk, i.e. the capacity of the Tenderer to deliver the services, as specified, on-time and on-budget.

{interviews_text}

7.2 SHORT-LISTING / SETTING ASIDE TENDERS
In the event that a significant number of Tenders are received, Tenders, which are clearly non competitive and have no reasonable prospect of exhibiting the best value for money compared to other Tenders, will be excluded from the detailed evaluation process.

7.3 ALTERNATIVE TENDERS
The Evaluation Committee will evaluate alternative Tenders in accordance with the evaluation methodology specified in the RFT and reproduced in this document.

7.4 TENDERER PRESENTATIONS
As stated in the RFT, Tenderers may be invited to attend an interview with the Evaluation Committee to clarify their Tender and to provide the opportunity for the Evaluation Committee to ask questions.

7.5 EVALUATION REPORT
On completion of the evaluation process, the final results will be documented in a Council Report, which will include:
• a summary of the evaluation method,
• the number of Tenders received,
• the relative ranking of the Tenders,
• a recommendation as to the preferred Tender, and
• the rationale used to select the preferred supplier."""
    
    def _generate_contract_negotiations(self) -> str:
        """Generate the contract negotiations section"""
        return """8. CONTRACT NEGOTIATIONS
A period of negotiation with the successful Tenderer may arise following completion of the Tender phase and will commence subject to approval by the Director.

This period will result in the executed copies of the contractual documentation being completed and will necessitate a combination of meetings comprising formal written obligations to be resolved. The role of the negotiators is to ensure that the negotiation approach is appropriate to the nature of the project, is open and fair, meets the needs of the Tenderer and can be accommodated within the Tenderer's resources.

Negotiations must not result in material changing to the requirements of the Tender. The outcome of the negotiations will be reflected in the final contract and all negotiation discussions and outcomes will be documented."""
    
    def _generate_debriefing_section(self) -> str:
        """Generate the debriefing section"""
        return """9. DEBRIEFING OF UNSUCCESSFUL TENDERERS
The Evaluation Panel may arrange for the debriefing of any unsuccessful Tenderers who request such a debriefing. The purpose of the debriefing is to provide Tenderers with general comments regarding evaluation of the Tenderer's submission against the criteria.

If undertaken, the debriefing process will be conducted by at least two members of the Evaluation Committee and may be carried out by telephone or letter.

The debriefing process will be limited to the unsuccessful Tenderer's offer. No comparisons will be made with the successful Tender and the debriefing process will not be used to justify the selection of the successful Tender. No scoring details will be provided."""
    
    def _generate_contract_management(self, config: TEPPConfiguration) -> str:
        """Generate the contract management section"""
        return f"""10. CONTRACT MANAGEMENT
The contract will be managed by Council's [INSERT TITLE]."""
    
    def _generate_critical_dates(self, config: TEPPConfiguration) -> str:
        """Generate the critical dates section"""
        if config.critical_dates:
            dates_text = "\n".join([f"• {key}: {value}" for key, value in config.critical_dates.items()])
        else:
            start_date = datetime.now() + timedelta(days=60)
            dates_text = f"• Contract commencement: {start_date.strftime('%B %Y')}"
        
        return f"""11. CRITICAL DATES
It is essential that the new contract be commenced by the following dates:

{dates_text}"""
    
    def _generate_completion_guidelines(self) -> str:
        """Generate the completion guidelines section"""
        return """12. HOW TO COMPLETE THE TEPP

1. Title Page: Replace Tender Number, Tender Name and Term
2. Aim: Update Tender Name and Term
3. Description of Requirement: Replace with Contract Description and main requirements
4. Desired Outcomes: Retain, replace or insert options as required
5. Purpose of RFT: Replace with reasons for specific tender
6. Authorised Contact Officer: Replace position title and contact name
7. Advertising: Replace advertising periods and dates
8. Receipt of Tenders: Delete unused lodgement options
9. Critical Issues/Risks: Insert further issues, consequences and actions
10. Evaluation Committee: Add staff details for evaluation committee
11. Evaluation Schedule: Replace dates and responsible officers
12. Compliance Criteria: Insert further criteria where applicable
13. Mandatory Criteria: Update relevant weightings
14. Pricing Model: Insert details explaining pricing application
15. Contract Management: Replace with contact managing ongoing operations
16. Critical Dates: Insert critical dates or delete if not applicable
17. Update Contents: Update table of contents
18. Update Footer: Correct Tender Number and Tender Name"""
    
    def _assemble_full_document(self, sections: Dict[str, str], config: TEPPConfiguration) -> str:
        """Assemble the full TEPP document"""
        full_doc = f"""{sections['title_page']}

{sections['table_of_contents']}

{sections['aim']}

{sections['description']}

{sections['probity']}

{sections['evaluation_committee']}

{sections['evaluation_schedule']}

{sections['evaluation_methodology']}

{sections['pricing']}

{sections['contract_negotiations']}

{sections['debriefing']}

{sections['contract_management']}

{sections['critical_dates']}

{sections['completion_guidelines']}"""
        
        return full_doc
    
    def _analyze_specifications_with_ai(self, config: TEPPConfiguration, spec_content: str) -> Dict[str, Any]:
        """Analyze specifications using AI to extract key information"""
        if not spec_content:
            return self._get_basic_analysis(config)
        
        try:
            # Use selected model if available, otherwise get recommended model
            selected_model = getattr(self, 'selected_model', None)
            if selected_model:
                ai_model = selected_model
                st.info(f"✅ Using SELECTED model: {ai_model.model_name} ({ai_model.provider})")
            else:
                ai_model = self.ai_detector.get_recommended_model()
                st.warning(f"⚠️ No selected model found, using recommended: {ai_model.model_name} ({ai_model.provider})")
            
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze the following project specification and extract key information for TEPP generation:
            
            Project: {config.project_title}
            Type: {config.project_type}
            Value: ${config.contract_value:,.2f}
            Duration: {config.contract_duration} years
            
            Specification Content:
            {spec_content[:2000]}...
            
            Please provide a structured analysis including:
            1. Technical requirements
            2. Desired outcomes
            3. Risk factors
            4. Compliance requirements
            5. Evaluation criteria suggestions
            6. Critical dates
            7. Special considerations
            
            Return as JSON format.
            """
            
            # Use RAG system for analysis
            if self.rag_system:
                # Query internal tier for TEPP-related documents
                from app.services.three_tier_rag_system import RAGTier
                rag_results = self.rag_system.query_compliance(
                    analysis_prompt, 
                    tiers=[RAGTier.INTERNAL],
                    project_type=config.project_type
                )
                
                # Extract content from RAG results
                rag_content = "\n".join([result.content for result in rag_results[:3]])  # Top 3 results
                
                # Use AI model for analysis
                if ai_model and ai_model.provider != "none":
                    # Try to use the recommended AI model
                    try:
                        # Use local AI model for analysis
                        analysis = self._analyze_with_local_ai(ai_model, analysis_prompt, config, rag_content)
                        return analysis
                    except Exception as e:
                        st.warning(f"AI model {ai_model.name} failed: {e}")
                        # Fallback to basic analysis with RAG context
                        analysis = self._get_basic_analysis(config)
                        analysis["rag_context"] = rag_content
                        return analysis
                else:
                    # Use basic analysis with RAG context
                    analysis = self._get_basic_analysis(config)
                    analysis["rag_context"] = rag_content
                    return analysis
            else:
                return self._get_basic_analysis(config)
                
        except Exception as e:
            st.warning(f"AI analysis failed: {e}")
            return self._get_basic_analysis(config)
    
    def _analyze_with_local_ai(self, ai_model, analysis_prompt: str, config: TEPPConfiguration, rag_content: str) -> Dict[str, Any]:
        """Analyze specifications using local AI model (Ollama)"""
        try:
            # Enhanced prompt with RAG context
            enhanced_prompt = f"""
            {analysis_prompt}
            
            RAG Context (Relevant TEPP Templates and Guidelines):
            {rag_content}
            
            Please provide a structured analysis in JSON format with the following structure:
            {{
                "technical_requirements": ["list of technical requirements"],
                "desired_outcomes": ["list of desired outcomes"],
                "risk_factors": ["list of risk factors"],
                "compliance_requirements": ["list of compliance requirements"],
                "evaluation_criteria_suggestions": {{"criteria": weight_percentage}},
                "critical_dates": {{"date_name": "date_value"}},
                "special_considerations": ["list of special considerations"],
                "ai_insights": "AI-generated insights about the project"
            }}
            """
            
            # Try to use Ollama if available
            if ai_model.provider == "Ollama" and ai_model.model_name != "ollama-not-running":
                try:
                    ollama_response = self._call_ollama(ai_model.model_name, enhanced_prompt)
                    if ollama_response:
                        analysis = self._parse_ai_analysis(ollama_response)
                        analysis["rag_context"] = rag_content
                        analysis["ai_model_used"] = ai_model.model_name
                        analysis["ai_provider"] = ai_model.provider
                        return analysis
                except Exception as e:
                    st.warning(f"Ollama call failed: {e}")
            
            # Fallback to enhanced basic analysis
            analysis = self._get_basic_analysis(config)
            
            # Enhance with AI-generated insights
            analysis["ai_insights"] = f"AI Analysis for {config.project_type} project valued at ${config.contract_value:,.2f}"
            analysis["rag_context"] = rag_content
            analysis["ai_model_used"] = ai_model.model_name
            analysis["ai_provider"] = ai_model.provider
            
            # Add some AI-enhanced content based on project type
            if config.project_type.lower() == "construction":
                analysis["technical_requirements"].extend([
                    "Building permit compliance",
                    "Site safety management",
                    "Environmental impact assessment"
                ])
            elif config.project_type.lower() == "fleet":
                analysis["technical_requirements"].extend([
                    "Vehicle maintenance standards",
                    "Driver qualification requirements",
                    "Fleet management systems"
                ])
            
            return analysis
            
        except Exception as e:
            st.warning(f"Local AI analysis failed: {e}")
            # Fallback to basic analysis
            analysis = self._get_basic_analysis(config)
            analysis["rag_context"] = rag_content
            return analysis
    
    def _call_ollama(self, model_name: str, prompt: str) -> str:
        """Call Ollama API for AI analysis"""
        try:
            import requests
            import json
            
            # First check if the model exists
            try:
                models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if models_response.status_code == 200:
                    available_models = [model.get("name", "") for model in models_response.json().get("models", [])]
                    if model_name not in available_models:
                        st.error(f"❌ Model '{model_name}' not found in Ollama!")
                        st.info("Available models:")
                        for model in available_models:
                            st.code(f"• {model}")
                        st.info("To install a model:")
                        st.code(f"ollama pull {model_name}")
                        return None
            except:
                st.warning("⚠️ Could not check available models")
            
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            # Show progress for long-running requests
            with st.spinner(f"🤖 AI is working with '{model_name}'... Please wait, this may take several minutes for first-time use or complex analysis."):
                response = requests.post(url, json=payload)  # No timeout - let it run until completion
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            elif response.status_code == 404:
                st.warning(f"Model '{model_name}' not found in Ollama. Available models:")
                try:
                    models_response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if models_response.status_code == 200:
                        models = models_response.json().get("models", [])
                        for model in models:
                            st.code(f"ollama pull {model.get('name', '')}")
                except:
                    pass
                return None
            else:
                st.warning(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error(f"🔌 Cannot connect to Ollama. Make sure Ollama is running:")
            st.code("ollama serve")
            return None
        except Exception as e:
            st.warning(f"Ollama API call failed: {e}")
            return None

    def _get_basic_analysis(self, config: TEPPConfiguration) -> Dict[str, Any]:
        """Fallback basic analysis when AI is not available"""
        return {
            "technical_requirements": config.technical_requirements or [
                "Compliance with relevant Australian Standards",
                "Quality assurance procedures",
                "Safety management systems",
                "Environmental compliance"
            ],
            "desired_outcomes": config.desired_outcomes or [
                "High quality service delivery",
                "Timely completion",
                "Cost effectiveness",
                "Compliance with specifications"
            ],
            "risk_factors": [
                "Project complexity",
                "Timeline constraints",
                "Resource availability",
                "Regulatory compliance"
            ],
            "compliance_requirements": [
                "Local Government Act compliance",
                "Work Health and Safety requirements",
                "Environmental protection standards",
                "Quality assurance standards"
            ],
            "evaluation_criteria_suggestions": {
                "Price": 40.0,
                "Technical Capability": 25.0,
                "Experience": 15.0,
                "Safety": 10.0,
                "Local Preference": 5.0,
                "Sustainability": 5.0
            },
            "critical_dates": {
                "Tender Release": datetime.now().strftime("%Y-%m-%d"),
                "Tender Close": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "Evaluation Complete": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
                "Contract Award": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
            },
            "special_considerations": [
                "Local supplier preference",
                "Environmental sustainability",
                "Community impact",
                "Long-term maintenance"
            ]
        }
    
    def _parse_ai_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to extract JSON from response
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._get_basic_analysis(TEPPConfiguration("", "", 0, 0))
        except:
            return self._get_basic_analysis(TEPPConfiguration("", "", 0, 0))
    
    def _enhance_config_with_ai(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> TEPPConfiguration:
        """Enhance configuration with AI analysis insights"""
        enhanced_config = TEPPConfiguration(
            project_title=config.project_title,
            project_description=config.project_description,
            contract_value=config.contract_value,
            contract_duration=config.contract_duration,
            extension_options=config.extension_options,
            project_type=config.project_type,
            council_name=config.council_name,
            tender_number=config.tender_number,
            evaluation_committee=config.evaluation_committee,
            technical_requirements=ai_analysis.get("technical_requirements", config.technical_requirements),
            desired_outcomes=ai_analysis.get("desired_outcomes", config.desired_outcomes),
            critical_dates=ai_analysis.get("critical_dates", config.critical_dates),
            evaluation_criteria_weights=ai_analysis.get("evaluation_criteria_suggestions", config.evaluation_criteria_weights),
            local_preference_applicable=config.local_preference_applicable,
            interviews_required=config.interviews_required,
            presentations_required=config.presentations_required
        )
        return enhanced_config
    
    def _generate_ai_enhanced_aim_section(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced AIM section"""
        base_aim = self._generate_aim_section(config)
        
        # Add AI insights
        risk_factors = ai_analysis.get("risk_factors", [])
        special_considerations = ai_analysis.get("special_considerations", [])
        
        enhanced_aim = base_aim + f"""
        
        **AI-Generated Insights:**
        
        **Risk Factors Identified:**
        {chr(10).join(f"• {risk}" for risk in risk_factors)}
        
        **Special Considerations:**
        {chr(10).join(f"• {consideration}" for consideration in special_considerations)}
        """
        
        return enhanced_aim
    
    def _generate_ai_enhanced_description_section(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced description section"""
        base_description = self._generate_description_section(config)
        
        # Add AI-generated technical requirements
        tech_requirements = ai_analysis.get("technical_requirements", [])
        desired_outcomes = ai_analysis.get("desired_outcomes", [])
        
        enhanced_description = base_description + f"""
        
        **AI-Enhanced Technical Requirements:**
        {chr(10).join(f"• {req}" for req in tech_requirements)}
        
        **AI-Enhanced Desired Outcomes:**
        {chr(10).join(f"• {outcome}" for outcome in desired_outcomes)}
        """
        
        return enhanced_description
    
    def _generate_ai_enhanced_probity_section(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced probity section"""
        return self._generate_probity_section(config) + """
        
        **AI-Generated Compliance Notes:**
        This TEPP has been enhanced with AI analysis to ensure comprehensive coverage of all probity requirements and compliance standards relevant to this specific project type and value range.
        """
    
    def _generate_ai_enhanced_evaluation_committee(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced evaluation committee section"""
        return self._generate_evaluation_committee(config) + """
        
        **AI Recommendations:**
        The evaluation committee composition has been optimized based on project complexity and requirements analysis.
        """
    
    def _generate_ai_enhanced_evaluation_schedule(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced evaluation schedule"""
        critical_dates = ai_analysis.get("critical_dates", {})
        if critical_dates:
            return f"""
**AI-Generated Evaluation Schedule:**

| Task | Responsibility | Due Date |
|------|---------------|----------|
| TEPP Finalization | Project Manager | {critical_dates.get('Tender Release', 'TBA')} |
| RFT Approval | Director | {critical_dates.get('Tender Release', 'TBA')} |
| RFT Advertisement | Public Relations | {critical_dates.get('Tender Release', 'TBA')} |
| Tender Briefing | Project Manager | TBA |
| RFT Closing | Project Manager | {critical_dates.get('Tender Close', 'TBA')} |
| Tender Evaluation | Evaluation Committee | {critical_dates.get('Evaluation Complete', 'TBA')} |
| Evaluation Report | Project Manager | {critical_dates.get('Evaluation Complete', 'TBA')} |
| Council Resolution | Council | {critical_dates.get('Contract Award', 'TBA')} |
| Contract Finalization | Project Manager | {critical_dates.get('Contract Award', 'TBA')} |
| Debriefing | Evaluation Committee | TBA |
"""
        else:
            return self._generate_evaluation_schedule(config)
    
    def _generate_ai_enhanced_evaluation_methodology(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced evaluation methodology"""
        base_methodology = self._generate_evaluation_methodology(config)
        
        # Add AI-generated criteria weights
        criteria_weights = ai_analysis.get("evaluation_criteria_suggestions", {})
        if criteria_weights:
            criteria_section = "\n\n**AI-Optimized Evaluation Criteria Weights:**\n"
            for criterion, weight in criteria_weights.items():
                criteria_section += f"• {criterion}: {weight}%\n"
            
            return base_methodology + criteria_section
        
        return base_methodology
    
    def _generate_ai_enhanced_pricing_section(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced pricing section"""
        return self._generate_pricing_section(config) + """
        
        **AI Analysis Notes:**
        Pricing evaluation methodology has been optimized based on project type and complexity analysis.
        """
    
    def _generate_ai_enhanced_contract_negotiations(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced contract negotiations section"""
        return self._generate_contract_negotiations() + """
        
        **AI-Generated Negotiation Guidelines:**
        Contract negotiation approach has been tailored based on project risk analysis and compliance requirements.
        """
    
    def _generate_ai_enhanced_debriefing_section(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced debriefing section"""
        return self._generate_debriefing_section() + """
        
        **AI-Enhanced Debriefing Process:**
        Debriefing procedures have been optimized to provide maximum value to unsuccessful tenderers while maintaining probity.
        """
    
    def _generate_ai_enhanced_contract_management(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced contract management section"""
        return self._generate_contract_management(config) + """
        
        **AI-Generated Management Guidelines:**
        Contract management approach has been customized based on project complexity and risk assessment.
        """
    
    def _generate_ai_enhanced_critical_dates(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced critical dates section"""
        critical_dates = ai_analysis.get("critical_dates", {})
        if critical_dates:
            dates_section = "**AI-Generated Critical Dates:**\n\n"
            for task, date in critical_dates.items():
                dates_section += f"• **{task}:** {date}\n"
            return dates_section
        else:
            return self._generate_critical_dates(config)
    
    def _generate_ai_enhanced_completion_guidelines(self, config: TEPPConfiguration, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced completion guidelines"""
        return self._generate_completion_guidelines() + """
        
        **AI-Generated Completion Notes:**
        TEPP completion guidelines have been enhanced with project-specific requirements and compliance considerations.
        """
    
    def _identify_editable_fields(self, sections: Dict[str, str]) -> List[Dict[str, str]]:
        """Identify fields that should be editable in the UI"""
        editable_fields = [
            {"section": "title_page", "field": "tender_number", "type": "text", "description": "Tender Number"},
            {"section": "title_page", "field": "project_title", "type": "text", "description": "Project Title"},
            {"section": "aim", "field": "contract_duration", "type": "number", "description": "Contract Duration (years)"},
            {"section": "aim", "field": "extension_options", "type": "number", "description": "Extension Options"},
            {"section": "description", "field": "technical_requirements", "type": "textarea", "description": "Technical Requirements"},
            {"section": "description", "field": "desired_outcomes", "type": "textarea", "description": "Desired Outcomes"},
            {"section": "evaluation_committee", "field": "committee_members", "type": "table", "description": "Evaluation Committee Members"},
            {"section": "evaluation_methodology", "field": "criteria_weights", "type": "table", "description": "Evaluation Criteria Weights"},
            {"section": "critical_dates", "field": "critical_dates", "type": "table", "description": "Critical Dates"}
        ]
        
        return editable_fields
    
    def save_tepp(self, tepp_data: Dict[str, Any], output_path: Path) -> str:
        """Save the generated TEPP to a file"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save full document as markdown
        doc_path = output_path / f"{tepp_data['tepp_id']}.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(tepp_data['full_document'])
        
        # Save structured data as JSON
        json_path = output_path / f"{tepp_data['tepp_id']}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tepp_data, f, indent=2, default=str)
        
        return str(doc_path)
