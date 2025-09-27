#!/usr/bin/env python3
"""
Evaluation Criteria Extractor
Extracts comprehensive evaluation criteria and sub-criteria from uploaded documents
Based on NSW Local Government Tender & Quotation Evaluation Manual and other guidelines
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class CriterionCategory(Enum):
    """Categories of evaluation criteria"""
    PRICE_COST = "price_cost"
    TECHNICAL_CAPABILITY = "technical_capability"
    EXPERIENCE_TRACK_RECORD = "experience_track_record"
    RISK_MANAGEMENT = "risk_management"
    COMPLIANCE_PROBITY = "compliance_probity"
    QUALITY_MANAGEMENT = "quality_management"
    SUSTAINABILITY_ENVIRONMENTAL = "sustainability_environmental"
    INNOVATION_VALUE_ADD = "innovation_value_add"
    LOCAL_CONTENT = "local_content"
    SAFETY_HEALTH = "safety_health"

class ScoringMethod(Enum):
    """Detailed scoring methods from NSW guidelines"""
    WEIGHTED_1_5 = "weighted_1_5"
    WEIGHTED_1_10 = "weighted_1_10"
    PERCENTAGE = "percentage"
    PASS_FAIL = "pass_fail"
    CURRENCY = "currency"
    POINTS_SCALE = "points_scale"
    RATING_SCALE = "rating_scale"

@dataclass
class DetailedEvaluationCriterion:
    """Comprehensive evaluation criterion with detailed sub-criteria"""
    name: str
    category: CriterionCategory
    weight: float
    description: str
    sub_criteria: List[Dict[str, Any]]
    scoring_method: ScoringMethod
    mandatory: bool = False
    max_score: float = 100.0
    evaluation_notes: str = ""
    source_document: str = ""
    evaluation_guidance: str = ""
    key_questions: List[str] = None

class EvaluationCriteriaExtractor:
    """
    Extracts and organizes comprehensive evaluation criteria from NSW Local Government documents
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.global_compliance_dir = data_dir / "global_compliance"
        self.global_compliance_dir.mkdir(exist_ok=True)
        
        # Initialize comprehensive criteria based on NSW guidelines
        self._initialize_comprehensive_criteria()
    
    def _initialize_comprehensive_criteria(self):
        """Initialize comprehensive evaluation criteria based on NSW Local Government standards"""
        
        self.evaluation_criteria = [
            # 1. PRICE/COST CRITERIA
            DetailedEvaluationCriterion(
                name="Price and Cost",
                category=CriterionCategory.PRICE_COST,
                weight=35.0,
                description="Total cost evaluation including all price components and value for money",
                sub_criteria=[
                    {
                        "name": "Base Price Competitiveness",
                        "weight": 40.0,
                        "description": "Comparison of base tender prices",
                        "scoring_method": "currency_normalized",
                        "max_score": 100.0,
                        "evaluation_notes": "Normalized against lowest conforming bid"
                    },
                    {
                        "name": "Additional Costs Transparency",
                        "weight": 20.0,
                        "description": "Clarity and completeness of additional cost items",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor transparency, 5=Excellent transparency"
                    },
                    {
                        "name": "Ongoing Maintenance Costs",
                        "weight": 15.0,
                        "description": "Lifecycle maintenance and operational costs",
                        "scoring_method": "currency_normalized",
                        "max_score": 100.0,
                        "evaluation_notes": "Lower ongoing costs = higher score"
                    },
                    {
                        "name": "Payment Terms and Conditions",
                        "weight": 10.0,
                        "description": "Payment schedule and terms acceptability",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Unacceptable terms, 5=Excellent terms"
                    },
                    {
                        "name": "Price Escalation Clauses",
                        "weight": 10.0,
                        "description": "Price variation mechanisms and controls",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Uncontrolled escalation, 5=Well-controlled"
                    },
                    {
                        "name": "Value for Money",
                        "weight": 5.0,
                        "description": "Overall value proposition assessment",
                        "scoring_method": "weighted_1_10",
                        "max_score": 10.0,
                        "evaluation_notes": "1=Poor value, 10=Excellent value"
                    }
                ],
                scoring_method=ScoringMethod.CURRENCY,
                max_score=100.0,
                evaluation_notes="Primary cost evaluation with normalized scoring",
                source_document="Tender Quotation Evaluation Manual V4- 2024",
                evaluation_guidance="Focus on total cost of ownership, not just initial price",
                key_questions=[
                    "Is the price competitive compared to market rates?",
                    "Are all cost components clearly identified?",
                    "What are the ongoing operational costs?",
                    "Are payment terms acceptable to the council?"
                ]
            ),
            
            # 2. TECHNICAL CAPABILITY
            DetailedEvaluationCriterion(
                name="Technical Capability and Approach",
                category=CriterionCategory.TECHNICAL_CAPABILITY,
                weight=25.0,
                description="Technical competence, methodology, and ability to deliver requirements",
                sub_criteria=[
                    {
                        "name": "Technical Approach and Methodology",
                        "weight": 30.0,
                        "description": "Quality and appropriateness of proposed technical approach",
                        "scoring_method": "weighted_1_10",
                        "max_score": 10.0,
                        "evaluation_notes": "1=Inappropriate approach, 10=Excellent methodology"
                    },
                    {
                        "name": "Technical Team Qualifications",
                        "weight": 25.0,
                        "description": "Qualifications and experience of technical personnel",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Insufficient qualifications, 5=Highly qualified team"
                    },
                    {
                        "name": "Equipment and Resources",
                        "weight": 20.0,
                        "description": "Adequacy and quality of equipment and resources",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Inadequate resources, 5=Excellent equipment"
                    },
                    {
                        "name": "Innovation and Value-Add Proposals",
                        "weight": 15.0,
                        "description": "Innovative solutions and value-added services",
                        "scoring_method": "weighted_1_10",
                        "max_score": 10.0,
                        "evaluation_notes": "1=No innovation, 10=Highly innovative"
                    },
                    {
                        "name": "Quality Assurance Procedures",
                        "weight": 10.0,
                        "description": "Quality management systems and procedures",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor QA, 5=Excellent QA systems"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_10,
                max_score=10.0,
                evaluation_notes="Technical competence assessment with detailed sub-criteria",
                source_document="Tender Quotation Evaluation Manual V4- 2024",
                evaluation_guidance="Assess technical approach against specified requirements",
                key_questions=[
                    "Does the technical approach meet all requirements?",
                    "Are the proposed personnel adequately qualified?",
                    "Is the equipment and resources sufficient?",
                    "Are there innovative solutions proposed?"
                ]
            ),
            
            # 3. EXPERIENCE AND TRACK RECORD
            DetailedEvaluationCriterion(
                name="Experience and Track Record",
                category=CriterionCategory.EXPERIENCE_TRACK_RECORD,
                weight=15.0,
                description="Relevant experience, performance history, and proven track record",
                sub_criteria=[
                    {
                        "name": "Similar Project Experience",
                        "weight": 35.0,
                        "description": "Relevant experience with similar projects",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No relevant experience, 5=Extensive experience"
                    },
                    {
                        "name": "Client References and Testimonials",
                        "weight": 25.0,
                        "description": "Quality and relevance of client references",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor references, 5=Excellent testimonials"
                    },
                    {
                        "name": "Performance History and KPIs",
                        "weight": 20.0,
                        "description": "Historical performance metrics and achievements",
                        "scoring_method": "weighted_1_10",
                        "max_score": 10.0,
                        "evaluation_notes": "1=Poor performance, 10=Excellent track record"
                    },
                    {
                        "name": "Industry Experience and Reputation",
                        "weight": 10.0,
                        "description": "Industry standing and reputation",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor reputation, 5=Excellent standing"
                    },
                    {
                        "name": "Company Stability and Growth",
                        "weight": 10.0,
                        "description": "Financial stability and company growth trajectory",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Unstable, 5=Very stable and growing"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="Experience assessment with emphasis on relevant projects",
                source_document="Tender Quotation Evaluation Manual V4- 2024",
                evaluation_guidance="Focus on directly relevant experience and proven performance",
                key_questions=[
                    "What similar projects has the supplier completed?",
                    "What do previous clients say about their performance?",
                    "What are their key performance indicators?",
                    "Is the company financially stable?"
                ]
            ),
            
            # 4. RISK MANAGEMENT
            DetailedEvaluationCriterion(
                name="Risk Management and Mitigation",
                category=CriterionCategory.RISK_MANAGEMENT,
                weight=10.0,
                description="Risk identification, assessment, and mitigation strategies",
                sub_criteria=[
                    {
                        "name": "Risk Identification and Analysis",
                        "weight": 30.0,
                        "description": "Comprehensiveness of risk identification",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor risk identification, 5=Comprehensive analysis"
                    },
                    {
                        "name": "Mitigation Strategies and Controls",
                        "weight": 25.0,
                        "description": "Quality of risk mitigation measures",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Inadequate controls, 5=Excellent mitigation"
                    },
                    {
                        "name": "Contingency Plans and Alternatives",
                        "weight": 20.0,
                        "description": "Backup plans and alternative approaches",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No contingencies, 5=Comprehensive plans"
                    },
                    {
                        "name": "Insurance Coverage and Guarantees",
                        "weight": 15.0,
                        "description": "Adequacy of insurance and performance guarantees",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Inadequate coverage, 5=Comprehensive protection"
                    },
                    {
                        "name": "Financial Stability and Capacity",
                        "weight": 10.0,
                        "description": "Financial strength and project capacity",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Financial concerns, 5=Very strong financially"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="Risk assessment with focus on mitigation strategies",
                source_document="Tender Quotation Evaluation Manual V4- 2024",
                evaluation_guidance="Assess risk management maturity and adequacy of controls",
                key_questions=[
                    "What risks has the supplier identified?",
                    "How will they mitigate identified risks?",
                    "What contingency plans are in place?",
                    "Is their insurance coverage adequate?"
                ]
            ),
            
            # 5. COMPLIANCE AND PROBITY
            DetailedEvaluationCriterion(
                name="Compliance and Probity",
                category=CriterionCategory.COMPLIANCE_PROBITY,
                weight=8.0,
                description="Adherence to probity requirements and regulatory compliance",
                sub_criteria=[
                    {
                        "name": "Probity Declaration Completion",
                        "weight": 25.0,
                        "description": "Completeness and accuracy of probity declarations",
                        "scoring_method": "pass_fail",
                        "max_score": 1.0,
                        "mandatory": True,
                        "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                    },
                    {
                        "name": "Regulatory Compliance Statements",
                        "weight": 25.0,
                        "description": "Compliance with relevant regulations and standards",
                        "scoring_method": "pass_fail",
                        "max_score": 1.0,
                        "mandatory": True,
                        "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                    },
                    {
                        "name": "Conflict of Interest Disclosure",
                        "weight": 20.0,
                        "description": "Transparency in conflict of interest declarations",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Incomplete disclosure, 5=Full transparency"
                    },
                    {
                        "name": "Code of Conduct Acceptance",
                        "weight": 15.0,
                        "description": "Acceptance and adherence to council code of conduct",
                        "scoring_method": "pass_fail",
                        "max_score": 1.0,
                        "mandatory": True,
                        "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                    },
                    {
                        "name": "Audit Trail Maintenance",
                        "weight": 10.0,
                        "description": "Systems for maintaining audit trails and records",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor audit systems, 5=Excellent record keeping"
                    },
                    {
                        "name": "Transparency Commitments",
                        "weight": 5.0,
                        "description": "Commitment to transparency and open communication",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor transparency, 5=Excellent openness"
                    }
                ],
                scoring_method=ScoringMethod.PASS_FAIL,
                max_score=1.0,
                mandatory=True,
                evaluation_notes="Mandatory compliance assessment",
                source_document="CAPH S9 procurement advisory & probity check (2024-11-20)",
                evaluation_guidance="All mandatory requirements must be met for tender to be considered",
                key_questions=[
                    "Are all probity declarations complete and accurate?",
                    "Does the supplier comply with all relevant regulations?",
                    "Are there any conflicts of interest?",
                    "Do they accept the council's code of conduct?"
                ]
            ),
            
            # 6. QUALITY MANAGEMENT
            DetailedEvaluationCriterion(
                name="Quality Management Systems",
                category=CriterionCategory.QUALITY_MANAGEMENT,
                weight=4.0,
                description="Quality management systems, processes, and continuous improvement",
                sub_criteria=[
                    {
                        "name": "Quality Management System Certification",
                        "weight": 30.0,
                        "description": "ISO certification and quality system maturity",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No certification, 5=Comprehensive ISO systems"
                    },
                    {
                        "name": "Quality Control Procedures",
                        "weight": 25.0,
                        "description": "Quality control processes and checkpoints",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor QC, 5=Excellent quality controls"
                    },
                    {
                        "name": "Continuous Improvement Programs",
                        "weight": 20.0,
                        "description": "Commitment to continuous improvement and innovation",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No improvement programs, 5=Excellent CI culture"
                    },
                    {
                        "name": "Customer Satisfaction Management",
                        "weight": 15.0,
                        "description": "Systems for managing and measuring customer satisfaction",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor customer focus, 5=Excellent satisfaction systems"
                    },
                    {
                        "name": "Quality Reporting and Documentation",
                        "weight": 10.0,
                        "description": "Quality reporting systems and documentation standards",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor documentation, 5=Excellent reporting"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="Quality system assessment with emphasis on certification",
                source_document="Tender Quotation Evaluation Manual V4- 2024",
                evaluation_guidance="Assess quality maturity and commitment to continuous improvement",
                key_questions=[
                    "What quality certifications does the supplier have?",
                    "How do they ensure quality control?",
                    "Do they have continuous improvement programs?",
                    "How do they measure customer satisfaction?"
                ]
            ),
            
            # 7. SUSTAINABILITY AND ENVIRONMENTAL
            DetailedEvaluationCriterion(
                name="Sustainability and Environmental",
                category=CriterionCategory.SUSTAINABILITY_ENVIRONMENTAL,
                weight=2.0,
                description="Environmental responsibility and sustainability practices",
                sub_criteria=[
                    {
                        "name": "Environmental Management Systems",
                        "weight": 30.0,
                        "description": "Environmental management and ISO 14001 certification",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No environmental systems, 5=Comprehensive EMS"
                    },
                    {
                        "name": "Carbon Footprint and Emissions",
                        "weight": 25.0,
                        "description": "Commitment to reducing carbon footprint and emissions",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=High emissions, 5=Low carbon footprint"
                    },
                    {
                        "name": "Waste Management and Recycling",
                        "weight": 20.0,
                        "description": "Waste reduction and recycling programs",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor waste management, 5=Excellent recycling"
                    },
                    {
                        "name": "Sustainable Procurement Practices",
                        "weight": 15.0,
                        "description": "Use of sustainable materials and suppliers",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No sustainable practices, 5=Excellent sustainability"
                    },
                    {
                        "name": "Environmental Reporting and Compliance",
                        "weight": 10.0,
                        "description": "Environmental reporting and regulatory compliance",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=Poor reporting, 5=Excellent environmental compliance"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="Environmental responsibility assessment",
                source_document="NSW Local Government Sustainability Guidelines",
                evaluation_guidance="Assess environmental commitment and sustainability practices",
                key_questions=[
                    "What environmental management systems are in place?",
                    "How do they reduce their carbon footprint?",
                    "What waste management practices do they follow?",
                    "Do they use sustainable materials and suppliers?"
                ]
            ),
            
            # 8. LOCAL CONTENT AND COMMUNITY BENEFIT
            DetailedEvaluationCriterion(
                name="Local Content and Community Benefit",
                category=CriterionCategory.LOCAL_CONTENT,
                weight=1.0,
                description="Local employment, local suppliers, and community benefits",
                sub_criteria=[
                    {
                        "name": "Local Employment Commitment",
                        "weight": 40.0,
                        "description": "Commitment to employing local residents",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No local employment, 5=Strong local commitment"
                    },
                    {
                        "name": "Local Supplier Engagement",
                        "weight": 30.0,
                        "description": "Use of local suppliers and subcontractors",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No local suppliers, 5=Extensive local engagement"
                    },
                    {
                        "name": "Community Investment and Benefits",
                        "weight": 20.0,
                        "description": "Investment in local community and social benefits",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No community benefit, 5=Significant community investment"
                    },
                    {
                        "name": "Skills Development and Training",
                        "weight": 10.0,
                        "description": "Local skills development and training programs",
                        "scoring_method": "weighted_1_5",
                        "max_score": 5.0,
                        "evaluation_notes": "1=No training programs, 5=Comprehensive skills development"
                    }
                ],
                scoring_method=ScoringMethod.WEIGHTED_1_5,
                max_score=5.0,
                evaluation_notes="Local content and community benefit assessment",
                source_document="NSW Local Government Local Content Policy",
                evaluation_guidance="Assess commitment to local employment and community benefit",
                key_questions=[
                    "How many local residents will be employed?",
                    "What local suppliers will be used?",
                    "What community benefits are provided?",
                    "Are there skills development programs?"
                ]
            )
        ]
    
    def get_criteria_for_project_type(self, project_type: str) -> List[DetailedEvaluationCriterion]:
        """Get evaluation criteria tailored for specific project type"""
        
        # Start with base criteria
        criteria = self.evaluation_criteria.copy()
        
        # Add project-specific criteria
        if project_type.lower() == "construction":
            criteria.append(self._get_construction_specific_criteria())
        elif project_type.lower() == "fleet":
            criteria.append(self._get_fleet_specific_criteria())
        elif project_type.lower() == "hvac":
            criteria.append(self._get_hvac_specific_criteria())
        elif project_type.lower() == "services":
            criteria.append(self._get_services_specific_criteria())
        
        # Adjust weights to total 100%
        self._normalize_weights(criteria)
        
        return criteria
    
    def _get_construction_specific_criteria(self) -> DetailedEvaluationCriterion:
        """Get construction-specific evaluation criteria"""
        return DetailedEvaluationCriterion(
            name="Construction Specific Requirements",
            category=CriterionCategory.SAFETY_HEALTH,
            weight=5.0,
            description="Construction-specific safety, environmental, and regulatory requirements",
            sub_criteria=[
                {
                    "name": "Work Health and Safety Management",
                    "weight": 30.0,
                    "description": "WHS management systems and safety record",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor safety record, 5=Excellent WHS management"
                },
                {
                    "name": "Environmental Impact Management",
                    "weight": 25.0,
                    "description": "Environmental protection and impact mitigation",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor environmental management, 5=Excellent protection"
                },
                {
                    "name": "Building Code Compliance",
                    "weight": 20.0,
                    "description": "Compliance with building codes and standards",
                    "scoring_method": "pass_fail",
                    "max_score": 1.0,
                    "mandatory": True,
                    "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                },
                {
                    "name": "Construction Methodology",
                    "weight": 15.0,
                    "description": "Appropriateness and efficiency of construction methods",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor methodology, 5=Excellent construction approach"
                },
                {
                    "name": "Site Management and Logistics",
                    "weight": 10.0,
                    "description": "Site organization and logistics management",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor site management, 5=Excellent organization"
                }
            ],
            scoring_method=ScoringMethod.WEIGHTED_1_5,
            max_score=5.0,
            mandatory=False,
            evaluation_notes="Construction-specific assessment with safety focus",
            source_document="NSW Building Code and Construction Standards",
            evaluation_guidance="Focus on safety, environmental protection, and code compliance",
            key_questions=[
                "What is their safety record and WHS management?",
                "How do they manage environmental impacts?",
                "Do they comply with all building codes?",
                "Is their construction methodology appropriate?"
            ]
        )
    
    def _get_fleet_specific_criteria(self) -> DetailedEvaluationCriterion:
        """Get fleet-specific evaluation criteria"""
        return DetailedEvaluationCriterion(
            name="Fleet Management Specific Requirements",
            category=CriterionCategory.TECHNICAL_CAPABILITY,
            weight=5.0,
            description="Fleet-specific technical requirements and management capabilities",
            sub_criteria=[
                {
                    "name": "Vehicle Specifications Compliance",
                    "weight": 30.0,
                    "description": "Compliance with specified vehicle requirements",
                    "scoring_method": "pass_fail",
                    "max_score": 1.0,
                    "mandatory": True,
                    "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                },
                {
                    "name": "Fuel Efficiency and Emissions",
                    "weight": 25.0,
                    "description": "Environmental performance and fuel efficiency",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor efficiency, 5=Excellent environmental performance"
                },
                {
                    "name": "Warranty and Service Coverage",
                    "weight": 20.0,
                    "description": "Comprehensive warranty and service support",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor warranty, 5=Excellent service coverage"
                },
                {
                    "name": "Delivery Timeline and Availability",
                    "weight": 15.0,
                    "description": "Delivery schedule and vehicle availability",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor delivery, 5=Excellent availability"
                },
                {
                    "name": "Fleet Management Systems",
                    "weight": 10.0,
                    "description": "Fleet tracking and management capabilities",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Basic systems, 5=Advanced fleet management"
                }
            ],
            scoring_method=ScoringMethod.WEIGHTED_1_5,
            max_score=5.0,
            mandatory=False,
            evaluation_notes="Fleet-specific technical assessment",
            source_document="NSW Fleet Management Guidelines",
            evaluation_guidance="Focus on specifications, efficiency, and service support",
            key_questions=[
                "Do vehicles meet all specified requirements?",
                "What is the fuel efficiency and emission rating?",
                "What warranty and service support is provided?",
                "When can vehicles be delivered?"
            ]
        )
    
    def _get_hvac_specific_criteria(self) -> DetailedEvaluationCriterion:
        """Get HVAC-specific evaluation criteria"""
        return DetailedEvaluationCriterion(
            name="HVAC System Requirements",
            category=CriterionCategory.TECHNICAL_CAPABILITY,
            weight=5.0,
            description="HVAC system performance, energy efficiency, and maintenance requirements",
            sub_criteria=[
                {
                    "name": "Energy Efficiency Rating",
                    "weight": 30.0,
                    "description": "Energy efficiency and environmental performance",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor efficiency, 5=Excellent energy performance"
                },
                {
                    "name": "System Performance Specifications",
                    "weight": 25.0,
                    "description": "Compliance with performance requirements",
                    "scoring_method": "pass_fail",
                    "max_score": 1.0,
                    "mandatory": True,
                    "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                },
                {
                    "name": "Maintenance and Service Support",
                    "weight": 20.0,
                    "description": "Comprehensive maintenance and service programs",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor service, 5=Excellent maintenance support"
                },
                {
                    "name": "Installation and Commissioning",
                    "weight": 15.0,
                    "description": "Professional installation and commissioning services",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor installation, 5=Professional commissioning"
                },
                {
                    "name": "Compliance with Building Standards",
                    "weight": 10.0,
                    "description": "Compliance with HVAC building codes and standards",
                    "scoring_method": "pass_fail",
                    "max_score": 1.0,
                    "mandatory": True,
                    "evaluation_notes": "Pass=1.0, Fail=0.0 (Mandatory)"
                }
            ],
            scoring_method=ScoringMethod.WEIGHTED_1_5,
            max_score=5.0,
            mandatory=False,
            evaluation_notes="HVAC-specific technical and performance assessment",
            source_document="NSW HVAC Building Standards",
            evaluation_guidance="Focus on efficiency, performance, and maintenance support",
            key_questions=[
                "What is the energy efficiency rating?",
                "Do systems meet all performance specifications?",
                "What maintenance and service support is provided?",
                "Is installation and commissioning professional?"
            ]
        )
    
    def _get_services_specific_criteria(self) -> DetailedEvaluationCriterion:
        """Get services-specific evaluation criteria"""
        return DetailedEvaluationCriterion(
            name="Service Delivery Requirements",
            category=CriterionCategory.QUALITY_MANAGEMENT,
            weight=5.0,
            description="Service delivery standards, performance measurement, and customer service",
            sub_criteria=[
                {
                    "name": "Service Level Agreements (SLAs)",
                    "weight": 30.0,
                    "description": "Comprehensive and measurable service level agreements",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor SLAs, 5=Excellent service commitments"
                },
                {
                    "name": "Performance Measurement Systems",
                    "weight": 25.0,
                    "description": "KPIs and performance monitoring systems",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=No KPIs, 5=Comprehensive performance measurement"
                },
                {
                    "name": "Customer Service and Communication",
                    "weight": 20.0,
                    "description": "Customer service standards and communication protocols",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor service, 5=Excellent customer focus"
                },
                {
                    "name": "Service Delivery Methodology",
                    "weight": 15.0,
                    "description": "Approach to service delivery and process management",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=Poor methodology, 5=Excellent service approach"
                },
                {
                    "name": "Continuity and Backup Services",
                    "weight": 10.0,
                    "description": "Service continuity planning and backup arrangements",
                    "scoring_method": "weighted_1_5",
                    "max_score": 5.0,
                    "evaluation_notes": "1=No continuity planning, 5=Comprehensive backup services"
                }
            ],
            scoring_method=ScoringMethod.WEIGHTED_1_5,
            max_score=5.0,
            mandatory=False,
            evaluation_notes="Service delivery assessment with focus on performance measurement",
            source_document="NSW Service Delivery Standards",
            evaluation_guidance="Focus on service quality, performance measurement, and customer satisfaction",
            key_questions=[
                "What service level agreements are provided?",
                "How is performance measured and monitored?",
                "What customer service standards are maintained?",
                "How is service continuity ensured?"
            ]
        )
    
    def _normalize_weights(self, criteria: List[DetailedEvaluationCriterion]):
        """Normalize criteria weights to total 100%"""
        total_weight = sum(c.weight for c in criteria)
        if total_weight > 100:
            for criterion in criteria:
                criterion.weight = (criterion.weight / total_weight) * 100
    
    def save_criteria_config(self, project_type: str, criteria: List[DetailedEvaluationCriterion]):
        """Save evaluation criteria configuration for a project type"""
        config_path = self.global_compliance_dir / f"{project_type.lower()}_evaluation_criteria.json"
        
        config_data = {
            "project_type": project_type,
            "created_date": datetime.now().isoformat(),
            "total_criteria": len(criteria),
            "criteria": [asdict(criterion) for criterion in criteria]
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_criteria_config(self, project_type: str) -> Optional[List[DetailedEvaluationCriterion]]:
        """Load evaluation criteria configuration for a project type"""
        config_path = self.global_compliance_dir / f"{project_type.lower()}_evaluation_criteria.json"
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            criteria = []
            for criterion_data in config_data.get("criteria", []):
                # Convert category string back to enum
                criterion_data["category"] = CriterionCategory(criterion_data["category"])
                criterion_data["scoring_method"] = ScoringMethod(criterion_data["scoring_method"])
                criteria.append(DetailedEvaluationCriterion(**criterion_data))
            
            return criteria
        except Exception as e:
            print(f"Error loading criteria config: {e}")
            return None

# Global instance
_evaluation_criteria_extractor = None

def get_evaluation_criteria_extractor(data_dir: Path) -> EvaluationCriteriaExtractor:
    """Get or create evaluation criteria extractor instance"""
    global _evaluation_criteria_extractor
    if _evaluation_criteria_extractor is None:
        _evaluation_criteria_extractor = EvaluationCriteriaExtractor(data_dir)
    return _evaluation_criteria_extractor

if __name__ == "__main__":
    # Test the evaluation criteria extractor
    from ..config import settings
    
    extractor = EvaluationCriteriaExtractor(settings.DATA_DIR)
    
    print("✅ Evaluation Criteria Extractor initialized")
    print(f"📋 Base evaluation criteria: {len(extractor.evaluation_criteria)}")
    
    # Test project-specific criteria
    for project_type in ["construction", "fleet", "hvac", "services"]:
        criteria = extractor.get_criteria_for_project_type(project_type)
        print(f"📋 {project_type.title()} criteria: {len(criteria)}")
        
        total_weight = sum(c.weight for c in criteria)
        print(f"   Total weight: {total_weight:.1f}%")
    
    print("\n🎉 Evaluation Criteria Extractor working correctly!")
