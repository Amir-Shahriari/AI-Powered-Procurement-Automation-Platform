#!/usr/bin/env python3
"""
TEPP Integration System
Integrates TEPP documents and methodology into collaborative evaluation system
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os

# AI Integration
import google.generativeai as genai
from app.config import settings

class TEPPComplianceLevel(Enum):
    """TEPP compliance levels"""
    FULLY_COMPLIANT = "fully_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"

class TEPPEvaluationMethod(Enum):
    """TEPP evaluation methods"""
    LOWEST_PRICE_CONFORMING = "lowest_price_conforming"
    MEAT = "meat"  # Most Economically Advantageous Tender
    COST_BENEFIT = "cost_benefit"
    QUALITY_COST_RATIO = "quality_cost_ratio"

@dataclass
class TEPPCriterion:
    """TEPP evaluation criterion"""
    criterion_id: str
    name: str
    description: str
    weight: float
    max_score: float
    evaluation_method: TEPPEvaluationMethod
    compliance_requirements: List[str]
    scoring_guidelines: str
    mandatory: bool = False
    tier: str = "primary"  # primary, secondary, tertiary

@dataclass
class TEPPWeighting:
    """TEPP weighting structure"""
    price_weight: float
    quality_weight: float
    experience_weight: float
    compliance_weight: float
    innovation_weight: float = 0.0
    sustainability_weight: float = 0.0
    local_content_weight: float = 0.0

@dataclass
class ReturnableScheduleItem:
    """Returnable Schedule item mapping"""
    item_id: str
    item_name: str
    description: str
    tepp_criterion_id: str
    mandatory: bool
    response_type: str  # text, file, yes_no, multiple_choice
    validation_rules: List[str]
    scoring_weight: float
    compliance_indicators: List[str]

@dataclass
class TEPPComplianceResult:
    """TEPP compliance validation result"""
    item_id: str
    criterion_id: str
    compliance_level: TEPPComplianceLevel
    compliance_score: float
    issues_found: List[str]
    recommendations: List[str]
    evidence_provided: List[str]
    missing_requirements: List[str]

@dataclass
class TEPPEvaluationSession:
    """TEPP evaluation session"""
    session_id: str
    project_id: str
    project_title: str
    tepp_document_id: str
    evaluation_method: TEPPEvaluationMethod
    criteria: List[TEPPCriterion]
    weightings: TEPPWeighting
    returnable_schedule_items: List[ReturnableScheduleItem]
    supplier_responses: Dict[str, Dict[str, Any]]
    compliance_results: List[TEPPComplianceResult]
    created_date: str
    last_updated: str
    status: str = "active"

class TEPPIntegrationSystem:
    """TEPP Integration System for collaborative evaluation"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.tepp_dir = data_dir / "tepp_documents"
        self.evaluations_dir = data_dir / "tepp_evaluations"
        self.returnable_schedules_dir = data_dir / "returnable_schedules"
        
        # Create directories if they don't exist
        self.tepp_dir.mkdir(exist_ok=True)
        self.evaluations_dir.mkdir(exist_ok=True)
        self.returnable_schedules_dir.mkdir(exist_ok=True)
        
        # Initialize AI model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Load TEPP templates and standards
        self.tepp_templates = self._load_tepp_templates()
        self.evaluation_sessions = self._load_evaluation_sessions()
    
    def _load_tepp_templates(self) -> Dict[str, Any]:
        """Load TEPP templates and standards"""
        templates = {}
        
        # Load from templates_catalog if available
        templates_path = Path("app/templates_catalog")
        if templates_path.exists():
            for template_file in templates_path.glob("**/*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates[template_file.stem] = template_data
                except Exception as e:
                    print(f"⚠️ Error loading template {template_file}: {e}")
        
        return templates
    
    def _load_evaluation_sessions(self) -> List[TEPPEvaluationSession]:
        """Load existing TEPP evaluation sessions"""
        sessions = []
        
        if self.evaluations_dir.exists():
            for session_file in self.evaluations_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        session = TEPPEvaluationSession(**session_data)
                        sessions.append(session)
                except Exception as e:
                    print(f"⚠️ Error loading session {session_file}: {e}")
        
        return sessions
    
    def create_tepp_evaluation_session(self, 
                                     project_id: str, 
                                     project_title: str,
                                     tepp_document_path: str,
                                     evaluation_method: TEPPEvaluationMethod) -> str:
        """Create a new TEPP evaluation session"""
        
        session_id = f"tepp_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze TEPP document to extract criteria and weightings
        tepp_analysis = self._analyze_tepp_document(tepp_document_path)
        
        # Create evaluation session
        session = TEPPEvaluationSession(
            session_id=session_id,
            project_id=project_id,
            project_title=project_title,
            tepp_document_id=tepp_analysis.get("document_id", ""),
            evaluation_method=evaluation_method,
            criteria=tepp_analysis.get("criteria", []),
            weightings=tepp_analysis.get("weightings", TEPPWeighting(0.4, 0.3, 0.2, 0.1)),
            returnable_schedule_items=tepp_analysis.get("returnable_schedule_items", []),
            supplier_responses={},
            compliance_results=[],
            created_date=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        # Save session
        self._save_evaluation_session(session)
        self.evaluation_sessions.append(session)
        
        return session_id
    
    def _analyze_tepp_document(self, tepp_document_path: str) -> Dict[str, Any]:
        """Analyze TEPP document to extract criteria and structure"""
        
        try:
            # Read TEPP document
            with open(tepp_document_path, 'r', encoding='utf-8') as f:
                tepp_content = f.read()
            
            # Use AI to analyze TEPP document
            prompt = f"""
            Analyze this TEPP (Tender Evaluation Plan & Process) document and extract:
            
            1. Evaluation criteria with weights and scoring guidelines
            2. Returnable Schedule items and their requirements
            3. Compliance requirements and validation rules
            4. Evaluation methodology and scoring framework
            
            TEPP Document Content:
            {tepp_content}
            
            Return the analysis in JSON format with the following structure:
            {{
                "document_id": "unique_document_id",
                "criteria": [
                    {{
                        "criterion_id": "criterion_1",
                        "name": "Criterion Name",
                        "description": "Detailed description",
                        "weight": 0.3,
                        "max_score": 100,
                        "evaluation_method": "meat",
                        "compliance_requirements": ["requirement1", "requirement2"],
                        "scoring_guidelines": "Detailed scoring guidelines",
                        "mandatory": true,
                        "tier": "primary"
                    }}
                ],
                "weightings": {{
                    "price_weight": 0.4,
                    "quality_weight": 0.3,
                    "experience_weight": 0.2,
                    "compliance_weight": 0.1
                }},
                "returnable_schedule_items": [
                    {{
                        "item_id": "item_1",
                        "item_name": "Item Name",
                        "description": "Item description",
                        "tepp_criterion_id": "criterion_1",
                        "mandatory": true,
                        "response_type": "text",
                        "validation_rules": ["rule1", "rule2"],
                        "scoring_weight": 0.5,
                        "compliance_indicators": ["indicator1", "indicator2"]
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                analysis = json.loads(response.text)
                return analysis
            except json.JSONDecodeError:
                # Fallback to basic structure if AI response is not valid JSON
                return self._create_fallback_tepp_analysis()
                
        except Exception as e:
            print(f"⚠️ Error analyzing TEPP document: {e}")
            return self._create_fallback_tepp_analysis()
    
    def _create_fallback_tepp_analysis(self) -> Dict[str, Any]:
        """Create fallback TEPP analysis structure"""
        return {
            "document_id": f"tepp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "criteria": [
                TEPPCriterion(
                    criterion_id="price",
                    name="Price",
                    description="Total cost evaluation",
                    weight=0.4,
                    max_score=100,
                    evaluation_method=TEPPEvaluationMethod.LOWEST_PRICE_CONFORMING,
                    compliance_requirements=["Valid pricing", "No hidden costs"],
                    scoring_guidelines="Lower price gets higher score",
                    mandatory=True,
                    tier="primary"
                ),
                TEPPCriterion(
                    criterion_id="quality",
                    name="Quality",
                    description="Quality of goods/services",
                    weight=0.3,
                    max_score=100,
                    evaluation_method=TEPPEvaluationMethod.MEAT,
                    compliance_requirements=["Quality standards", "Specifications"],
                    scoring_guidelines="Higher quality gets higher score",
                    mandatory=True,
                    tier="primary"
                ),
                TEPPCriterion(
                    criterion_id="experience",
                    name="Experience",
                    description="Supplier experience and capability",
                    weight=0.2,
                    max_score=100,
                    evaluation_method=TEPPEvaluationMethod.MEAT,
                    compliance_requirements=["Relevant experience", "References"],
                    scoring_guidelines="More relevant experience gets higher score",
                    mandatory=True,
                    tier="primary"
                ),
                TEPPCriterion(
                    criterion_id="compliance",
                    name="Compliance",
                    description="Regulatory and policy compliance",
                    weight=0.1,
                    max_score=100,
                    evaluation_method=TEPPEvaluationMethod.MEAT,
                    compliance_requirements=["Legal compliance", "Policy adherence"],
                    scoring_guidelines="Full compliance gets higher score",
                    mandatory=True,
                    tier="primary"
                )
            ],
            "weightings": TEPPWeighting(0.4, 0.3, 0.2, 0.1),
            "returnable_schedule_items": []
        }
    
    def map_supplier_response_to_tepp(self, 
                                    session_id: str, 
                                    supplier_id: str, 
                                    response_data: Dict[str, Any]) -> List[TEPPComplianceResult]:
        """Map supplier response to TEPP criteria and validate compliance"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return []
        
        compliance_results = []
        
        for item in session.returnable_schedule_items:
            # Get supplier response for this item
            supplier_response = response_data.get(item.item_id, {})
            
            # Validate compliance
            compliance_result = self._validate_tepp_compliance(
                item, 
                supplier_response, 
                session.criteria
            )
            
            compliance_results.append(compliance_result)
        
        # Update session with compliance results
        session.compliance_results.extend(compliance_results)
        session.last_updated = datetime.now().isoformat()
        self._save_evaluation_session(session)
        
        return compliance_results
    
    def _validate_tepp_compliance(self, 
                                item: ReturnableScheduleItem, 
                                response: Dict[str, Any], 
                                criteria: List[TEPPCriterion]) -> TEPPComplianceResult:
        """Validate TEPP compliance for a specific item"""
        
        # Find the corresponding criterion
        criterion = next((c for c in criteria if c.criterion_id == item.tepp_criterion_id), None)
        if not criterion:
            return TEPPComplianceResult(
                item_id=item.item_id,
                criterion_id=item.tepp_criterion_id,
                compliance_level=TEPPComplianceLevel.NOT_APPLICABLE,
                compliance_score=0.0,
                issues_found=["Criterion not found"],
                recommendations=["Update criterion mapping"],
                evidence_provided=[],
                missing_requirements=item.compliance_indicators
            )
        
        # Check if response is provided
        if not response or not response.get("value"):
            return TEPPComplianceResult(
                item_id=item.item_id,
                criterion_id=item.tepp_criterion_id,
                compliance_level=TEPPComplianceLevel.NON_COMPLIANT,
                compliance_score=0.0,
                issues_found=["No response provided"],
                recommendations=["Provide response for this item"],
                evidence_provided=[],
                missing_requirements=item.compliance_indicators
            )
        
        # Validate response against requirements
        issues_found = []
        evidence_provided = []
        missing_requirements = []
        
        # Check mandatory requirements
        if item.mandatory and not response.get("value"):
            issues_found.append("Mandatory item not provided")
            missing_requirements.append("Response required")
        
        # Check compliance indicators
        for indicator in item.compliance_indicators:
            if indicator.lower() in str(response.get("value", "")).lower():
                evidence_provided.append(indicator)
            else:
                missing_requirements.append(indicator)
        
        # Calculate compliance score
        if not issues_found and len(evidence_provided) >= len(item.compliance_indicators) * 0.8:
            compliance_level = TEPPComplianceLevel.FULLY_COMPLIANT
            compliance_score = 100.0
        elif len(evidence_provided) >= len(item.compliance_indicators) * 0.5:
            compliance_level = TEPPComplianceLevel.PARTIALLY_COMPLIANT
            compliance_score = 60.0
        else:
            compliance_level = TEPPComplianceLevel.NON_COMPLIANT
            compliance_score = 20.0
        
        # Generate recommendations
        recommendations = []
        if missing_requirements:
            recommendations.append(f"Address missing requirements: {', '.join(missing_requirements)}")
        if issues_found:
            recommendations.append(f"Resolve issues: {', '.join(issues_found)}")
        if not recommendations:
            recommendations.append("Response meets all requirements")
        
        return TEPPComplianceResult(
            item_id=item.item_id,
            criterion_id=item.tepp_criterion_id,
            compliance_level=compliance_level,
            compliance_score=compliance_score,
            issues_found=issues_found,
            recommendations=recommendations,
            evidence_provided=evidence_provided,
            missing_requirements=missing_requirements
        )
    
    def calculate_tepp_scores(self, session_id: str, supplier_id: str) -> Dict[str, Any]:
        """Calculate TEPP-based scores for a supplier"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Get supplier's compliance results
        supplier_compliance = [r for r in session.compliance_results 
                             if r.item_id in session.supplier_responses.get(supplier_id, {})]
        
        if not supplier_compliance:
            return {"error": "No compliance data found for supplier"}
        
        # Calculate scores by criterion
        criterion_scores = {}
        for criterion in session.criteria:
            criterion_compliance = [r for r in supplier_compliance 
                                  if r.criterion_id == criterion.criterion_id]
            
            if criterion_compliance:
                avg_score = sum(r.compliance_score for r in criterion_compliance) / len(criterion_compliance)
                weighted_score = avg_score * criterion.weight
                
                criterion_scores[criterion.criterion_id] = {
                    "raw_score": avg_score,
                    "weighted_score": weighted_score,
                    "weight": criterion.weight,
                    "max_score": criterion.max_score,
                    "compliance_level": criterion_compliance[0].compliance_level.value
                }
            else:
                criterion_scores[criterion.criterion_id] = {
                    "raw_score": 0.0,
                    "weighted_score": 0.0,
                    "weight": criterion.weight,
                    "max_score": criterion.max_score,
                    "compliance_level": "not_applicable"
                }
        
        # Calculate total score
        total_score = sum(score["weighted_score"] for score in criterion_scores.values())
        
        # Calculate overall compliance level
        compliance_levels = [score["compliance_level"] for score in criterion_scores.values()]
        if all(level == "fully_compliant" for level in compliance_levels):
            overall_compliance = TEPPComplianceLevel.FULLY_COMPLIANT
        elif any(level == "fully_compliant" for level in compliance_levels):
            overall_compliance = TEPPComplianceLevel.PARTIALLY_COMPLIANT
        else:
            overall_compliance = TEPPComplianceLevel.NON_COMPLIANT
        
        return {
            "supplier_id": supplier_id,
            "total_score": total_score,
            "overall_compliance": overall_compliance.value,
            "criterion_scores": criterion_scores,
            "compliance_results": [
                {
                    "item_id": r.item_id,
                    "criterion_id": r.criterion_id,
                    "compliance_level": r.compliance_level.value,
                    "compliance_score": r.compliance_score,
                    "issues_found": r.issues_found,
                    "recommendations": r.recommendations
                }
                for r in supplier_compliance
            ]
        }
    
    def get_tepp_evaluation_dashboard_data(self, session_id: str) -> Dict[str, Any]:
        """Get dashboard data for TEPP evaluation session"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Calculate scores for all suppliers
        supplier_scores = {}
        for supplier_id in session.supplier_responses.keys():
            scores = self.calculate_tepp_scores(session_id, supplier_id)
            if "error" not in scores:
                supplier_scores[supplier_id] = scores
        
        # Sort suppliers by score
        ranked_suppliers = sorted(supplier_scores.items(), 
                                key=lambda x: x[1]["total_score"], 
                                reverse=True)
        
        return {
            "session_id": session_id,
            "project_title": session.project_title,
            "evaluation_method": session.evaluation_method.value,
            "total_criteria": len(session.criteria),
            "total_suppliers": len(session.supplier_responses),
            "ranked_suppliers": [
                {
                    "supplier_id": supplier_id,
                    "total_score": scores["total_score"],
                    "overall_compliance": scores["overall_compliance"],
                    "rank": i + 1
                }
                for i, (supplier_id, scores) in enumerate(ranked_suppliers)
            ],
            "criteria_summary": [
                {
                    "criterion_id": c.criterion_id,
                    "name": c.name,
                    "weight": c.weight,
                    "max_score": c.max_score,
                    "mandatory": c.mandatory
                }
                for c in session.criteria
            ],
            "compliance_summary": {
                "total_items": len(session.returnable_schedule_items),
                "mandatory_items": len([i for i in session.returnable_schedule_items if i.mandatory]),
                "compliance_results": len(session.compliance_results)
            }
        }
    
    def _get_evaluation_session(self, session_id: str) -> Optional[TEPPEvaluationSession]:
        """Get evaluation session by ID"""
        return next((s for s in self.evaluation_sessions if s.session_id == session_id), None)
    
    def _save_evaluation_session(self, session: TEPPEvaluationSession):
        """Save evaluation session to file"""
        try:
            session_file = self.evaluations_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving evaluation session: {e}")
    
    def get_active_tepp_sessions(self) -> List[Dict[str, Any]]:
        """Get all active TEPP evaluation sessions"""
        return [
            {
                "session_id": session.session_id,
                "project_id": session.project_id,
                "project_title": session.project_title,
                "evaluation_method": session.evaluation_method.value,
                "total_criteria": len(session.criteria),
                "total_suppliers": len(session.supplier_responses),
                "created_date": session.created_date,
                "last_updated": session.last_updated,
                "status": session.status
            }
            for session in self.evaluation_sessions
            if session.status == "active"
        ]
    
    def apply_tepp_weightings(self, session_id: str, custom_weightings: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Apply TEPP-specified weightings and scoring scales"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Use custom weightings if provided, otherwise use session weightings
        if custom_weightings:
            weightings = TEPPWeighting(**custom_weightings)
        else:
            weightings = session.weightings
        
        # Validate weightings sum to 1.0
        total_weight = (weightings.price_weight + weightings.quality_weight + 
                       weightings.experience_weight + weightings.compliance_weight +
                       weightings.innovation_weight + weightings.sustainability_weight + 
                       weightings.local_content_weight)
        
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
            return {"error": f"Weightings must sum to 1.0, current sum: {total_weight:.3f}"}
        
        # Update session weightings
        session.weightings = weightings
        session.last_updated = datetime.now().isoformat()
        self._save_evaluation_session(session)
        
        # Recalculate all supplier scores with new weightings
        updated_scores = {}
        for supplier_id in session.supplier_responses.keys():
            scores = self.calculate_tepp_scores(session_id, supplier_id)
            if "error" not in scores:
                updated_scores[supplier_id] = scores
        
        return {
            "session_id": session_id,
            "weightings_applied": {
                "price_weight": weightings.price_weight,
                "quality_weight": weightings.quality_weight,
                "experience_weight": weightings.experience_weight,
                "compliance_weight": weightings.compliance_weight,
                "innovation_weight": weightings.innovation_weight,
                "sustainability_weight": weightings.sustainability_weight,
                "local_content_weight": weightings.local_content_weight
            },
            "updated_scores": updated_scores,
            "total_suppliers": len(updated_scores)
        }
    
    def score_returnable_schedule_items(self, session_id: str, supplier_id: str) -> Dict[str, Any]:
        """Implement item-by-item scoring of Returnable Schedule responses against TEPP criteria"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        supplier_responses = session.supplier_responses.get(supplier_id, {})
        if not supplier_responses:
            return {"error": "No responses found for supplier"}
        
        item_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for item in session.returnable_schedule_items:
            # Get supplier response for this item
            response = supplier_responses.get(item.item_id, {})
            
            # Calculate item score based on TEPP criteria
            item_score = self._calculate_item_score(item, response, session.criteria)
            
            # Apply item weighting
            weighted_score = item_score * item.scoring_weight
            total_weighted_score += weighted_score
            total_weight += item.scoring_weight
            
            item_scores[item.item_id] = {
                "item_name": item.item_name,
                "criterion_id": item.tepp_criterion_id,
                "mandatory": item.mandatory,
                "response_type": item.response_type,
                "raw_score": item_score,
                "weight": item.scoring_weight,
                "weighted_score": weighted_score,
                "response_value": response.get("value", ""),
                "compliance_status": self._assess_compliance_status(item, response)
            }
        
        # Calculate final score
        final_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "supplier_id": supplier_id,
            "final_score": final_score,
            "total_weight": total_weight,
            "item_scores": item_scores,
            "scoring_summary": {
                "total_items": len(session.returnable_schedule_items),
                "mandatory_items": len([i for i in session.returnable_schedule_items if i.mandatory]),
                "scored_items": len([s for s in item_scores.values() if s["raw_score"] > 0]),
                "compliance_rate": len([s for s in item_scores.values() if s["compliance_status"] == "compliant"]) / len(item_scores) if item_scores else 0
            }
        }
    
    def _calculate_item_score(self, item: ReturnableScheduleItem, response: Dict[str, Any], criteria: List[TEPPCriterion]) -> float:
        """Calculate score for a specific returnable schedule item"""
        
        # Find the corresponding criterion
        criterion = next((c for c in criteria if c.criterion_id == item.tepp_criterion_id), None)
        if not criterion:
            return 0.0
        
        # Get response value
        response_value = response.get("value", "")
        if not response_value:
            return 0.0
        
        # Calculate score based on response type and criterion
        if item.response_type == "yes_no":
            return 100.0 if response_value.lower() in ["yes", "true", "1"] else 0.0
        
        elif item.response_type == "text":
            # Score based on content quality and completeness
            score = self._score_text_response(response_value, criterion)
            return min(score, criterion.max_score)
        
        elif item.response_type == "file":
            # Score based on file presence and type
            score = self._score_file_response(response_value, criterion)
            return min(score, criterion.max_score)
        
        elif item.response_type == "multiple_choice":
            # Score based on selected option
            score = self._score_multiple_choice_response(response_value, criterion)
            return min(score, criterion.max_score)
        
        else:
            # Default scoring
            return 50.0 if response_value else 0.0
    
    def _score_text_response(self, response_value: str, criterion: TEPPCriterion) -> float:
        """Score text response based on content quality"""
        
        # Basic scoring factors
        length_score = min(len(response_value) / 100, 1.0) * 20  # Up to 20 points for length
        completeness_score = 30 if len(response_value.split()) >= 10 else 10  # Up to 30 points for completeness
        
        # AI-powered content analysis
        try:
            prompt = f"""
            Score this response for the criterion: {criterion.name}
            Description: {criterion.description}
            Scoring Guidelines: {criterion.scoring_guidelines}
            
            Response: {response_value}
            
            Rate the response from 0-50 based on:
            1. Relevance to the criterion
            2. Completeness of information
            3. Quality of explanation
            4. Professional presentation
            
            Return only a number between 0-50.
            """
            
            ai_response = self.model.generate_content(prompt)
            ai_score = float(ai_response.text.strip())
            ai_score = max(0, min(50, ai_score))  # Clamp between 0-50
            
        except Exception:
            ai_score = 25  # Default score if AI analysis fails
        
        return length_score + completeness_score + ai_score
    
    def _score_file_response(self, response_value: str, criterion: TEPPCriterion) -> float:
        """Score file response based on file type and content"""
        
        # Check file type
        file_extension = Path(response_value).suffix.lower()
        supported_types = ['.pdf', '.docx', '.xlsx', '.txt', '.jpg', '.png']
        
        if file_extension in supported_types:
            type_score = 40
        else:
            type_score = 20
        
        # Check if file exists and has content
        file_path = Path(response_value)
        if file_path.exists() and file_path.stat().st_size > 0:
            content_score = 30
        else:
            content_score = 0
        
        return type_score + content_score
    
    def _score_multiple_choice_response(self, response_value: str, criterion: TEPPCriterion) -> float:
        """Score multiple choice response"""
        
        # Map response to score based on criterion
        response_lower = response_value.lower()
        
        if "excellent" in response_lower or "outstanding" in response_lower:
            return 100.0
        elif "good" in response_lower or "satisfactory" in response_lower:
            return 75.0
        elif "fair" in response_lower or "adequate" in response_lower:
            return 50.0
        elif "poor" in response_lower or "unsatisfactory" in response_lower:
            return 25.0
        else:
            return 50.0  # Default score
    
    def _assess_compliance_status(self, item: ReturnableScheduleItem, response: Dict[str, Any]) -> str:
        """Assess compliance status for an item"""
        
        if not response.get("value"):
            return "non_compliant" if item.mandatory else "not_applicable"
        
        # Check against compliance indicators
        response_value = str(response.get("value", "")).lower()
        matching_indicators = [ind for ind in item.compliance_indicators if ind.lower() in response_value]
        
        if len(matching_indicators) >= len(item.compliance_indicators) * 0.8:
            return "compliant"
        elif len(matching_indicators) >= len(item.compliance_indicators) * 0.5:
            return "partially_compliant"
        else:
            return "non_compliant"
    
    def create_tepp_audit_trail(self, session_id: str) -> Dict[str, Any]:
        """Create comprehensive audit trail for TEPP evaluation"""
        
        session = self._get_evaluation_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        audit_trail = {
            "session_id": session_id,
            "project_title": session.project_title,
            "tepp_document_id": session.tepp_document_id,
            "evaluation_method": session.evaluation_method.value,
            "created_date": session.created_date,
            "last_updated": session.last_updated,
            "audit_timestamp": datetime.now().isoformat(),
            "tepp_standards_compliance": {
                "criteria_count": len(session.criteria),
                "weightings_applied": {
                    "price_weight": session.weightings.price_weight,
                    "quality_weight": session.weightings.quality_weight,
                    "experience_weight": session.weightings.experience_weight,
                    "compliance_weight": session.weightings.compliance_weight
                },
                "returnable_schedule_items": len(session.returnable_schedule_items),
                "mandatory_items": len([i for i in session.returnable_schedule_items if i.mandatory])
            },
            "supplier_evaluations": [],
            "compliance_audit": {
                "total_compliance_checks": len(session.compliance_results),
                "compliance_summary": self._generate_compliance_summary(session.compliance_results)
            },
            "evaluation_timeline": {
                "session_created": session.created_date,
                "last_updated": session.last_updated,
                "evaluation_duration": self._calculate_evaluation_duration(session)
            }
        }
        
        # Add supplier evaluation details
        for supplier_id, responses in session.supplier_responses.items():
            supplier_scores = self.calculate_tepp_scores(session_id, supplier_id)
            if "error" not in supplier_scores:
                audit_trail["supplier_evaluations"].append({
                    "supplier_id": supplier_id,
                    "total_score": supplier_scores["total_score"],
                    "overall_compliance": supplier_scores["overall_compliance"],
                    "evaluation_timestamp": datetime.now().isoformat()
                })
        
        # Save audit trail
        audit_file = self.evaluations_dir / f"{session_id}_audit_trail.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_trail, f, indent=2, ensure_ascii=False)
        
        return audit_trail
    
    def _generate_compliance_summary(self, compliance_results: List[TEPPComplianceResult]) -> Dict[str, Any]:
        """Generate compliance summary for audit trail"""
        
        if not compliance_results:
            return {"total_checks": 0, "compliance_rate": 0.0}
        
        compliance_levels = [r.compliance_level.value for r in compliance_results]
        
        return {
            "total_checks": len(compliance_results),
            "fully_compliant": compliance_levels.count("fully_compliant"),
            "partially_compliant": compliance_levels.count("partially_compliant"),
            "non_compliant": compliance_levels.count("non_compliant"),
            "not_applicable": compliance_levels.count("not_applicable"),
            "compliance_rate": compliance_levels.count("fully_compliant") / len(compliance_levels)
        }
    
    def _calculate_evaluation_duration(self, session: TEPPEvaluationSession) -> str:
        """Calculate evaluation duration"""
        
        try:
            start_date = datetime.fromisoformat(session.created_date)
            end_date = datetime.fromisoformat(session.last_updated)
            duration = end_date - start_date
            
            if duration.days > 0:
                return f"{duration.days} days, {duration.seconds // 3600} hours"
            else:
                return f"{duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes"
        except Exception:
            return "Unknown duration"
