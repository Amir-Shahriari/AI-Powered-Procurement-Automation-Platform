#!/usr/bin/env python3
"""
Blacktown City Council RAG System
Stores official evaluation criteria and matrices as RAG data for easy updates
Based on Tender & Quotation Evaluation Manual - Table 1, 2, 3, and 4
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class BlacktownRAGDocument:
    """RAG document for Blacktown City Council standards"""
    document_id: str
    title: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_date: str
    updated_date: str
    version: str

class BlacktownRAGSystem:
    """
    RAG system for Blacktown City Council evaluation standards
    Stores official criteria and matrices as searchable documents
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rag_dir = data_dir / "blacktown_rag"
        self.rag_dir.mkdir(exist_ok=True)
        
        # Initialize RAG documents with official standards
        self._initialize_rag_documents()
    
    def _initialize_rag_documents(self):
        """Initialize RAG documents with official Blacktown City Council standards"""
        
        # Document 1: Table 1 - Criteria evaluation options
        table_1_doc = BlacktownRAGDocument(
            document_id="table_1_criteria_options",
            title="Table 1 - Criteria Evaluation Options",
            content={
                "criteria_categories": {
                    "compliance": {
                        "name": "Compliance",
                        "description": "Conformity with conditions of Tender",
                        "sub_criteria": [
                            {
                                "name": "Completion of corporate information",
                                "description": "All corporate information fields completed",
                                "scoring": "pass_fail"
                            },
                            {
                                "name": "Completion of schedules", 
                                "description": "All required schedules completed",
                                "scoring": "pass_fail"
                            },
                            {
                                "name": "Supply of accreditations",
                                "description": "All required accreditations provided",
                                "scoring": "pass_fail"
                            }
                        ]
                    },
                    "price": {
                        "name": "Price (Full Cost)",
                        "description": "Total cost of Quotation/Tender (whole of life cost)",
                        "sub_criteria": [
                            {
                                "name": "Total cost of Quotation/Tender",
                                "description": "Whole of life cost comparison",
                                "scoring": "currency_normalized"
                            },
                            {
                                "name": "Comparison of tenders received",
                                "description": "Competitive pricing analysis", 
                                "scoring": "comparative"
                            },
                            {
                                "name": "Comparison of benchmarks",
                                "description": "Market benchmark comparison",
                                "scoring": "benchmark"
                            },
                            {
                                "name": "Analysis of individual tendered items",
                                "description": "Item-by-item cost analysis",
                                "scoring": "detailed_analysis"
                            }
                        ]
                    },
                    "relevant_experience": {
                        "name": "Relevant Experience",
                        "description": "General performance history and similar project experience",
                        "sub_criteria": [
                            {
                                "name": "General performance history",
                                "description": "Overall track record and performance",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Experience with contracts of similar nature",
                                "description": "Similar projects and contracts",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Profile and experience of staff",
                                "description": "Key personnel experience and expertise",
                                "scoring": "weighted_1_5"
                            }
                        ]
                    },
                    "capability": {
                        "name": "Capability",
                        "description": "Demonstrated capability to perform the works as specified",
                        "sub_criteria": [
                            {
                                "name": "Demonstrated capability to perform works",
                                "description": "Ability to deliver specified requirements",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Ability to perform within workload",
                                "description": "Capacity to handle contract within existing workload",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Current workload assessment",
                                "description": "Evaluation of current commitments",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Technical skills",
                                "description": "Technical competency and expertise",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Appropriate resources",
                                "description": "Resources including condition of plant and equipment",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Capacity to complete on time",
                                "description": "Ability to deliver project satisfactorily and on time",
                                "scoring": "weighted_1_5"
                            }
                        ]
                    },
                    "management_financial": {
                        "name": "Management & Financial",
                        "description": "Financial capacity and management capabilities",
                        "sub_criteria": [
                            {
                                "name": "Financial capacity against contract requirements",
                                "description": "Financial strength relative to contract value",
                                "scoring": "financial_assessment"
                            },
                            {
                                "name": "Level of Council supervision required",
                                "description": "Independence and self-management capability",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Management and Senior Personnel skills",
                                "description": "Quality of management and senior staff",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Financial stability and operating history",
                                "description": "Business stability and track record",
                                "scoring": "stability_assessment"
                            },
                            {
                                "name": "Ability to manage within budget",
                                "description": "Budget management and accurate accounting",
                                "scoring": "weighted_1_5"
                            }
                        ]
                    },
                    "quality_management": {
                        "name": "Quality Management",
                        "description": "Quality management systems and procedures",
                        "sub_criteria": [
                            {
                                "name": "Level and detail of quality plan",
                                "description": "Comprehensiveness of quality management plan",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Minimum standards of safety plan",
                                "description": "Safety plan standards and implementation",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Reporting procedures",
                                "description": "Quality reporting and monitoring procedures",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Response and resolution",
                                "description": "Issue response and resolution procedures",
                                "scoring": "weighted_1_5"
                            }
                        ]
                    },
                    "work_health_safety": {
                        "name": "Work Health & Safety",
                        "description": "WHS compliance and safety management systems",
                        "sub_criteria": [
                            {
                                "name": "Completion and signing of WHS051.5",
                                "description": "WHS declaration form completion",
                                "scoring": "pass_fail"
                            },
                            {
                                "name": "Completion and signing of WHS051.6",
                                "description": "Contractor WHS requirements completion",
                                "scoring": "pass_fail"
                            },
                            {
                                "name": "WHS System Manual and evidence",
                                "description": "Comprehensive WHS management system",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Compliance with industry standards",
                                "description": "NSW Workcover and Australian Standards compliance",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Independent certification AS/NZS 48001:2001",
                                "description": "Certified Safety Management System",
                                "scoring": "certification"
                            }
                        ]
                    },
                    "sustainability": {
                        "name": "Sustainable Environmental Management",
                        "description": "Environmental management and sustainability practices",
                        "sub_criteria": [
                            {
                                "name": "Environmental Policy/Management Plan",
                                "description": "Comprehensive environmental management system",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Independent certification",
                                "description": "ISO 14001 or equivalent certification",
                                "scoring": "certification"
                            },
                            {
                                "name": "Environmental training procedures",
                                "description": "Staff environmental training programs",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Sustainability record",
                                "description": "Historical environmental performance including waste minimisation, energy efficiency, recycling, pollution levels, habitat protection, recycled content, product recycling, sourcing location, and environmental prosecutions",
                                "scoring": "sustainability_assessment"
                            }
                        ]
                    },
                    "social_community": {
                        "name": "Social & Community",
                        "description": "Social procurement and community benefit criteria",
                        "sub_criteria": [
                            {
                                "name": "Knowledge of local conditions",
                                "description": "Understanding of local area and conditions",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Social impact on local economy",
                                "description": "Positive economic impact on local community",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Cooperation with community groups",
                                "description": "Ability to work with committees and community groups",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Community benefit projects",
                                "description": "Projects delivering community benefits including disability access, cultural accommodation, local charity support",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Employment for disadvantaged groups",
                                "description": "Employment opportunities for disadvantaged groups within local community",
                                "scoring": "weighted_1_5"
                            },
                            {
                                "name": "Social inclusion and diversity",
                                "description": "Social inclusion, employment & training, diversity & equality, enhancing local amenities, addressing local negative issues",
                                "scoring": "weighted_1_5"
                            }
                        ]
                    },
                    "eeo_fair_employment": {
                        "name": "EEO & Fair Employment",
                        "description": "Equal employment opportunity and fair employment practices",
                        "sub_criteria": [
                            {
                                "name": "Wages paid under award or EA",
                                "description": "Compliance with award or enterprise agreement",
                                "scoring": "compliance_check"
                            },
                            {
                                "name": "Superannuation paid",
                                "description": "Superannuation guarantee compliance",
                                "scoring": "compliance_check"
                            },
                            {
                                "name": "Location of records kept",
                                "description": "Record keeping and accessibility",
                                "scoring": "compliance_check"
                            },
                            {
                                "name": "EEO and anti-discrimination policies",
                                "description": "Equal opportunity and anti-discrimination policies including training and development, dispute resolution",
                                "scoring": "policy_assessment"
                            },
                            {
                                "name": "Aboriginal and Torres Strait Islander employment",
                                "description": "Indigenous employment policies and implementation",
                                "scoring": "policy_assessment"
                            },
                            {
                                "name": "Apprenticeships and traineeships",
                                "description": "Training and development opportunities",
                                "scoring": "training_assessment"
                            }
                        ]
                    }
                }
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "table_reference": "Table 1",
                "section": "A.7 EVALUATION CRITERIA MATRIX",
                "document_type": "evaluation_criteria"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Document 2: Table 2 - Evaluation Criteria Matrix (Quotation Value $100,000-$249,999)
        table_2_doc = BlacktownRAGDocument(
            document_id="table_2_quotation_matrix",
            title="Table 2 - Evaluation Criteria Matrix: Quotation Value ($100,000-$249,999)",
            content={
                "purchase_categories": {
                    "standard_product_good": {
                        "name": "Standard product or good",
                        "description": "A product or good that is well tested in the market place and is utilised by many other firms.",
                        "risk_profile": "Low Risk - Risk level can increase as price increases",
                        "criteria": {
                            "price": {"weighting_range": [40, 60], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": []
                    },
                    "construction_contract": {
                        "name": "Construction contract valued up to $249,999",
                        "description": "Contract focuses on the delivery of the construction works",
                        "risk_profile": "Low Risk - Essential to ensure works comply with specification",
                        "criteria": {
                            "price": {"weighting_range": [40, 60], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 20]},
                            "capability": {"weighting_range": [5, 20]},
                            "quality_management": {"weighting_range": [2, 10]},
                            "management_financial": {"weighting_range": [0, 10]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": ["sustainability", "eeo_fair_employment"]
                    },
                    "consultancy_contract": {
                        "name": "Consultancy contract valued up to $249,999",
                        "description": "Consultancy requiring a limited range of professional input",
                        "risk_profile": "Low Risk - Essential to ensure timeline, budgets and specification is met",
                        "criteria": {
                            "price": {"weighting_range": [20, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [5, 30]},
                            "management_financial": {"weighting_range": [0, 10]},
                            "quality_management": {"weighting_range": [2, 5]},
                            "work_health_safety": {"weighting_range": [2, 5]}
                        },
                        "combined_10_percent": []
                    },
                    "service_delivery_contract": {
                        "name": "Service delivery contract valued up to $249,999",
                        "description": "Service contract that is for a limited period of time (regular or intermittent service provision)",
                        "risk_profile": "Low Risk - Essential to ensure service delivery",
                        "criteria": {
                            "price": {"weighting_range": [20, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 40]},
                            "capability": {"weighting_range": [5, 30]},
                            "management_financial": {"weighting_range": [0, 10]},
                            "quality_management": {"weighting_range": [2, 5]},
                            "work_health_safety": {"weighting_range": [2, 10]}
                        },
                        "combined_10_percent": []
                    },
                    "management_contract": {
                        "name": "Management Contract up to $249,999",
                        "description": "A contract where the contractor manages a facility for council (i.e. Café, Showground)",
                        "risk_profile": "Medium Risk - Dependant on staff appointed to deliver the contract",
                        "criteria": {
                            "price": {"weighting_range": [30, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 10]},
                            "quality_management": {"weighting_range": [2, 10]},
                            "work_health_safety": {"weighting_range": [0, 10]}
                        },
                        "combined_10_percent": []
                    },
                    "lease_license": {
                        "name": "Lease / Licence up to $249,999",
                        "description": "Where a supplier is submitting price to access a Council service or resource (i.e. commercial activity)",
                        "risk_profile": "Medium Risk - Dependant on experience and track record of proposed service provider",
                        "criteria": {
                            "price": {"weighting_range": [30, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 10]},
                            "quality_management": {"weighting_range": [0, 10]},
                            "work_health_safety": {"weighting_range": [0, 10]}
                        },
                        "combined_10_percent": []
                    }
                }
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "table_reference": "Table 2",
                "section": "A.7.1 Staff should apply the relevant criteria weighting range based on the type of purchase category",
                "contract_value_range": "$100,000 - $249,999",
                "document_type": "evaluation_matrix"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Document 3: Table 3 - Evaluation Criteria Matrix (Tender Value $250,000+)
        table_3_doc = BlacktownRAGDocument(
            document_id="table_3_tender_matrix",
            title="Table 3 - Evaluation Criteria Matrix: Tender Value ($250,000+)",
            content={
                "local_preference_note": "When evaluating submissions any supplier identified as local to the Blacktown LGA or the wider Western Sydney area will attract a percentage price discount as dictated by their physical location. The evaluation spread sheet located on the procurement – tenders section of the intranet must be used.",
                "purchase_categories": {
                    "standard_product_good": {
                        "name": "Standard product or good",
                        "description": "Refers to a product or good that is well tested in the market place and is utilised by many other organisations.",
                        "risk_profile": "Medium Risk - Risk level can increase as price increases",
                        "criteria": {
                            "price": {"weighting_range": [40, 60], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": ["sustainability", "eeo_fair_employment"],
                        "local_preference": True
                    },
                    "construction_contract": {
                        "name": "Construction contract valued at over $249,999",
                        "description": "Typically a contract requiring a limited level of professional input combined with construction works",
                        "risk_profile": "Medium – High Risk - Essential to ensure time lines and budget met. Works comply with specifications",
                        "criteria": {
                            "price": {"weighting_range": [35, 60], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 20]},
                            "capability": {"weighting_range": [5, 20]},
                            "management_financial": {"weighting_range": [5, 15]},
                            "quality_management": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": ["sustainability", "eeo_fair_employment"],
                        "local_preference": True
                    },
                    "consultancy_contract": {
                        "name": "Consultancy contract valued at over $249,999",
                        "description": "Consultancy requiring a high level of technical expertise often from a range of professionals. May also include a high level of innovation",
                        "risk_profile": "Medium to High Risk - Essential to ensure project team satisfy the specification",
                        "criteria": {
                            "price": {"weighting_range": [25, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": ["social_community", "eeo_fair_employment"],
                        "local_preference": True
                    },
                    "service_delivery_contract": {
                        "name": "Service delivery contract valued at over $249,999",
                        "description": "Service delivery contract involving the provision of a service that often covers more than one year and/or multiple service components",
                        "risk_profile": "Medium to High Risk - Essential to ensure service delivered on time and on a long term basis",
                        "criteria": {
                            "price": {"weighting_range": [30, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 10]},
                            "quality_management": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [5, 10]}
                        },
                        "combined_10_percent": ["sustainability", "social_community", "eeo_fair_employment"],
                        "local_preference": True
                    },
                    "management_contract": {
                        "name": "Management Contract valued at over $249,999",
                        "description": "Refers to a contract where the contractor manages a facility for council (i.e. Café, showground)",
                        "risk_profile": "Medium to High Risk - Dependent on staff appointed to deliver the contract and period of contract",
                        "criteria": {
                            "price": {"weighting_range": [30, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 15]},
                            "quality_management": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [0, 10]}
                        },
                        "combined_10_percent": ["sustainability", "social_community", "eeo_fair_employment"],
                        "local_preference": True
                    },
                    "lease_license": {
                        "name": "Lease / License valued at over $249,999",
                        "description": "Where a supplier is submitting a price to access a Council service or resource (i.e. commercial activity)",
                        "risk_profile": "Medium to High Risk - Highly dependent on experience and track record of proposed service provider",
                        "criteria": {
                            "price": {"weighting_range": [30, 50], "description": "Full Cost"},
                            "relevant_experience": {"weighting_range": [10, 30]},
                            "capability": {"weighting_range": [10, 30]},
                            "management_financial": {"weighting_range": [5, 15]},
                            "quality_management": {"weighting_range": [5, 10]},
                            "work_health_safety": {"weighting_range": [0, 10]}
                        },
                        "combined_10_percent": [],
                        "local_preference": True
                    }
                }
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "table_reference": "Table 3",
                "section": "For purchases $250,000 and over (inclusive of GST)",
                "contract_value_range": "$250,000+",
                "document_type": "evaluation_matrix"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Document 4: Table 4 - Rating scales
        table_4_doc = BlacktownRAGDocument(
            document_id="table_4_rating_scales",
            title="Table 4 - Rating scales for WHS, Sustainable Environmental Management, Social and Community and EEO & Fair Employment",
            content={
                "rating_scales": {
                    "whs": {
                        "scale_name": "Work Health & Safety Rating Scale",
                        "scores": {
                            5: {
                                "level": "Excellent",
                                "requirements": "Extensive WHS System + Risk Assessment + Safe Work Methods Statements + Hazardous Chemicals Statements + WHS Representative + Training Records"
                            },
                            4: {
                                "level": "Very Good",
                                "requirements": "Detailed WHS System Submitted (Evidence Supplied)"
                            },
                            3: {
                                "level": "Good",
                                "requirements": "Satisfactory WHS System Submitted (Evidence Supplied)"
                            },
                            2: {
                                "level": "Fair",
                                "requirements": "Simple WHS Policy System (Evidence Supplied)"
                            },
                            1: {
                                "level": "Poor",
                                "requirements": "WHS051.6 Contractors WHS Requirements – Completed (No Evidence Supplied)"
                            },
                            0: {
                                "level": "Unacceptable",
                                "requirements": "No information provided or WHS system in place"
                            }
                        }
                    },
                    "sustainability": {
                        "scale_name": "Sustainable Environmental Management Rating Scale",
                        "scores": {
                            5: {
                                "level": "Excellent",
                                "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance with the system + detailed sustainable policies and practices of waste minimisation, recycling and energy conservation etc."
                            },
                            4: {
                                "level": "Very Good",
                                "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance with the system + sustainable policies and practices of waste minimisation, recycling and energy conservation etc."
                            },
                            3: {
                                "level": "Good",
                                "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance with the system + sustainable policies and practices of some waste minimisation, recycling and energy conservation etc."
                            },
                            2: {
                                "level": "Fair",
                                "requirements": "An Environmental Management system + sustainable policies and practices of one waste minimisation, recycling and energy conservation etc."
                            },
                            1: {
                                "level": "Poor",
                                "requirements": "An Environmental Management system + no sustainable policies and practices of waste minimisation, recycling and energy conservation etc."
                            },
                            0: {
                                "level": "Unacceptable",
                                "requirements": "No information or no Environmental Sustainable System"
                            }
                        }
                    },
                    "social_community": {
                        "scale_name": "Social and Community Rating Scale",
                        "scores": {
                            5: {
                                "level": "Excellent",
                                "requirements": "Excellent response to criteria, exceeds all requirements and is fully substantiated (provides extra value for money solutions)"
                            },
                            4: {
                                "level": "Very Good",
                                "requirements": "Very satisfactory response, meets all requirements and is fully substantiated"
                            },
                            3: {
                                "level": "Good",
                                "requirements": "Satisfactory, meets all requirements and appropriately substantiated"
                            },
                            2: {
                                "level": "Fair",
                                "requirements": "Adequate response with material defects that prevent a full submission to the requirements"
                            },
                            1: {
                                "level": "Poor",
                                "requirements": "Unsatisfactory response, does not meet minimum requirements or is inadequately substantiated"
                            },
                            0: {
                                "level": "Unacceptable",
                                "requirements": "Non response or a response where claims are unsubstantiated"
                            }
                        }
                    },
                    "eeo_fair_employment": {
                        "scale_name": "EEO & Fair Employment Rating Scale",
                        "scores": {
                            5: {
                                "level": "Excellent",
                                "requirements": "Wages paid under award/EA + super paid + location of records kept + Policies on EEO, recruitment, training & development, anti-discrimination, unionism and dispute resolution and implementation + Aboriginal & Torres Strait Islander Employment Policies & Implementation + Apprenticeships or Traineeships Offered or In Place"
                            },
                            4: {
                                "level": "Very Good",
                                "requirements": "Wages paid under award/EA + super paid + location of records kept + Policies on EEO, recruitment, training & development, anti-discrimination, unionism and dispute resolution and implementation + Aboriginal & Torres Strait Islander Employment Policies + Apprenticeships or Traineeships Offered or In Place"
                            },
                            3: {
                                "level": "Good",
                                "requirements": "Wages paid under award/EA + super paid + location of records kept + Policies on EEO, recruitment, training & development, anti-discrimination, unionism and dispute resolution + Aboriginal & Torres Strait Islander Employment Policies + Apprenticeships or Traineeships"
                            },
                            2: {
                                "level": "Fair",
                                "requirements": "Wages paid under award + super paid + location of records kept + policies on EEO, recruitment, training & development, anti-discrimination, unionism and dispute resolution"
                            },
                            1: {
                                "level": "Poor",
                                "requirements": "Wages paid under award + super paid + location of records kept + no policies on EEO, recruitment, training & development, anti-discrimination, unionism and dispute resolution"
                            },
                            0: {
                                "level": "Unacceptable",
                                "requirements": "No information or no fair employment offered"
                            }
                        }
                    }
                }
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "table_reference": "Table 4",
                "section": "Rating scales for WHS, Sustainable Environmental Management, Social and Community and EEO & Fair Employment",
                "document_type": "rating_scales"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Document 5: Local Preference Policy
        local_preference_doc = BlacktownRAGDocument(
            document_id="local_preference_policy",
            title="Local Preference Policy - Blacktown City Council",
            content={
                "policy_details": {
                    "blacktown_lga": {
                        "discount_percentage": 5.0,
                        "max_benefit": 50000,
                        "description": "Supplier with a principal place of business or part of their business address (not being a PO Box) that is located within the Blacktown City local government area.",
                        "application": "5% discount on the tendered pricing capped at a maximum benefit of $50,000"
                    },
                    "western_sydney": {
                        "discount_percentage": 2.5,
                        "max_benefit": 25000,
                        "description": "Supplier with a principal place of business or part of their business address (not being a PO Box) that is located within a Western Sydney Council LGA",
                        "councils": [
                            "Blue Mountains City Council",
                            "City of Parramatta Council",
                            "Cumberland City Council",
                            "Fairfield City Council",
                            "Hawkesbury City Council",
                            "Liverpool City Council",
                            "Parramatta City Council",
                            "Penrith City Council",
                            "The Hills Shire Council"
                        ],
                        "application": "2.5% discount capped at a maximum of $25,000 for those suppliers located in Western Sydney Councils"
                    }
                },
                "application_requirements": [
                    "For any suppliers identified as being eligible for application of local preference benefit please provide the address confirming them as local in the third tab of the tender evaluation spreadsheet",
                    "The evaluation spread sheet located on the procurement – tenders section of the intranet must be used",
                    "Applicants will be evaluated in accordance with the Local Preference Policy as specified in the Procurement Policy P000553.1"
                ]
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "section": "A.9 LOCAL PREFERENCE CRITERIA",
                "policy_reference": "Procurement Policy P000553.1",
                "document_type": "local_preference_policy"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Document 6: Social Procurement Guidelines
        social_procurement_doc = BlacktownRAGDocument(
            document_id="social_procurement_guidelines",
            title="Social & Community Requirements - Social Procurement Guidelines",
            content={
                "social_procurement_definition": "Social procurement involves using procurement processes and purchasing power to generate positive social outcomes in addition to the delivery of efficient goods, services and works. These are achieved by setting social value objectives.",
                "social_value_objectives": {
                    "employment_training": {
                        "name": "Employment and Training",
                        "how_achieved": [
                            "Building in to contracts opportunities for employment for people who have been excluded from the workforce",
                            "Strengthening Place-based employment",
                            "Generating training opportunities for people who have experienced long term unemployment as a pathway into labour market participation"
                        ]
                    },
                    "social_inclusion": {
                        "name": "Social Inclusion",
                        "how_achieved": [
                            "Building into contracts consideration about how suppliers could respond to reducing social exclusion in place or amongst particular populations by addressing: poverty and low income; lack of access to the job market; limited social supports and networks; lack of opportunities in local neighbourhoods; exclusion from services",
                            "Including, where appropriate, consideration of how suppliers could address disadvantage and exclusion associated with housing and tenancy",
                            "Including, where appropriate, consideration of how suppliers could contribute to empowerment and capacity-building opportunities that generate pathways out of exclusion and disadvantage"
                        ]
                    },
                    "diversity_equality": {
                        "name": "Diversity and Equality",
                        "how_achieved": [
                            "Ensuring that 'minority' businesses have fair and equal access to procurement opportunities eg. Indigenous businesses",
                            "Building a diverse supplier base that reflects the diversity of the community",
                            "Ensuring that small businesses and social benefit suppliers have fair and equal access to procurement opportunities"
                        ]
                    },
                    "local_sustainability": {
                        "name": "Local Sustainability",
                        "how_achieved": [
                            "Ensuring that the viability and sustainability of a local community and their economy is considered in purchasing and procurement decisions",
                            "Using local suppliers can help to stimulate the local economy, particularly in those communities that have experienced economic or social hardship"
                        ]
                    },
                    "social_service_innovation": {
                        "name": "Social and Service Innovation",
                        "how_achieved": [
                            "Ensuring that purchasing and procurement can play a role in supporting social innovation by enabling entities to test and develop and scale innovations in a market environment",
                            "Procurement can support social innovation and market creation through consideration of how procurement can open new markets"
                        ]
                    },
                    "fair_trade": {
                        "name": "Fair Trade",
                        "how_achieved": [
                            "Ensuring that supply chains are adhering to fair trade practices can generate social benefits for disadvantaged communities locally and internationally"
                        ]
                    }
                },
                "application_guidelines": [
                    "Social procurement includes all organisations that can meet the social procurement criteria defined in the specification",
                    "This meets the requirements of obtaining submissions through a public advertisement through an open tender or expression of interest for a selective tender required under the Local Government (General) Regulation 2005, Part 7 Tendering, Section 166",
                    "Social and Community criteria should be included in the specification as specific requirements under the heading of Social and Community",
                    "These should also include the performance measurements and how the criteria will be assessed",
                    "Under Local Government and Competition and Consumer Acts the criteria must not restrict tender submissions",
                    "The specification should detail the outcomes required and not a specific supplier's solution"
                ],
                "reference_document": "A Guide to Achieving Social Value through Public Sector Procurement - http://socialprocurementaustralasia.com/ninox/wp-content/uploads/2013/09/Social-Procurement-in-NSW-Full-Guide.pdf"
            },
            metadata={
                "source": "Blacktown City Council Tender & Quotation Evaluation Manual",
                "section": "A.10 SOCIAL & COMMUNITY CRITERIA",
                "document_type": "social_procurement_guidelines"
            },
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            version="1.0"
        )
        
        # Save all documents
        documents = [
            table_1_doc,
            table_2_doc, 
            table_3_doc,
            table_4_doc,
            local_preference_doc,
            social_procurement_doc
        ]
        
        for doc in documents:
            self.save_rag_document(doc)
    
    def save_rag_document(self, document: BlacktownRAGDocument):
        """Save RAG document to file"""
        file_path = self.rag_dir / f"{document.document_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(document), f, indent=2, ensure_ascii=False)
    
    def load_rag_document(self, document_id: str) -> Optional[BlacktownRAGDocument]:
        """Load RAG document from file"""
        file_path = self.rag_dir / f"{document_id}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return BlacktownRAGDocument(**data)
            except Exception as e:
                print(f"Error loading RAG document {document_id}: {e}")
                return None
        return None
    
    def get_all_rag_documents(self) -> List[BlacktownRAGDocument]:
        """Get all RAG documents"""
        documents = []
        for file_path in self.rag_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                documents.append(BlacktownRAGDocument(**data))
            except Exception as e:
                print(f"Error loading RAG document {file_path}: {e}")
        return documents
    
    def search_rag_documents(self, query: str, document_type: Optional[str] = None) -> List[BlacktownRAGDocument]:
        """Search RAG documents by query and optionally filter by document type"""
        all_docs = self.get_all_rag_documents()
        
        if document_type:
            all_docs = [doc for doc in all_docs if doc.metadata.get("document_type") == document_type]
        
        # Simple text search in title and content
        matching_docs = []
        query_lower = query.lower()
        
        for doc in all_docs:
            if (query_lower in doc.title.lower() or 
                query_lower in str(doc.content).lower() or
                query_lower in str(doc.metadata).lower()):
                matching_docs.append(doc)
        
        return matching_docs
    
    def update_rag_document(self, document_id: str, updates: Dict[str, Any]):
        """Update existing RAG document"""
        doc = self.load_rag_document(document_id)
        if doc:
            # Update fields
            for key, value in updates.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)
            
            # Update timestamp
            doc.updated_date = datetime.now().isoformat()
            
            # Save updated document
            self.save_rag_document(doc)
            return True
        return False
    
    def get_evaluation_criteria_by_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get evaluation criteria for specific category"""
        table_1 = self.load_rag_document("table_1_criteria_options")
        if table_1 and "criteria_categories" in table_1.content:
            return table_1.content["criteria_categories"].get(category)
        return None
    
    def get_evaluation_matrix(self, purchase_category: str, contract_value_range: str) -> Optional[Dict[str, Any]]:
        """Get evaluation matrix for specific purchase category and contract value"""
        if contract_value_range == "$100,000 - $249,999":
            table_doc = self.load_rag_document("table_2_quotation_matrix")
        else:
            table_doc = self.load_rag_document("table_3_tender_matrix")
        
        if table_doc and "purchase_categories" in table_doc.content:
            return table_doc.content["purchase_categories"].get(purchase_category)
        return None
    
    def get_rating_scale(self, scale_name: str) -> Optional[Dict[str, Any]]:
        """Get rating scale for specific criterion"""
        table_4 = self.load_rag_document("table_4_rating_scales")
        if table_4 and "rating_scales" in table_4.content:
            return table_4.content["rating_scales"].get(scale_name)
        return None
    
    def get_local_preference_policy(self) -> Optional[Dict[str, Any]]:
        """Get local preference policy details"""
        local_pref_doc = self.load_rag_document("local_preference_policy")
        if local_pref_doc and "policy_details" in local_pref_doc.content:
            return local_pref_doc.content["policy_details"]
        return None

# Global instance
_blacktown_rag_system = None

def get_blacktown_rag_system(data_dir: Path) -> BlacktownRAGSystem:
    """Get or create Blacktown RAG system instance"""
    global _blacktown_rag_system
    if _blacktown_rag_system is None:
        _blacktown_rag_system = BlacktownRAGSystem(data_dir)
    return _blacktown_rag_system

if __name__ == "__main__":
    # Test the Blacktown RAG system
    from ..config import settings
    
    rag_system = BlacktownRAGSystem(settings.DATA_DIR)
    
    print("✅ Blacktown City Council RAG System initialized")
    
    # Test document loading
    all_docs = rag_system.get_all_rag_documents()
    print(f"📚 Total RAG documents: {len(all_docs)}")
    
    for doc in all_docs:
        print(f"   - {doc.title} (v{doc.version})")
    
    # Test search functionality
    search_results = rag_system.search_rag_documents("construction")
    print(f"\n🔍 Search results for 'construction': {len(search_results)}")
    
    # Test specific retrievals
    construction_criteria = rag_system.get_evaluation_criteria_by_category("capability")
    print(f"\n📋 Capability criteria loaded: {construction_criteria is not None}")
    
    matrix = rag_system.get_evaluation_matrix("construction_contract", "$250,000+")
    print(f"📊 Construction matrix loaded: {matrix is not None}")
    
    whs_scale = rag_system.get_rating_scale("whs")
    print(f"📏 WHS rating scale loaded: {whs_scale is not None}")
    
    local_pref = rag_system.get_local_preference_policy()
    print(f"🏠 Local preference policy loaded: {local_pref is not None}")
    
    print("\n🎉 Blacktown City Council RAG System ready!")
    print("📝 All official standards stored as RAG data for easy updates")
