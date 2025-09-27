"""
NSW Local Government Procurement Compliance RAG System
=====================================================

This module provides a comprehensive compliance framework for NSW Local Government
procurement, including RAG (Retrieval-Augmented Generation) capabilities for
ensuring adherence to all relevant guidelines, standards, and regulations.

Compliance Areas Covered:
- NSW Local Government Act 1993
- Tendering Guidelines for NSW Local Government
- NSW Government Procurement Policy Framework
- Work Health and Safety (WHS) Management
- Australian Design Rules (ADR)
- Australian Standards (AS/NZS)
- Environmental Management
- Industrial Relations
- Privacy and Data Protection
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import requests
from dataclasses import dataclass

from app.services.llm import rag_json
from app.services.vectorstores import get_vs, build_index
from app.services.textio import chunks


@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement with its status and details."""
    area: str
    requirement: str
    status: str  # "GREEN", "AMBER", "RED"
    description: str
    source: str
    last_updated: str
    applicable_categories: List[str]
    mandatory: bool = True
    weight: float = 1.0


@dataclass
class ComplianceCheck:
    """Represents the result of a compliance check."""
    requirement: ComplianceRequirement
    compliant: bool
    score: float
    evidence: str
    recommendations: List[str]
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"


class NSWComplianceRAG:
    """
    NSW Local Government Procurement Compliance RAG System
    
    Provides comprehensive compliance checking and guidance for NSW Local Government
    procurement processes, ensuring adherence to all relevant guidelines and standards.
    """
    
    def __init__(self):
        self.compliance_requirements = self._load_compliance_requirements()
        self.vector_store = None
        self._build_compliance_index()
    
    def _load_compliance_requirements(self) -> List[ComplianceRequirement]:
        """Load comprehensive compliance requirements for NSW Local Government."""
        return [
            # NSW Local Government Act 1993 Requirements
            ComplianceRequirement(
                area="NSW Local Government Act 1993",
                requirement="Section 55 - Tendering Requirements",
                status="GREEN",
                description="All contracts over $150,000 must be publicly tendered",
                source="NSW Local Government Act 1993, Section 55",
                last_updated="2024-01-01",
                applicable_categories=["construction", "services", "goods", "consultancy"],
                mandatory=True,
                weight=1.0
            ),
            
            # Tendering Guidelines
            ComplianceRequirement(
                area="Tendering Guidelines",
                requirement="Probity and Transparency",
                status="GREEN",
                description="All procurement processes must maintain probity, transparency, and accountability",
                source="Tendering Guidelines for NSW Local Government",
                last_updated="2024-01-01",
                applicable_categories=["all"],
                mandatory=True,
                weight=1.0
            ),
            
            # WHS Requirements
            ComplianceRequirement(
                area="Work Health and Safety",
                requirement="WHS Management System",
                status="GREEN",
                description="Contractors must have certified WHS management systems",
                source="Work Health and Safety Act 2011",
                last_updated="2024-01-01",
                applicable_categories=["construction", "services", "maintenance"],
                mandatory=True,
                weight=1.0
            ),
            
            # ADR Compliance
            ComplianceRequirement(
                area="Australian Design Rules",
                requirement="Vehicle Safety Standards",
                status="AMBER",
                description="All vehicles must comply with current ADR standards",
                source="Australian Design Rules",
                last_updated="2024-01-01",
                applicable_categories=["vehicles", "transport", "fleet"],
                mandatory=True,
                weight=0.8
            ),
            
            # Environmental Management
            ComplianceRequirement(
                area="Environmental Management",
                requirement="Environmental Impact Assessment",
                status="GREEN",
                description="Environmental considerations must be included in procurement decisions",
                source="Environmental Planning and Assessment Act 1979",
                last_updated="2024-01-01",
                applicable_categories=["construction", "infrastructure", "services"],
                mandatory=True,
                weight=0.9
            ),
            
            # Privacy and Data Protection
            ComplianceRequirement(
                area="Privacy and Data Protection",
                requirement="Privacy Act Compliance",
                status="GREEN",
                description="All data handling must comply with Privacy Act 1988",
                source="Privacy Act 1988",
                last_updated="2024-01-01",
                applicable_categories=["all"],
                mandatory=True,
                weight=1.0
            ),
            
            # Industrial Relations
            ComplianceRequirement(
                area="Industrial Relations",
                requirement="Fair Work Compliance",
                status="GREEN",
                description="All employment practices must comply with Fair Work Act 2009",
                source="Fair Work Act 2009",
                last_updated="2024-01-01",
                applicable_categories=["services", "construction", "maintenance"],
                mandatory=True,
                weight=0.9
            ),
            
            # Australian Standards
            ComplianceRequirement(
                area="Australian Standards",
                requirement="AS/NZS Compliance",
                status="GREEN",
                description="Goods and services must meet relevant Australian Standards",
                source="Standards Australia",
                last_updated="2024-01-01",
                applicable_categories=["goods", "services", "construction"],
                mandatory=True,
                weight=0.8
            ),
            
            # Financial Management
            ComplianceRequirement(
                area="Financial Management",
                requirement="Value for Money",
                status="GREEN",
                description="All procurement must demonstrate value for money",
                source="NSW Government Procurement Policy Framework",
                last_updated="2024-01-01",
                applicable_categories=["all"],
                mandatory=True,
                weight=1.0
            ),
            
            # Risk Management
            ComplianceRequirement(
                area="Risk Management",
                requirement="Risk Assessment",
                status="GREEN",
                description="Comprehensive risk assessment must be conducted",
                source="NSW Government Risk Management Framework",
                last_updated="2024-01-01",
                applicable_categories=["all"],
                mandatory=True,
                weight=0.9
            )
        ]
    
    def _build_compliance_index(self):
        """Build vector index for compliance requirements."""
        compliance_texts = []
        for req in self.compliance_requirements:
            text = f"""
            Area: {req.area}
            Requirement: {req.requirement}
            Description: {req.description}
            Source: {req.source}
            Applicable Categories: {', '.join(req.applicable_categories)}
            Status: {req.status}
            Mandatory: {req.mandatory}
            Weight: {req.weight}
            """
            compliance_texts.append(text)
        
        if compliance_texts:
            compliance_chunks = []
            for text in compliance_texts:
                compliance_chunks.extend(chunks(text))
            
            build_index("compliance", compliance_chunks)
            self.vector_store = get_vs("compliance")
    
    def check_compliance(self, 
                        procurement_category: str,
                        tender_value: float,
                        supplier_info: Dict[str, Any],
                        evaluation_criteria: List[Dict[str, Any]]) -> List[ComplianceCheck]:
        """
        Perform comprehensive compliance checking for a procurement process.
        
        Args:
            procurement_category: Category of procurement (construction, services, etc.)
            tender_value: Value of the tender
            supplier_info: Information about the supplier
            evaluation_criteria: List of evaluation criteria
            
        Returns:
            List of compliance check results
        """
        results = []
        
        for req in self.compliance_requirements:
            if procurement_category.lower() in [cat.lower() for cat in req.applicable_categories] or "all" in req.applicable_categories:
                check = self._perform_compliance_check(req, procurement_category, tender_value, supplier_info, evaluation_criteria)
                results.append(check)
        
        return results
    
    def _perform_compliance_check(self, 
                                 requirement: ComplianceRequirement,
                                 procurement_category: str,
                                 tender_value: float,
                                 supplier_info: Dict[str, Any],
                                 evaluation_criteria: List[Dict[str, Any]]) -> ComplianceCheck:
        """Perform individual compliance check."""
        
        # Use RAG to determine compliance
        prompt = f"""
        Analyze the following procurement scenario for compliance with NSW Local Government requirements:
        
        Procurement Category: {procurement_category}
        Tender Value: ${tender_value:,.2f}
        Supplier Info: {json.dumps(supplier_info, indent=2)}
        Evaluation Criteria: {json.dumps(evaluation_criteria, indent=2)}
        
        Compliance Requirement:
        Area: {requirement.area}
        Requirement: {requirement.requirement}
        Description: {requirement.description}
        Source: {requirement.source}
        
        Determine:
        1. Is this procurement compliant with this requirement? (true/false)
        2. What is the compliance score? (0.0 to 1.0)
        3. What evidence supports this assessment?
        4. What recommendations would improve compliance?
        5. What is the risk level? (LOW/MEDIUM/HIGH/CRITICAL)
        
        Return JSON format:
        {{
            "compliant": boolean,
            "score": float,
            "evidence": "string",
            "recommendations": ["string"],
            "risk_level": "string"
        }}
        """
        
        try:
            if self.vector_store:
                result = rag_json(
                    self.vector_store,
                    prompt,
                    field_queries=[requirement.area, requirement.requirement, procurement_category],
                    max_ctx=5,
                    min_chars=1000
                )
            else:
                # Fallback to basic compliance checking
                result = self._basic_compliance_check(requirement, procurement_category, tender_value, supplier_info)
            
            return ComplianceCheck(
                requirement=requirement,
                compliant=result.get("compliant", False),
                score=result.get("score", 0.0),
                evidence=result.get("evidence", "No evidence provided"),
                recommendations=result.get("recommendations", []),
                risk_level=result.get("risk_level", "MEDIUM")
            )
        except Exception as e:
            return ComplianceCheck(
                requirement=requirement,
                compliant=False,
                score=0.0,
                evidence=f"Error in compliance check: {str(e)}",
                recommendations=["Review compliance requirements manually"],
                risk_level="HIGH"
            )
    
    def _basic_compliance_check(self, 
                               requirement: ComplianceRequirement,
                               procurement_category: str,
                               tender_value: float,
                               supplier_info: Dict[str, Any]) -> Dict[str, Any]:
        """Basic compliance checking without RAG."""
        
        compliant = True
        score = 1.0
        evidence = "Basic compliance check passed"
        recommendations = []
        risk_level = "LOW"
        
        # Basic checks based on requirement type
        if "WHS" in requirement.area:
            if not supplier_info.get("whs_certified", False):
                compliant = False
                score = 0.3
                evidence = "Supplier does not have WHS certification"
                recommendations.append("Require WHS certification from supplier")
                risk_level = "HIGH"
        
        elif "Privacy" in requirement.area:
            if not supplier_info.get("privacy_compliant", False):
                compliant = False
                score = 0.5
                evidence = "Privacy compliance not verified"
                recommendations.append("Verify privacy compliance with supplier")
                risk_level = "MEDIUM"
        
        elif "Value" in requirement.requirement:
            if tender_value > 150000 and not supplier_info.get("public_tender", False):
                compliant = False
                score = 0.0
                evidence = "Contracts over $150,000 must be publicly tendered"
                recommendations.append("Conduct public tender process")
                risk_level = "CRITICAL"
        
        return {
            "compliant": compliant,
            "score": score,
            "evidence": evidence,
            "recommendations": recommendations,
            "risk_level": risk_level
        }
    
    def get_compliance_summary(self, checks: List[ComplianceCheck]) -> Dict[str, Any]:
        """Generate compliance summary from check results."""
        
        total_checks = len(checks)
        compliant_checks = sum(1 for check in checks if check.compliant)
        avg_score = sum(check.score for check in checks) / total_checks if total_checks > 0 else 0
        
        risk_counts = {}
        for check in checks:
            risk_counts[check.risk_level] = risk_counts.get(check.risk_level, 0) + 1
        
        critical_issues = [check for check in checks if check.risk_level == "CRITICAL"]
        high_risk_issues = [check for check in checks if check.risk_level == "HIGH"]
        
        return {
            "total_checks": total_checks,
            "compliant_checks": compliant_checks,
            "compliance_rate": (compliant_checks / total_checks) * 100 if total_checks > 0 else 0,
            "average_score": avg_score,
            "risk_distribution": risk_counts,
            "critical_issues": len(critical_issues),
            "high_risk_issues": len(high_risk_issues),
            "overall_status": "COMPLIANT" if len(critical_issues) == 0 and len(high_risk_issues) == 0 else "NON_COMPLIANT",
            "recommendations": [rec for check in checks for rec in check.recommendations]
        }
    
    def generate_compliance_report(self, checks: List[ComplianceCheck]) -> str:
        """Generate comprehensive compliance report."""
        
        summary = self.get_compliance_summary(checks)
        
        report = f"""
# NSW Local Government Procurement Compliance Report

## Executive Summary
- **Overall Status**: {summary['overall_status']}
- **Compliance Rate**: {summary['compliance_rate']:.1f}%
- **Average Score**: {summary['average_score']:.2f}/1.0
- **Critical Issues**: {summary['critical_issues']}
- **High Risk Issues**: {summary['high_risk_issues']}

## Risk Distribution
"""
        
        for risk_level, count in summary['risk_distribution'].items():
            report += f"- **{risk_level}**: {count} issues\n"
        
        report += "\n## Detailed Compliance Checks\n\n"
        
        for check in checks:
            status_icon = "✅" if check.compliant else "❌"
            risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}[check.risk_level]
            
            report += f"""
### {status_icon} {check.requirement.area} - {check.requirement.requirement}
- **Status**: {check.requirement.status}
- **Compliant**: {check.compliant}
- **Score**: {check.score:.2f}/1.0
- **Risk Level**: {risk_icon} {check.risk_level}
- **Evidence**: {check.evidence}
- **Source**: {check.requirement.source}

#### Recommendations:
"""
            for rec in check.recommendations:
                report += f"- {rec}\n"
            
            report += "\n---\n"
        
        if summary['recommendations']:
            report += "\n## Overall Recommendations\n\n"
            for i, rec in enumerate(set(summary['recommendations']), 1):
                report += f"{i}. {rec}\n"
        
        return report
    
    def update_compliance_requirements(self, new_requirements: List[ComplianceRequirement]):
        """Update compliance requirements with new ones."""
        self.compliance_requirements.extend(new_requirements)
        self._build_compliance_index()
    
    def get_requirements_by_category(self, category: str) -> List[ComplianceRequirement]:
        """Get compliance requirements for a specific category."""
        return [
            req for req in self.compliance_requirements
            if category.lower() in [cat.lower() for cat in req.applicable_categories] or "all" in req.applicable_categories
        ]


# Global compliance RAG instance
compliance_rag = NSWComplianceRAG()


def check_procurement_compliance(procurement_category: str,
                                tender_value: float,
                                supplier_info: Dict[str, Any],
                                evaluation_criteria: List[Dict[str, Any]]) -> Tuple[List[ComplianceCheck], Dict[str, Any]]:
    """
    Convenience function to check procurement compliance.
    
    Returns:
        Tuple of (compliance_checks, summary)
    """
    checks = compliance_rag.check_compliance(procurement_category, tender_value, supplier_info, evaluation_criteria)
    summary = compliance_rag.get_compliance_summary(checks)
    return checks, summary


def generate_compliance_report(checks: List[ComplianceCheck]) -> str:
    """Convenience function to generate compliance report."""
    return compliance_rag.generate_compliance_report(checks)
