"""
Unified Compliance Engine - NSW Procurement Platform
Integrates RAG, Global Compliance, Blacktown Standards, and AI intervention
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd

# Import existing systems
from app.services.blacktown_rag_system import BlacktownRAGSystem
from app.services.global_compliance_manager import GlobalComplianceManager
from app.services.unified_compliance_rag_system import UnifiedComplianceRAGSystem
from app.services.automated_compliance_checker import AutomatedComplianceChecker
from app.services.project_type_manager import ProjectTypeManager, ProjectType, ProcurementProcess
from app.services.advanced_evaluation_system import AdvancedEvaluationSystem, EvaluationModel

logger = logging.getLogger(__name__)

class ProcurementValue(Enum):
    """Procurement value thresholds based on NSW Local Government regulations"""
    QUOTATION = "Under $100,000"
    TENDER = "$100,000 - $249,999"
    FORMAL_TENDER = "$250,000 and above"

class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "✅ Compliant"
    PARTIAL = "⚠️ Partial Compliance"
    NON_COMPLIANT = "❌ Non-Compliant"
    REQUIRES_REVIEW = "🔍 Requires Review"

@dataclass
class ComplianceResult:
    """Result of compliance checking"""
    status: ComplianceStatus
    score: float
    issues: List[str]
    recommendations: List[str]
    applicable_rules: List[str]
    ai_insights: str

@dataclass
class ProcurementFlowStep:
    """Step in the procurement process"""
    step_id: str
    name: str
    description: str
    required_documents: List[str]
    compliance_checks: List[str]
    ai_requirements: List[str]
    next_steps: List[str]
    estimated_time: str
    mandatory: bool

@dataclass
class SmartProcurementFlow:
    """Intelligent procurement flow based on project requirements"""
    project_type: str
    procurement_value: ProcurementValue
    compliance_level: str
    required_steps: List[ProcurementFlowStep]
    ai_interventions: List[str]
    estimated_duration: str
    risk_level: str

class UnifiedComplianceEngine:
    """
    Unified Compliance Engine that integrates all compliance systems
    and provides AI-driven procurement guidance
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        
        # Initialize all compliance systems
        self.blacktown_rag = BlacktownRAGSystem(data_dir)
        self.global_compliance = GlobalComplianceManager(data_dir)
        self.unified_rag = UnifiedComplianceRAGSystem(data_dir)
        self.compliance_checker = AutomatedComplianceChecker(data_dir)
        self.project_manager = ProjectTypeManager(data_dir)
        self.evaluation_system = AdvancedEvaluationSystem(data_dir)
        
        # Load compliance rules and flows
        self._load_compliance_flows()
        self._load_ai_intervention_rules()
    
    def _load_compliance_flows(self):
        """Load NSW procurement compliance flows"""
        self.procurement_flows = {
            ProjectType.CONSTRUCTION: {
                ProcurementValue.QUOTATION: self._get_quotation_flow("construction"),
                ProcurementValue.TENDER: self._get_tender_flow("construction"),
                ProcurementValue.FORMAL_TENDER: self._get_formal_tender_flow("construction")
            },
            ProjectType.FLEET: {
                ProcurementValue.QUOTATION: self._get_quotation_flow("fleet"),
                ProcurementValue.TENDER: self._get_tender_flow("fleet"),
                ProcurementValue.FORMAL_TENDER: self._get_formal_tender_flow("fleet")
            },
            ProjectType.HVAC: {
                ProcurementValue.QUOTATION: self._get_quotation_flow("hvac"),
                ProcurementValue.TENDER: self._get_tender_flow("hvac"),
                ProcurementValue.FORMAL_TENDER: self._get_formal_tender_flow("hvac")
            },
            ProjectType.SERVICES: {
                ProcurementValue.QUOTATION: self._get_quotation_flow("services"),
                ProcurementValue.TENDER: self._get_tender_flow("services"),
                ProcurementValue.FORMAL_TENDER: self._get_formal_tender_flow("services")
            }
        }
    
    def _get_project_type_enum(self, project_type: str) -> ProjectType:
        """Convert project type string to ProjectType enum"""
        project_type_mapping = {
            "Construction": ProjectType.CONSTRUCTION,
            "Fleet": ProjectType.FLEET,
            "HVAC": ProjectType.HVAC,
            "IT Services": ProjectType.IT_SERVICES,
            "Services": ProjectType.SERVICES,
            "General Services": ProjectType.SERVICES
        }
        return project_type_mapping.get(project_type, ProjectType.SERVICES)
    
    def _load_ai_intervention_rules(self):
        """Load AI intervention rules for different scenarios"""
        self.ai_intervention_rules = {
            "compliance_check": {
                "trigger": "Any document upload or evaluation",
                "action": "Real-time compliance verification",
                "ai_models": ["compliance_checker", "rag_analyzer"],
                "output": "Compliance score and recommendations"
            },
            "evaluation_scoring": {
                "trigger": "Supplier response upload",
                "action": "AI-powered scoring with NSW standards",
                "ai_models": ["evaluation_engine", "criteria_matcher"],
                "output": "Weighted scores and rankings"
            },
            "document_generation": {
                "trigger": "Project specification upload",
                "action": "Generate compliant TEPP and schedules",
                "ai_models": ["document_generator", "compliance_ensurer"],
                "output": "NSW-compliant tender documents"
            },
            "risk_assessment": {
                "trigger": "Project setup or supplier evaluation",
                "action": "AI risk analysis and mitigation",
                "ai_models": ["risk_analyzer", "compliance_predictor"],
                "output": "Risk scores and mitigation strategies"
            }
        }
    
    def get_smart_procurement_flow(self, 
                                 project_type: str, 
                                 contract_value: float,
                                 project_details: Dict[str, Any]) -> SmartProcurementFlow:
        """Get intelligent procurement flow based on project requirements"""
        
        # Determine procurement value category
        if contract_value < 100000:
            value_category = ProcurementValue.QUOTATION
        elif contract_value < 250000:
            value_category = ProcurementValue.TENDER
        else:
            value_category = ProcurementValue.FORMAL_TENDER
        
        # Get project type enum
        project_type_enum = self._get_project_type_enum(project_type)
        
        # Get base flow
        base_flow = self.procurement_flows.get(project_type_enum, {}).get(value_category)
        if not base_flow:
            base_flow = self._get_default_flow(value_category)
        
        # Add AI interventions based on project specifics
        ai_interventions = self._determine_ai_interventions(project_type, contract_value, project_details)
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(project_type, contract_value, project_details)
        
        return SmartProcurementFlow(
            project_type=project_type,
            procurement_value=value_category,
            compliance_level="NSW Local Government Standard",
            required_steps=base_flow,
            ai_interventions=ai_interventions,
            estimated_duration=self._estimate_duration(value_category, project_type),
            risk_level=risk_level
        )
    
    def check_comprehensive_compliance(self, 
                                     project_data: Dict[str, Any],
                                     uploaded_documents: List[str],
                                     evaluation_data: Optional[Dict[str, Any]] = None) -> ComplianceResult:
        """Comprehensive compliance checking with AI intervention"""
        
        issues = []
        recommendations = []
        applicable_rules = []
        ai_insights = []
        
        # 1. Check NSW Global Compliance
        global_compliance = self.global_compliance.validate_tender_compliance(project_data)
        if global_compliance["compliance_rate"] < 90:
            issues.extend(global_compliance.get("issues", []))
            recommendations.extend(global_compliance.get("recommendations", []))
        
        # 2. Check Blacktown Standards (if applicable)
        blacktown_compliance = self.blacktown_rag.check_compliance_against_standards(project_data)
        if blacktown_compliance.get("compliance_score", 0) < 85:
            issues.extend(blacktown_compliance.get("issues", []))
            recommendations.extend(blacktown_compliance.get("recommendations", []))
        
        # 3. Check Unified RAG Compliance
        unified_compliance = self.unified_rag.check_compliance(project_data, uploaded_documents)
        if unified_compliance.get("overall_score", 0) < 80:
            issues.extend(unified_compliance.get("violations", []))
            recommendations.extend(unified_compliance.get("suggestions", []))
        
        # 4. AI-powered compliance insights
        ai_insights = self._generate_ai_compliance_insights(project_data, issues, recommendations)
        
        # 5. Calculate overall compliance score
        overall_score = self._calculate_overall_compliance_score(
            global_compliance, blacktown_compliance, unified_compliance
        )
        
        # 6. Determine compliance status
        if overall_score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            status = ComplianceStatus.PARTIAL
        elif overall_score >= 50:
            status = ComplianceStatus.REQUIRES_REVIEW
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        # 7. Get applicable rules
        applicable_rules = self._get_applicable_rules(project_data)
        
        return ComplianceResult(
            status=status,
            score=overall_score,
            issues=issues,
            recommendations=recommendations,
            applicable_rules=applicable_rules,
            ai_insights=ai_insights
        )
    
    def get_ai_guided_evaluation(self, 
                               suppliers: List[Dict[str, Any]],
                               project_type: str,
                               contract_value: float,
                               evaluation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-guided supplier evaluation with compliance integration"""
        
        # 1. Determine best evaluation model based on project characteristics
        evaluation_model = self._select_evaluation_model(project_type, contract_value, evaluation_criteria)
        
        # 2. Apply NSW compliance requirements to evaluation
        compliance_adjusted_criteria = self._adjust_criteria_for_compliance(
            evaluation_criteria, project_type, contract_value
        )
        
        # 3. Run AI-powered evaluation
        evaluation_results = self.evaluation_system.evaluate_suppliers(
            suppliers, evaluation_model, project_type
        )
        
        # 4. Apply compliance scoring adjustments
        compliance_adjusted_results = self._apply_compliance_scoring_adjustments(
            evaluation_results, project_type, contract_value
        )
        
        # 5. Generate AI insights and recommendations
        ai_insights = self._generate_evaluation_insights(
            compliance_adjusted_results, project_type, contract_value
        )
        
        return {
            "evaluation_model": evaluation_model.value,
            "results": compliance_adjusted_results,
            "compliance_adjustments": compliance_adjusted_criteria,
            "ai_insights": ai_insights,
            "recommendations": self._generate_evaluation_recommendations(compliance_adjusted_results)
        }
    
    def generate_compliance_driven_documents(self, 
                                           project_spec: Dict[str, Any],
                                           project_type: str,
                                           contract_value: float) -> Dict[str, Any]:
        """Generate documents with full compliance integration"""
        
        # 1. Get compliance requirements for project
        compliance_requirements = self._get_project_compliance_requirements(project_type, contract_value)
        
        # 2. Generate TEPP with compliance integration
        tepp_data = self._generate_compliant_tepp(project_spec, compliance_requirements)
        
        # 3. Generate returnable schedules with compliance requirements
        returnable_schedules = self._generate_compliant_returnable_schedules(
            project_spec, compliance_requirements
        )
        
        # 4. Generate evaluation criteria with NSW standards
        evaluation_criteria = self._generate_compliant_evaluation_criteria(
            project_type, contract_value, compliance_requirements
        )
        
        # 5. AI validation of generated documents
        ai_validation = self._validate_generated_documents(
            tepp_data, returnable_schedules, evaluation_criteria, compliance_requirements
        )
        
        return {
            "tepp": tepp_data,
            "returnable_schedules": returnable_schedules,
            "evaluation_criteria": evaluation_criteria,
            "compliance_requirements": compliance_requirements,
            "ai_validation": ai_validation,
            "compliance_score": ai_validation.get("overall_compliance_score", 0)
        }
    
    def _get_quotation_flow(self, project_type: str) -> List[ProcurementFlowStep]:
        """Get quotation flow for specific project type"""
        return [
            ProcurementFlowStep(
                step_id="spec_prep",
                name="Specification Preparation",
                description="Prepare detailed project specification",
                required_documents=["Project Specification", "Technical Requirements"],
                compliance_checks=["NSW Guidelines", "WHS Requirements", "Environmental Standards"],
                ai_requirements=["Document analysis", "Compliance verification", "Risk assessment"],
                next_steps=["Supplier identification", "Quote request"],
                estimated_time="1-2 weeks",
                mandatory=True
            ),
            ProcurementFlowStep(
                step_id="supplier_id",
                name="Supplier Identification",
                description="Identify and invite qualified suppliers",
                required_documents=["Supplier Database", "Qualification Criteria"],
                compliance_checks=["Local Preference Policy", "Supplier Registration"],
                ai_requirements=["Supplier matching", "Compliance checking"],
                next_steps=["Quote evaluation"],
                estimated_time="3-5 days",
                mandatory=True
            ),
            ProcurementFlowStep(
                step_id="quote_eval",
                name="Quote Evaluation",
                description="Evaluate received quotes",
                required_documents=["Quote Responses", "Evaluation Matrix"],
                compliance_checks=["Price comparison", "Technical compliance", "WHS compliance"],
                ai_requirements=["AI scoring", "Compliance verification", "Risk analysis"],
                next_steps=["Contract award"],
                estimated_time="1 week",
                mandatory=True
            )
        ]
    
    def _get_tender_flow(self, project_type: str) -> List[ProcurementFlowStep]:
        """Get tender flow for specific project type"""
        base_flow = self._get_quotation_flow(project_type)
        
        # Add tender-specific steps
        tender_steps = [
            ProcurementFlowStep(
                step_id="tender_prep",
                name="Tender Document Preparation",
                description="Prepare comprehensive tender documents",
                required_documents=["TEPP", "Returnable Schedules", "Conditions of Contract"],
                compliance_checks=["NSW Tender Guidelines", "Legal Requirements", "Probity Standards"],
                ai_requirements=["Document generation", "Compliance verification", "Risk assessment"],
                next_steps=["Tender advertisement"],
                estimated_time="2-3 weeks",
                mandatory=True
            ),
            ProcurementFlowStep(
                step_id="tender_adv",
                name="Tender Advertisement",
                description="Advertise tender publicly",
                required_documents=["Tender Notice", "Advertisement Material"],
                compliance_checks=["Publicity Requirements", "Accessibility Standards"],
                ai_requirements=["Content optimization", "Reach analysis"],
                next_steps=["Tender evaluation"],
                estimated_time="2-4 weeks",
                mandatory=True
            )
        ]
        
        return tender_steps + base_flow[1:]  # Replace first step, keep evaluation steps
    
    def _get_formal_tender_flow(self, project_type: str) -> List[ProcurementFlowStep]:
        """Get formal tender flow for specific project type"""
        tender_flow = self._get_tender_flow(project_type)
        
        # Add formal tender-specific steps
        formal_steps = [
            ProcurementFlowStep(
                step_id="pre_tender",
                name="Pre-Tender Briefing",
                description="Conduct pre-tender briefing session",
                required_documents=["Briefing Materials", "Q&A Log"],
                compliance_checks=["Probity Requirements", "Fair Access"],
                ai_requirements=["Content preparation", "Q&A analysis"],
                next_steps=["Tender submission"],
                estimated_time="1 week",
                mandatory=True
            ),
            ProcurementFlowStep(
                step_id="evaluation_panel",
                name="Evaluation Panel Setup",
                description="Establish evaluation panel",
                required_documents=["Panel Charter", "Evaluation Criteria"],
                compliance_checks=["Panel Composition", "Conflict of Interest"],
                ai_requirements=["Panel optimization", "Bias detection"],
                next_steps=["Evaluation process"],
                estimated_time="1 week",
                mandatory=True
            )
        ]
        
        return tender_flow + formal_steps
    
    def _get_default_flow(self, value_category: ProcurementValue) -> List[ProcurementFlowStep]:
        """Get default flow for unknown project types"""
        return self._get_quotation_flow("general")
    
    def _determine_ai_interventions(self, project_type: str, contract_value: float, project_details: Dict[str, Any]) -> List[str]:
        """Determine AI interventions based on project characteristics"""
        interventions = []
        
        # Always include compliance checking
        interventions.append("Real-time compliance verification")
        
        # Add based on project complexity
        if contract_value > 100000:
            interventions.append("AI-powered evaluation scoring")
        
        if contract_value > 250000:
            interventions.append("Risk assessment and mitigation")
            interventions.append("Probity monitoring")
        
        # Add based on project type
        if project_type.lower() in ["construction", "fleet"]:
            interventions.append("Technical specification analysis")
            interventions.append("Safety compliance checking")
        
        return interventions
    
    def _calculate_risk_level(self, project_type: str, contract_value: float, project_details: Dict[str, Any]) -> str:
        """Calculate risk level for the project"""
        risk_score = 0
        
        # Value-based risk
        if contract_value > 500000:
            risk_score += 3
        elif contract_value > 250000:
            risk_score += 2
        elif contract_value > 100000:
            risk_score += 1
        
        # Project type risk
        if project_type.lower() in ["construction", "fleet"]:
            risk_score += 2
        elif project_type.lower() == "services":
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return "High Risk"
        elif risk_score >= 2:
            return "Medium Risk"
        else:
            return "Low Risk"
    
    def _estimate_duration(self, value_category: ProcurementValue, project_type: str) -> str:
        """Estimate procurement duration"""
        if value_category == ProcurementValue.QUOTATION:
            return "2-4 weeks"
        elif value_category == ProcurementValue.TENDER:
            return "6-8 weeks"
        else:  # FORMAL_TENDER
            return "12-16 weeks"
    
    def _select_evaluation_model(self, project_type: str, contract_value: float, evaluation_criteria: Dict[str, Any]) -> EvaluationModel:
        """Select best evaluation model based on project characteristics"""
        if contract_value < 100000:
            return EvaluationModel.LOWEST_PRICE_CONFORMING
        elif contract_value < 250000:
            return EvaluationModel.MEAT
        else:
            # For high-value contracts, prefer quality-focused models
            if project_type.lower() in ["construction", "fleet"]:
                return EvaluationModel.TCO
            else:
                return EvaluationModel.QUALITY_COST_RATIO
    
    def _generate_ai_compliance_insights(self, project_data: Dict[str, Any], issues: List[str], recommendations: List[str]) -> str:
        """Generate AI-powered compliance insights"""
        if not issues:
            return "✅ Project appears fully compliant with NSW Local Government requirements. All major compliance areas have been verified."
        
        # Analyze issues and provide insights
        critical_issues = [issue for issue in issues if "critical" in issue.lower() or "mandatory" in issue.lower()]
        if critical_issues:
            return f"⚠️ {len(critical_issues)} critical compliance issues detected. Immediate attention required before proceeding."
        
        return f"📋 {len(issues)} compliance items require attention. Following recommendations will improve compliance score."
    
    def _calculate_overall_compliance_score(self, global_compliance: Dict, blacktown_compliance: Dict, unified_compliance: Dict) -> float:
        """Calculate overall compliance score"""
        scores = []
        
        if global_compliance.get("compliance_rate"):
            scores.append(global_compliance["compliance_rate"])
        
        if blacktown_compliance.get("compliance_score"):
            scores.append(blacktown_compliance["compliance_score"])
        
        if unified_compliance.get("overall_score"):
            scores.append(unified_compliance["overall_score"])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_applicable_rules(self, project_data: Dict[str, Any]) -> List[str]:
        """Get applicable NSW rules for the project"""
        rules = [
            "NSW Local Government Act 1993",
            "NSW Local Government (General) Regulation 2005",
            "NSW Government Procurement Guidelines",
            "Work Health and Safety Act 2011"
        ]
        
        # Add specific rules based on project type
        project_type = project_data.get("project_type", "").lower()
        if project_type in ["construction", "fleet"]:
            rules.extend([
                "Environmental Planning and Assessment Act 1979",
                "Building and Construction Industry Security of Payment Act 1999"
            ])
        
        return rules
