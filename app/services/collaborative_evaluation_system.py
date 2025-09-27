#!/usr/bin/env python3
"""
Collaborative Evaluation System
AI-powered initial scoring with human committee consensus finalization
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

class EvaluationStatus(Enum):
    """Evaluation workflow status"""
    AI_ANALYSIS = "ai_analysis"
    COMMITTEE_REVIEW = "committee_review"
    CONSENSUS_MEETING = "consensus_meeting"
    FINALIZED = "finalized"

class CommitteeRole(Enum):
    """Committee member roles"""
    CHAIR = "chair"
    MEMBER = "member"
    OBSERVER = "observer"

@dataclass
class CommitteeMember:
    """Committee member information"""
    member_id: str
    name: str
    email: str
    role: CommitteeRole
    department: str
    phone: str = ""
    is_active: bool = True

@dataclass
class AIScoringResult:
    """AI-generated scoring result"""
    criterion_name: str
    ai_score: float
    ai_justification: str
    supporting_evidence: List[str]
    confidence_level: float
    compliance_notes: List[str]
    risk_factors: List[str]

@dataclass
class MemberEvaluation:
    """Individual committee member evaluation"""
    member_id: str
    member_name: str
    criterion_name: str
    member_score: float
    member_justification: str
    comments: str
    evaluation_date: str
    is_final: bool = False

@dataclass
class ConsensusResult:
    """Final consensus result"""
    criterion_name: str
    final_score: float
    consensus_justification: str
    agreement_level: float
    dissenting_views: List[str]
    finalization_date: str

@dataclass
class SupplierEvaluation:
    """Complete supplier evaluation"""
    supplier_id: str
    supplier_name: str
    evaluation_id: str
    status: EvaluationStatus
    ai_analysis: List[AIScoringResult]
    member_evaluations: List[MemberEvaluation]
    consensus_results: List[ConsensusResult]
    total_score: float
    rank: int
    created_date: str
    finalized_date: str = ""

class CollaborativeEvaluationSystem:
    """AI-powered collaborative evaluation system with human consensus"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.evaluations_dir = data_dir / "collaborative_evaluations"
        self.evaluations_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Load existing evaluations
        self.evaluations = self._load_evaluations()
    
    def _load_evaluations(self) -> List[SupplierEvaluation]:
        """Load existing evaluations from storage"""
        evaluations = []
        
        if self.evaluations_dir.exists():
            for eval_file in self.evaluations_dir.glob("*.json"):
                try:
                    with open(eval_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        evaluations.append(SupplierEvaluation(**data))
                except Exception as e:
                    print(f"⚠️ Error loading evaluation {eval_file}: {e}")
        
        return evaluations
    
    def start_evaluation_process(self, 
                                suppliers: List[Dict[str, Any]], 
                                evaluation_criteria: List[Dict[str, Any]],
                                committee_members: List[CommitteeMember],
                                project_context: Dict[str, Any]) -> str:
        """Start collaborative evaluation process"""
        
        evaluation_id = hashlib.md5(f"eval_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Create evaluation records for each supplier
        for supplier in suppliers:
            evaluation = SupplierEvaluation(
                supplier_id=supplier["id"],
                supplier_name=supplier["name"],
                evaluation_id=evaluation_id,
                status=EvaluationStatus.AI_ANALYSIS,
                ai_analysis=[],
                member_evaluations=[],
                consensus_results=[],
                total_score=0.0,
                rank=0,
                created_date=datetime.now().isoformat()
            )
            
            # Perform AI analysis
            ai_analysis = self._perform_ai_analysis(supplier, evaluation_criteria, project_context)
            evaluation.ai_analysis = ai_analysis
            
            # Save evaluation
            self._save_evaluation(evaluation)
            self.evaluations.append(evaluation)
        
        return evaluation_id
    
    def _perform_ai_analysis(self, 
                           supplier: Dict[str, Any], 
                           criteria: List[Dict[str, Any]], 
                           context: Dict[str, Any]) -> List[AIScoringResult]:
        """Perform AI-powered initial analysis and scoring"""
        
        ai_results = []
        
        for criterion in criteria:
            try:
                # Generate AI analysis prompt
                prompt = self._generate_ai_analysis_prompt(supplier, criterion, context)
                
                # Get AI response
                response = self.model.generate_content(prompt)
                
                # Parse AI response
                ai_result = self._parse_ai_response(response.text, criterion)
                ai_results.append(ai_result)
                
            except Exception as e:
                print(f"⚠️ Error in AI analysis for {criterion['name']}: {e}")
                # Create fallback result
                ai_results.append(AIScoringResult(
                    criterion_name=criterion["name"],
                    ai_score=3.0,  # Neutral score
                    ai_justification="AI analysis unavailable",
                    supporting_evidence=[],
                    confidence_level=0.0,
                    compliance_notes=[],
                    risk_factors=[]
                ))
        
        return ai_results
    
    def _generate_ai_analysis_prompt(self, supplier: Dict[str, Any], criterion: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate AI analysis prompt"""
        
        return f"""
        You are an expert procurement evaluator. Analyze the following supplier submission against the specified criterion.
        
        SUPPLIER INFORMATION:
        - Name: {supplier.get('name', 'Unknown')}
        - Submission: {supplier.get('submission_text', 'No submission provided')}
        - Documents: {supplier.get('documents', [])}
        
        EVALUATION CRITERION:
        - Name: {criterion['name']}
        - Description: {criterion['description']}
        - Weight: {criterion['weight']}%
        - Sub-criteria: {criterion.get('sub_criteria', [])}
        
        PROJECT CONTEXT:
        - Project Type: {context.get('project_type', 'General')}
        - Contract Value: {context.get('contract_value', 'Not specified')}
        - Requirements: {context.get('requirements', [])}
        
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
        1. How well the supplier addresses the criterion
        2. Evidence from their submission documents
        3. Compliance with NSW Local Government requirements
        4. Risk factors and mitigation strategies
        5. Value for money considerations
        """
    
    def _parse_ai_response(self, response_text: str, criterion: Dict[str, Any]) -> AIScoringResult:
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
            
            return AIScoringResult(
                criterion_name=criterion["name"],
                ai_score=float(data.get("score", 3.0)),
                ai_justification=data.get("justification", "No justification provided"),
                supporting_evidence=data.get("supporting_evidence", []),
                confidence_level=float(data.get("confidence_level", 0.7)),
                compliance_notes=data.get("compliance_notes", []),
                risk_factors=data.get("risk_factors", [])
            )
            
        except Exception as e:
            print(f"⚠️ Error parsing AI response: {e}")
            return AIScoringResult(
                criterion_name=criterion["name"],
                ai_score=3.0,
                ai_justification="Error in AI analysis",
                supporting_evidence=[],
                confidence_level=0.0,
                compliance_notes=[],
                risk_factors=[]
            )
    
    def get_committee_evaluation_interface(self, evaluation_id: str, member_id: str) -> Dict[str, Any]:
        """Get evaluation interface for committee member"""
        
        # Find evaluations for this evaluation_id
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        
        if not evaluations:
            return {"error": "Evaluation not found"}
        
        # Get member's existing evaluations
        member_evaluations = []
        for evaluation in evaluations:
            member_evals = [me for me in evaluation.member_evaluations if me.member_id == member_id]
            member_evaluations.extend(member_evals)
        
        return {
            "evaluation_id": evaluation_id,
            "member_id": member_id,
            "suppliers": [
                {
                    "supplier_id": eval.supplier_id,
                    "supplier_name": eval.supplier_name,
                    "ai_analysis": [
                        {
                            "criterion_name": ai.criterion_name,
                            "ai_score": ai.ai_score,
                            "ai_justification": ai.ai_justification,
                            "supporting_evidence": ai.supporting_evidence,
                            "confidence_level": ai.confidence_level,
                            "compliance_notes": ai.compliance_notes,
                            "risk_factors": ai.risk_factors
                        } for ai in eval.ai_analysis
                    ],
                    "member_scores": [
                        {
                            "criterion_name": me.criterion_name,
                            "member_score": me.member_score,
                            "member_justification": me.member_justification,
                            "comments": me.comments,
                            "evaluation_date": me.evaluation_date,
                            "is_final": me.is_final
                        } for me in eval.member_evaluations if me.member_id == member_id
                    ]
                } for eval in evaluations
            ]
        }
    
    def submit_member_evaluation(self, 
                               evaluation_id: str, 
                               member_id: str, 
                               supplier_id: str, 
                               criterion_scores: List[Dict[str, Any]]) -> bool:
        """Submit committee member evaluation"""
        
        try:
            # Find the evaluation
            evaluation = None
            for eval in self.evaluations:
                if eval.evaluation_id == evaluation_id and eval.supplier_id == supplier_id:
                    evaluation = eval
                    break
            
            if not evaluation:
                return False
            
            # Update or create member evaluations
            for score_data in criterion_scores:
                # Remove existing evaluation for this member and criterion
                evaluation.member_evaluations = [
                    me for me in evaluation.member_evaluations 
                    if not (me.member_id == member_id and me.criterion_name == score_data["criterion_name"])
                ]
                
                # Add new evaluation
                member_eval = MemberEvaluation(
                    member_id=member_id,
                    member_name=score_data.get("member_name", "Unknown"),
                    criterion_name=score_data["criterion_name"],
                    member_score=float(score_data["member_score"]),
                    member_justification=score_data.get("member_justification", ""),
                    comments=score_data.get("comments", ""),
                    evaluation_date=datetime.now().isoformat(),
                    is_final=score_data.get("is_final", False)
                )
                
                evaluation.member_evaluations.append(member_eval)
            
            # Update status
            evaluation.status = EvaluationStatus.COMMITTEE_REVIEW
            
            # Save evaluation
            self._save_evaluation(evaluation)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error submitting member evaluation: {e}")
            return False
    
    def generate_consensus_meeting_data(self, evaluation_id: str) -> Dict[str, Any]:
        """Generate data for consensus meeting"""
        
        # Find all evaluations for this evaluation_id
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        
        if not evaluations:
            return {"error": "Evaluation not found"}
        
        consensus_data = {
            "evaluation_id": evaluation_id,
            "meeting_date": datetime.now().isoformat(),
            "suppliers": []
        }
        
        for evaluation in evaluations:
            supplier_data = {
                "supplier_id": evaluation.supplier_id,
                "supplier_name": evaluation.supplier_name,
                "criteria_analysis": []
            }
            
            # Group evaluations by criterion
            criteria_groups = {}
            for ai in evaluation.ai_analysis:
                criteria_groups[ai.criterion_name] = {
                    "ai_analysis": ai,
                    "member_evaluations": []
                }
            
            for me in evaluation.member_evaluations:
                if me.criterion_name in criteria_groups:
                    criteria_groups[me.criterion_name]["member_evaluations"].append(me)
            
            # Create consensus analysis for each criterion
            for criterion_name, data in criteria_groups.items():
                ai_analysis = data["ai_analysis"]
                member_evals = data["member_evaluations"]
                
                if member_evals:
                    # Calculate consensus metrics
                    scores = [me.member_score for me in member_evals]
                    avg_score = sum(scores) / len(scores)
                    score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
                    
                    consensus_data_item = {
                        "criterion_name": criterion_name,
                        "ai_score": ai_analysis.ai_score,
                        "ai_justification": ai_analysis.ai_justification,
                        "member_scores": [
                            {
                                "member_name": me.member_name,
                                "score": me.member_score,
                                "justification": me.member_justification,
                                "comments": me.comments
                            } for me in member_evals
                        ],
                        "average_score": avg_score,
                        "score_variance": score_variance,
                        "agreement_level": 1.0 - (score_variance / 25.0),  # Normalize to 0-1
                        "recommended_consensus_score": avg_score,
                        "supporting_evidence": ai_analysis.supporting_evidence,
                        "compliance_notes": ai_analysis.compliance_notes,
                        "risk_factors": ai_analysis.risk_factors
                    }
                    
                    supplier_data["criteria_analysis"].append(consensus_data_item)
            
            consensus_data["suppliers"].append(supplier_data)
        
        return consensus_data
    
    def finalize_consensus_scores(self, 
                                 evaluation_id: str, 
                                 consensus_scores: List[Dict[str, Any]]) -> bool:
        """Finalize consensus scores after meeting"""
        
        try:
            # Find evaluations
            evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
            
            for evaluation in evaluations:
                # Clear existing consensus results
                evaluation.consensus_results = []
                
                # Add new consensus results
                for consensus_data in consensus_scores:
                    if consensus_data["supplier_id"] == evaluation.supplier_id:
                        for criterion_data in consensus_data["criteria_scores"]:
                            consensus_result = ConsensusResult(
                                criterion_name=criterion_data["criterion_name"],
                                final_score=float(criterion_data["final_score"]),
                                consensus_justification=criterion_data.get("justification", ""),
                                agreement_level=float(criterion_data.get("agreement_level", 1.0)),
                                dissenting_views=criterion_data.get("dissenting_views", []),
                                finalization_date=datetime.now().isoformat()
                            )
                            evaluation.consensus_results.append(consensus_result)
                
                # Calculate total score
                total_score = sum(cr.final_score for cr in evaluation.consensus_results)
                evaluation.total_score = total_score
                
                # Update status
                evaluation.status = EvaluationStatus.FINALIZED
                evaluation.finalized_date = datetime.now().isoformat()
                
                # Save evaluation
                self._save_evaluation(evaluation)
            
            # Update rankings
            self._update_rankings(evaluation_id)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error finalizing consensus scores: {e}")
            return False
    
    def _update_rankings(self, evaluation_id: str):
        """Update supplier rankings based on final scores"""
        
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        evaluations.sort(key=lambda x: x.total_score, reverse=True)
        
        for i, evaluation in enumerate(evaluations):
            evaluation.rank = i + 1
            self._save_evaluation(evaluation)
    
    def _save_evaluation(self, evaluation: SupplierEvaluation):
        """Save evaluation to storage"""
        
        try:
            eval_file = self.evaluations_dir / f"{evaluation.evaluation_id}_{evaluation.supplier_id}.json"
            
            # Convert to serializable format
            eval_data = {
                "supplier_id": evaluation.supplier_id,
                "supplier_name": evaluation.supplier_name,
                "evaluation_id": evaluation.evaluation_id,
                "status": evaluation.status.value,
                "ai_analysis": [
                    {
                        "criterion_name": ai.criterion_name,
                        "ai_score": ai.ai_score,
                        "ai_justification": ai.ai_justification,
                        "supporting_evidence": ai.supporting_evidence,
                        "confidence_level": ai.confidence_level,
                        "compliance_notes": ai.compliance_notes,
                        "risk_factors": ai.risk_factors
                    } for ai in evaluation.ai_analysis
                ],
                "member_evaluations": [
                    {
                        "member_id": me.member_id,
                        "member_name": me.member_name,
                        "criterion_name": me.criterion_name,
                        "member_score": me.member_score,
                        "member_justification": me.member_justification,
                        "comments": me.comments,
                        "evaluation_date": me.evaluation_date,
                        "is_final": me.is_final
                    } for me in evaluation.member_evaluations
                ],
                "consensus_results": [
                    {
                        "criterion_name": cr.criterion_name,
                        "final_score": cr.final_score,
                        "consensus_justification": cr.consensus_justification,
                        "agreement_level": cr.agreement_level,
                        "dissenting_views": cr.dissenting_views,
                        "finalization_date": cr.finalization_date
                    } for cr in evaluation.consensus_results
                ],
                "total_score": evaluation.total_score,
                "rank": evaluation.rank,
                "created_date": evaluation.created_date,
                "finalized_date": evaluation.finalized_date
            }
            
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(eval_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error saving evaluation: {e}")
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active collaborative evaluation sessions"""
        active_sessions = []
        
        # Get unique evaluation IDs
        evaluation_ids = set(eval.evaluation_id for eval in self.evaluations)
        
        for eval_id in evaluation_ids:
            # Get evaluations for this session
            session_evaluations = [e for e in self.evaluations if e.evaluation_id == eval_id]
            
            if session_evaluations:
                # Get the first evaluation to get session details
                first_eval = session_evaluations[0]
                
                session_info = {
                    "evaluation_id": eval_id,
                    "project_title": getattr(first_eval, 'project_title', 'Unknown Project'),
                    "status": first_eval.status.value,
                    "total_suppliers": len(session_evaluations),
                    "created_date": getattr(first_eval, 'created_date', datetime.now().isoformat()),
                    "last_updated": getattr(first_eval, 'last_updated', datetime.now().isoformat()),
                    "committee_members": getattr(first_eval, 'committee_members', []),
                    "ai_analysis_complete": all(eval.ai_analysis_complete for eval in session_evaluations),
                    "consensus_reached": all(eval.consensus_reached for eval in session_evaluations)
                }
                
                active_sessions.append(session_info)
        
        return active_sessions

    def get_evaluation_summary(self, evaluation_id: str) -> Dict[str, Any]:
        """Get comprehensive evaluation summary"""
        
        evaluations = [e for e in self.evaluations if e.evaluation_id == evaluation_id]
        
        if not evaluations:
            return {"error": "Evaluation not found"}
        
        summary = {
            "evaluation_id": evaluation_id,
            "status": evaluations[0].status.value,
            "total_suppliers": len(evaluations),
            "suppliers": []
        }
        
        for evaluation in evaluations:
            supplier_summary = {
                "supplier_id": evaluation.supplier_id,
                "supplier_name": evaluation.supplier_name,
                "total_score": evaluation.total_score,
                "rank": evaluation.rank,
                "status": evaluation.status.value,
                "ai_analysis_complete": len(evaluation.ai_analysis) > 0,
                "member_evaluations_count": len(evaluation.member_evaluations),
                "consensus_finalized": len(evaluation.consensus_results) > 0
            }
            
            summary["suppliers"].append(supplier_summary)
        
        return summary
