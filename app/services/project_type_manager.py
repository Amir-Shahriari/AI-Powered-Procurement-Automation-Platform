#!/usr/bin/env python3
"""
Project Type and Procurement Process Manager
Handles project categorization and procurement process selection for Local Government and Councils
Uses a hybrid approach: Code-based for core functionality, RAG for dynamic content
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ProjectType(Enum):
    """Core project types that are stable and unlikely to change frequently"""
    CONSTRUCTION = "construction"
    FLEET = "fleet"
    HVAC = "hvac"
    SERVICES = "services"
    IT_SERVICES = "it_services"
    MAINTENANCE = "maintenance"
    CONSULTING = "consulting"
    SUPPLIES = "supplies"
    FACILITIES = "facilities"
    WASTE_MANAGEMENT = "waste_management"
    PARKS_RECREATION = "parks_recreation"

class ProcurementProcess(Enum):
    """Standard procurement processes used across councils"""
    QUOTE = "quote"  # < $10k
    QUOTATION = "quotation"  # $10k - $50k
    TENDER = "tender"  # $50k - $250k
    FORMAL_TENDER = "formal_tender"  # > $250k
    PANEL_ARRANGEMENT = "panel_arrangement"
    DIRECT_APPOINTMENT = "direct_appointment"
    EMERGENCY = "emergency"

@dataclass
class ProjectTypeConfig:
    """Configuration for a specific project type"""
    type: ProjectType
    name: str
    description: str
    typical_value_range: str
    default_process: ProcurementProcess
    required_documents: List[str]
    evaluation_criteria: List[str]
    compliance_requirements: List[str]
    special_considerations: List[str]

@dataclass
class ProcurementProcessConfig:
    """Configuration for a specific procurement process"""
    process: ProcurementProcess
    name: str
    description: str
    value_threshold: str
    required_steps: List[str]
    mandatory_documents: List[str]
    evaluation_methodology: str
    approval_requirements: List[str]
    timeline: str

class ProjectTypeManager:
    """Manages project types and procurement processes with hybrid RAG/code approach"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.config_dir = data_dir / "project_configs"
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize with core configurations
        self._initialize_core_configs()
    
    def _initialize_core_configs(self):
        """Initialize core project type and process configurations (code-based)"""
        
        # Core project type configurations
        self.project_types = {
            ProjectType.CONSTRUCTION: ProjectTypeConfig(
                type=ProjectType.CONSTRUCTION,
                name="Construction & Infrastructure",
                description="Building construction, road works, infrastructure projects",
                typical_value_range="$50k - $5M+",
                default_process=ProcurementProcess.FORMAL_TENDER,
                required_documents=["Technical specifications", "Site plans", "Environmental assessments"],
                evaluation_criteria=["Technical capability", "Price", "Experience", "Safety record", "Timeline"],
                compliance_requirements=["Building codes", "Safety standards", "Environmental regulations"],
                special_considerations=["Weather delays", "Site access", "Community impact"]
            ),
            ProjectType.FLEET: ProjectTypeConfig(
                type=ProjectType.FLEET,
                name="Fleet & Vehicles",
                description="Vehicle procurement, fleet management, automotive services",
                typical_value_range="$20k - $500k",
                default_process=ProcurementProcess.TENDER,
                required_documents=["Vehicle specifications", "Service requirements", "Delivery timeline"],
                evaluation_criteria=["Vehicle specifications", "Price", "Supplier reliability", "Warranty", "Service network"],
                compliance_requirements=["ADR standards", "Emission standards", "Safety ratings"],
                special_considerations=["Fuel efficiency", "Maintenance costs", "Resale value"]
            ),
            ProjectType.HVAC: ProjectTypeConfig(
                type=ProjectType.HVAC,
                name="HVAC & Climate Control",
                description="Heating, ventilation, air conditioning systems and services",
                typical_value_range="$30k - $1M+",
                default_process=ProcurementProcess.TENDER,
                required_documents=["System specifications", "Energy efficiency requirements", "Installation plans"],
                evaluation_criteria=["Technical specifications", "Energy efficiency", "Price", "Installation quality", "Maintenance support"],
                compliance_requirements=["Energy efficiency standards", "Building codes", "Safety regulations"],
                special_considerations=["Energy consumption", "Maintenance requirements", "System integration"]
            ),
            ProjectType.SERVICES: ProjectTypeConfig(
                type=ProjectType.SERVICES,
                name="General Services",
                description="Professional services, consulting, maintenance, and general service delivery",
                typical_value_range="$10k - $1M+",
                default_process=ProcurementProcess.QUOTATION,
                required_documents=["Service specifications", "Performance requirements", "Timeline"],
                evaluation_criteria=["Service quality", "Price", "Experience", "Reliability", "Compliance"],
                compliance_requirements=["Service standards", "Professional qualifications", "Insurance requirements"],
                special_considerations=["Service delivery", "Quality assurance", "Performance monitoring"]
            ),
            ProjectType.IT_SERVICES: ProjectTypeConfig(
                type=ProjectType.IT_SERVICES,
                name="IT Services & Technology",
                description="Software, hardware, IT consulting, digital services",
                typical_value_range="$10k - $2M+",
                default_process=ProcurementProcess.QUOTATION,
                required_documents=["Technical requirements", "Security specifications", "Integration plans"],
                evaluation_criteria=["Technical solution", "Price", "Vendor experience", "Security compliance", "Support"],
                compliance_requirements=["Data protection", "Security standards", "Accessibility"],
                special_considerations=["Data security", "System integration", "Future scalability"]
            ),
            ProjectType.MAINTENANCE: ProjectTypeConfig(
                type=ProjectType.MAINTENANCE,
                name="Maintenance & Repairs",
                description="Ongoing maintenance, repairs, facility management",
                typical_value_range="$5k - $200k",
                default_process=ProcurementProcess.QUOTATION,
                required_documents=["Maintenance schedules", "Service requirements", "Response times"],
                evaluation_criteria=["Service quality", "Price", "Response time", "Experience", "Reliability"],
                compliance_requirements=["Safety standards", "Environmental regulations", "Licensing"],
                special_considerations=["Preventive maintenance", "Emergency response", "Cost efficiency"]
            )
        }
        
        # Core procurement process configurations
        self.procurement_processes = {
            ProcurementProcess.QUOTE: ProcurementProcessConfig(
                process=ProcurementProcess.QUOTE,
                name="Simple Quote",
                description="Low-value purchases under $10,000",
                value_threshold="< $10,000",
                required_steps=["Request quotes", "Compare prices", "Select supplier", "Purchase"],
                mandatory_documents=["Quote request", "Supplier quotes", "Purchase order"],
                evaluation_methodology="Price comparison",
                approval_requirements=["Manager approval"],
                timeline="1-3 days"
            ),
            ProcurementProcess.QUOTATION: ProcurementProcessConfig(
                process=ProcurementProcess.QUOTATION,
                name="Formal Quotation",
                description="Medium-value purchases $10,000 - $50,000",
                value_threshold="$10,000 - $50,000",
                required_steps=["Prepare specification", "Request quotations", "Evaluate responses", "Select supplier", "Award contract"],
                mandatory_documents=["Specification", "Quotation request", "Supplier responses", "Evaluation report", "Contract"],
                evaluation_methodology="Price and capability assessment",
                approval_requirements=["Manager approval", "Finance approval"],
                timeline="1-2 weeks"
            ),
            ProcurementProcess.TENDER: ProcurementProcessConfig(
                process=ProcurementProcess.TENDER,
                name="Open Tender",
                description="High-value purchases $50,000 - $250,000",
                value_threshold="$50,000 - $250,000",
                required_steps=["Prepare tender documents", "Advertise tender", "Receive submissions", "Evaluate responses", "Award contract"],
                mandatory_documents=["TEPP", "Returnable schedules", "Tender responses", "Evaluation report", "Contract"],
                evaluation_methodology="Multi-criteria evaluation",
                approval_requirements=["Manager approval", "Finance approval", "Council approval"],
                timeline="4-8 weeks"
            ),
            ProcurementProcess.FORMAL_TENDER: ProcurementProcessConfig(
                process=ProcurementProcess.FORMAL_TENDER,
                name="Formal Tender Process",
                description="Major purchases over $250,000",
                value_threshold="> $250,000",
                required_steps=["Prepare tender documents", "Public advertisement", "Pre-tender briefing", "Receive submissions", "Evaluation panel", "Award contract"],
                mandatory_documents=["TEPP", "Returnable schedules", "Tender responses", "Evaluation report", "Council resolution", "Contract"],
                evaluation_methodology="Comprehensive multi-criteria evaluation",
                approval_requirements=["Manager approval", "Finance approval", "Council resolution", "Legal review"],
                timeline="8-16 weeks"
            )
        }
    
    def get_project_types(self) -> List[ProjectTypeConfig]:
        """Get all available project types"""
        return list(self.project_types.values())
    
    def get_procurement_processes(self) -> List[ProcurementProcessConfig]:
        """Get all available procurement processes"""
        return list(self.procurement_processes.values())
    
    def get_project_type_config(self, project_type: ProjectType) -> Optional[ProjectTypeConfig]:
        """Get configuration for a specific project type"""
        return self.project_types.get(project_type)
    
    def get_procurement_process_config(self, process: ProcurementProcess) -> Optional[ProcurementProcessConfig]:
        """Get configuration for a specific procurement process"""
        return self.procurement_processes.get(process)
    
    def recommend_process_for_value(self, value: float) -> ProcurementProcess:
        """Recommend procurement process based on contract value"""
        if value < 10000:
            return ProcurementProcess.QUOTE
        elif value < 50000:
            return ProcurementProcess.QUOTATION
        elif value < 250000:
            return ProcurementProcess.TENDER
        else:
            return ProcurementProcess.FORMAL_TENDER
    
    def get_council_specific_config(self, council_name: str) -> Dict[str, Any]:
        """Get council-specific configurations (RAG-based for dynamic content)"""
        config_file = self.config_dir / f"{council_name.lower().replace(' ', '_')}_config.json"
        
        if config_file.exists():
            return json.loads(config_file.read_text(encoding="utf-8"))
        else:
            # Return default configuration
            return {
                "council_name": council_name,
                "specific_requirements": [],
                "additional_documents": [],
                "special_processes": [],
                "contact_details": {},
                "last_updated": None
            }
    
    def update_council_config(self, council_name: str, config: Dict[str, Any]):
        """Update council-specific configuration (RAG-based for dynamic updates)"""
        config_file = self.config_dir / f"{council_name.lower().replace(' ', '_')}_config.json"
        config["last_updated"] = json.dumps({"timestamp": "now"})
        config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def get_evaluation_criteria_for_project(self, project_type: ProjectType, process: ProcurementProcess) -> List[Dict[str, Any]]:
        """Get evaluation criteria for a specific project type and process"""
        project_config = self.get_project_type_config(project_type)
        process_config = self.get_procurement_process_config(process)
        
        if not project_config or not process_config:
            return []
        
        # Import global compliance manager
        from app.services.global_compliance_manager import get_global_compliance_manager
        
        # Get NSW Local Government standard criteria first
        global_manager = get_global_compliance_manager(self.data_dir)
        global_criteria = global_manager.get_global_evaluation_criteria(process.value)
        
        # Convert global criteria to project format
        criteria = []
        for gc in global_criteria:
            criteria.append({
                "criterion": gc["name"],
                "weight": gc["weight"],
                "description": gc["description"],
                "sub_criteria": gc["sub_criteria"],
                "scoring_method": gc["scoring_method"],
                "mandatory": gc["mandatory"],
                "source": "nsw_global_standards",
                "source_document": gc["source_document"]
            })
        
        # Add project-specific criteria if needed
        project_specific_criteria = []
        for criterion in project_config.evaluation_criteria:
            # Check if this criterion is already covered by global standards
            if not any(gc["name"].lower() == criterion.lower() for gc in global_criteria):
                project_specific_criteria.append({
                    "criterion": criterion,
                    "weight": 5,  # Lower weight for project-specific criteria
                    "description": f"Evaluation of {criterion.lower()} for {project_config.name}",
                    "source": "project_type"
                })
        
        criteria.extend(project_specific_criteria)
        
        return criteria
    
    def get_global_compliance_requirements(self, project_type: ProjectType, process: ProcurementProcess) -> List[Dict[str, Any]]:
        """Get NSW Local Government global compliance requirements"""
        from app.services.global_compliance_manager import get_global_compliance_manager
        
        global_manager = get_global_compliance_manager(self.data_dir)
        return global_manager.get_global_compliance_requirements(process.value, project_type.value)
    
    def get_required_documents_for_project(self, project_type: ProjectType, process: ProcurementProcess) -> List[str]:
        """Get required documents for a specific project type and process"""
        project_config = self.get_project_type_config(project_type)
        process_config = self.get_procurement_process_config(process)
        
        documents = []
        
        if project_config:
            documents.extend(project_config.required_documents)
        
        if process_config:
            documents.extend(process_config.mandatory_documents)
        
        return list(set(documents))  # Remove duplicates
    
    def save_project_configuration(self, project_id: str, project_type: ProjectType, 
                                 process: ProcurementProcess, council_name: str, 
                                 additional_config: Dict[str, Any] = None):
        """Save project configuration for future reference"""
        config = {
            "project_id": project_id,
            "project_type": project_type.value,
            "procurement_process": process.value,
            "council_name": council_name,
            "evaluation_criteria": self.get_evaluation_criteria_for_project(project_type, process),
            "required_documents": self.get_required_documents_for_project(project_type, process),
            "additional_config": additional_config or {},
            "created_at": "now"
        }
        
        config_file = self.data_dir / f"{project_id}_project_config.json"
        config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def load_project_configuration(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load saved project configuration"""
        config_file = self.data_dir / f"{project_id}_project_config.json"
        if config_file.exists():
            return json.loads(config_file.read_text(encoding="utf-8"))
        return None

def get_project_type_manager(data_dir: Path) -> ProjectTypeManager:
    """Get or create project type manager instance"""
    return ProjectTypeManager(data_dir)
