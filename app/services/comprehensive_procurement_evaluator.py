#!/usr/bin/env python3
"""
Comprehensive Procurement Evaluator
Integrates TEPP, Returnable Schedules, RFT, and all technical documents
with supplier response packages for fair and efficient evaluation
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import os

# AI Integration
import google.generativeai as genai
from app.config import settings

class DocumentType(Enum):
    """Types of procurement documents"""
    TEPP = "tepp"
    RFT = "rft"
    RETURNABLE_SCHEDULE = "returnable_schedule"
    TECHNICAL_SPECIFICATION = "technical_specification"
    EVALUATION_CRITERIA = "evaluation_criteria"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    CONTRACT_TERMS = "contract_terms"
    PROJECT_BRIEF = "project_brief"

class EvaluationStatus(Enum):
    """Evaluation status for document items"""
    NOT_EVALUATED = "not_evaluated"
    PARTIALLY_EVALUATED = "partially_evaluated"
    FULLY_EVALUATED = "fully_evaluated"
    NON_COMPLIANT = "non_compliant"
    COMPLIANT = "compliant"

@dataclass
class ProcurementDocument:
    """Base procurement document structure"""
    document_id: str
    document_type: DocumentType
    title: str
    content: str
    metadata: Dict[str, Any]
    created_date: str
    updated_date: str
    version: str
    council: str
    project_id: str

@dataclass
class TEPPDocument(ProcurementDocument):
    """TEPP document with evaluation criteria"""
    evaluation_criteria: List[Dict[str, Any]]
    returnable_schedules: List[Dict[str, Any]]
    compliance_requirements: List[Dict[str, Any]]
    evaluation_methodology: str
    scoring_weights: Dict[str, float]

@dataclass
class RFTDocument(ProcurementDocument):
    """RFT document with requirements"""
    technical_requirements: List[Dict[str, Any]]
    commercial_requirements: List[Dict[str, Any]]
    compliance_requirements: List[Dict[str, Any]]
    submission_requirements: List[Dict[str, Any]]

@dataclass
class ReturnableSchedule:
    """Returnable schedule item"""
    schedule_id: str
    schedule_name: str
    description: str
    required: bool
    evaluation_criteria: List[str]
    scoring_method: str
    max_score: float
    compliance_requirements: List[str]

@dataclass
class SupplierResponse:
    """Supplier response to procurement documents"""
    response_id: str
    supplier_id: str
    supplier_name: str
    document_responses: Dict[str, Any]  # Maps document_id to response content
    returnable_schedule_responses: Dict[str, Any]  # Maps schedule_id to response
    supporting_documents: List[str]  # File paths to supporting documents
    submission_date: str
    compliance_status: Dict[str, str]  # Maps requirement to compliance status

@dataclass
class EvaluationResult:
    """Result of evaluating a supplier response"""
    supplier_id: str
    document_type: DocumentType
    document_id: str
    item_id: str  # Specific item being evaluated
    ai_score: float
    ai_justification: str
    supporting_evidence: List[str]
    compliance_notes: List[str]
    risk_factors: List[str]
    confidence_level: float
    evaluation_date: str
    evaluator_id: str = ""

@dataclass
class ComprehensiveEvaluation:
    """Complete evaluation of a supplier against all procurement documents"""
    evaluation_id: str
    supplier_id: str
    supplier_name: str
    project_id: str
    procurement_documents: List[ProcurementDocument]
    supplier_response: SupplierResponse
    evaluation_results: List[EvaluationResult]
    overall_score: float
    compliance_score: float
    risk_score: float
    final_ranking: int
    evaluation_date: str
    status: str

class ComprehensiveProcurementEvaluator:
    """Comprehensive evaluator that integrates all procurement documents"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.evaluations_dir = data_dir / "comprehensive_evaluations"
        self.evaluations_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Load existing evaluations
        self.evaluations = self._load_evaluations()
    
    def _load_evaluations(self) -> List[ComprehensiveEvaluation]:
        """Load existing evaluations from storage"""
        evaluations = []
        
        if self.evaluations_dir.exists():
            for eval_file in self.evaluations_dir.glob("*.json"):
                try:
                    with open(eval_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        evaluations.append(ComprehensiveEvaluation(**data))
                except Exception as e:
                    print(f"⚠️ Error loading evaluation {eval_file}: {e}")
        
        return evaluations
    
    def start_comprehensive_evaluation(self, 
                                      project_id: str,
                                      procurement_documents: List[ProcurementDocument],
                                      supplier_responses: List[SupplierResponse],
                                      evaluation_criteria: Dict[str, Any]) -> str:
        """Start comprehensive evaluation process"""
        
        evaluation_id = hashlib.md5(f"comp_eval_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Create comprehensive evaluations for each supplier
        for supplier_response in supplier_responses:
            evaluation = ComprehensiveEvaluation(
                evaluation_id=evaluation_id,
                supplier_id=supplier_response.supplier_id,
                supplier_name=supplier_response.supplier_name,
                project_id=project_id,
                procurement_documents=procurement_documents,
                supplier_response=supplier_response,
                evaluation_results=[],
                overall_score=0.0,
                compliance_score=0.0,
                risk_score=0.0,
                final_ranking=0,
                evaluation_date=datetime.now().isoformat(),
                status="in_progress"
            )
            
            # Perform comprehensive AI analysis
            evaluation_results = self._perform_comprehensive_ai_analysis(
                procurement_documents, supplier_response, evaluation_criteria
            )
            evaluation.evaluation_results = evaluation_results
            
            # Calculate scores
            evaluation.overall_score = self._calculate_overall_score(evaluation_results)
            evaluation.compliance_score = self._calculate_compliance_score(evaluation_results)
            evaluation.risk_score = self._calculate_risk_score(evaluation_results)
            
            # Save evaluation
            self._save_evaluation(evaluation)
            self.evaluations.append(evaluation)
        
        # Update rankings
        self._update_rankings(evaluation_id)
        
        return evaluation_id
    
    def _perform_comprehensive_ai_analysis(self, 
                                         procurement_documents: List[ProcurementDocument],
                                         supplier_response: SupplierResponse,
                                         evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Perform comprehensive AI analysis across all procurement documents"""
        
        evaluation_results = []
        
        for document in procurement_documents:
            # Analyze against each document type
            if document.document_type == DocumentType.TEPP:
                results = self._analyze_tepp_compliance(document, supplier_response, evaluation_criteria)
            elif document.document_type == DocumentType.RFT:
                results = self._analyze_rft_compliance(document, supplier_response, evaluation_criteria)
            elif document.document_type == DocumentType.RETURNABLE_SCHEDULE:
                results = self._analyze_returnable_schedule_compliance(document, supplier_response, evaluation_criteria)
            elif document.document_type == DocumentType.TECHNICAL_SPECIFICATION:
                results = self._analyze_technical_compliance(document, supplier_response, evaluation_criteria)
            else:
                results = self._analyze_general_compliance(document, supplier_response, evaluation_criteria)
            
            evaluation_results.extend(results)
        
        return evaluation_results
    
    def _analyze_tepp_compliance(self, 
                               tepp_document: TEPPDocument, 
                               supplier_response: SupplierResponse,
                               evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Analyze supplier response against TEPP document"""
        
        results = []
        
        # Analyze each evaluation criterion
        for criterion in tepp_document.evaluation_criteria:
            try:
                prompt = self._generate_tepp_analysis_prompt(tepp_document, supplier_response, criterion)
                response = self.model.generate_content(prompt)
                
                result = self._parse_ai_response(response.text, criterion, "TEPP")
                result.supplier_id = supplier_response.supplier_id
                result.document_id = tepp_document.document_id
                result.document_type = DocumentType.TEPP
                result.evaluation_date = datetime.now().isoformat()
                
                results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing TEPP criterion {criterion.get('name', 'Unknown')}: {e}")
        
        return results
    
    def _analyze_rft_compliance(self, 
                              rft_document: RFTDocument, 
                              supplier_response: SupplierResponse,
                              evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Analyze supplier response against RFT document"""
        
        results = []
        
        # Analyze technical requirements
        for requirement in rft_document.technical_requirements:
            try:
                prompt = self._generate_rft_analysis_prompt(rft_document, supplier_response, requirement)
                response = self.model.generate_content(prompt)
                
                result = self._parse_ai_response(response.text, requirement, "RFT")
                result.supplier_id = supplier_response.supplier_id
                result.document_id = rft_document.document_id
                result.document_type = DocumentType.RFT
                result.evaluation_date = datetime.now().isoformat()
                
                results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing RFT requirement {requirement.get('name', 'Unknown')}: {e}")
        
        return results
    
    def _analyze_returnable_schedule_compliance(self, 
                                              schedule_document: ProcurementDocument, 
                                              supplier_response: SupplierResponse,
                                              evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Analyze supplier response against returnable schedule"""
        
        results = []
        
        # Analyze each returnable schedule item
        for schedule_item in supplier_response.returnable_schedule_responses:
            try:
                prompt = self._generate_schedule_analysis_prompt(schedule_document, supplier_response, schedule_item)
                response = self.model.generate_content(prompt)
                
                result = self._parse_ai_response(response.text, schedule_item, "Returnable Schedule")
                result.supplier_id = supplier_response.supplier_id
                result.document_id = schedule_document.document_id
                result.document_type = DocumentType.RETURNABLE_SCHEDULE
                result.evaluation_date = datetime.now().isoformat()
                
                results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing schedule item {schedule_item.get('name', 'Unknown')}: {e}")
        
        return results
    
    def _analyze_technical_compliance(self, 
                                    tech_document: ProcurementDocument, 
                                    supplier_response: SupplierResponse,
                                    evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Analyze supplier response against technical specifications"""
        
        results = []
        
        try:
            prompt = self._generate_technical_analysis_prompt(tech_document, supplier_response)
            response = self.model.generate_content(prompt)
            
            result = self._parse_ai_response(response.text, {"name": "Technical Compliance"}, "Technical")
            result.supplier_id = supplier_response.supplier_id
            result.document_id = tech_document.document_id
            result.document_type = DocumentType.TECHNICAL_SPECIFICATION
            result.evaluation_date = datetime.now().isoformat()
            
            results.append(result)
            
        except Exception as e:
            print(f"⚠️ Error analyzing technical compliance: {e}")
        
        return results
    
    def _analyze_general_compliance(self, 
                                  document: ProcurementDocument, 
                                  supplier_response: SupplierResponse,
                                  evaluation_criteria: Dict[str, Any]) -> List[EvaluationResult]:
        """Analyze supplier response against general procurement document"""
        
        results = []
        
        try:
            prompt = self._generate_general_analysis_prompt(document, supplier_response)
            response = self.model.generate_content(prompt)
            
            result = self._parse_ai_response(response.text, {"name": "General Compliance"}, "General")
            result.supplier_id = supplier_response.supplier_id
            result.document_id = document.document_id
            result.document_type = document.document_type
            result.evaluation_date = datetime.now().isoformat()
            
            results.append(result)
            
        except Exception as e:
            print(f"⚠️ Error analyzing general compliance: {e}")
        
        return results
    
    def _generate_tepp_analysis_prompt(self, 
                                    tepp_document: TEPPDocument, 
                                    supplier_response: SupplierResponse, 
                                    criterion: Dict[str, Any]) -> str:
        """Generate AI prompt for TEPP analysis"""
        
        return f"""
        You are an expert procurement evaluator analyzing a supplier response against TEPP evaluation criteria.
        
        TEPP DOCUMENT:
        - Title: {tepp_document.title}
        - Evaluation Methodology: {tepp_document.evaluation_methodology}
        - Scoring Weights: {tepp_document.scoring_weights}
        
        EVALUATION CRITERION:
        - Name: {criterion.get('name', 'Unknown')}
        - Description: {criterion.get('description', 'No description')}
        - Weight: {criterion.get('weight', 0)}%
        - Scoring Method: {criterion.get('scoring_method', 'Standard')}
        
        SUPPLIER RESPONSE:
        - Supplier: {supplier_response.supplier_name}
        - Response Content: {supplier_response.document_responses.get(tepp_document.document_id, 'No response')}
        - Supporting Documents: {len(supplier_response.supporting_documents)} files
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "score": <float between 0-5>,
            "justification": "<detailed justification for the score>",
            "supporting_evidence": ["<evidence 1>", "<evidence 2>"],
            "confidence_level": <float between 0-1>,
            "compliance_notes": ["<compliance note 1>", "<compliance note 2>"],
            "risk_factors": ["<risk 1>", "<risk 2>"]
        }}
        
        Focus on:
        1. How well the supplier addresses the specific TEPP criterion
        2. Evidence from their response documents
        3. Compliance with NSW Local Government requirements
        4. Risk factors and mitigation strategies
        5. Value for money considerations
        """
    
    def _generate_rft_analysis_prompt(self, 
                                    rft_document: RFTDocument, 
                                    supplier_response: SupplierResponse, 
                                    requirement: Dict[str, Any]) -> str:
        """Generate AI prompt for RFT analysis"""
        
        return f"""
        You are an expert procurement evaluator analyzing a supplier response against RFT requirements.
        
        RFT DOCUMENT:
        - Title: {rft_document.title}
        - Technical Requirements: {len(rft_document.technical_requirements)} items
        - Commercial Requirements: {len(rft_document.commercial_requirements)} items
        
        SPECIFIC REQUIREMENT:
        - Name: {requirement.get('name', 'Unknown')}
        - Description: {requirement.get('description', 'No description')}
        - Type: {requirement.get('type', 'Technical')}
        - Mandatory: {requirement.get('mandatory', True)}
        
        SUPPLIER RESPONSE:
        - Supplier: {supplier_response.supplier_name}
        - Response Content: {supplier_response.document_responses.get(rft_document.document_id, 'No response')}
        - Supporting Documents: {len(supplier_response.supporting_documents)} files
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "score": <float between 0-5>,
            "justification": "<detailed justification for the score>",
            "supporting_evidence": ["<evidence 1>", "<evidence 2>"],
            "confidence_level": <float between 0-1>,
            "compliance_notes": ["<compliance note 1>", "<compliance note 2>"],
            "risk_factors": ["<risk 1>", "<risk 2>"]
        }}
        
        Focus on:
        1. How well the supplier meets the specific RFT requirement
        2. Technical capability and experience
        3. Commercial viability and pricing
        4. Compliance with procurement standards
        5. Risk assessment and mitigation
        """
    
    def _generate_schedule_analysis_prompt(self, 
                                         schedule_document: ProcurementDocument, 
                                         supplier_response: SupplierResponse, 
                                         schedule_item: Dict[str, Any]) -> str:
        """Generate AI prompt for returnable schedule analysis"""
        
        return f"""
        You are an expert procurement evaluator analyzing a supplier response against returnable schedule requirements.
        
        RETURNABLE SCHEDULE:
        - Document: {schedule_document.title}
        - Schedule Item: {schedule_item.get('name', 'Unknown')}
        - Description: {schedule_item.get('description', 'No description')}
        - Required: {schedule_item.get('required', True)}
        - Max Score: {schedule_item.get('max_score', 5.0)}
        
        SUPPLIER RESPONSE:
        - Supplier: {supplier_response.supplier_name}
        - Response: {schedule_item.get('response', 'No response')}
        - Supporting Documents: {len(supplier_response.supporting_documents)} files
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "score": <float between 0-{schedule_item.get('max_score', 5.0)}>,
            "justification": "<detailed justification for the score>",
            "supporting_evidence": ["<evidence 1>", "<evidence 2>"],
            "confidence_level": <float between 0-1>,
            "compliance_notes": ["<compliance note 1>", "<compliance note 2>"],
            "risk_factors": ["<risk 1>", "<risk 2>"]
        }}
        
        Focus on:
        1. Completeness of the schedule response
        2. Accuracy and relevance of information provided
        3. Compliance with schedule requirements
        4. Quality of supporting documentation
        5. Risk factors and potential issues
        """
    
    def _generate_technical_analysis_prompt(self, 
                                         tech_document: ProcurementDocument, 
                                         supplier_response: SupplierResponse) -> str:
        """Generate AI prompt for technical specification analysis"""
        
        return f"""
        You are an expert procurement evaluator analyzing a supplier response against technical specifications.
        
        TECHNICAL DOCUMENT:
        - Title: {tech_document.title}
        - Content: {tech_document.content[:1000]}...
        
        SUPPLIER RESPONSE:
        - Supplier: {supplier_response.supplier_name}
        - Response Content: {supplier_response.document_responses.get(tech_document.document_id, 'No response')}
        - Supporting Documents: {len(supplier_response.supporting_documents)} files
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "score": <float between 0-5>,
            "justification": "<detailed justification for the score>",
            "supporting_evidence": ["<evidence 1>", "<evidence 2>"],
            "confidence_level": <float between 0-1>,
            "compliance_notes": ["<compliance note 1>", "<compliance note 2>"],
            "risk_factors": ["<risk 1>", "<risk 2>"]
        }}
        
        Focus on:
        1. Technical capability and experience
        2. Understanding of requirements
        3. Proposed solution quality
        4. Innovation and value-add
        5. Risk assessment and mitigation
        """
    
    def _generate_general_analysis_prompt(self, 
                                       document: ProcurementDocument, 
                                       supplier_response: SupplierResponse) -> str:
        """Generate AI prompt for general document analysis"""
        
        return f"""
        You are an expert procurement evaluator analyzing a supplier response against procurement requirements.
        
        DOCUMENT:
        - Title: {document.title}
        - Type: {document.document_type.value}
        - Content: {document.content[:1000]}...
        
        SUPPLIER RESPONSE:
        - Supplier: {supplier_response.supplier_name}
        - Response Content: {supplier_response.document_responses.get(document.document_id, 'No response')}
        - Supporting Documents: {len(supplier_response.supporting_documents)} files
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "score": <float between 0-5>,
            "justification": "<detailed justification for the score>",
            "supporting_evidence": ["<evidence 1>", "<evidence 2>"],
            "confidence_level": <float between 0-1>,
            "compliance_notes": ["<compliance note 1>", "<compliance note 2>"],
            "risk_factors": ["<risk 1>", "<risk 2>"]
        }}
        
        Focus on:
        1. How well the supplier addresses the requirements
        2. Evidence from their response documents
        3. Compliance with procurement standards
        4. Risk factors and mitigation strategies
        5. Overall suitability for the project
        """
    
    def _parse_ai_response(self, response_text: str, item: Dict[str, Any], document_type: str) -> EvaluationResult:
        """Parse AI response into structured result"""
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback parsing
                data = {
                    "score": 3.0,
                    "justification": "AI analysis completed",
                    "supporting_evidence": [],
                    "confidence_level": 0.7,
                    "compliance_notes": [],
                    "risk_factors": []
                }
            
            return EvaluationResult(
                supplier_id="",
                document_type=DocumentType.TEPP,  # Will be set by caller
                document_id="",
                item_id=item.get("name", "Unknown"),
                ai_score=float(data.get("score", 3.0)),
                ai_justification=data.get("justification", "No justification provided"),
                supporting_evidence=data.get("supporting_evidence", []),
                compliance_notes=data.get("compliance_notes", []),
                risk_factors=data.get("risk_factors", []),
                confidence_level=float(data.get("confidence_level", 0.7)),
                evaluation_date=""
            )
            
        except Exception as e:
            print(f"⚠️ Error parsing AI response: {e}")
            return EvaluationResult(
                supplier_id="",
                document_type=DocumentType.TEPP,
                document_id="",
                item_id=item.get("name", "Unknown"),
                ai_score=3.0,
                ai_justification="Error in AI analysis",
                supporting_evidence=[],
                compliance_notes=[],
                risk_factors=[],
                confidence_level=0.0,
                evaluation_date=""
            )
    
    def _calculate_overall_score(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate overall score from all evaluation results"""
        if not evaluation_results:
            return 0.0
        
        total_score = sum(result.ai_score for result in evaluation_results)
        return total_score / len(evaluation_results)
    
    def _calculate_compliance_score(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate compliance score from evaluation results"""
        if not evaluation_results:
            return 0.0
        
        compliance_notes = []
        for result in evaluation_results:
            compliance_notes.extend(result.compliance_notes)
        
        # Simple compliance scoring based on positive/negative notes
        positive_notes = len([note for note in compliance_notes if "compliant" in note.lower() or "meets" in note.lower()])
        total_notes = len(compliance_notes)
        
        if total_notes == 0:
            return 100.0
        
        return (positive_notes / total_notes) * 100.0
    
    def _calculate_risk_score(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate risk score from evaluation results"""
        if not evaluation_results:
            return 0.0
        
        risk_factors = []
        for result in evaluation_results:
            risk_factors.extend(result.risk_factors)
        
        # Risk scoring based on number and severity of risk factors
        high_risk_factors = len([risk for risk in risk_factors if "high" in risk.lower() or "critical" in risk.lower()])
        medium_risk_factors = len([risk for risk in risk_factors if "medium" in risk.lower() or "moderate" in risk.lower()])
        low_risk_factors = len([risk for risk in risk_factors if "low" in risk.lower() or "minor" in risk.lower()])
        
        total_risk_score = (high_risk_factors * 3) + (medium_risk_factors * 2) + (low_risk_factors * 1)
        max_possible_risk = len(risk_factors) * 3
        
        if max_possible_risk == 0:
            return 0.0
        
        return (total_risk_score / max_possible_risk) * 100.0
    
    def _update_rankings(self, evaluation_id: str):
        """Update supplier rankings based on final scores"""
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        evaluations.sort(key=lambda x: x.overall_score, reverse=True)
        
        for i, evaluation in enumerate(evaluations):
            evaluation.final_ranking = i + 1
            self._save_evaluation(evaluation)
    
    def _save_evaluation(self, evaluation: ComprehensiveEvaluation):
        """Save evaluation to storage"""
        try:
            eval_file = self.evaluations_dir / f"{evaluation.evaluation_id}_{evaluation.supplier_id}.json"
            
            # Convert to serializable format
            eval_data = {
                "evaluation_id": evaluation.evaluation_id,
                "supplier_id": evaluation.supplier_id,
                "supplier_name": evaluation.supplier_name,
                "project_id": evaluation.project_id,
                "procurement_documents": [asdict(doc) for doc in evaluation.procurement_documents],
                "supplier_response": asdict(evaluation.supplier_response),
                "evaluation_results": [asdict(result) for result in evaluation.evaluation_results],
                "overall_score": evaluation.overall_score,
                "compliance_score": evaluation.compliance_score,
                "risk_score": evaluation.risk_score,
                "final_ranking": evaluation.final_ranking,
                "evaluation_date": evaluation.evaluation_date,
                "status": evaluation.status
            }
            
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(eval_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error saving evaluation: {e}")
    
    def get_evaluation_summary(self, evaluation_id: str) -> Dict[str, Any]:
        """Get comprehensive evaluation summary"""
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        
        if not evaluations:
            return {"error": "Evaluation not found"}
        
        summary = {
            "evaluation_id": evaluation_id,
            "project_id": evaluations[0].project_id,
            "total_suppliers": len(evaluations),
            "suppliers": []
        }
        
        for evaluation in evaluations:
            supplier_summary = {
                "supplier_id": evaluation.supplier_id,
                "supplier_name": evaluation.supplier_name,
                "overall_score": evaluation.overall_score,
                "compliance_score": evaluation.compliance_score,
                "risk_score": evaluation.risk_score,
                "final_ranking": evaluation.final_ranking,
                "status": evaluation.status,
                "evaluation_date": evaluation.evaluation_date
            }
            
            summary["suppliers"].append(supplier_summary)
        
        return summary
