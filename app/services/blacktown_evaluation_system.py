#!/usr/bin/env python3
"""
Blacktown City Council Evaluation System
Official evaluation criteria and matrices based on Tender & Quotation Evaluation Manual
Implements Table 1, 2, 3, and 4 from the official Blacktown City Council standards
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class PurchaseCategory(Enum):
    """Purchase categories from Blacktown City Council standards"""
    STANDARD_PRODUCT_GOOD = "standard_product_good"
    CONSTRUCTION_CONTRACT = "construction_contract"
    CONSULTANCY_CONTRACT = "consultancy_contract"
    SERVICE_DELIVERY_CONTRACT = "service_delivery_contract"
    MANAGEMENT_CONTRACT = "management_contract"
    LEASE_LICENSE = "lease_license"

class ContractValue(Enum):
    """Contract value ranges"""
    QUOTATION_100K_249K = "quotation_100k_249k"  # $100,000 - $249,999
    TENDER_250K_PLUS = "tender_250k_plus"        # $250,000+

class LocalPreferenceCategory(Enum):
    """Local preference categories"""
    BLACKTOWN_LGA = "blacktown_lga"
    WESTERN_SYDNEY = "western_sydney"
    OTHER = "other"

@dataclass
class BlacktownEvaluationCriterion:
    """Blacktown City Council evaluation criterion"""
    name: str
    description: str
    sub_criteria: List[Dict[str, Any]]
    weighting_range: Tuple[float, float]
    scoring_method: str
    mandatory: bool = False
    rating_scale: Optional[Dict[str, Any]] = None

@dataclass
class SupplierLocation:
    """Supplier location for local preference calculation"""
    business_address: str
    is_blacktown_lga: bool = False
    is_western_sydney: bool = False
    local_preference_discount: float = 0.0

class BlacktownEvaluationSystem:
    """
    Blacktown City Council evaluation system implementing official criteria and matrices
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._initialize_criteria()
        self._initialize_evaluation_matrices()
        self._initialize_rating_scales()
        self._initialize_local_preference()
    
    def _initialize_criteria(self):
        """Initialize evaluation criteria from Table 1"""
        
        self.evaluation_criteria = {
            "compliance": BlacktownEvaluationCriterion(
                name="Compliance",
                description="Conformity with conditions of Tender",
                sub_criteria=[
                    {
                        "name": "Completion of corporate information",
                        "description": "All corporate information fields completed",
                        "weight": 33.3,
                        "scoring": "pass_fail"
                    },
                    {
                        "name": "Completion of schedules",
                        "description": "All required schedules completed",
                        "weight": 33.3,
                        "scoring": "pass_fail"
                    },
                    {
                        "name": "Supply of accreditations",
                        "description": "All required accreditations provided",
                        "weight": 33.4,
                        "scoring": "pass_fail"
                    }
                ],
                weighting_range=(0, 0),  # Mandatory pass/fail
                scoring_method="pass_fail",
                mandatory=True
            ),
            
            "price": BlacktownEvaluationCriterion(
                name="Price (Full Cost)",
                description="Total cost of Quotation/Tender (whole of life cost)",
                sub_criteria=[
                    {
                        "name": "Total cost of Quotation/Tender",
                        "description": "Whole of life cost comparison",
                        "weight": 40.0,
                        "scoring": "currency_normalized"
                    },
                    {
                        "name": "Comparison of tenders received",
                        "description": "Competitive pricing analysis",
                        "weight": 25.0,
                        "scoring": "comparative"
                    },
                    {
                        "name": "Comparison of benchmarks",
                        "description": "Market benchmark comparison",
                        "weight": 20.0,
                        "scoring": "benchmark"
                    },
                    {
                        "name": "Analysis of individual tendered items",
                        "description": "Item-by-item cost analysis",
                        "weight": 15.0,
                        "scoring": "detailed_analysis"
                    }
                ],
                weighting_range=(20, 60),  # Varies by category
                scoring_method="currency_normalized"
            ),
            
            "relevant_experience": BlacktownEvaluationCriterion(
                name="Relevant Experience",
                description="General performance history and similar project experience",
                sub_criteria=[
                    {
                        "name": "General performance history",
                        "description": "Overall track record and performance",
                        "weight": 40.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Experience with contracts of similar nature",
                        "description": "Similar projects and contracts",
                        "weight": 35.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Profile and experience of staff",
                        "description": "Key personnel experience and expertise",
                        "weight": 25.0,
                        "scoring": "weighted_1_5"
                    }
                ],
                weighting_range=(10, 40),
                scoring_method="weighted_1_5"
            ),
            
            "capability": BlacktownEvaluationCriterion(
                name="Capability",
                description="Demonstrated capability to perform the works as specified",
                sub_criteria=[
                    {
                        "name": "Demonstrated capability to perform works",
                        "description": "Ability to deliver specified requirements",
                        "weight": 25.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Ability to perform within workload",
                        "description": "Capacity to handle contract within existing workload",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Current workload assessment",
                        "description": "Evaluation of current commitments",
                        "weight": 15.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Technical skills",
                        "description": "Technical competency and expertise",
                        "weight": 15.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Appropriate resources",
                        "description": "Resources including condition of plant and equipment",
                        "weight": 15.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Capacity to complete on time",
                        "description": "Ability to deliver project satisfactorily and on time",
                        "weight": 10.0,
                        "scoring": "weighted_1_5"
                    }
                ],
                weighting_range=(5, 30),
                scoring_method="weighted_1_5"
            ),
            
            "management_financial": BlacktownEvaluationCriterion(
                name="Management & Financial",
                description="Financial capacity and management capabilities",
                sub_criteria=[
                    {
                        "name": "Financial capacity against contract requirements",
                        "description": "Financial strength relative to contract value",
                        "weight": 30.0,
                        "scoring": "financial_assessment"
                    },
                    {
                        "name": "Level of Council supervision required",
                        "description": "Independence and self-management capability",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Management and Senior Personnel skills",
                        "description": "Quality of management and senior staff",
                        "weight": 25.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Financial stability and operating history",
                        "description": "Business stability and track record",
                        "weight": 15.0,
                        "scoring": "stability_assessment"
                    },
                    {
                        "name": "Ability to manage within budget",
                        "description": "Budget management and accurate accounting",
                        "weight": 10.0,
                        "scoring": "weighted_1_5"
                    }
                ],
                weighting_range=(0, 15),
                scoring_method="weighted_1_5"
            ),
            
            "quality_management": BlacktownEvaluationCriterion(
                name="Quality Management",
                description="Quality management systems and procedures",
                sub_criteria=[
                    {
                        "name": "Level and detail of quality plan",
                        "description": "Comprehensiveness of quality management plan",
                        "weight": 40.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Minimum standards of safety plan",
                        "description": "Safety plan standards and implementation",
                        "weight": 30.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Reporting procedures",
                        "description": "Quality reporting and monitoring procedures",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Response and resolution",
                        "description": "Issue response and resolution procedures",
                        "weight": 10.0,
                        "scoring": "weighted_1_5"
                    }
                ],
                weighting_range=(2, 10),
                scoring_method="weighted_1_5"
            ),
            
            "work_health_safety": BlacktownEvaluationCriterion(
                name="Work Health & Safety",
                description="WHS compliance and safety management systems",
                sub_criteria=[
                    {
                        "name": "Completion and signing of WHS051.5",
                        "description": "WHS declaration form completion",
                        "weight": 20.0,
                        "scoring": "pass_fail"
                    },
                    {
                        "name": "Completion and signing of WHS051.6",
                        "description": "Contractor WHS requirements completion",
                        "weight": 20.0,
                        "scoring": "pass_fail"
                    },
                    {
                        "name": "WHS System Manual and evidence",
                        "description": "Comprehensive WHS management system",
                        "weight": 30.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Compliance with industry standards",
                        "description": "NSW Workcover and Australian Standards compliance",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Independent certification AS/NZS 48001:2001",
                        "description": "Certified Safety Management System",
                        "weight": 10.0,
                        "scoring": "certification"
                    }
                ],
                weighting_range=(2, 10),
                scoring_method="weighted_1_5",
                rating_scale="whs_rating_scale"
            ),
            
            "sustainability": BlacktownEvaluationCriterion(
                name="Sustainable Environmental Management",
                description="Environmental management and sustainability practices",
                sub_criteria=[
                    {
                        "name": "Environmental Policy/Management Plan",
                        "description": "Comprehensive environmental management system",
                        "weight": 25.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Independent certification",
                        "description": "ISO 14001 or equivalent certification",
                        "weight": 20.0,
                        "scoring": "certification"
                    },
                    {
                        "name": "Environmental training procedures",
                        "description": "Staff environmental training programs",
                        "weight": 15.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Sustainability record",
                        "description": "Historical environmental performance",
                        "weight": 40.0,
                        "scoring": "sustainability_assessment"
                    }
                ],
                weighting_range=(0, 10),  # Part of combined 10%
                scoring_method="weighted_1_5",
                rating_scale="sustainability_rating_scale"
            ),
            
            "social_community": BlacktownEvaluationCriterion(
                name="Social & Community",
                description="Social procurement and community benefit criteria",
                sub_criteria=[
                    {
                        "name": "Knowledge of local conditions",
                        "description": "Understanding of local area and conditions",
                        "weight": 15.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Social impact on local economy",
                        "description": "Positive economic impact on local community",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Cooperation with community groups",
                        "description": "Ability to work with committees and community groups",
                        "weight": 20.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Community benefit projects",
                        "description": "Projects delivering community benefits",
                        "weight": 25.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Support of local charities",
                        "description": "Charitable and community support activities",
                        "weight": 10.0,
                        "scoring": "weighted_1_5"
                    },
                    {
                        "name": "Employment for disadvantaged groups",
                        "description": "Employment opportunities for disadvantaged groups",
                        "weight": 10.0,
                        "scoring": "weighted_1_5"
                    }
                ],
                weighting_range=(0, 10),  # Part of combined 10%
                scoring_method="weighted_1_5",
                rating_scale="social_community_rating_scale"
            ),
            
            "eeo_fair_employment": BlacktownEvaluationCriterion(
                name="EEO & Fair Employment",
                description="Equal employment opportunity and fair employment practices",
                sub_criteria=[
                    {
                        "name": "Wages paid under award or EA",
                        "description": "Compliance with award or enterprise agreement",
                        "weight": 25.0,
                        "scoring": "compliance_check"
                    },
                    {
                        "name": "Superannuation paid",
                        "description": "Superannuation guarantee compliance",
                        "weight": 20.0,
                        "scoring": "compliance_check"
                    },
                    {
                        "name": "Location of records kept",
                        "description": "Record keeping and accessibility",
                        "weight": 10.0,
                        "scoring": "compliance_check"
                    },
                    {
                        "name": "EEO and anti-discrimination policies",
                        "description": "Equal opportunity and anti-discrimination policies",
                        "weight": 20.0,
                        "scoring": "policy_assessment"
                    },
                    {
                        "name": "Aboriginal and Torres Strait Islander employment",
                        "description": "Indigenous employment policies and implementation",
                        "weight": 15.0,
                        "scoring": "policy_assessment"
                    },
                    {
                        "name": "Apprenticeships and traineeships",
                        "description": "Training and development opportunities",
                        "weight": 10.0,
                        "scoring": "training_assessment"
                    }
                ],
                weighting_range=(0, 10),  # Part of combined 10%
                scoring_method="weighted_1_5",
                rating_scale="eeo_fair_employment_rating_scale"
            )
        }
    
    def _initialize_evaluation_matrices(self):
        """Initialize evaluation matrices from Table 2 and Table 3"""
        
        # Table 2: Quotation Value ($100,000 - $249,999)
        self.quotation_matrix = {
            PurchaseCategory.STANDARD_PRODUCT_GOOD: {
                "criteria": ["price", "relevant_experience", "capability", "work_health_safety"],
                "weighting_ranges": {
                    "price": (40, 60),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": []
            },
            
            PurchaseCategory.CONSTRUCTION_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "quality_management", "management_financial", "work_health_safety"],
                "weighting_ranges": {
                    "price": (40, 60),
                    "relevant_experience": (10, 20),
                    "capability": (5, 20),
                    "quality_management": (2, 10),
                    "management_financial": (0, 10),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": ["sustainability", "eeo_fair_employment"]
            },
            
            PurchaseCategory.CONSULTANCY_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (20, 50),
                    "relevant_experience": (10, 30),
                    "capability": (5, 30),
                    "management_financial": (0, 10),
                    "quality_management": (2, 5),
                    "work_health_safety": (2, 5)
                },
                "combined_10_percent": []
            },
            
            PurchaseCategory.SERVICE_DELIVERY_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (20, 50),
                    "relevant_experience": (10, 40),
                    "capability": (5, 30),
                    "management_financial": (0, 10),
                    "quality_management": (2, 5),
                    "work_health_safety": (2, 10)
                },
                "combined_10_percent": []
            },
            
            PurchaseCategory.MANAGEMENT_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (30, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 10),
                    "quality_management": (2, 10),
                    "work_health_safety": (0, 10)
                },
                "combined_10_percent": []
            },
            
            PurchaseCategory.LEASE_LICENSE: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (30, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 10),
                    "quality_management": (0, 10),
                    "work_health_safety": (0, 10)
                },
                "combined_10_percent": []
            }
        }
        
        # Table 3: Tender Value ($250,000+)
        self.tender_matrix = {
            PurchaseCategory.STANDARD_PRODUCT_GOOD: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "work_health_safety"],
                "weighting_ranges": {
                    "price": (40, 60),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 10),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": ["sustainability", "eeo_fair_employment"],
                "local_preference": True
            },
            
            PurchaseCategory.CONSTRUCTION_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (35, 60),
                    "relevant_experience": (10, 20),
                    "capability": (5, 20),
                    "management_financial": (5, 15),
                    "quality_management": (5, 10),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": ["sustainability", "eeo_fair_employment"],
                "local_preference": True
            },
            
            PurchaseCategory.CONSULTANCY_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "work_health_safety"],
                "weighting_ranges": {
                    "price": (25, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 10),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": ["social_community", "eeo_fair_employment"],
                "local_preference": True
            },
            
            PurchaseCategory.SERVICE_DELIVERY_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (30, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 10),
                    "quality_management": (5, 10),
                    "work_health_safety": (5, 10)
                },
                "combined_10_percent": ["sustainability", "social_community", "eeo_fair_employment"],
                "local_preference": True
            },
            
            PurchaseCategory.MANAGEMENT_CONTRACT: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (30, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 15),
                    "quality_management": (5, 10),
                    "work_health_safety": (0, 10)
                },
                "combined_10_percent": ["sustainability", "social_community", "eeo_fair_employment"],
                "local_preference": True
            },
            
            PurchaseCategory.LEASE_LICENSE: {
                "criteria": ["price", "relevant_experience", "capability", "management_financial", "quality_management", "work_health_safety"],
                "weighting_ranges": {
                    "price": (30, 50),
                    "relevant_experience": (10, 30),
                    "capability": (10, 30),
                    "management_financial": (5, 15),
                    "quality_management": (5, 10),
                    "work_health_safety": (0, 10)
                },
                "combined_10_percent": [],
                "local_preference": True
            }
        }
    
    def _initialize_rating_scales(self):
        """Initialize rating scales from Table 4"""
        
        self.rating_scales = {
            "whs_rating_scale": {
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
            },
            
            "sustainability_rating_scale": {
                5: {
                    "level": "Excellent",
                    "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance + detailed sustainable policies and practices of waste minimisation, recycling and energy conservation"
                },
                4: {
                    "level": "Very Good",
                    "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance + sustainable policies and practices of waste minimisation, recycling and energy conservation"
                },
                3: {
                    "level": "Good",
                    "requirements": "Certified Environmental Management System to ISO14001 + Confirmed Compliance + sustainable policies and practices of some waste minimisation, recycling and energy conservation"
                },
                2: {
                    "level": "Fair",
                    "requirements": "An Environmental Management system + sustainable policies and practices of one waste minimisation, recycling and energy conservation"
                },
                1: {
                    "level": "Poor",
                    "requirements": "An Environmental Management system + no sustainable policies and practices of waste minimisation, recycling and energy conservation"
                },
                0: {
                    "level": "Unacceptable",
                    "requirements": "No information or no Environmental Sustainable System"
                }
            },
            
            "social_community_rating_scale": {
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
            },
            
            "eeo_fair_employment_rating_scale": {
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
    
    def _initialize_local_preference(self):
        """Initialize local preference system"""
        
        self.local_preference_config = {
            LocalPreferenceCategory.BLACKTOWN_LGA: {
                "discount_percentage": 5.0,
                "max_benefit": 50000,
                "description": "Supplier with principal place of business in Blacktown City LGA"
            },
            LocalPreferenceCategory.WESTERN_SYDNEY: {
                "discount_percentage": 2.5,
                "max_benefit": 25000,
                "description": "Supplier with principal place of business in Western Sydney Councils",
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
                ]
            }
        }
    
    def get_evaluation_matrix(self, purchase_category: PurchaseCategory, contract_value: ContractValue) -> Dict[str, Any]:
        """Get evaluation matrix for specific category and value"""
        
        if contract_value == ContractValue.QUOTATION_100K_249K:
            return self.quotation_matrix.get(purchase_category, {})
        else:
            return self.tender_matrix.get(purchase_category, {})
    
    def calculate_local_preference_discount(self, supplier_location: SupplierLocation, tender_price: float) -> float:
        """Calculate local preference discount for supplier"""
        
        if supplier_location.is_blacktown_lga:
            config = self.local_preference_config[LocalPreferenceCategory.BLACKTOWN_LGA]
            discount = min(tender_price * (config["discount_percentage"] / 100), config["max_benefit"])
            return discount
        elif supplier_location.is_western_sydney:
            config = self.local_preference_config[LocalPreferenceCategory.WESTERN_SYDNEY]
            discount = min(tender_price * (config["discount_percentage"] / 100), config["max_benefit"])
            return discount
        
        return 0.0
    
    def apply_combined_10_percent_weighting(self, matrix: Dict[str, Any], price_weighting: float) -> Dict[str, float]:
        """Apply combined 10% weighting rule for sustainability, social, and EEO criteria"""
        
        combined_weighting = price_weighting * 0.10  # 10% of price weighting
        
        criteria_weights = {}
        combined_criteria = matrix.get("combined_10_percent", [])
        
        if combined_criteria:
            # Split equally among combined criteria
            weight_per_criterion = combined_weighting / len(combined_criteria)
            for criterion in combined_criteria:
                criteria_weights[criterion] = weight_per_criterion
        
        return criteria_weights
    
    def evaluate_supplier_criterion(self, criterion_name: str, supplier_data: Dict[str, Any]) -> float:
        """Evaluate supplier against specific criterion using Blacktown standards"""
        
        criterion = self.evaluation_criteria.get(criterion_name)
        if not criterion:
            return 0.0
        
        # Calculate weighted score from sub-criteria
        total_score = 0.0
        total_weight = 0.0
        
        for sub_criterion in criterion.sub_criteria:
            sub_score = self._evaluate_sub_criterion(sub_criterion, supplier_data)
            weight = sub_criterion["weight"]
            
            total_score += sub_score * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_score = total_score / total_weight
            return min(weighted_score, 5.0)  # Cap at 5.0 for 1-5 scale
        
        return 0.0
    
    def _evaluate_sub_criterion(self, sub_criterion: Dict[str, Any], supplier_data: Dict[str, Any]) -> float:
        """Evaluate specific sub-criterion"""
        
        scoring_method = sub_criterion.get("scoring", "weighted_1_5")
        
        if scoring_method == "pass_fail":
            return 5.0 if supplier_data.get(sub_criterion["name"].lower().replace(" ", "_"), False) else 0.0
        elif scoring_method == "weighted_1_5":
            return supplier_data.get(sub_criterion["name"].lower().replace(" ", "_"), 3.0)
        elif scoring_method == "currency_normalized":
            # Normalize against lowest price
            return supplier_data.get("price_score", 3.0)
        else:
            return supplier_data.get(sub_criterion["name"].lower().replace(" ", "_"), 3.0)

# Global instance
_blacktown_evaluation_system = None

def get_blacktown_evaluation_system(data_dir: Path) -> BlacktownEvaluationSystem:
    """Get or create Blacktown evaluation system instance"""
    global _blacktown_evaluation_system
    if _blacktown_evaluation_system is None:
        _blacktown_evaluation_system = BlacktownEvaluationSystem(data_dir)
    return _blacktown_evaluation_system

if __name__ == "__main__":
    # Test the Blacktown evaluation system
    from ..config import settings
    
    system = BlacktownEvaluationSystem(settings.DATA_DIR)
    
    print("✅ Blacktown City Council Evaluation System initialized")
    print(f"📋 Evaluation criteria: {len(system.evaluation_criteria)}")
    print(f"📊 Quotation matrix categories: {len(system.quotation_matrix)}")
    print(f"📊 Tender matrix categories: {len(system.tender_matrix)}")
    print(f"📏 Rating scales: {len(system.rating_scales)}")
    
    # Test evaluation matrix retrieval
    matrix = system.get_evaluation_matrix(
        PurchaseCategory.CONSTRUCTION_CONTRACT,
        ContractValue.TENDER_250K_PLUS
    )
    
    print(f"\n🏗️ Construction Contract ($250k+):")
    print(f"   Criteria: {matrix.get('criteria', [])}")
    print(f"   Combined 10%: {matrix.get('combined_10_percent', [])}")
    print(f"   Local preference: {matrix.get('local_preference', False)}")
    
    print("\n🎉 Blacktown City Council Evaluation System ready!")
