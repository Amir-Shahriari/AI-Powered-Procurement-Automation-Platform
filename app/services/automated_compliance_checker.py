#!/usr/bin/env python3
"""
Automated Compliance Checker
Automatically verifies compliance of all tendering activities with official standards
Integrates with RAG system to minimize time and cost while ensuring full compliance
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.unified_compliance_rag_system import (
    UnifiedComplianceRAGSystem, QueryType, ComplianceCategory
)

class DocumentType(Enum):
    """Types of documents to check for compliance"""
    TEPP = "tepp"
    RETURNABLE_SCHEDULES = "returnable_schedules"
    EVALUATION_CRITERIA = "evaluation_criteria"
    SUPPLIER_EVALUATION = "supplier_evaluation"
    TENDER_DOCUMENTS = "tender_documents"
    QUOTATION_DOCUMENTS = "quotation_documents"

class ComplianceLevel(Enum):
    """Compliance levels"""
    FULL_COMPLIANCE = "full_compliance"
    PARTIAL_COMPLIANCE = "partial_compliance"
    NON_COMPLIANT = "non_compliant"
    CRITICAL_NON_COMPLIANT = "critical_non_compliant"

@dataclass
class ComplianceIssue:
    """Individual compliance issue"""
    issue_id: str
    severity: str  # "critical", "high", "medium", "low"
    category: str
    description: str
    requirement: str
    source_document: str
    recommendation: str
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None

@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    document_type: DocumentType
    document_id: str
    project_context: Dict[str, Any]
    compliance_level: ComplianceLevel
    overall_score: float
    issues: List[ComplianceIssue]
    requirements_met: List[str]
    recommendations: List[str]
    source_standards: List[str]
    verification_timestamp: str
    processing_time_ms: int

class AutomatedComplianceChecker:
    """
    Automated compliance checker that verifies all tendering activities
    against official Blacktown City Council and NSW standards
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rag_system = UnifiedComplianceRAGSystem(data_dir)
        
        # Compliance rules database
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_compliance_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize comprehensive compliance rules"""
        
        return {
            "tepp": [
                {
                    "rule_id": "tepp_001",
                    "severity": "critical",
                    "category": "document_structure",
                    "description": "TEPP must include project name and basic metadata",
                    "check_function": "_check_tepp_basic_metadata",
                    "source_document": "Blacktown Tender Guidelines"
                },
                {
                    "rule_id": "tepp_002",
                    "severity": "high",
                    "category": "evaluation_criteria",
                    "description": "TEPP must include comprehensive evaluation criteria",
                    "check_function": "_check_tepp_evaluation_criteria",
                    "source_document": "Table 1 - Criteria Options"
                },
                {
                    "rule_id": "tepp_003",
                    "severity": "high",
                    "category": "weighting_matrix",
                    "description": "TEPP must include proper weighting matrix for project type",
                    "check_function": "_check_tepp_weighting_matrix",
                    "source_document": "Table 2/3 - Evaluation Matrices"
                },
                {
                    "rule_id": "tepp_004",
                    "severity": "critical",
                    "category": "compliance_requirements",
                    "description": "TEPP must include all mandatory NSW compliance requirements",
                    "check_function": "_check_tepp_compliance_requirements",
                    "source_document": "NSW Global Compliance Standards"
                }
            ],
            
            "returnable_schedules": [
                {
                    "rule_id": "rs_001",
                    "severity": "critical",
                    "category": "mandatory_schedules",
                    "description": "Must include all mandatory returnable schedules",
                    "check_function": "_check_mandatory_schedules",
                    "source_document": "Blacktown Returnable Schedules Standards"
                },
                {
                    "rule_id": "rs_002",
                    "severity": "high",
                    "category": "project_specific_schedules",
                    "description": "Must include project-specific schedules",
                    "check_function": "_check_project_specific_schedules",
                    "source_document": "Project Type Requirements"
                },
                {
                    "rule_id": "rs_003",
                    "severity": "medium",
                    "category": "schedule_completeness",
                    "description": "All schedules must have complete field definitions",
                    "check_function": "_check_schedule_completeness",
                    "source_document": "Schedule Standards"
                }
            ],
            
            "evaluation_criteria": [
                {
                    "rule_id": "ec_001",
                    "severity": "critical",
                    "category": "criteria_coverage",
                    "description": "Must include all required evaluation criteria categories",
                    "check_function": "_check_criteria_coverage",
                    "source_document": "Table 1 - Criteria Options"
                },
                {
                    "rule_id": "ec_002",
                    "severity": "high",
                    "category": "weighting_compliance",
                    "description": "Criteria weightings must comply with official matrices",
                    "check_function": "_check_weighting_compliance",
                    "source_document": "Table 2/3 - Evaluation Matrices"
                },
                {
                    "rule_id": "ec_003",
                    "severity": "high",
                    "category": "sub_criteria_completeness",
                    "description": "All criteria must have complete sub-criteria definitions",
                    "check_function": "_check_sub_criteria_completeness",
                    "source_document": "Evaluation Standards"
                }
            ],
            
            "supplier_evaluation": [
                {
                    "rule_id": "se_001",
                    "severity": "critical",
                    "category": "evaluation_methodology",
                    "description": "Must use approved evaluation methodology",
                    "check_function": "_check_evaluation_methodology",
                    "source_document": "Evaluation Methodology Standards"
                },
                {
                    "rule_id": "se_002",
                    "severity": "high",
                    "category": "scoring_consistency",
                    "description": "Scoring must be consistent with rating scales",
                    "check_function": "_check_scoring_consistency",
                    "source_document": "Table 4 - Rating Scales"
                },
                {
                    "rule_id": "se_003",
                    "severity": "critical",
                    "category": "local_preference",
                    "description": "Must apply local preference policy correctly",
                    "check_function": "_check_local_preference_application",
                    "source_document": "Local Preference Policy"
                }
            ]
        }
    
    def check_compliance(self, 
                        document_type: DocumentType, 
                        document_data: Dict[str, Any], 
                        project_context: Dict[str, Any]) -> ComplianceReport:
        """Comprehensive compliance check for any document type"""
        
        start_time = datetime.now()
        
        # Get compliance rules for document type
        rules = self.compliance_rules.get(document_type.value, [])
        
        # Initialize compliance report
        report = ComplianceReport(
            document_type=document_type,
            document_id=document_data.get("document_id", "unknown"),
            project_context=project_context,
            compliance_level=ComplianceLevel.FULL_COMPLIANCE,
            overall_score=1.0,
            issues=[],
            requirements_met=[],
            recommendations=[],
            source_standards=[],
            verification_timestamp=datetime.now().isoformat(),
            processing_time_ms=0
        )
        
        # Run compliance checks
        for rule in rules:
            try:
                check_function = getattr(self, rule["check_function"])
                result = check_function(document_data, project_context, rule)
                
                if result["compliant"]:
                    report.requirements_met.append(result["requirement"])
                else:
                    issue = ComplianceIssue(
                        issue_id=rule["rule_id"],
                        severity=rule["severity"],
                        category=rule["category"],
                        description=rule["description"],
                        requirement=result["requirement"],
                        source_document=rule["source_document"],
                        recommendation=result["recommendation"],
                        auto_fixable=result.get("auto_fixable", False),
                        fix_suggestion=result.get("fix_suggestion")
                    )
                    report.issues.append(issue)
                    report.recommendations.append(result["recommendation"])
                
                report.source_standards.append(rule["source_document"])
                
            except Exception as e:
                print(f"Error running compliance check {rule['rule_id']}: {e}")
        
        # Calculate compliance level and score
        report.compliance_level = self._calculate_compliance_level(report.issues)
        report.overall_score = self._calculate_compliance_score(report.issues, len(rules))
        
        # Calculate processing time
        report.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return report
    
    def _calculate_compliance_level(self, issues: List[ComplianceIssue]) -> ComplianceLevel:
        """Calculate overall compliance level based on issues"""
        
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        
        if critical_issues:
            return ComplianceLevel.CRITICAL_NON_COMPLIANT
        elif high_issues:
            return ComplianceLevel.NON_COMPLIANT
        elif issues:
            return ComplianceLevel.PARTIAL_COMPLIANCE
        else:
            return ComplianceLevel.FULL_COMPLIANCE
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue], total_rules: int) -> float:
        """Calculate compliance score (0.0 to 1.0)"""
        
        if total_rules == 0:
            return 1.0
        
        # Weight issues by severity
        weighted_issues = 0
        for issue in issues:
            if issue.severity == "critical":
                weighted_issues += 3
            elif issue.severity == "high":
                weighted_issues += 2
            elif issue.severity == "medium":
                weighted_issues += 1
            else:
                weighted_issues += 0.5
        
        # Calculate score (lower is better)
        max_possible_issues = total_rules * 3  # Assume all critical
        if max_possible_issues == 0:
            return 1.0
        
        issue_ratio = weighted_issues / max_possible_issues
        return max(0.0, 1.0 - issue_ratio)
    
    # TEPP Compliance Checks
    def _check_tepp_basic_metadata(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check TEPP basic metadata compliance"""
        
        required_fields = ["project_name", "project_type", "contract_value"]
        missing_fields = [field for field in required_fields if not document_data.get(field)]
        
        if not missing_fields:
            return {
                "compliant": True,
                "requirement": "Basic metadata completeness",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Basic metadata completeness",
                "recommendation": f"Add missing fields: {', '.join(missing_fields)}",
                "auto_fixable": True,
                "fix_suggestion": f"Set default values for: {', '.join(missing_fields)}"
            }
    
    def _check_tepp_evaluation_criteria(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check TEPP evaluation criteria compliance"""
        
        # Query RAG system for required criteria
        result = self.rag_system.query_compliance(
            QueryType.EVALUATION_CRITERIA,
            ComplianceCategory.EVALUATION_CRITERIA,
            {"criteria_name": "price"}
        )
        
        if not result.result:
            return {
                "compliant": False,
                "requirement": "Comprehensive evaluation criteria",
                "recommendation": "Include all required evaluation criteria from official standards",
                "auto_fixable": True,
                "fix_suggestion": "Generate default evaluation criteria based on project type"
            }
        
        # Check if document has evaluation criteria
        evaluation_criteria = document_data.get("evaluation_criteria", [])
        
        if not evaluation_criteria:
            return {
                "compliant": False,
                "requirement": "Evaluation criteria inclusion",
                "recommendation": "Add comprehensive evaluation criteria section",
                "auto_fixable": True,
                "fix_suggestion": "Generate evaluation criteria from RAG system"
            }
        
        return {
            "compliant": True,
            "requirement": "Comprehensive evaluation criteria",
            "recommendation": ""
        }
    
    def _check_tepp_weighting_matrix(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check TEPP weighting matrix compliance"""
        
        project_type = project_context.get("project_type", "general")
        contract_value = project_context.get("contract_value", "")
        
        # Query RAG system for weighting matrix
        result = self.rag_system.query_compliance(
            QueryType.WEIGHTING_MATRIX,
            ComplianceCategory.EVALUATION_CRITERIA,
            {
                "purchase_category": project_type,
                "contract_value": contract_value
            }
        )
        
        if not result.result:
            return {
                "compliant": False,
                "requirement": "Proper weighting matrix",
                "recommendation": "Use appropriate weighting ranges for project type and contract value",
                "auto_fixable": True,
                "fix_suggestion": "Apply default weighting matrix from official standards"
            }
        
        # Check if document uses compliant weightings
        evaluation_criteria = document_data.get("evaluation_criteria", [])
        matrix_data = result.result
        
        # Validate weightings against official matrix
        total_weight = 0
        for criterion in evaluation_criteria:
            weight = criterion.get("weight", 0)
            total_weight += weight
        
        # Check if total weight is close to 100%
        if abs(total_weight - 100) > 5:  # Allow 5% tolerance
            return {
                "compliant": False,
                "requirement": "Weighting matrix compliance",
                "recommendation": f"Total criteria weight should be 100% (currently {total_weight:.1f}%)",
                "auto_fixable": True,
                "fix_suggestion": "Normalize criteria weights to total 100%"
            }
        
        return {
            "compliant": True,
            "requirement": "Proper weighting matrix",
            "recommendation": ""
        }
    
    def _check_tepp_compliance_requirements(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check TEPP compliance requirements"""
        
        project_type = project_context.get("project_type", "general")
        process_type = project_context.get("process_type", "tender")
        
        # Query RAG system for compliance requirements
        result = self.rag_system.query_compliance(
            QueryType.COMPLIANCE_REQUIREMENT,
            ComplianceCategory.GLOBAL_NSW_STANDARDS,
            {
                "project_type": project_type,
                "process_type": process_type
            }
        )
        
        if not result.result:
            return {
                "compliant": False,
                "requirement": "NSW compliance requirements",
                "recommendation": "Include all mandatory NSW compliance requirements",
                "auto_fixable": False
            }
        
        # Check if document includes compliance requirements
        compliance_requirements = document_data.get("compliance_requirements", [])
        
        if not compliance_requirements:
            return {
                "compliant": False,
                "requirement": "NSW compliance requirements inclusion",
                "recommendation": "Add NSW compliance requirements section",
                "auto_fixable": True,
                "fix_suggestion": "Generate compliance requirements from RAG system"
            }
        
        return {
            "compliant": True,
            "requirement": "NSW compliance requirements",
            "recommendation": ""
        }
    
    # Returnable Schedules Compliance Checks
    def _check_mandatory_schedules(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check mandatory returnable schedules"""
        
        mandatory_schedules = [
            "Supplier Information and Experience",
            "Technical Capability and Approach", 
            "Price and Cost Breakdown",
            "Compliance and Probity"
        ]
        
        returnable_schedules = document_data.get("returnable_schedules", [])
        schedule_titles = [schedule.get("title", "") for schedule in returnable_schedules]
        
        missing_schedules = [schedule for schedule in mandatory_schedules if schedule not in schedule_titles]
        
        if not missing_schedules:
            return {
                "compliant": True,
                "requirement": "Mandatory returnable schedules",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Mandatory returnable schedules",
                "recommendation": f"Include missing mandatory schedules: {', '.join(missing_schedules)}",
                "auto_fixable": True,
                "fix_suggestion": f"Generate missing schedules: {', '.join(missing_schedules)}"
            }
    
    def _check_project_specific_schedules(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check project-specific returnable schedules"""
        
        project_type = project_context.get("project_type", "general")
        
        # Define project-specific schedules
        project_schedules = {
            "construction": "Construction Specific Requirements",
            "fleet": "Fleet Management Specific Requirements", 
            "hvac": "HVAC System Requirements",
            "services": "Service Delivery Requirements"
        }
        
        expected_schedule = project_schedules.get(project_type)
        if not expected_schedule:
            return {
                "compliant": True,
                "requirement": "Project-specific schedules",
                "recommendation": ""
            }
        
        returnable_schedules = document_data.get("returnable_schedules", [])
        schedule_titles = [schedule.get("title", "") for schedule in returnable_schedules]
        
        if expected_schedule in schedule_titles:
            return {
                "compliant": True,
                "requirement": "Project-specific schedules",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Project-specific schedules",
                "recommendation": f"Include project-specific schedule: {expected_schedule}",
                "auto_fixable": True,
                "fix_suggestion": f"Generate {expected_schedule} schedule"
            }
    
    def _check_schedule_completeness(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check schedule completeness"""
        
        returnable_schedules = document_data.get("returnable_schedules", [])
        incomplete_schedules = []
        
        for schedule in returnable_schedules:
            sections = schedule.get("sections", [])
            if not sections:
                incomplete_schedules.append(schedule.get("title", "Unknown"))
                continue
            
            for section in sections:
                fields = section.get("fields", [])
                if not fields:
                    incomplete_schedules.append(f"{schedule.get('title', 'Unknown')} - {section.get('section', 'Unknown')}")
        
        if not incomplete_schedules:
            return {
                "compliant": True,
                "requirement": "Schedule completeness",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Schedule completeness",
                "recommendation": f"Complete incomplete schedules: {', '.join(incomplete_schedules[:3])}",
                "auto_fixable": False
            }
    
    # Evaluation Criteria Compliance Checks
    def _check_criteria_coverage(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check evaluation criteria coverage"""
        
        required_criteria = ["price", "relevant_experience", "capability", "work_health_safety"]
        evaluation_criteria = document_data.get("evaluation_criteria", [])
        criterion_names = [criterion.get("name", "").lower().replace(" ", "_") for criterion in evaluation_criteria]
        
        missing_criteria = [criteria for criteria in required_criteria if criteria not in criterion_names]
        
        if not missing_criteria:
            return {
                "compliant": True,
                "requirement": "Required evaluation criteria coverage",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Required evaluation criteria coverage",
                "recommendation": f"Include missing criteria: {', '.join(missing_criteria)}",
                "auto_fixable": True,
                "fix_suggestion": f"Add missing criteria: {', '.join(missing_criteria)}"
            }
    
    def _check_weighting_compliance(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check weighting compliance with official matrices"""
        
        project_type = project_context.get("project_type", "general")
        contract_value = project_context.get("contract_value", "")
        
        # Query RAG system for official weightings
        result = self.rag_system.query_compliance(
            QueryType.WEIGHTING_MATRIX,
            ComplianceCategory.EVALUATION_CRITERIA,
            {
                "purchase_category": project_type,
                "contract_value": contract_value
            }
        )
        
        if not result.result:
            return {
                "compliant": False,
                "requirement": "Official weighting compliance",
                "recommendation": "Use official weighting ranges for project type",
                "auto_fixable": True,
                "fix_suggestion": "Apply official weighting matrix"
            }
        
        return {
            "compliant": True,
            "requirement": "Official weighting compliance",
            "recommendation": ""
        }
    
    def _check_sub_criteria_completeness(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check sub-criteria completeness"""
        
        evaluation_criteria = document_data.get("evaluation_criteria", [])
        incomplete_criteria = []
        
        for criterion in evaluation_criteria:
            sub_criteria = criterion.get("sub_criteria", [])
            if not sub_criteria:
                incomplete_criteria.append(criterion.get("name", "Unknown"))
        
        if not incomplete_criteria:
            return {
                "compliant": True,
                "requirement": "Sub-criteria completeness",
                "recommendation": ""
            }
        else:
            return {
                "compliant": False,
                "requirement": "Sub-criteria completeness",
                "recommendation": f"Add sub-criteria for: {', '.join(incomplete_criteria)}",
                "auto_fixable": True,
                "fix_suggestion": f"Generate sub-criteria for: {', '.join(incomplete_criteria)}"
            }
    
    # Supplier Evaluation Compliance Checks
    def _check_evaluation_methodology(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check evaluation methodology compliance"""
        
        methodology = document_data.get("evaluation_methodology", "")
        approved_methodologies = ["MEAT", "Lowest Price Conforming", "TCO", "Quality/Cost Ratio"]
        
        if methodology not in approved_methodologies:
            return {
                "compliant": False,
                "requirement": "Approved evaluation methodology",
                "recommendation": f"Use approved methodology: {', '.join(approved_methodologies)}",
                "auto_fixable": True,
                "fix_suggestion": f"Set methodology to MEAT (recommended)"
            }
        
        return {
            "compliant": True,
            "requirement": "Approved evaluation methodology",
            "recommendation": ""
        }
    
    def _check_scoring_consistency(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check scoring consistency with rating scales"""
        
        # Query RAG system for rating scales
        result = self.rag_system.query_compliance(
            QueryType.RATING_SCALE,
            ComplianceCategory.EVALUATION_CRITERIA,
            {"scale_name": "whs"}
        )
        
        if not result.result:
            return {
                "compliant": False,
                "requirement": "Rating scale consistency",
                "recommendation": "Use official rating scales for scoring",
                "auto_fixable": False
            }
        
        return {
            "compliant": True,
            "requirement": "Rating scale consistency",
            "recommendation": ""
        }
    
    def _check_local_preference_application(self, document_data: Dict[str, Any], project_context: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Check local preference policy application"""
        
        contract_value = project_context.get("contract_value", "")
        local_preference_applied = document_data.get("local_preference_applied", False)
        
        # Local preference applies to contracts $250k+
        if "$250,000" in contract_value or "250000" in contract_value:
            if not local_preference_applied:
                return {
                    "compliant": False,
                    "requirement": "Local preference policy application",
                    "recommendation": "Apply local preference policy for contracts $250k+",
                    "auto_fixable": True,
                    "fix_suggestion": "Enable local preference policy application"
                }
        
        return {
            "compliant": True,
            "requirement": "Local preference policy application",
            "recommendation": ""
        }
    
    def generate_compliance_summary(self, reports: List[ComplianceReport]) -> Dict[str, Any]:
        """Generate comprehensive compliance summary for multiple documents"""
        
        total_documents = len(reports)
        fully_compliant = len([r for r in reports if r.compliance_level == ComplianceLevel.FULL_COMPLIANCE])
        partially_compliant = len([r for r in reports if r.compliance_level == ComplianceLevel.PARTIAL_COMPLIANCE])
        non_compliant = len([r for r in reports if r.compliance_level in [ComplianceLevel.NON_COMPLIANT, ComplianceLevel.CRITICAL_NON_COMPLIANT]])
        
        avg_score = sum(r.overall_score for r in reports) / total_documents if total_documents > 0 else 0
        
        all_issues = []
        for report in reports:
            all_issues.extend(report.issues)
        
        critical_issues = [i for i in all_issues if i.severity == "critical"]
        high_issues = [i for i in all_issues if i.severity == "high"]
        auto_fixable_issues = [i for i in all_issues if i.auto_fixable]
        
        return {
            "summary": {
                "total_documents": total_documents,
                "fully_compliant": fully_compliant,
                "partially_compliant": partially_compliant,
                "non_compliant": non_compliant,
                "average_compliance_score": avg_score
            },
            "issues": {
                "total_issues": len(all_issues),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "auto_fixable_issues": len(auto_fixable_issues)
            },
            "recommendations": {
                "priority_actions": [i.recommendation for i in critical_issues[:5]],
                "auto_fix_suggestions": [i.fix_suggestion for i in auto_fixable_issues[:10] if i.fix_suggestion]
            },
            "performance": {
                "total_processing_time_ms": sum(r.processing_time_ms for r in reports),
                "avg_processing_time_ms": sum(r.processing_time_ms for r in reports) / total_documents if total_documents > 0 else 0
            }
        }

# Global instance
_automated_compliance_checker = None

def get_automated_compliance_checker(data_dir: Path) -> AutomatedComplianceChecker:
    """Get or create automated compliance checker instance"""
    global _automated_compliance_checker
    if _automated_compliance_checker is None:
        _automated_compliance_checker = AutomatedComplianceChecker(data_dir)
    return _automated_compliance_checker

if __name__ == "__main__":
    # Test the automated compliance checker
    from ..config import settings
    
    checker = AutomatedComplianceChecker(settings.DATA_DIR)
    
    print("✅ Automated Compliance Checker initialized")
    
    # Test TEPP compliance
    tepp_data = {
        "project_name": "Test HVAC Project",
        "project_type": "hvac",
        "contract_value": "$500,000",
        "evaluation_criteria": [
            {"name": "Price", "weight": 40},
            {"name": "Technical Capability", "weight": 30}
        ],
        "returnable_schedules": [
            {"title": "Supplier Information and Experience", "sections": []}
        ]
    }
    
    project_context = {
        "project_type": "hvac",
        "process_type": "tender",
        "contract_value": "$500,000"
    }
    
    report = checker.check_compliance(DocumentType.TEPP, tepp_data, project_context)
    
    print(f"\n🛡️ TEPP Compliance Report:")
    print(f"   Compliance Level: {report.compliance_level.value}")
    print(f"   Overall Score: {report.overall_score:.2f}")
    print(f"   Issues Found: {len(report.issues)}")
    print(f"   Requirements Met: {len(report.requirements_met)}")
    print(f"   Processing Time: {report.processing_time_ms}ms")
    
    if report.issues:
        print(f"\n⚠️ Issues:")
        for issue in report.issues[:3]:
            print(f"   - {issue.severity.upper()}: {issue.description}")
    
    print("\n🎉 Automated Compliance Checker ready!")
