"""
Intelligent Tender Generation System
Integrates Blacktown RAG + Global RAG data for automated TEPP and Returnable Schedule creation
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.blacktown_rag_system import BlacktownRAGSystem
from app.services.unified_compliance_rag_system import UnifiedComplianceRAGSystem
from app.services.project_type_manager import ProjectType, ProcurementProcess, ProjectTypeManager
from app.services.smart_rag import SmartRAGSystem
from app.services.three_tier_rag_system import ThreeTierRAGSystem, RAGTier, DocumentCategory


class TenderType(Enum):
    QUOTATION = "quotation"
    TENDER = "tender"
    FORMAL_TENDER = "formal_tender"


class EvaluationMethod(Enum):
    MEAT = "meat"  # Most Economically Advantageous Tender
    LOWEST_PRICE = "lowest_price"
    TCO = "tco"  # Total Cost of Ownership
    QUALITY_COST_RATIO = "quality_cost_ratio"


@dataclass
class CriterionWeight:
    """Individual criterion with weight and justification"""
    name: str
    weight_percentage: float
    sub_criteria: List[Dict[str, Any]]
    justification: str
    source_document: str
    compliance_requirement: str


@dataclass
class TEPPData:
    """Tender Evaluation and Procurement Plan data"""
    project_title: str
    project_type: str
    contract_value_range: str
    tender_type: str
    evaluation_method: str
    criteria_weights: List[CriterionWeight]
    local_preference_applicable: bool
    social_procurement_required: bool
    compliance_requirements: List[str]
    evaluation_timeline: Dict[str, str]
    created_date: str
    version: str


@dataclass
class ReturnableScheduleItem:
    """Individual returnable schedule item"""
    item_number: str
    description: str
    required: bool
    format: str
    submission_deadline: str
    evaluation_weight: Optional[float]
    compliance_reference: str
    guidance_notes: str


@dataclass
class ReturnableSchedule:
    """Complete returnable schedule"""
    project_title: str
    tender_type: str
    items: List[ReturnableScheduleItem]
    general_instructions: List[str]
    submission_requirements: Dict[str, Any]
    created_date: str
    version: str


class IntelligentTenderGenerator:
    """
    Intelligent Tender Generator that uses RAG data to create comprehensive TEPP and Returnable Schedules
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.blacktown_rag = BlacktownRAGSystem(data_dir)
        self.global_rag = UnifiedComplianceRAGSystem(data_dir)
        self.smart_rag = SmartRAGSystem()
        self.three_tier_rag = ThreeTierRAGSystem(data_dir)
        self.project_manager = ProjectTypeManager(data_dir)
        
        # Initialize AI providers for content generation
        self._init_ai_providers()
    
    def _init_ai_providers(self):
        """Initialize AI providers for content generation"""
        try:
            from app.services.ai_providers import AIProviderManager
            self.ai_provider = AIProviderManager()
        except ImportError:
            self.ai_provider = None
    
    def generate_comprehensive_tender_package(
        self,
        project_title: str,
        project_type: ProjectType,
        contract_value: str,
        council_type: str = "Blacktown City Council",
        additional_requirements: Optional[Dict[str, Any]] = None,
        specification_file: Optional[Any] = None,
        specification_text: Optional[str] = None,
        specification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive tender package using RAG data
        """
        try:
            # Process specification input
            specification_content = ""
            if specification_type == "uploaded_file" and specification_file:
                # Extract text from uploaded file
                specification_content = self._extract_text_from_file(specification_file)
            elif specification_type == "manual_input" and specification_text:
                # Use manual text input
                specification_content = specification_text
            else:
                # Fallback to basic project analysis
                specification_content = f"Project: {project_title}, Type: {project_type.value}, Value: {contract_value}"
            
            # Step 1: Analyze project requirements using RAG data
            project_analysis = self._analyze_project_requirements(
                project_title, project_type, contract_value, council_type, specification_content
            )
            
            # Step 2: Determine procurement process and evaluation method
            procurement_config = self._determine_procurement_config(
                project_type, contract_value, project_analysis
            )
            
            # Step 3: Generate TEPP using RAG data
            tepp_data = self._generate_tepp(
                project_title, project_type, contract_value, 
                procurement_config, project_analysis
            )
            
            # Step 4: Generate Returnable Schedule
            returnable_schedule = self._generate_returnable_schedule(
                project_title, procurement_config, project_analysis
            )
            
            # Step 5: Generate compliance checklist
            compliance_checklist = self._generate_compliance_checklist(
                project_type, contract_value, council_type
            )
            
            # Step 6: Generate evaluation timeline
            evaluation_timeline = self._generate_evaluation_timeline(
                procurement_config, project_analysis
            )
            
            return {
                "project_analysis": project_analysis,
                "procurement_config": procurement_config,
                "tepp": tepp_data.__dict__,
                "returnable_schedule": returnable_schedule.__dict__,
                "compliance_checklist": compliance_checklist,
                "evaluation_timeline": evaluation_timeline,
                "generated_date": datetime.now().isoformat(),
                "version": "1.0"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate tender package: {str(e)}",
                "generated_date": datetime.now().isoformat()
            }
    
    def _extract_text_from_file(self, uploaded_file) -> str:
        """Extract text from uploaded file"""
        try:
            if uploaded_file.type == "text/plain":
                return str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type in ["application/pdf"]:
                # For PDF files, we'd need PyPDF2 or similar
                # For now, return a placeholder
                return f"[PDF file: {uploaded_file.name}] - Content extraction not implemented yet"
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                # For Word documents, we'd need python-docx
                # For now, return a placeholder
                return f"[Word document: {uploaded_file.name}] - Content extraction not implemented yet"
            else:
                return f"[File: {uploaded_file.name}] - Unsupported file type"
        except Exception as e:
            return f"[Error extracting text from {uploaded_file.name}: {str(e)}]"
    
    def _analyze_project_requirements(
        self, 
        project_title: str, 
        project_type: ProjectType, 
        contract_value: str,
        council_type: str,
        specification_content: str = ""
    ) -> Dict[str, Any]:
        """Analyze project requirements using RAG data"""
        
        # Get project type configuration
        project_config = self.project_manager.get_project_type_config(project_type)
        
        # Query RAG systems for relevant information
        rag_queries = [
            f"evaluation criteria for {project_type.value} projects",
            f"procurement requirements for {contract_value} contracts",
            f"compliance requirements for {council_type}",
            f"best practices for {project_type.value} tendering"
        ]
        
        # Add specification-specific queries if content is provided
        if specification_content and len(specification_content.strip()) > 50:
            rag_queries.extend([
                f"evaluation criteria for projects involving {specification_content[:100]}...",
                f"compliance requirements for {project_type.value} projects with technical specifications"
            ])
        
        rag_results = []
        for query in rag_queries:
            # Query Blacktown RAG
            blacktown_results = self.blacktown_rag.search_rag_documents(query)
            rag_results.extend(blacktown_results)
            
            # Query Global RAG
            try:
                from app.services.unified_compliance_rag_system import QueryType, ComplianceCategory
                global_result = self.global_rag.query_compliance(
                    QueryType.EVALUATION_CRITERIA,
                    ComplianceCategory.GLOBAL_NSW_STANDARDS,
                    {"query": query}
                )
                if global_result and global_result.result:
                    rag_results.append({
                        "title": f"Global Compliance: {query}",
                        "content": str(global_result.result),
                        "source": "Global NSW Standards",
                        "relevance_score": global_result.confidence_score
                    })
            except Exception as e:
                print(f"Warning: Could not query global RAG: {e}")
        
        # Analyze contract value to determine tender type
        value_numeric = self._parse_contract_value(contract_value)
        if value_numeric < 100000:
            tender_type = "quotation"
        elif value_numeric < 250000:
            tender_type = "tender"
        else:
            tender_type = "formal_tender"
        
        return {
            "project_type": project_type.value,
            "contract_value": contract_value,
            "contract_value_numeric": value_numeric,
            "tender_type": tender_type,
            "council_type": council_type,
            "project_config": project_config.__dict__ if project_config else {},
            "rag_insights": rag_results[:10],  # Top 10 most relevant results
            "compliance_requirements": project_config.compliance_requirements if project_config else [],
            "evaluation_criteria": project_config.evaluation_criteria if project_config else [],
            "specification_content": specification_content[:500] + "..." if len(specification_content) > 500 else specification_content
        }
    
    def _determine_procurement_config(
        self, 
        project_type: ProjectType, 
        contract_value: str,
        project_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine procurement configuration based on RAG data"""
        
        value_numeric = project_analysis["contract_value_numeric"]
        tender_type = project_analysis["tender_type"]
        
        # Get evaluation matrix from Blacktown RAG
        if value_numeric < 250000:
            matrix = self.blacktown_rag.get_evaluation_matrix(
                project_type.value, "$100,000 - $249,999"
            )
        else:
            matrix = self.blacktown_rag.get_evaluation_matrix(
                project_type.value, "$250,000+"
            )
        
        # Determine evaluation method based on project type and value
        if project_type in [ProjectType.CONSTRUCTION, ProjectType.IT_SERVICES]:
            evaluation_method = EvaluationMethod.MEAT
        elif value_numeric < 50000:
            evaluation_method = EvaluationMethod.LOWEST_PRICE
        else:
            evaluation_method = EvaluationMethod.TCO
        
        # Check if local preference applies
        local_preference_applicable = value_numeric >= 250000
        
        # Check if social procurement is required
        social_procurement_required = (
            value_numeric >= 100000 and 
            project_type in [ProjectType.CONSTRUCTION, ProjectType.SERVICES]
        )
        
        return {
            "tender_type": tender_type,
            "evaluation_method": evaluation_method.value,
            "evaluation_matrix": matrix,
            "local_preference_applicable": local_preference_applicable,
            "social_procurement_required": social_procurement_required,
            "procurement_process": self._get_procurement_process(tender_type),
            "timeline_days": self._get_timeline_days(tender_type, value_numeric)
        }
    
    def _generate_tepp(
        self,
        project_title: str,
        project_type: ProjectType,
        contract_value: str,
        procurement_config: Dict[str, Any],
        project_analysis: Dict[str, Any]
    ) -> TEPPData:
        """Generate TEPP using RAG data"""
        
        # Get evaluation criteria from RAG data
        criteria_weights = self._generate_criteria_weights(
            project_type, contract_value, procurement_config, project_analysis
        )
        
        # Generate compliance requirements
        compliance_requirements = self._generate_compliance_requirements(
            project_type, contract_value, project_analysis
        )
        
        # Generate evaluation timeline
        evaluation_timeline = self._generate_evaluation_timeline(
            procurement_config, project_analysis
        )
        
        return TEPPData(
            project_title=project_title,
            project_type=project_type.value,
            contract_value_range=contract_value,
            tender_type=procurement_config["tender_type"],  # Already a string
            evaluation_method=procurement_config["evaluation_method"],  # Already a string
            criteria_weights=criteria_weights,
            local_preference_applicable=procurement_config["local_preference_applicable"],
            social_procurement_required=procurement_config["social_procurement_required"],
            compliance_requirements=compliance_requirements,
            evaluation_timeline=evaluation_timeline,
            created_date=datetime.now().isoformat(),
            version="1.0"
        )
    
    def _generate_criteria_weights(
        self,
        project_type: ProjectType,
        contract_value: str,
        procurement_config: Dict[str, Any],
        project_analysis: Dict[str, Any]
    ) -> List[CriterionWeight]:
        """Generate criteria weights using RAG data"""
        
        criteria_weights = []
        value_numeric = project_analysis["contract_value_numeric"]
        
        # Get evaluation matrix from Blacktown RAG
        matrix = procurement_config.get("evaluation_matrix", {})
        
        # Define base criteria based on project type and value
        base_criteria = self._get_base_criteria(project_type, value_numeric)
        
        for criterion_name, weight_range in base_criteria.items():
            # Get specific weight from matrix or use range midpoint
            weight = self._get_criterion_weight(criterion_name, matrix, weight_range)
            
            # Generate sub-criteria
            sub_criteria = self._generate_sub_criteria(criterion_name, project_type)
            
            # Generate justification using RAG data
            justification = self._generate_criterion_justification(
                criterion_name, weight, project_type, contract_value
            )
            
            # Get compliance requirement
            compliance_req = self._get_compliance_requirement(criterion_name)
            
            criteria_weights.append(CriterionWeight(
                name=criterion_name,
                weight_percentage=weight,
                sub_criteria=sub_criteria,
                justification=justification,
                source_document="Blacktown City Council Tender & Quotation Evaluation Manual",
                compliance_requirement=compliance_req
            ))
        
        return criteria_weights
    
    def _generate_returnable_schedule(
        self,
        project_title: str,
        procurement_config: Dict[str, Any],
        project_analysis: Dict[str, Any]
    ) -> ReturnableSchedule:
        """Generate returnable schedule using RAG data"""
        
        tender_type_str = procurement_config["tender_type"]
        project_type = project_analysis["project_type"]
        
        # Get base returnable items from RAG data
        base_items = self._get_base_returnable_items(tender_type_str, project_type)
        
        # Generate project-specific items
        project_items = self._generate_project_specific_items(
            project_title, project_type, tender_type_str
        )
        
        # Combine and format items
        all_items = base_items + project_items
        
        # Generate general instructions
        general_instructions = self._generate_general_instructions(tender_type_str)
        
        # Generate submission requirements
        submission_requirements = self._generate_submission_requirements(tender_type_str)
        
        return ReturnableSchedule(
            project_title=project_title,
            tender_type=procurement_config["tender_type"],  # Use string value
            items=all_items,
            general_instructions=general_instructions,
            submission_requirements=submission_requirements,
            created_date=datetime.now().isoformat(),
            version="1.0"
        )
    
    def _parse_contract_value(self, contract_value: str) -> float:
        """Parse contract value string to numeric value"""
        try:
            # Remove common prefixes and suffixes
            value_str = contract_value.lower().replace("$", "").replace(",", "").replace("k", "000")
            
            if "under" in value_str:
                return 50000  # Default for "under $100k"
            elif "over" in value_str or "+" in value_str:
                return 1000000  # Default for "over $1M"
            else:
                # Extract numeric value
                import re
                numbers = re.findall(r'\d+', value_str)
                if numbers:
                    return float(numbers[0])
                return 100000  # Default
        except:
            return 100000  # Default fallback
    
    def _get_base_criteria(self, project_type: ProjectType, value_numeric: float) -> Dict[str, Tuple[float, float]]:
        """Get base criteria based on project type and value"""
        
        if value_numeric < 250000:
            # Quotation criteria
            if project_type == ProjectType.CONSTRUCTION:
                return {
                    "Price (Full Cost)": (40, 60),
                    "Relevant Experience": (10, 20),
                    "Capability": (5, 20),
                    "Quality Management": (2, 10),
                    "Management & Financial": (0, 10),
                    "WHS": (5, 10)
                }
            elif project_type == ProjectType.IT_SERVICES:
                return {
                    "Price (Full Cost)": (20, 50),
                    "Relevant Experience": (10, 30),
                    "Capability": (5, 30),
                    "Management & Financial": (0, 10),
                    "Quality Management": (2, 5),
                    "WHS": (2, 5)
                }
            else:  # General services
                return {
                    "Price (Full Cost)": (20, 50),
                    "Relevant Experience": (10, 40),
                    "Capability": (5, 30),
                    "Management & Financial": (0, 10),
                    "Quality Management": (2, 5),
                    "WHS": (2, 10)
                }
        else:
            # Tender criteria (higher value)
            if project_type == ProjectType.CONSTRUCTION:
                return {
                    "Price (Full Cost)": (35, 60),
                    "Relevant Experience": (10, 20),
                    "Capability": (5, 20),
                    "Management & Financial Capacity": (5, 15),
                    "Quality Management": (5, 10),
                    "WHS": (5, 10),
                    "Local Preference": (0, 0)  # Will be calculated separately
                }
            else:
                return {
                    "Price (Full Cost)": (25, 50),
                    "Relevant Experience": (10, 30),
                    "Capability": (10, 30),
                    "Management & Financial Capacity": (5, 10),
                    "WHS": (5, 10),
                    "Local Preference": (0, 0)  # Will be calculated separately
                }
    
    def _get_criterion_weight(self, criterion_name: str, matrix: Dict, weight_range: Tuple[float, float]) -> float:
        """Get specific weight for criterion from matrix or use range midpoint"""
        if matrix and criterion_name in matrix:
            return matrix[criterion_name]
        else:
            # Use midpoint of range
            return (weight_range[0] + weight_range[1]) / 2
    
    def _generate_sub_criteria(self, criterion_name: str, project_type: ProjectType) -> List[Dict[str, Any]]:
        """Generate sub-criteria for main criterion"""
        
        sub_criteria_map = {
            "Relevant Experience": [
                {"name": "General performance history", "weight": 40, "max_score": 5},
                {"name": "Experience with contracts of similar nature", "weight": 35, "max_score": 5},
                {"name": "Profile and experience of staff", "weight": 25, "max_score": 5}
            ],
            "Capability": [
                {"name": "Demonstrated capability to perform works", "weight": 30, "max_score": 5},
                {"name": "Ability to perform within workload", "weight": 25, "max_score": 5},
                {"name": "Technical skills", "weight": 25, "max_score": 5},
                {"name": "Appropriate resources", "weight": 20, "max_score": 5}
            ],
            "Management & Financial": [
                {"name": "Financial capacity", "weight": 40, "max_score": 5},
                {"name": "Level of supervision required", "weight": 30, "max_score": 5},
                {"name": "Management and personnel skills", "weight": 30, "max_score": 5}
            ],
            "WHS": [
                {"name": "WHS System Manual", "weight": 30, "max_score": 5},
                {"name": "Risk Assessment", "weight": 25, "max_score": 5},
                {"name": "Safe Work Methods", "weight": 25, "max_score": 5},
                {"name": "Training Records", "weight": 20, "max_score": 5}
            ]
        }
        
        return sub_criteria_map.get(criterion_name, [])
    
    def _generate_criterion_justification(
        self, 
        criterion_name: str, 
        weight: float, 
        project_type: ProjectType, 
        contract_value: str
    ) -> str:
        """Generate justification for criterion weight using RAG data"""
        
        justifications = {
            "Price (Full Cost)": f"Price represents {weight}% of total evaluation as it ensures value for money while maintaining quality standards for {project_type.value} projects.",
            "Relevant Experience": f"Experience weighting of {weight}% ensures suppliers have proven track record in {project_type.value} projects, reducing project risk.",
            "Capability": f"Capability assessment at {weight}% ensures technical competence and resource availability for successful project delivery.",
            "Management & Financial": f"Financial and management assessment at {weight}% ensures supplier stability and project management capability.",
            "WHS": f"WHS weighting of {weight}% ensures compliance with safety standards and risk mitigation for {project_type.value} projects.",
            "Quality Management": f"Quality management at {weight}% ensures consistent delivery standards and compliance with specifications."
        }
        
        return justifications.get(criterion_name, f"This criterion is weighted at {weight}% based on project requirements and industry best practices.")
    
    def _get_compliance_requirement(self, criterion_name: str) -> str:
        """Get compliance requirement for criterion"""
        
        compliance_map = {
            "Price (Full Cost)": "NSW Local Government Act 1993 - Section 55",
            "Relevant Experience": "Blacktown Procurement Policy P000553.1",
            "Capability": "NSW Government Procurement Guidelines",
            "Management & Financial": "Local Government (General) Regulation 2005",
            "WHS": "Work Health and Safety Act 2011 (NSW)",
            "Quality Management": "ISO 9001:2015 Quality Management Systems"
        }
        
        return compliance_map.get(criterion_name, "General procurement compliance requirements")
    
    def _get_base_returnable_items(self, tender_type: str, project_type: str) -> List[ReturnableScheduleItem]:
        """Get base returnable items based on tender type"""
        
        base_items = [
            ReturnableScheduleItem(
                item_number="1.1",
                description="Completed Tender/Quotation Form",
                required=True,
                format="PDF",
                submission_deadline="Closing Date",
                evaluation_weight=None,
                compliance_reference="Standard tender requirements",
                guidance_notes="Complete all sections accurately"
            ),
            ReturnableScheduleItem(
                item_number="1.2",
                description="Pricing Schedule",
                required=True,
                format="Excel/PDF",
                submission_deadline="Closing Date",
                evaluation_weight=40.0,
                compliance_reference="Price evaluation criteria",
                guidance_notes="Include all costs, taxes, and fees"
            ),
            ReturnableScheduleItem(
                item_number="1.3",
                description="Company Profile and Experience",
                required=True,
                format="PDF",
                submission_deadline="Closing Date",
                evaluation_weight=20.0,
                compliance_reference="Relevant experience criteria",
                guidance_notes="Include relevant project examples"
            )
        ]
        
        if tender_type in [TenderType.TENDER, TenderType.FORMAL_TENDER]:
            base_items.extend([
                ReturnableScheduleItem(
                    item_number="2.1",
                    description="WHS Management System",
                    required=True,
                    format="PDF",
                    submission_deadline="Closing Date",
                    evaluation_weight=10.0,
                    compliance_reference="WHS Act 2011 (NSW)",
                    guidance_notes="Include WHS policies and procedures"
                ),
                ReturnableScheduleItem(
                    item_number="2.2",
                    description="Quality Management System",
                    required=True,
                    format="PDF",
                    submission_deadline="Closing Date",
                    evaluation_weight=5.0,
                    compliance_reference="Quality management criteria",
                    guidance_notes="Include quality assurance processes"
                )
            ])
        
        return base_items
    
    def _generate_project_specific_items(
        self, 
        project_title: str, 
        project_type: str, 
        tender_type: TenderType
    ) -> List[ReturnableScheduleItem]:
        """Generate project-specific returnable items"""
        
        project_items = []
        
        if project_type == "construction":
            project_items.append(ReturnableScheduleItem(
                item_number="3.1",
                description="Construction Methodology",
                required=True,
                format="PDF",
                submission_deadline="Closing Date",
                evaluation_weight=15.0,
                compliance_reference="Construction capability criteria",
                guidance_notes="Detail construction approach and timeline"
            ))
        
        elif project_type == "it_services":
            project_items.append(ReturnableScheduleItem(
                item_number="3.1",
                description="Technical Solution",
                required=True,
                format="PDF",
                submission_deadline="Closing Date",
                evaluation_weight=15.0,
                compliance_reference="Technical capability criteria",
                guidance_notes="Detail technical approach and architecture"
            ))
        
        return project_items
    
    def _generate_general_instructions(self, tender_type: str) -> List[str]:
        """Generate general instructions for returnable schedule"""
        
        instructions = [
            "All submissions must be received by the closing date and time specified",
            "Late submissions will not be accepted",
            "All documents must be in English",
            "Electronic submissions are preferred",
            "All pricing must be in Australian Dollars (AUD) including GST"
        ]
        
        if tender_type in [TenderType.TENDER, TenderType.FORMAL_TENDER]:
            instructions.extend([
                "Compliance with all specified requirements is mandatory",
                "Non-compliant submissions may be excluded from evaluation",
                "Suppliers must demonstrate relevant experience and capability",
                "Financial capacity will be assessed as part of evaluation"
            ])
        
        return instructions
    
    def _generate_submission_requirements(self, tender_type: str) -> Dict[str, Any]:
        """Generate submission requirements"""
        
        return {
            "submission_method": "Electronic submission preferred",
            "file_formats": ["PDF", "Excel", "Word"],
            "max_file_size": "50MB per file",
            "naming_convention": "CompanyName_ItemNumber_Description",
            "confidentiality": "All submissions treated as confidential",
            "contact_person": "Procurement Team",
            "email": "procurement@blacktown.nsw.gov.au",
            "phone": "(02) 9839 6000"
        }
    
    def _generate_compliance_requirements(
        self, 
        project_type: ProjectType, 
        contract_value: str,
        project_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate compliance requirements using three-tier RAG system"""
        try:
            # Query all three tiers for comprehensive compliance
            query = f"compliance requirements for {project_type.value} projects {contract_value}"
            
            # Query Global RAG (Tier 1)
            global_results = self.three_tier_rag.query_compliance(
                query, 
                tiers=[RAGTier.GLOBAL],
                categories=[DocumentCategory.PROCUREMENT_GUIDELINES, DocumentCategory.TENDERING_STANDARDS]
            )
            
            # Query Internal RAG (Tier 2) - Council-specific
            internal_results = self.three_tier_rag.query_compliance(
                query,
                tiers=[RAGTier.INTERNAL],
                categories=[DocumentCategory.COUNCIL_POLICIES, DocumentCategory.INTERNAL_PROCEDURES],
                council="Blacktown City Council"
            )
            
            # Query Project RAG (Tier 3) - Project-specific compliance
            project_results = self.three_tier_rag.query_compliance(
                query,
                tiers=[RAGTier.PROJECT],
                categories=[DocumentCategory.WHS_COMPLIANCE, DocumentCategory.ISO_STANDARDS, DocumentCategory.ENVIRONMENTAL],
                project_type=project_type.value
            )
            
            # Combine requirements from all tiers
            all_requirements = []
            
            # Add global requirements
            for result in global_results[:3]:
                all_requirements.extend(result.compliance_requirements)
            
            # Add internal requirements
            for result in internal_results[:3]:
                all_requirements.extend(result.compliance_requirements)
            
            # Add project-specific requirements
            for result in project_results[:3]:
                all_requirements.extend(result.compliance_requirements)
            
            # Generate additional compliance checklist
            compliance_checklist = self._generate_compliance_checklist(project_type, contract_value, "Blacktown City Council")
            all_requirements.extend(compliance_checklist)
            
            return list(set(all_requirements))  # Remove duplicates
            
        except Exception as e:
            print(f"Error generating compliance requirements: {e}")
            return self._generate_compliance_checklist(project_type, contract_value, "Blacktown City Council")
    
    def validate_document_alignment(self, 
                                  document_type: str, 
                                  content: str, 
                                  project_type: str,
                                  council: str = "Blacktown City Council") -> Dict[str, Any]:
        """
        Validate that generated documents are aligned with all three RAG tiers
        Ensures TEPP, Returnable Schedules, RFT/RFQ comply with all compliance requirements
        """
        try:
            return self.three_tier_rag.validate_document_alignment(document_type, content)
        except Exception as e:
            print(f"Error validating document alignment: {e}")
            return {
                "document_type": document_type,
                "overall_compliance": False,
                "error": str(e),
                "recommendations": ["Unable to validate compliance - check RAG system configuration"]
            }
    
    def _generate_evaluation_timeline(
        self, 
        procurement_config: Dict[str, Any], 
        project_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate evaluation timeline"""
        
        timeline_days = procurement_config.get("timeline_days", 30)
        
        return {
            "tender_release": "Day 0",
            "site_visit": f"Day {timeline_days // 4}",
            "questions_deadline": f"Day {timeline_days // 2}",
            "tender_closing": f"Day {timeline_days}",
            "evaluation_period": f"Day {timeline_days + 1} to Day {timeline_days + 14}",
            "award_notification": f"Day {timeline_days + 21}",
            "contract_execution": f"Day {timeline_days + 28}"
        }
    
    def _generate_compliance_checklist(
        self, 
        project_type: ProjectType, 
        contract_value: str,
        council_type: str
    ) -> List[str]:
        """Generate compliance checklist using RAG data"""
        
        requirements = [
            "Compliance with NSW Local Government Act 1993",
            "Compliance with Local Government (General) Regulation 2005",
            "Compliance with Work Health and Safety Act 2011 (NSW)",
            "Compliance with Blacktown City Council Procurement Policy"
        ]
        
        # Add project-specific requirements
        if project_type == ProjectType.CONSTRUCTION:
            requirements.extend([
                "Compliance with Building Code of Australia",
                "Compliance with NSW Construction Code",
                "Public Liability Insurance minimum $20M"
            ])
        
        elif project_type == ProjectType.IT_SERVICES:
            requirements.extend([
                "Compliance with Australian Cyber Security Centre Guidelines",
                "Data Protection and Privacy compliance",
                "Professional Indemnity Insurance minimum $5M"
            ])
        
        # Add value-specific requirements
        value_numeric = self._parse_contract_value(contract_value)
        if value_numeric >= 250000:
            requirements.extend([
                "Local Preference Policy compliance",
                "Social Procurement requirements",
                "Environmental Management System"
            ])
        
        return requirements
    
    def _get_procurement_process(self, tender_type: str) -> str:
        """Get procurement process description"""
        
        processes = {
            "quotation": "Request for Quotation (RFQ) - Simplified process for lower value contracts",
            "tender": "Request for Tender (RFT) - Standard competitive process",
            "formal_tender": "Formal Tender Process - Comprehensive evaluation for high-value contracts"
        }
        
        return processes.get(tender_type, "Standard procurement process")
    
    def _get_timeline_days(self, tender_type: str, value_numeric: float) -> int:
        """Get timeline in days based on tender type and value"""
        
        if tender_type == "quotation":
            return 14
        elif tender_type == "tender":
            return 30
        else:  # Formal tender
            return 45 if value_numeric > 1000000 else 30


# Global instance
_intelligent_tender_generator = None

def get_intelligent_tender_generator(data_dir: Path) -> IntelligentTenderGenerator:
    """Get global instance of IntelligentTenderGenerator"""
    global _intelligent_tender_generator
    if _intelligent_tender_generator is None:
        _intelligent_tender_generator = IntelligentTenderGenerator(data_dir)
    return _intelligent_tender_generator
