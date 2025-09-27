#!/usr/bin/env python3
"""
Historical Project Matching Service
AI-powered matching of new projects with historical data for improved planning and cost estimation
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

class MatchType(Enum):
    """Types of historical matches"""
    EXACT = "exact"
    SIMILAR = "similar"
    RELATED = "related"
    PARTIAL = "partial"

class ProjectCategory(Enum):
    """Project categories for matching"""
    INFRASTRUCTURE = "infrastructure"
    BUILDING_CONSTRUCTION = "building_construction"
    ROAD_WORKS = "road_works"
    UTILITIES = "utilities"
    LANDSCAPING = "landscaping"
    MAINTENANCE = "maintenance"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    CONSULTING = "consulting"
    TECHNOLOGY = "technology"

@dataclass
class HistoricalProject:
    """Historical project data structure"""
    project_id: str
    title: str
    description: str
    category: ProjectCategory
    start_date: str
    end_date: str
    total_cost: float
    council: str
    project_type: str
    key_specifications: List[str]
    success_factors: List[str]
    challenges: List[str]
    lessons_learned: List[str]
    contractor_performance: Dict[str, Any]
    compliance_issues: List[str]
    metadata: Dict[str, Any]
    created_date: str
    updated_date: str

@dataclass
class ProjectMatch:
    """Project matching result"""
    historical_project: HistoricalProject
    match_type: MatchType
    similarity_score: float
    matching_factors: List[str]
    cost_estimate_range: Tuple[float, float]
    timeline_estimate: Tuple[int, int]  # days
    risk_factors: List[str]
    recommendations: List[str]
    confidence_level: float

class HistoricalMatchingService:
    """AI-powered historical project matching service"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.historical_dir = data_dir / "historical_projects"
        self.historical_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Load historical projects
        self.historical_projects = self._load_historical_projects()
    
    def _load_historical_projects(self) -> List[HistoricalProject]:
        """Load historical projects from storage"""
        projects = []
        
        if self.historical_dir.exists():
            for project_file in self.historical_dir.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Convert string enums back to enum objects
                        if 'category' in data and isinstance(data['category'], str):
                            data['category'] = ProjectCategory(data['category'])
                        
                        projects.append(HistoricalProject(**data))
                except Exception as e:
                    print(f"⚠️ Error loading historical project {project_file}: {e}")
        
        return projects
    
    def _save_historical_project(self, project: HistoricalProject):
        """Save historical project to storage"""
        try:
            # Convert to serializable format
            project_data = {
                "project_id": project.project_id,
                "title": project.title,
                "description": project.description,
                "category": project.category.value,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "total_cost": project.total_cost,
                "council": project.council,
                "project_type": project.project_type,
                "key_specifications": project.key_specifications,
                "success_factors": project.success_factors,
                "challenges": project.challenges,
                "lessons_learned": project.lessons_learned,
                "contractor_performance": project.contractor_performance,
                "compliance_issues": project.compliance_issues,
                "metadata": project.metadata,
                "created_date": project.created_date,
                "updated_date": project.updated_date
            }
            
            project_file = self.historical_dir / f"{project.project_id}.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving historical project: {e}")
    
    def add_historical_project(self, 
                             title: str,
                             description: str,
                             category: ProjectCategory,
                             start_date: str,
                             end_date: str,
                             total_cost: float,
                             council: str,
                             project_type: str,
                             key_specifications: List[str],
                             success_factors: List[str] = None,
                             challenges: List[str] = None,
                             lessons_learned: List[str] = None,
                             contractor_performance: Dict[str, Any] = None,
                             compliance_issues: List[str] = None,
                             metadata: Dict[str, Any] = None) -> str:
        """Add a new historical project"""
        
        project_id = hashlib.md5(f"{title}_{council}_{start_date}".encode()).hexdigest()[:12]
        
        project = HistoricalProject(
            project_id=project_id,
            title=title,
            description=description,
            category=category,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            council=council,
            project_type=project_type,
            key_specifications=key_specifications,
            success_factors=success_factors or [],
            challenges=challenges or [],
            lessons_learned=lessons_learned or [],
            contractor_performance=contractor_performance or {},
            compliance_issues=compliance_issues or [],
            metadata=metadata or {},
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat()
        )
        
        self._save_historical_project(project)
        self.historical_projects.append(project)
        
        return project_id
    
    def find_matching_projects(self, 
                             new_project_description: str,
                             new_project_category: ProjectCategory,
                             new_project_budget: Optional[float] = None,
                             new_project_timeline: Optional[int] = None,
                             council: str = "Blacktown City Council") -> List[ProjectMatch]:
        """Find historical projects that match the new project"""
        
        if not self.historical_projects:
            return []
        
        # Filter projects by category and council
        relevant_projects = [
            p for p in self.historical_projects 
            if p.category == new_project_category and p.council == council
        ]
        
        if not relevant_projects:
            # Fallback to all projects if no category matches
            relevant_projects = [p for p in self.historical_projects if p.council == council]
        
        matches = []
        
        for project in relevant_projects:
            # Calculate similarity using AI
            similarity_score, matching_factors = self._calculate_similarity(
                new_project_description, project
            )
            
            if similarity_score > 0.3:  # Minimum similarity threshold
                # Generate AI-powered analysis
                analysis = self._analyze_project_match(
                    new_project_description, project, new_project_budget, new_project_timeline
                )
                
                match = ProjectMatch(
                    historical_project=project,
                    match_type=self._determine_match_type(similarity_score),
                    similarity_score=similarity_score,
                    matching_factors=matching_factors,
                    cost_estimate_range=analysis['cost_range'],
                    timeline_estimate=analysis['timeline_range'],
                    risk_factors=analysis['risk_factors'],
                    recommendations=analysis['recommendations'],
                    confidence_level=analysis['confidence']
                )
                
                matches.append(match)
        
        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    def _calculate_similarity(self, new_description: str, historical_project: HistoricalProject) -> Tuple[float, List[str]]:
        """Calculate similarity between new project and historical project using AI"""
        
        try:
            prompt = f"""
            Analyze the similarity between a new project and a historical project.
            
            NEW PROJECT DESCRIPTION:
            {new_description}
            
            HISTORICAL PROJECT:
            Title: {historical_project.title}
            Description: {historical_project.description}
            Category: {historical_project.category.value}
            Key Specifications: {', '.join(historical_project.key_specifications)}
            Success Factors: {', '.join(historical_project.success_factors)}
            Challenges: {', '.join(historical_project.challenges)}
            Lessons Learned: {', '.join(historical_project.lessons_learned)}
            
            Provide a similarity score (0.0 to 1.0) and list the matching factors.
            Return in JSON format:
            {{
                "similarity_score": 0.85,
                "matching_factors": ["factor1", "factor2", "factor3"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                # Extract JSON from response
                response_text = response.text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text.strip()
                
                result = json.loads(json_text)
                return result['similarity_score'], result['matching_factors']
                
            except Exception as e:
                print(f"⚠️ Error parsing AI response: {e}")
                # Fallback to basic similarity
                return 0.5, ["Basic similarity match"]
                
        except Exception as e:
            print(f"⚠️ Error calculating similarity: {e}")
            return 0.0, []
    
    def _analyze_project_match(self, 
                             new_description: str, 
                             historical_project: HistoricalProject,
                             new_budget: Optional[float] = None,
                             new_timeline: Optional[int] = None) -> Dict[str, Any]:
        """Analyze project match and provide recommendations"""
        
        try:
            prompt = f"""
            Analyze a historical project match and provide detailed recommendations.
            
            NEW PROJECT: {new_description}
            BUDGET: {new_budget or 'Not specified'}
            TIMELINE: {new_timeline or 'Not specified'} days
            
            HISTORICAL PROJECT:
            Title: {historical_project.title}
            Cost: ${historical_project.total_cost:,.2f}
            Duration: {self._calculate_duration(historical_project)} days
            Success Factors: {', '.join(historical_project.success_factors)}
            Challenges: {', '.join(historical_project.challenges)}
            Lessons Learned: {', '.join(historical_project.lessons_learned)}
            Contractor Performance: {historical_project.contractor_performance}
            Compliance Issues: {', '.join(historical_project.compliance_issues)}
            
            Provide analysis in JSON format:
            {{
                "cost_range": [min_cost, max_cost],
                "timeline_range": [min_days, max_days],
                "risk_factors": ["risk1", "risk2"],
                "recommendations": ["rec1", "rec2"],
                "confidence": 0.85
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                response_text = response.text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text.strip()
                
                return json.loads(json_text)
                
            except Exception as e:
                print(f"⚠️ Error parsing analysis response: {e}")
                # Fallback analysis
                return self._fallback_analysis(historical_project, new_budget, new_timeline)
                
        except Exception as e:
            print(f"⚠️ Error analyzing project match: {e}")
            return self._fallback_analysis(historical_project, new_budget, new_timeline)
    
    def _fallback_analysis(self, project: HistoricalProject, new_budget: Optional[float], new_timeline: Optional[int]) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        
        # Calculate cost range based on historical project
        cost_variance = 0.2  # 20% variance
        min_cost = project.total_cost * (1 - cost_variance)
        max_cost = project.total_cost * (1 + cost_variance)
        
        # Calculate timeline range
        duration = self._calculate_duration(project)
        timeline_variance = 0.3  # 30% variance
        min_timeline = int(duration * (1 - timeline_variance))
        max_timeline = int(duration * (1 + timeline_variance))
        
        return {
            "cost_range": [min_cost, max_cost],
            "timeline_range": [min_timeline, max_timeline],
            "risk_factors": project.challenges[:3] if project.challenges else ["Unknown risks"],
            "recommendations": project.lessons_learned[:3] if project.lessons_learned else ["Follow best practices"],
            "confidence": 0.6
        }
    
    def _calculate_duration(self, project: HistoricalProject) -> int:
        """Calculate project duration in days"""
        try:
            start_date = datetime.strptime(project.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(project.end_date, "%Y-%m-%d")
            return (end_date - start_date).days
        except:
            return 90  # Default duration
    
    def _determine_match_type(self, similarity_score: float) -> MatchType:
        """Determine match type based on similarity score"""
        if similarity_score >= 0.9:
            return MatchType.EXACT
        elif similarity_score >= 0.7:
            return MatchType.SIMILAR
        elif similarity_score >= 0.5:
            return MatchType.RELATED
        else:
            return MatchType.PARTIAL
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical projects"""
        if not self.historical_projects:
            return {
                "total_projects": 0,
                "total_value": 0,
                "average_cost": 0,
                "categories": {},
                "councils": {},
                "average_duration": 0
            }
        
        total_value = sum(p.total_cost for p in self.historical_projects)
        average_cost = total_value / len(self.historical_projects)
        
        categories = {}
        councils = {}
        
        for project in self.historical_projects:
            # Count categories
            cat = project.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            # Count councils
            council = project.council
            councils[council] = councils.get(council, 0) + 1
        
        # Calculate average duration
        durations = [self._calculate_duration(p) for p in self.historical_projects]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_projects": len(self.historical_projects),
            "total_value": total_value,
            "average_cost": average_cost,
            "categories": categories,
            "councils": councils,
            "average_duration": average_duration
        }
    
    def initialize_sample_data(self):
        """Initialize with sample historical projects"""
        sample_projects = [
            {
                "title": "Blacktown Leisure Centre HVAC Upgrade",
                "description": "Complete HVAC system upgrade for Blacktown Leisure Centre including AHU refurbishment, chiller installation, and control system integration",
                "category": ProjectCategory.BUILDING_CONSTRUCTION,
                "start_date": "2023-03-01",
                "end_date": "2023-08-15",
                "total_cost": 450000.0,
                "council": "Blacktown City Council",
                "project_type": "Infrastructure",
                "key_specifications": ["HVAC systems", "Energy efficiency", "Building automation", "Compliance standards"],
                "success_factors": ["Early contractor engagement", "Detailed specifications", "Regular progress monitoring"],
                "challenges": ["Coordination with existing systems", "Weather delays", "Supply chain issues"],
                "lessons_learned": ["Allow extra time for coordination", "Have backup suppliers", "Regular stakeholder communication"],
                "contractor_performance": {"quality": 4.5, "timeliness": 4.0, "communication": 4.2},
                "compliance_issues": ["Minor documentation delays"]
            },
            {
                "title": "Stanhope Gardens Community Centre Construction",
                "description": "New community centre construction including main hall, meeting rooms, kitchen facilities, and outdoor areas",
                "category": ProjectCategory.BUILDING_CONSTRUCTION,
                "start_date": "2022-09-01",
                "end_date": "2023-12-15",
                "total_cost": 2800000.0,
                "council": "Blacktown City Council",
                "project_type": "Community Infrastructure",
                "key_specifications": ["Community facilities", "Accessibility compliance", "Sustainable design", "Landscaping"],
                "success_factors": ["Community consultation", "Clear project scope", "Experienced contractor"],
                "challenges": ["Site access issues", "Material cost increases", "Weather delays"],
                "lessons_learned": ["Include contingency for cost increases", "Plan for weather delays", "Maintain community engagement"],
                "contractor_performance": {"quality": 4.8, "timeliness": 3.5, "communication": 4.5},
                "compliance_issues": ["Building permit delays"]
            },
            {
                "title": "Local Road Resurfacing Program",
                "description": "Comprehensive road resurfacing program covering 15 local streets including drainage improvements and line marking",
                "category": ProjectCategory.ROAD_WORKS,
                "start_date": "2023-01-15",
                "end_date": "2023-06-30",
                "total_cost": 850000.0,
                "council": "Blacktown City Council",
                "project_type": "Road Infrastructure",
                "key_specifications": ["Asphalt resurfacing", "Drainage systems", "Traffic management", "Line marking"],
                "success_factors": ["Phased approach", "Minimal disruption", "Quality materials"],
                "challenges": ["Traffic management", "Weather dependency", "Utility coordination"],
                "lessons_learned": ["Plan traffic management carefully", "Monitor weather forecasts", "Coordinate with utilities"],
                "contractor_performance": {"quality": 4.3, "timeliness": 4.5, "communication": 4.0},
                "compliance_issues": []
            }
        ]
        
        for project_data in sample_projects:
            try:
                self.add_historical_project(**project_data)
            except Exception as e:
                print(f"⚠️ Error adding sample project {project_data['title']}: {e}")
        
        print(f"✅ Initialized {len(sample_projects)} sample historical projects")
