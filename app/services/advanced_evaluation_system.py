#!/usr/bin/env python3
"""
Advanced Evaluation System
Comprehensive evaluation system with price evaluation models, scoring, and supplier ranking
Based on NSW Local Government Tender & Quotation Evaluation Manual
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class EvaluationModel(Enum):
    """Price evaluation models from NSW guidelines"""
    LOWEST_PRICE_CONFORMING = "lowest_price_conforming"
    MEAT = "most_economically_advantageous_tender"
    TCO = "total_cost_ownership"
    QUALITY_COST_RATIO = "quality_cost_ratio"

class ScoringMethod(Enum):
    """Scoring methods for evaluation criteria"""
    WEIGHTED_1_5 = "weighted_1_5"
    WEIGHTED_1_10 = "weighted_1_10"
    PERCENTAGE = "percentage"
    PASS_FAIL = "pass_fail"
    CURRENCY = "currency"

@dataclass
class EvaluationCriterion:
    """Enhanced evaluation criterion with detailed scoring"""
    name: str
    weight: float
    description: str
    sub_criteria: List[str]
    scoring_method: ScoringMethod
    mandatory: bool = False
    max_score: float = 100.0
    evaluation_notes: str = ""
    source_document: str = ""

@dataclass
class SupplierResponse:
    """Supplier response data"""
    supplier_name: str
    price: float
    technical_score: float
    experience_score: float
    risk_score: float
    compliance_score: float
    additional_data: Dict[str, Any] = None

@dataclass
class EvaluationResult:
    """Complete evaluation result for a supplier"""
    supplier_name: str
    total_score: float
    weighted_score: float
    rank: int
    price_score: float
    technical_score: float
    experience_score: float
    risk_score: float
    compliance_score: float
    evaluation_model: EvaluationModel
    detailed_scores: Dict[str, float]
    recommendations: List[str]
    risk_factors: List[str]

class AdvancedEvaluationSystem:
    """
    Advanced evaluation system implementing NSW Local Government standards
    with comprehensive price evaluation models
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.evaluation_config_dir = data_dir / "evaluation_configs"
        self.evaluation_config_dir.mkdir(exist_ok=True)
        
        # Initialize evaluation criteria based on NSW standards
        self._initialize_evaluation_criteria()
        
        # Price evaluation models
        self.price_evaluation_models = self._initialize_price_models()
    
    def _initialize_evaluation_criteria(self):
        """Initialize comprehensive evaluation criteria based on NSW guidelines"""
        
        self.evaluation_criteria = [
            EvaluationCriterion(
                name="Price/Cost",
                weight=40.0,
                description="Total cost including all fees, taxes, and ongoing costs",
                sub_criteria=[
                    "Base price competitiveness",
                    "Additional costs transparency", 
                    "Ongoing maintenance costs",
                    "Total cost of ownership",
                    "Payment terms and conditions",
                    "Price escalation clauses"
                ],
                scoring_method=ScoringMethod.CURRENCY,
                max_score=100.0,
                evaluation_notes="Lower price = higher score. Normalized against lowest bid.",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Technical Capability",
                weight=30.0,
                description="Technical competence and ability to deliver requirements",
                sub_criteria=[
                    "Technical approach and methodology",
                    "Innovation and value-add proposals",
                    "Technical team qualifications",
                    "Equipment and resources",
                    "Quality assurance procedures",
                    "Project management capability"
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_10,
                max_score=10.0,
                evaluation_notes="1=Poor, 5=Average, 10=Excellent",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Experience & Track Record",
                weight=15.0,
                description="Relevant experience and proven track record",
                sub_criteria=[
                    "Similar project experience",
                    "Client references and testimonials",
                    "Industry experience and reputation",
                    "Performance history and KPIs",
                    "Team experience and qualifications",
                    "Company stability and growth"
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="1=Poor, 3=Average, 5=Excellent",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Risk Management",
                weight=10.0,
                description="Risk identification, assessment, and mitigation strategies",
                sub_criteria=[
                    "Risk identification and analysis",
                    "Mitigation strategies and controls",
                    "Contingency plans and alternatives",
                    "Insurance coverage and guarantees",
                    "Financial stability and capacity",
                    "Performance bonds and security"
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="1=High Risk, 3=Medium Risk, 5=Low Risk",
                source_document="Tender Quotation Evaluation Manual V4- 2024"
            ),
            EvaluationCriterion(
                name="Probity & Compliance",
                weight=5.0,
                description="Adherence to probity requirements and regulatory compliance",
                sub_criteria=[
                    "Probity declaration completion",
                    "Regulatory compliance statements",
                    "Conflict of interest disclosure",
                    "Code of conduct acceptance",
                    "Audit trail maintenance",
                    "Transparency commitments"
                ],
                scoring_method=ScoringMethod.PASS_FAIL,
                max_score=1.0,
                mandatory=True,
                evaluation_notes="Pass=1.0, Fail=0.0 (Mandatory)",
                source_document="CAPH S9 procurement advisory & probity check (2024-11-20)"
            )
        ]
    
    def _initialize_price_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize price evaluation models"""
        
        return {
            "lowest_price_conforming": {
                "name": "Lowest Price Conforming",
                "description": "Select lowest price among compliant bids",
                "use_case": "Simple, standardized purchases where price is primary",
                "weighting": {"price": 100.0},
                "formula": "Score = (Lowest Price / Supplier Price) × 100"
            },
            "meat": {
                "name": "Most Economically Advantageous Tender (MEAT)",
                "description": "Weighted scoring combining price and quality factors",
                "use_case": "Complex projects requiring balance of cost and quality",
                "weighting": {
                    "price": 40.0,
                    "technical": 30.0,
                    "experience": 15.0,
                    "risk": 10.0,
                    "compliance": 5.0
                },
                "formula": "Total Score = Σ(Criterion Score × Weight)"
            },
            "tco": {
                "name": "Total Cost of Ownership (TCO)",
                "description": "Comprehensive cost analysis over entire lifecycle",
                "use_case": "Long-term contracts with ongoing costs",
                "weighting": {
                    "acquisition_cost": 30.0,
                    "operating_cost": 40.0,
                    "maintenance_cost": 20.0,
                    "disposal_cost": 10.0
                },
                "formula": "TCO = Acquisition + Operating + Maintenance + Disposal - Residual"
            },
            "quality_cost_ratio": {
                "name": "Quality/Cost Ratio",
                "description": "Balance quality and cost for optimal value",
                "use_case": "Services where quality is critical",
                "weighting": {
                    "quality": 60.0,
                    "cost": 40.0
                },
                "formula": "Ratio = Quality Score / Cost Score"
            }
        }
    
    def evaluate_suppliers(self, 
                          suppliers: List[SupplierResponse], 
                          evaluation_model: EvaluationModel,
                          project_type: str = "general") -> List[EvaluationResult]:
        """Evaluate suppliers using specified evaluation model"""
        
        results = []
        
        for supplier in suppliers:
            if evaluation_model == EvaluationModel.LOWEST_PRICE_CONFORMING:
                result = self._evaluate_lowest_price_conforming(supplier, suppliers)
            elif evaluation_model == EvaluationModel.MEAT:
                result = self._evaluate_meat(supplier, suppliers)
            elif evaluation_model == EvaluationModel.TCO:
                result = self._evaluate_tco(supplier, suppliers, project_type)
            elif evaluation_model == EvaluationModel.QUALITY_COST_RATIO:
                result = self._evaluate_quality_cost_ratio(supplier, suppliers)
            else:
                result = self._evaluate_meat(supplier, suppliers)  # Default to MEAT
            
            results.append(result)
        
        # Sort by weighted score (highest first)
        results.sort(key=lambda x: x.weighted_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    def _evaluate_lowest_price_conforming(self, 
                                        supplier: SupplierResponse, 
                                        all_suppliers: List[SupplierResponse]) -> EvaluationResult:
        """Evaluate using lowest price conforming model"""
        
        lowest_price = min(s.price for s in all_suppliers)
        price_score = (lowest_price / supplier.price) * 100 if supplier.price > 0 else 0
        
        total_score = price_score
        weighted_score = total_score  # 100% price weighting
        
        return EvaluationResult(
            supplier_name=supplier.supplier_name,
            total_score=total_score,
            weighted_score=weighted_score,
            rank=0,  # Will be set later
            price_score=price_score,
            technical_score=0,
            experience_score=0,
            risk_score=0,
            compliance_score=1.0 if supplier.compliance_score > 0 else 0,
            evaluation_model=EvaluationModel.LOWEST_PRICE_CONFORMING,
            detailed_scores={"price": price_score},
            recommendations=["Price-focused evaluation completed"],
            risk_factors=["Quality not considered in this model"]
        )
    
    def _evaluate_meat(self, 
                      supplier: SupplierResponse, 
                      all_suppliers: List[SupplierResponse]) -> EvaluationResult:
        """Evaluate using Most Economically Advantageous Tender (MEAT) model"""
        
        # Normalize scores to 0-100 scale
        max_technical = max(s.technical_score for s in all_suppliers) or 1
        max_experience = max(s.experience_score for s in all_suppliers) or 1
        max_risk = max(s.risk_score for s in all_suppliers) or 1
        
        # Price scoring (lower price = higher score)
        min_price = min(s.price for s in all_suppliers)
        price_score = (min_price / supplier.price) * 100 if supplier.price > 0 else 0
        
        # Technical scoring (normalized to 100)
        technical_score = (supplier.technical_score / max_technical) * 100
        
        # Experience scoring (normalized to 100)
        experience_score = (supplier.experience_score / max_experience) * 100
        
        # Risk scoring (higher risk score = lower risk = higher score)
        risk_score = (supplier.risk_score / max_risk) * 100
        
        # Compliance scoring (pass/fail)
        compliance_score = 100.0 if supplier.compliance_score > 0 else 0
        
        # Calculate weighted total
        weights = self.price_evaluation_models["meat"]["weighting"]
        weighted_score = (
            (price_score * weights["price"]) +
            (technical_score * weights["technical"]) +
            (experience_score * weights["experience"]) +
            (risk_score * weights["risk"]) +
            (compliance_score * weights["compliance"])
        ) / 100
        
        # Generate recommendations
        recommendations = []
        if price_score < 80:
            recommendations.append("Price may not be competitive")
        if technical_score < 70:
            recommendations.append("Technical capability concerns")
        if experience_score < 60:
            recommendations.append("Limited relevant experience")
        if risk_score < 70:
            recommendations.append("Higher risk profile")
        if compliance_score == 0:
            recommendations.append("Compliance issues - review required")
        
        # Risk factors
        risk_factors = []
        if supplier.price < min_price * 0.8:
            risk_factors.append("Unusually low price - quality risk")
        if technical_score < 50:
            risk_factors.append("Technical capability risk")
        if experience_score < 40:
            risk_factors.append("Experience and track record risk")
        
        return EvaluationResult(
            supplier_name=supplier.supplier_name,
            total_score=(price_score + technical_score + experience_score + risk_score + compliance_score) / 5,
            weighted_score=weighted_score,
            rank=0,
            price_score=price_score,
            technical_score=technical_score,
            experience_score=experience_score,
            risk_score=risk_score,
            compliance_score=compliance_score,
            evaluation_model=EvaluationModel.MEAT,
            detailed_scores={
                "price": price_score,
                "technical": technical_score,
                "experience": experience_score,
                "risk": risk_score,
                "compliance": compliance_score
            },
            recommendations=recommendations,
            risk_factors=risk_factors
        )
    
    def _evaluate_tco(self, 
                     supplier: SupplierResponse, 
                     all_suppliers: List[SupplierResponse],
                     project_type: str) -> EvaluationResult:
        """Evaluate using Total Cost of Ownership (TCO) model"""
        
        # Simplified TCO calculation (in real implementation, this would be more complex)
        acquisition_cost = supplier.price
        operating_cost = acquisition_cost * 0.3  # Assume 30% of acquisition cost per year
        maintenance_cost = acquisition_cost * 0.1  # Assume 10% maintenance per year
        disposal_cost = acquisition_cost * -0.1  # Assume 10% residual value
        
        tco = acquisition_cost + operating_cost + maintenance_cost + disposal_cost
        
        # Normalize against lowest TCO
        all_tcos = []
        for s in all_suppliers:
            s_acq = s.price
            s_op = s_acq * 0.3
            s_maint = s_acq * 0.1
            s_disp = s_acq * -0.1
            all_tcos.append(s_acq + s_op + s_maint + s_disp)
        
        min_tco = min(all_tcos)
        tco_score = (min_tco / tco) * 100 if tco > 0 else 0
        
        # For TCO, we still consider other factors but with different weighting
        max_technical = max(s.technical_score for s in all_suppliers) or 1
        technical_score = (supplier.technical_score / max_technical) * 100
        
        compliance_score = 100.0 if supplier.compliance_score > 0 else 0
        
        # TCO weighting focuses on long-term value
        weighted_score = (
            (tco_score * 50.0) +  # 50% TCO
            (technical_score * 30.0) +  # 30% Technical
            (compliance_score * 20.0)  # 20% Compliance
        ) / 100
        
        recommendations = []
        if tco_score < 80:
            recommendations.append("Higher total cost of ownership")
        if technical_score < 70:
            recommendations.append("Technical capability may impact long-term performance")
        
        risk_factors = []
        if tco_score < 60:
            risk_factors.append("High total cost of ownership risk")
        
        return EvaluationResult(
            supplier_name=supplier.supplier_name,
            total_score=tco_score,
            weighted_score=weighted_score,
            rank=0,
            price_score=tco_score,
            technical_score=technical_score,
            experience_score=0,
            risk_score=0,
            compliance_score=compliance_score,
            evaluation_model=EvaluationModel.TCO,
            detailed_scores={
                "tco": tco_score,
                "acquisition_cost": acquisition_cost,
                "operating_cost": operating_cost,
                "maintenance_cost": maintenance_cost,
                "disposal_cost": disposal_cost
            },
            recommendations=recommendations,
            risk_factors=risk_factors
        )
    
    def _evaluate_quality_cost_ratio(self, 
                                   supplier: SupplierResponse, 
                                   all_suppliers: List[SupplierResponse]) -> EvaluationResult:
        """Evaluate using Quality/Cost Ratio model"""
        
        # Calculate quality score (combination of technical and experience)
        max_technical = max(s.technical_score for s in all_suppliers) or 1
        max_experience = max(s.experience_score for s in all_suppliers) or 1
        
        technical_score = (supplier.technical_score / max_technical) * 100
        experience_score = (supplier.experience_score / max_experience) * 100
        quality_score = (technical_score + experience_score) / 2
        
        # Calculate cost score (lower cost = higher score)
        min_price = min(s.price for s in all_suppliers)
        cost_score = (min_price / supplier.price) * 100 if supplier.price > 0 else 0
        
        # Calculate ratio
        ratio = quality_score / cost_score if cost_score > 0 else 0
        
        # Weighted score emphasizes quality
        compliance_score = 100.0 if supplier.compliance_score > 0 else 0
        weighted_score = (
            (quality_score * 60.0) +  # 60% Quality
            (cost_score * 40.0)  # 40% Cost
        ) / 100
        
        recommendations = []
        if quality_score < 70:
            recommendations.append("Quality concerns identified")
        if cost_score < 60:
            recommendations.append("Cost competitiveness issues")
        
        risk_factors = []
        if quality_score < 50:
            risk_factors.append("Quality risk")
        if cost_score < 40:
            risk_factors.append("Cost risk")
        
        return EvaluationResult(
            supplier_name=supplier.supplier_name,
            total_score=ratio * 100,
            weighted_score=weighted_score,
            rank=0,
            price_score=cost_score,
            technical_score=technical_score,
            experience_score=experience_score,
            risk_score=0,
            compliance_score=compliance_score,
            evaluation_model=EvaluationModel.QUALITY_COST_RATIO,
            detailed_scores={
                "quality_score": quality_score,
                "cost_score": cost_score,
                "ratio": ratio
            },
            recommendations=recommendations,
            risk_factors=risk_factors
        )
    
    def generate_evaluation_report(self, 
                                 results: List[EvaluationResult],
                                 project_name: str,
                                 evaluation_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        
        return {
            "project_name": project_name,
            "evaluation_date": evaluation_date.isoformat(),
            "total_suppliers": len(results),
            "evaluation_model": results[0].evaluation_model.value if results else "N/A",
            "results": [asdict(result) for result in results],
            "summary": {
                "recommended_supplier": results[0].supplier_name if results else "None",
                "average_score": sum(r.weighted_score for r in results) / len(results) if results else 0,
                "score_range": {
                    "highest": max(r.weighted_score for r in results) if results else 0,
                    "lowest": min(r.weighted_score for r in results) if results else 0
                }
            },
            "recommendations": {
                "primary": results[0].recommendations if results else [],
                "all_suppliers": [r.recommendations for r in results]
            },
            "risk_assessment": {
                "high_risk_suppliers": [r.supplier_name for r in results if len(r.risk_factors) > 2],
                "common_risks": list(set(risk for r in results for risk in r.risk_factors))
            }
        }
    
    def get_evaluation_criteria_for_project_type(self, project_type: str) -> List[EvaluationCriterion]:
        """Get evaluation criteria tailored for specific project type"""
        
        # Base criteria (already initialized)
        criteria = self.evaluation_criteria.copy()
        
        # Add project-specific criteria if needed
        if project_type.lower() == "construction":
            criteria.append(EvaluationCriterion(
                name="Safety & Environmental",
                weight=10.0,
                description="Safety management and environmental compliance",
                sub_criteria=[
                    "Safety management systems",
                    "Environmental impact management",
                    "Workplace safety record",
                    "Environmental certifications",
                    "Waste management procedures"
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                source_document="Construction-specific requirements"
            ))
        
        elif project_type.lower() == "fleet":
            criteria.append(EvaluationCriterion(
                name="Vehicle Specifications",
                weight=15.0,
                description="Vehicle specifications and compliance",
                sub_criteria=[
                    "Technical specifications compliance",
                    "Fuel efficiency and emissions",
                    "Safety features and ratings",
                    "Warranty and service coverage",
                    "Delivery timeline and availability"
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_10,
                max_score=10.0,
                source_document="Fleet management requirements"
            ))
        
        # Adjust weights to total 100%
        total_weight = sum(c.weight for c in criteria)
        if total_weight > 100:
            # Proportionally reduce weights
            for criterion in criteria:
                criterion.weight = (criterion.weight / total_weight) * 100
        
        return criteria

# Global instance
_advanced_evaluation_system = None

def get_advanced_evaluation_system(data_dir: Path) -> AdvancedEvaluationSystem:
    """Get or create advanced evaluation system instance"""
    global _advanced_evaluation_system
    if _advanced_evaluation_system is None:
        _advanced_evaluation_system = AdvancedEvaluationSystem(data_dir)
    return _advanced_evaluation_system

if __name__ == "__main__":
    # Test the advanced evaluation system
    from ..config import settings
    
    system = AdvancedEvaluationSystem(settings.DATA_DIR)
    
    print("✅ Advanced Evaluation System initialized")
    print(f"📋 Evaluation criteria: {len(system.evaluation_criteria)}")
    print(f"💰 Price evaluation models: {len(system.price_evaluation_models)}")
    
    # Test with sample suppliers
    suppliers = [
        SupplierResponse("Supplier A", 100000, 8.5, 4.0, 4.5, 1.0),
        SupplierResponse("Supplier B", 95000, 7.0, 3.5, 4.0, 1.0),
        SupplierResponse("Supplier C", 110000, 9.0, 4.5, 5.0, 1.0)
    ]
    
    results = system.evaluate_suppliers(suppliers, EvaluationModel.MEAT)
    
    print(f"\n🎯 MEAT Evaluation Results:")
    for result in results:
        print(f"   {result.rank}. {result.supplier_name}: {result.weighted_score:.1f}%")
    
    print("\n🎉 Advanced Evaluation System working correctly!")
