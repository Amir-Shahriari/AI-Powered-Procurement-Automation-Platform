#!/usr/bin/env python3
"""
Global Compliance Manager
Manages universal procurement guidelines that apply to ALL project types
Based on uploaded NSW Local Government procurement documents
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class EvaluationCriterion:
    """Standard evaluation criterion from NSW procurement guidelines"""
    name: str
    weight: float
    description: str
    sub_criteria: List[str]
    scoring_method: str  # "weighted", "pass_fail", "percentage"
    mandatory: bool = True
    source_document: str = ""
    
@dataclass
class GlobalComplianceRequirement:
    """Universal compliance requirement from NSW guidelines"""
    requirement: str
    category: str  # "probity", "process", "documentation", "evaluation"
    mandatory: bool = True
    applicable_processes: List[str] = None  # None means all processes
    source_document: str = ""
    
@dataclass
class ScoringMatrix:
    """Standard scoring matrix from NSW evaluation manual"""
    criterion: str
    weight: float
    scoring_scale: str  # "1-5", "1-10", "pass_fail", "percentage"
    evaluation_notes: str
    source_document: str = ""

class GlobalComplianceManager:
    """
    Manages universal NSW Local Government procurement compliance requirements
    Based on uploaded procurement manuals and guidelines
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.global_config_dir = data_dir / "global_compliance"
        self.global_config_dir.mkdir(exist_ok=True)
        
        # Initialize with NSW Local Government standards
        self._initialize_nsw_standards()
    
    def _initialize_nsw_standards(self):
        """Initialize NSW Local Government procurement standards"""
        
        # Universal evaluation criteria from Tender Quotation Evaluation Manual V4- 2024
        self.global_evaluation_criteria = [
            EvaluationCriterion(
                name="Price/Cost",
                weight=40.0,
                description="Total cost including all fees, taxes, and ongoing costs",
                sub_criteria=["Base price", "Additional costs", "Ongoing maintenance", "Total cost of ownership"],
                scoring_method="weighted",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Technical Capability",
                weight=30.0,
                description="Technical competence and ability to deliver requirements",
                sub_criteria=["Technical approach", "Methodology", "Innovation", "Technical team"],
                scoring_method="weighted",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Experience & Track Record",
                weight=15.0,
                description="Relevant experience and proven track record",
                sub_criteria=["Similar projects", "Client references", "Industry experience", "Performance history"],
                scoring_method="weighted",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Risk Management",
                weight=10.0,
                description="Risk identification, assessment, and mitigation strategies",
                sub_criteria=["Risk identification", "Mitigation strategies", "Contingency plans", "Insurance coverage"],
                scoring_method="weighted",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Probity & Compliance",
                weight=5.0,
                description="Adherence to probity requirements and regulatory compliance",
                sub_criteria=["Probity declaration", "Regulatory compliance", "Conflict of interest", "Code of conduct"],
                scoring_method="pass_fail",
                mandatory=True,
                source_document="CAPH S9 procurement advisory & probity check (2024-11-20)"
            )
        ]
        
        # Universal compliance requirements from all uploaded documents
        self.global_compliance_requirements = [
            # From Procurement Manual V4.8 2025
            GlobalComplianceRequirement(
                requirement="Probity declaration must be completed by all suppliers",
                category="probity",
                source_document="Procurement Manual V4.8 2025"
            ),
            GlobalComplianceRequirement(
                requirement="Conflict of interest disclosure required",
                category="probity",
                source_document="Procurement Manual V4.8 2025"
            ),
            GlobalComplianceRequirement(
                requirement="Supplier must demonstrate financial capacity",
                category="process",
                source_document="Procurement Manual V4.8 2025"
            ),
            
            # From Tendering Guidelines November 21 V4 4
            GlobalComplianceRequirement(
                requirement="Tender documents must include clear evaluation criteria",
                category="documentation",
                source_document="Tendering Guidelines November 21 V4 4"
            ),
            GlobalComplianceRequirement(
                requirement="Evaluation panel must include at least 3 members",
                category="evaluation",
                source_document="Tendering Guidelines November 21 V4 4"
            ),
            GlobalComplianceRequirement(
                requirement="Evaluation must be documented with clear justification",
                category="evaluation",
                source_document="Tendering Guidelines November 21 V4 4"
            ),
            
            # From CAPH S9 procurement advisory
            GlobalComplianceRequirement(
                requirement="Probity audit trail must be maintained",
                category="probity",
                source_document="CAPH S9 procurement advisory & probity check (2024-11-20)"
            ),
            GlobalComplianceRequirement(
                requirement="Independent probity advisor required for high-value tenders",
                category="probity",
                applicable_processes=["formal_tender", "selective_tender"],
                source_document="CAPH S9 procurement advisory & probity check (2024-11-20)"
            )
        ]
        
        # Standard scoring matrices
        self.scoring_matrices = {
            "weighted_1_5": {
                "scale": "1-5",
                "description": "1 = Poor, 2 = Below Average, 3 = Average, 4 = Good, 5 = Excellent",
                "source": "Tender Quotation Evaluation Manual V4- 2024"
            },
            "weighted_1_10": {
                "scale": "1-10", 
                "description": "1 = Poor, 10 = Excellent",
                "source": "Tender Quotation Evaluation Manual V4- 2024"
            },
            "pass_fail": {
                "scale": "Pass/Fail",
                "description": "Pass = Meets requirement, Fail = Does not meet requirement",
                "source": "CAPH S9 procurement advisory & probity check (2024-11-20)"
            }
        }
    
    def get_global_evaluation_criteria(self, procurement_process: str = None) -> List[Dict[str, Any]]:
        """Get universal evaluation criteria for all NSW Local Government tenders"""
        criteria = []
        
        for criterion in self.global_evaluation_criteria:
            # Check if criterion applies to this process
            if criterion.name == "Probity & Compliance" and procurement_process in ["quote", "request_for_quote"]:
                # Adjust weight for simpler processes
                weight = 10.0
            else:
                weight = criterion.weight
                
            criteria.append({
                "name": criterion.name,
                "weight": weight,
                "description": criterion.description,
                "sub_criteria": criterion.sub_criteria,
                "scoring_method": criterion.scoring_method,
                "mandatory": criterion.mandatory,
                "source_document": criterion.source_document
            })
        
        return criteria
    
    def get_global_compliance_requirements(self, procurement_process: str = None, project_type: str = None) -> List[Dict[str, Any]]:
        """Get universal compliance requirements for all NSW Local Government tenders"""
        requirements = []
        
        for req in self.global_compliance_requirements:
            # Check if requirement applies to this process
            if req.applicable_processes and procurement_process not in req.applicable_processes:
                continue
                
            requirements.append({
                "requirement": req.requirement,
                "category": req.category,
                "mandatory": req.mandatory,
                "source_document": req.source_document
            })
        
        return requirements
    
    def get_standard_evaluation_template(self) -> Dict[str, Any]:
        """Get standard NSW Local Government evaluation template"""
        return {
            "evaluation_process": {
                "steps": [
                    "1. Preliminary compliance check",
                    "2. Technical evaluation",
                    "3. Price evaluation", 
                    "4. Risk assessment",
                    "5. Probity verification",
                    "6. Final scoring and ranking"
                ],
                "source": "Tender Quotation Evaluation Manual V4- 2024"
            },
            "evaluation_panel": {
                "minimum_members": 3,
                "roles": ["Technical evaluator", "Financial evaluator", "Probity advisor"],
                "source": "Tendering Guidelines November 21 V4 4"
            },
            "scoring_methodology": {
                "weighted_scoring": True,
                "minimum_passing_score": 60,
                "probity_requirement": "Pass/Fail mandatory",
                "source": "Tender Quotation Evaluation Manual V4- 2024"
            }
        }
    
    def get_standard_tender_structure(self) -> Dict[str, Any]:
        """Get standard NSW Local Government tender document structure"""
        return {
            "mandatory_sections": [
                "1. Executive Summary",
                "2. Project Background",
                "3. Scope of Works/Services",
                "4. Technical Specifications",
                "5. Evaluation Criteria and Weights",
                "6. Terms and Conditions",
                "7. Probity Requirements",
                "8. Submission Requirements",
                "9. Timetable",
                "10. Contact Information"
            ],
            "source": "Tendering Guidelines November 21 V4 4",
            "compliance_notes": [
                "All sections must be included",
                "Evaluation criteria must be clearly defined with weights",
                "Probity requirements must be prominently featured",
                "Submission requirements must be specific and measurable"
            ]
        }
    
    def get_returnable_schedules_template(self) -> Dict[str, Any]:
        """Get standard NSW Local Government returnable schedules template"""
        return {
            "schedule_1": {
                "title": "Supplier Information and Capability",
                "requirements": [
                    "Company details and registration",
                    "Financial capacity statements",
                    "Technical capability statements",
                    "Relevant experience and references",
                    "Key personnel and qualifications"
                ]
            },
            "schedule_2": {
                "title": "Technical Response",
                "requirements": [
                    "Technical approach and methodology",
                    "Project management plan",
                    "Quality assurance procedures",
                    "Risk management strategies",
                    "Innovation and value-add proposals"
                ]
            },
            "schedule_3": {
                "title": "Commercial Response",
                "requirements": [
                    "Pricing schedule",
                    "Payment terms",
                    "Contract terms acceptance",
                    "Insurance and indemnity",
                    "Performance guarantees"
                ]
            },
            "schedule_4": {
                "title": "Probity and Compliance",
                "requirements": [
                    "Probity declaration",
                    "Conflict of interest disclosure",
                    "Code of conduct acceptance",
                    "Regulatory compliance statements",
                    "Audit and transparency commitments"
                ]
            },
            "source": "Procurement Manual V4.8 2025"
        }
    
    def validate_tender_compliance(self, tender_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tender against NSW Local Government compliance requirements"""
        compliance_check = {
            "overall_compliance": True,
            "compliance_rate": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        # Check evaluation criteria compliance
        if "evaluation_criteria" not in tender_data:
            compliance_check["issues"].append("Missing evaluation criteria")
            compliance_check["overall_compliance"] = False
        else:
            criteria = tender_data["evaluation_criteria"]
            if not any(c.get("name") == "Price/Cost" for c in criteria):
                compliance_check["issues"].append("Missing mandatory Price/Cost criterion")
                compliance_check["overall_compliance"] = False
            
            if not any(c.get("name") == "Probity & Compliance" for c in criteria):
                compliance_check["issues"].append("Missing mandatory Probity & Compliance criterion")
                compliance_check["overall_compliance"] = False
        
        # Check document structure compliance
        required_sections = self.get_standard_tender_structure()["mandatory_sections"]
        if "document_structure" in tender_data:
            for section in required_sections[:5]:  # Check first 5 mandatory sections
                if section not in str(tender_data["document_structure"]):
                    compliance_check["issues"].append(f"Missing required section: {section}")
                    compliance_check["overall_compliance"] = False
        
        # Calculate compliance rate
        total_checks = len(compliance_check["issues"]) + 5  # 5 basic checks
        passed_checks = total_checks - len(compliance_check["issues"])
        compliance_check["compliance_rate"] = (passed_checks / total_checks) * 100
        
        return compliance_check
    
    def add_global_documents(self, documents: List[Any]) -> List[str]:
        """Add new global documents and extract universal requirements"""
        new_requirements = []
        
        for doc in documents:
            # Extract document name
            doc_name = getattr(doc, 'name', str(doc))
            
            # Add as new global compliance requirement
            new_req = GlobalComplianceRequirement(
                requirement=f"Compliance with {doc_name} standards",
                category="documentation",
                source_document=doc_name
            )
            
            self.global_compliance_requirements.append(new_req)
            new_requirements.append(f"Document: {doc_name}")
        
        # Save updated configuration
        self.save_global_config()
        
        return new_requirements
    
    def get_source_documents(self) -> List[str]:
        """Get list of all source documents currently in use"""
        source_docs = set()
        
        # Extract from evaluation criteria
        for criterion in self.global_evaluation_criteria:
            if criterion.source_document:
                source_docs.add(criterion.source_document)
        
        # Extract from compliance requirements
        for req in self.global_compliance_requirements:
            if req.source_document:
                source_docs.add(req.source_document)
        
        return sorted(list(source_docs))
    
    def save_global_config(self):
        """Save global compliance configuration to file"""
        # Get dynamic source documents
        source_docs = self.get_source_documents()
        
        config = {
            "evaluation_criteria": [asdict(c) for c in self.global_evaluation_criteria],
            "compliance_requirements": [asdict(r) for r in self.global_compliance_requirements],
            "scoring_matrices": self.scoring_matrices,
            "last_updated": datetime.now().isoformat(),
            "source_documents": source_docs
        }
        
        config_file = self.global_config_dir / "nsw_global_compliance.json"
        config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def load_global_config(self):
        """Load global compliance configuration from file"""
        config_file = self.global_config_dir / "nsw_global_compliance.json"
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding="utf-8"))
            
            # Reconstruct evaluation criteria
            self.global_evaluation_criteria = [
                EvaluationCriterion(**c) for c in config.get("evaluation_criteria", [])
            ]
            
            # Reconstruct compliance requirements  
            self.global_compliance_requirements = [
                GlobalComplianceRequirement(**r) for r in config.get("compliance_requirements", [])
            ]
            
            self.scoring_matrices = config.get("scoring_matrices", {})

# Global instance
_global_compliance_manager = None

def get_global_compliance_manager(data_dir: Path) -> GlobalComplianceManager:
    """Get or create global compliance manager instance"""
    global _global_compliance_manager
    if _global_compliance_manager is None:
        _global_compliance_manager = GlobalComplianceManager(data_dir)
        _global_compliance_manager.load_global_config()
    return _global_compliance_manager

if __name__ == "__main__":
    # Test the global compliance manager
    from ..config import settings
    
    manager = GlobalComplianceManager(settings.DATA_DIR)
    
    print("✅ NSW Global Compliance Manager initialized")
    print(f"📋 Global evaluation criteria: {len(manager.global_evaluation_criteria)}")
    print(f"🛡️ Global compliance requirements: {len(manager.global_compliance_requirements)}")
    print(f"📊 Scoring matrices: {len(manager.scoring_matrices)}")
    
    # Test getting criteria for different processes
    formal_tender_criteria = manager.get_global_evaluation_criteria("formal_tender")
    print(f"\n🎯 Formal Tender Criteria: {len(formal_tender_criteria)}")
    
    quote_criteria = manager.get_global_evaluation_criteria("quote")
    print(f"💬 Quote Criteria: {len(quote_criteria)}")
    
    # Test compliance validation
    test_tender = {
        "evaluation_criteria": [
            {"name": "Price/Cost", "weight": 40},
            {"name": "Technical Capability", "weight": 30},
            {"name": "Probity & Compliance", "weight": 5}
        ]
    }
    
    compliance = manager.validate_tender_compliance(test_tender)
    print(f"\n✅ Test Tender Compliance: {compliance['compliance_rate']:.1f}%")
    
    manager.save_global_config()
    print("💾 Global compliance configuration saved")
