#!/usr/bin/env python3
"""
Enhanced Document Generator
Generates comprehensive TEPP and returnable schedules with detailed evaluation criteria
Based on NSW Local Government standards and comprehensive evaluation system
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from app.services.evaluation_criteria_extractor import (
    EvaluationCriteriaExtractor, DetailedEvaluationCriterion, CriterionCategory
)
from app.services.project_type_manager import ProjectTypeManager, ProjectType, ProcurementProcess

@dataclass
class EnhancedTEPP:
    """Enhanced TEPP with comprehensive evaluation criteria"""
    project_name: str
    project_type: str
    procurement_process: str
    contract_value: str
    council_name: str
    evaluation_criteria: List[Dict[str, Any]]
    returnable_schedules: List[Dict[str, Any]]
    compliance_requirements: List[Dict[str, Any]]
    document_metadata: Dict[str, Any]

class EnhancedDocumentGenerator:
    """
    Enhanced document generator that creates comprehensive TEPP and returnable schedules
    with detailed evaluation criteria based on NSW Local Government standards
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.criteria_extractor = EvaluationCriteriaExtractor(data_dir)
        self.project_type_manager = ProjectTypeManager(data_dir)
    
    def generate_enhanced_tepp(self, 
                             project_name: str,
                             project_type: str,
                             procurement_process: str,
                             contract_value: str,
                             council_name: str,
                             additional_requirements: Optional[Dict[str, Any]] = None) -> EnhancedTEPP:
        """Generate enhanced TEPP with comprehensive evaluation criteria"""
        
        # Get evaluation criteria for the project type
        criteria = self.criteria_extractor.get_criteria_for_project_type(project_type.lower())
        
        # Convert criteria to serializable format
        evaluation_criteria = []
        for criterion in criteria:
            criterion_data = {
                "name": criterion.name,
                "category": criterion.category.value,
                "weight": criterion.weight,
                "description": criterion.description,
                "sub_criteria": criterion.sub_criteria,
                "scoring_method": criterion.scoring_method.value,
                "mandatory": criterion.mandatory,
                "max_score": criterion.max_score,
                "evaluation_notes": criterion.evaluation_notes,
                "source_document": criterion.source_document,
                "evaluation_guidance": criterion.evaluation_guidance,
                "key_questions": criterion.key_questions or []
            }
            evaluation_criteria.append(criterion_data)
        
        # Generate returnable schedules based on criteria
        returnable_schedules = self._generate_returnable_schedules(criteria, project_type)
        
        # Generate compliance requirements
        compliance_requirements = self._generate_compliance_requirements(project_type, procurement_process)
        
        # Create document metadata
        document_metadata = {
            "generated_date": datetime.now().isoformat(),
            "generator_version": "2.0.0",
            "project_type": project_type,
            "procurement_process": procurement_process,
            "contract_value": contract_value,
            "council_name": council_name,
            "evaluation_model": "MEAT",  # Default to MEAT
            "total_criteria": len(criteria),
            "total_weight": sum(c.weight for c in criteria),
            "additional_requirements": additional_requirements or {}
        }
        
        return EnhancedTEPP(
            project_name=project_name,
            project_type=project_type,
            procurement_process=procurement_process,
            contract_value=contract_value,
            council_name=council_name,
            evaluation_criteria=evaluation_criteria,
            returnable_schedules=returnable_schedules,
            compliance_requirements=compliance_requirements,
            document_metadata=document_metadata
        )
    
    def _generate_returnable_schedules(self, 
                                     criteria: List[DetailedEvaluationCriterion], 
                                     project_type: str) -> List[Dict[str, Any]]:
        """Generate comprehensive returnable schedules based on evaluation criteria"""
        
        schedules = []
        
        # Schedule 1: Supplier Information and Experience
        schedules.append({
            "schedule_number": "Schedule 1",
            "title": "Supplier Information and Experience",
            "description": "Comprehensive supplier background and experience details",
            "mandatory": True,
            "sections": [
                {
                    "section": "1.1 Company Information",
                    "fields": [
                        {"field": "Company Name", "type": "text", "mandatory": True},
                        {"field": "ABN/ACN", "type": "text", "mandatory": True},
                        {"field": "Registered Address", "type": "text", "mandatory": True},
                        {"field": "Contact Person", "type": "text", "mandatory": True},
                        {"field": "Email Address", "type": "email", "mandatory": True},
                        {"field": "Phone Number", "type": "text", "mandatory": True},
                        {"field": "Website", "type": "url", "mandatory": False}
                    ]
                },
                {
                    "section": "1.2 Financial Information",
                    "fields": [
                        {"field": "Annual Turnover (Last 3 Years)", "type": "currency", "mandatory": True},
                        {"field": "Net Profit (Last 3 Years)", "type": "currency", "mandatory": True},
                        {"field": "Current Assets", "type": "currency", "mandatory": True},
                        {"field": "Current Liabilities", "type": "currency", "mandatory": True},
                        {"field": "Professional Indemnity Insurance", "type": "currency", "mandatory": True},
                        {"field": "Public Liability Insurance", "type": "currency", "mandatory": True}
                    ]
                },
                {
                    "section": "1.3 Relevant Experience",
                    "fields": [
                        {"field": "Number of Similar Projects (Last 5 Years)", "type": "number", "mandatory": True},
                        {"field": "Total Value of Similar Projects", "type": "currency", "mandatory": True},
                        {"field": "Largest Single Project Value", "type": "currency", "mandatory": True},
                        {"field": "Experience with NSW Local Government", "type": "text", "mandatory": True},
                        {"field": "Client References (Minimum 3)", "type": "file", "mandatory": True}
                    ]
                }
            ]
        })
        
        # Schedule 2: Technical Capability and Approach
        schedules.append({
            "schedule_number": "Schedule 2",
            "title": "Technical Capability and Approach",
            "description": "Detailed technical approach and capability demonstration",
            "mandatory": True,
            "sections": [
                {
                    "section": "2.1 Technical Approach",
                    "fields": [
                        {"field": "Detailed Methodology", "type": "text_area", "mandatory": True},
                        {"field": "Innovation and Value-Add Proposals", "type": "text_area", "mandatory": False},
                        {"field": "Risk Management Strategy", "type": "text_area", "mandatory": True},
                        {"field": "Quality Assurance Procedures", "type": "text_area", "mandatory": True},
                        {"field": "Project Management Approach", "type": "text_area", "mandatory": True}
                    ]
                },
                {
                    "section": "2.2 Technical Team",
                    "fields": [
                        {"field": "Project Manager CV", "type": "file", "mandatory": True},
                        {"field": "Technical Lead CV", "type": "file", "mandatory": True},
                        {"field": "Key Personnel Qualifications", "type": "file", "mandatory": True},
                        {"field": "Team Size and Structure", "type": "text", "mandatory": True},
                        {"field": "Certifications and Accreditations", "type": "file", "mandatory": True}
                    ]
                },
                {
                    "section": "2.3 Equipment and Resources",
                    "fields": [
                        {"field": "Equipment List and Specifications", "type": "file", "mandatory": True},
                        {"field": "Software and Tools", "type": "text", "mandatory": True},
                        {"field": "Resource Availability", "type": "text", "mandatory": True},
                        {"field": "Subcontractor Arrangements", "type": "text", "mandatory": False}
                    ]
                }
            ]
        })
        
        # Schedule 3: Price and Cost Breakdown
        schedules.append({
            "schedule_number": "Schedule 3",
            "title": "Price and Cost Breakdown",
            "description": "Detailed pricing and cost structure",
            "mandatory": True,
            "sections": [
                {
                    "section": "3.1 Base Price",
                    "fields": [
                        {"field": "Total Project Price (Excl. GST)", "type": "currency", "mandatory": True},
                        {"field": "GST Amount", "type": "currency", "mandatory": True},
                        {"field": "Total Project Price (Incl. GST)", "type": "currency", "mandatory": True},
                        {"field": "Price Validity Period", "type": "text", "mandatory": True},
                        {"field": "Payment Terms", "type": "text", "mandatory": True}
                    ]
                },
                {
                    "section": "3.2 Cost Breakdown",
                    "fields": [
                        {"field": "Labor Costs", "type": "currency", "mandatory": True},
                        {"field": "Materials and Equipment", "type": "currency", "mandatory": True},
                        {"field": "Overhead and Profit", "type": "currency", "mandatory": True},
                        {"field": "Contingency Allowance", "type": "currency", "mandatory": True},
                        {"field": "Additional Costs", "type": "currency", "mandatory": False}
                    ]
                },
                {
                    "section": "3.3 Ongoing Costs",
                    "fields": [
                        {"field": "Annual Maintenance Cost", "type": "currency", "mandatory": True},
                        {"field": "Operating Costs (Annual)", "type": "currency", "mandatory": True},
                        {"field": "Replacement Costs", "type": "currency", "mandatory": False},
                        {"field": "Disposal Costs", "type": "currency", "mandatory": False}
                    ]
                }
            ]
        })
        
        # Schedule 4: Compliance and Probity
        schedules.append({
            "schedule_number": "Schedule 4",
            "title": "Compliance and Probity",
            "description": "Compliance declarations and probity requirements",
            "mandatory": True,
            "sections": [
                {
                    "section": "4.1 Probity Declarations",
                    "fields": [
                        {"field": "Probity Declaration Signed", "type": "file", "mandatory": True},
                        {"field": "Conflict of Interest Declaration", "type": "file", "mandatory": True},
                        {"field": "Code of Conduct Acceptance", "type": "file", "mandatory": True},
                        {"field": "Audit Trail Commitment", "type": "file", "mandatory": True}
                    ]
                },
                {
                    "section": "4.2 Regulatory Compliance",
                    "fields": [
                        {"field": "Work Health and Safety Compliance", "type": "file", "mandatory": True},
                        {"field": "Environmental Compliance", "type": "file", "mandatory": True},
                        {"field": "Building Code Compliance", "type": "file", "mandatory": True},
                        {"field": "Industry Standards Compliance", "type": "file", "mandatory": True}
                    ]
                },
                {
                    "section": "4.3 Insurance and Guarantees",
                    "fields": [
                        {"field": "Professional Indemnity Certificate", "type": "file", "mandatory": True},
                        {"field": "Public Liability Certificate", "type": "file", "mandatory": True},
                        {"field": "Performance Bond Details", "type": "file", "mandatory": True},
                        {"field": "Warranty Terms", "type": "text", "mandatory": True}
                    ]
                }
            ]
        })
        
        # Add project-specific schedules
        if project_type.lower() == "construction":
            schedules.extend(self._get_construction_schedules())
        elif project_type.lower() == "fleet":
            schedules.extend(self._get_fleet_schedules())
        elif project_type.lower() == "hvac":
            schedules.extend(self._get_hvac_schedules())
        elif project_type.lower() == "services":
            schedules.extend(self._get_services_schedules())
        
        # Schedule for Sustainability and Environmental
        if any(c.category == CriterionCategory.SUSTAINABILITY_ENVIRONMENTAL for c in criteria):
            schedules.append({
                "schedule_number": f"Schedule {len(schedules) + 1}",
                "title": "Sustainability and Environmental",
                "description": "Environmental responsibility and sustainability practices",
                "mandatory": False,
                "sections": [
                    {
                        "section": "Environmental Management",
                        "fields": [
                            {"field": "Environmental Management System", "type": "file", "mandatory": False},
                            {"field": "Carbon Footprint Reduction Plan", "type": "text_area", "mandatory": False},
                            {"field": "Waste Management Strategy", "type": "text_area", "mandatory": False},
                            {"field": "Sustainable Procurement Practices", "type": "text_area", "mandatory": False}
                        ]
                    }
                ]
            })
        
        # Schedule for Local Content
        if any(c.category == CriterionCategory.LOCAL_CONTENT for c in criteria):
            schedules.append({
                "schedule_number": f"Schedule {len(schedules) + 1}",
                "title": "Local Content and Community Benefit",
                "description": "Local employment, suppliers, and community benefits",
                "mandatory": False,
                "sections": [
                    {
                        "section": "Local Engagement",
                        "fields": [
                            {"field": "Local Employment Plan", "type": "text_area", "mandatory": False},
                            {"field": "Local Supplier Usage", "type": "text", "mandatory": False},
                            {"field": "Community Investment Plan", "type": "text_area", "mandatory": False},
                            {"field": "Skills Development Programs", "type": "text_area", "mandatory": False}
                        ]
                    }
                ]
            })
        
        return schedules
    
    def _get_construction_schedules(self) -> List[Dict[str, Any]]:
        """Get construction-specific returnable schedules"""
        return [
            {
                "schedule_number": "Schedule 5",
                "title": "Construction Specific Requirements",
                "description": "Construction-specific safety, environmental, and regulatory requirements",
                "mandatory": True,
                "sections": [
                    {
                        "section": "5.1 Safety Management",
                        "fields": [
                            {"field": "Work Health and Safety Management Plan", "type": "file", "mandatory": True},
                            {"field": "Safety Record (Last 3 Years)", "type": "file", "mandatory": True},
                            {"field": "Safety Training Programs", "type": "file", "mandatory": True},
                            {"field": "Incident Reporting Procedures", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.2 Environmental Protection",
                        "fields": [
                            {"field": "Environmental Management Plan", "type": "file", "mandatory": True},
                            {"field": "Waste Management Plan", "type": "file", "mandatory": True},
                            {"field": "Erosion and Sediment Control", "type": "file", "mandatory": True},
                            {"field": "Environmental Impact Assessment", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.3 Construction Methodology",
                        "fields": [
                            {"field": "Construction Sequence and Timeline", "type": "file", "mandatory": True},
                            {"field": "Quality Control Procedures", "type": "file", "mandatory": True},
                            {"field": "Site Management Plan", "type": "file", "mandatory": True},
                            {"field": "Traffic Management Plan", "type": "file", "mandatory": True}
                        ]
                    }
                ]
            }
        ]
    
    def _get_fleet_schedules(self) -> List[Dict[str, Any]]:
        """Get fleet-specific returnable schedules"""
        return [
            {
                "schedule_number": "Schedule 5",
                "title": "Fleet Management Specific Requirements",
                "description": "Fleet-specific technical requirements and management capabilities",
                "mandatory": True,
                "sections": [
                    {
                        "section": "5.1 Vehicle Specifications",
                        "fields": [
                            {"field": "Vehicle Specifications Compliance", "type": "file", "mandatory": True},
                            {"field": "Fuel Efficiency Certificates", "type": "file", "mandatory": True},
                            {"field": "Emission Standards Compliance", "type": "file", "mandatory": True},
                            {"field": "Safety Ratings and Certifications", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.2 Service and Support",
                        "fields": [
                            {"field": "Warranty Terms and Conditions", "type": "file", "mandatory": True},
                            {"field": "Service Network Coverage", "type": "file", "mandatory": True},
                            {"field": "Parts Availability and Support", "type": "file", "mandatory": True},
                            {"field": "Training and Documentation", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.3 Delivery and Availability",
                        "fields": [
                            {"field": "Delivery Schedule", "type": "file", "mandatory": True},
                            {"field": "Vehicle Availability Confirmation", "type": "file", "mandatory": True},
                            {"field": "Fleet Management Systems", "type": "file", "mandatory": True},
                            {"field": "Tracking and Monitoring Capabilities", "type": "file", "mandatory": True}
                        ]
                    }
                ]
            }
        ]
    
    def _get_hvac_schedules(self) -> List[Dict[str, Any]]:
        """Get HVAC-specific returnable schedules"""
        return [
            {
                "schedule_number": "Schedule 5",
                "title": "HVAC System Requirements",
                "description": "HVAC system performance, energy efficiency, and maintenance requirements",
                "mandatory": True,
                "sections": [
                    {
                        "section": "5.1 System Specifications",
                        "fields": [
                            {"field": "HVAC System Specifications", "type": "file", "mandatory": True},
                            {"field": "Energy Efficiency Ratings", "type": "file", "mandatory": True},
                            {"field": "Performance Specifications", "type": "file", "mandatory": True},
                            {"field": "Building Code Compliance", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.2 Installation and Commissioning",
                        "fields": [
                            {"field": "Installation Methodology", "type": "file", "mandatory": True},
                            {"field": "Commissioning Procedures", "type": "file", "mandatory": True},
                            {"field": "Testing and Validation", "type": "file", "mandatory": True},
                            {"field": "Handover Documentation", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.3 Maintenance and Service",
                        "fields": [
                            {"field": "Maintenance Schedule", "type": "file", "mandatory": True},
                            {"field": "Service Level Agreements", "type": "file", "mandatory": True},
                            {"field": "Emergency Response Procedures", "type": "file", "mandatory": True},
                            {"field": "Performance Monitoring", "type": "file", "mandatory": True}
                        ]
                    }
                ]
            }
        ]
    
    def _get_services_schedules(self) -> List[Dict[str, Any]]:
        """Get services-specific returnable schedules"""
        return [
            {
                "schedule_number": "Schedule 5",
                "title": "Service Delivery Requirements",
                "description": "Service delivery standards, performance measurement, and customer service",
                "mandatory": True,
                "sections": [
                    {
                        "section": "5.1 Service Delivery",
                        "fields": [
                            {"field": "Service Level Agreements", "type": "file", "mandatory": True},
                            {"field": "Performance Measurement Systems", "type": "file", "mandatory": True},
                            {"field": "Customer Service Standards", "type": "file", "mandatory": True},
                            {"field": "Service Delivery Methodology", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.2 Performance Management",
                        "fields": [
                            {"field": "Key Performance Indicators", "type": "file", "mandatory": True},
                            {"field": "Reporting and Monitoring", "type": "file", "mandatory": True},
                            {"field": "Continuous Improvement Programs", "type": "file", "mandatory": True},
                            {"field": "Customer Satisfaction Management", "type": "file", "mandatory": True}
                        ]
                    },
                    {
                        "section": "5.3 Service Continuity",
                        "fields": [
                            {"field": "Business Continuity Plan", "type": "file", "mandatory": True},
                            {"field": "Backup Service Arrangements", "type": "file", "mandatory": True},
                            {"field": "Emergency Response Procedures", "type": "file", "mandatory": True},
                            {"field": "Service Recovery Plans", "type": "file", "mandatory": True}
                        ]
                    }
                ]
            }
        ]
    
    def _generate_compliance_requirements(self, project_type: str, procurement_process: str) -> List[Dict[str, Any]]:
        """Generate compliance requirements based on project type and process"""
        
        # Get global compliance requirements
        global_requirements = self.project_type_manager.get_global_compliance_requirements(
            ProjectType(project_type.lower()), 
            ProcurementProcess(procurement_process.lower())
        )
        
        # Add project-specific requirements (using evaluation criteria as compliance requirements)
        project_requirements = self.project_type_manager.get_evaluation_criteria_for_project(
            ProjectType(project_type.lower()), 
            ProcurementProcess(procurement_process.lower())
        )
        
        # Combine and format requirements
        all_requirements = global_requirements + project_requirements
        
        formatted_requirements = []
        for req in all_requirements:
            formatted_requirements.append({
                "requirement": req.get("name", ""),
                "description": req.get("description", ""),
                "mandatory": req.get("mandatory", True),
                "category": req.get("category", "general"),
                "source_document": req.get("source_document", ""),
                "verification_method": req.get("verification_method", "document_review"),
                "compliance_notes": req.get("compliance_notes", "")
            })
        
        return formatted_requirements
    
    def save_enhanced_tepp(self, tepp: EnhancedTEPP, output_path: Path):
        """Save enhanced TEPP to file"""
        tepp_data = asdict(tepp)
        output_path.write_text(json.dumps(tepp_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def load_enhanced_tepp(self, file_path: Path) -> Optional[EnhancedTEPP]:
        """Load enhanced TEPP from file"""
        try:
            tepp_data = json.loads(file_path.read_text(encoding="utf-8"))
            return EnhancedTEPP(**tepp_data)
        except Exception as e:
            print(f"Error loading enhanced TEPP: {e}")
            return None

# Global instance
_enhanced_document_generator = None

def get_enhanced_document_generator(data_dir: Path) -> EnhancedDocumentGenerator:
    """Get or create enhanced document generator instance"""
    global _enhanced_document_generator
    if _enhanced_document_generator is None:
        _enhanced_document_generator = EnhancedDocumentGenerator(data_dir)
    return _enhanced_document_generator

if __name__ == "__main__":
    # Test the enhanced document generator
    from ..config import settings
    
    generator = EnhancedDocumentGenerator(settings.DATA_DIR)
    
    print("✅ Enhanced Document Generator initialized")
    
    # Generate sample TEPP
    tepp = generator.generate_enhanced_tepp(
        project_name="Test HVAC Project",
        project_type="hvac",
        procurement_process="tender",
        contract_value="$500,000 - $1,000,000",
        council_name="Blacktown City Council"
    )
    
    print(f"📋 Generated TEPP with {len(tepp.evaluation_criteria)} evaluation criteria")
    print(f"📄 Generated {len(tepp.returnable_schedules)} returnable schedules")
    print(f"🛡️ Generated {len(tepp.compliance_requirements)} compliance requirements")
    
    print("\n🎉 Enhanced Document Generator working correctly!")
