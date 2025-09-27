#!/usr/bin/env python3
"""
Project Manager for AI-Powered Procurement Platform
Handles historical projects, ongoing projects, and new tender/RFQ creation
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class ProjectStatus(Enum):
    """Project status categories"""
    COMPLETED = "completed"
    ONGOING = "ongoing"
    NEW_TENDER = "new_tender"
    NEW_RFQ = "new_rfq"
    DRAFT = "draft"
    CANCELLED = "cancelled"

class ProjectCategory(Enum):
    """Project categories"""
    CONSTRUCTION = "construction"
    FLEET = "fleet"
    HVAC = "hvac"
    SERVICES = "services"
    IT = "it"
    CONSULTING = "consulting"
    GENERAL = "general"

@dataclass
class Project:
    """Project data structure"""
    project_id: str
    title: str
    description: str
    category: ProjectCategory
    status: ProjectStatus
    contract_value: float
    council: str
    created_date: str
    last_modified: str = ""
    completion_date: Optional[str] = None
    project_manager: str = ""
    tags: List[str] = None
    keywords: List[str] = None
    tender_type: str = "tender"
    evaluation_method: str = "MEAT"
    compliance_level: str = "standard"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.keywords is None:
            self.keywords = []
        if not self.last_modified:
            self.last_modified = datetime.now().isoformat()

class ProjectManager:
    """
    Manages projects including historical, ongoing, and new tender/RFQ creation
    Provides search and categorization functionality
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        
        # Initialize with sample data if no projects exist
        self._initialize_sample_projects()
        
        # Load all projects
        self.projects = self._load_all_projects()
    
    def _initialize_sample_projects(self):
        """Initialize with sample historical and ongoing projects"""
        if not any(self.projects_dir.glob("*.json")):
            sample_projects = [
                {
                    "project_id": "proj_001",
                    "title": "Blacktown City Hall Renovation",
                    "description": "Complete renovation of Blacktown City Hall including HVAC, electrical, and structural upgrades",
                    "category": "construction",
                    "status": "completed",
                    "contract_value": 2500000.0,
                    "council": "Blacktown City Council",
                    "created_date": "2023-01-15T00:00:00",
                    "last_modified": "2023-12-15T00:00:00",
                    "completion_date": "2023-12-15T00:00:00",
                    "project_manager": "John Smith",
                    "tags": ["renovation", "city-hall", "hvac", "electrical"],
                    "keywords": ["renovation", "city hall", "hvac", "electrical", "structural", "upgrade"],
                    "tender_type": "formal_tender",
                    "evaluation_method": "MEAT",
                    "compliance_level": "high"
                },
                {
                    "project_id": "proj_002",
                    "title": "Fleet Vehicle Replacement Program",
                    "description": "Replacement of 15 council vehicles including cars, trucks, and specialized equipment",
                    "category": "fleet",
                    "status": "ongoing",
                    "contract_value": 850000.0,
                    "council": "Blacktown City Council",
                    "created_date": "2024-03-01T00:00:00",
                    "last_modified": "2024-12-01T00:00:00",
                    "project_manager": "Sarah Johnson",
                    "tags": ["fleet", "vehicles", "replacement", "equipment"],
                    "keywords": ["fleet", "vehicles", "replacement", "cars", "trucks", "equipment", "council"],
                    "tender_type": "tender",
                    "evaluation_method": "MEAT",
                    "compliance_level": "standard"
                },
                {
                    "project_id": "proj_003",
                    "title": "IT Infrastructure Upgrade",
                    "description": "Upgrade of council IT infrastructure including servers, network equipment, and security systems",
                    "category": "it",
                    "status": "ongoing",
                    "contract_value": 1200000.0,
                    "council": "Blacktown City Council",
                    "created_date": "2024-06-01T00:00:00",
                    "last_modified": "2024-12-01T00:00:00",
                    "project_manager": "Mike Chen",
                    "tags": ["it", "infrastructure", "servers", "network", "security"],
                    "keywords": ["it", "infrastructure", "servers", "network", "security", "upgrade", "technology"],
                    "tender_type": "formal_tender",
                    "evaluation_method": "MEAT",
                    "compliance_level": "high"
                },
                {
                    "project_id": "proj_004",
                    "title": "Parks and Recreation Maintenance",
                    "description": "Ongoing maintenance services for all council parks and recreation facilities",
                    "category": "services",
                    "status": "completed",
                    "contract_value": 450000.0,
                    "council": "Blacktown City Council",
                    "created_date": "2023-09-01T00:00:00",
                    "last_modified": "2024-08-31T00:00:00",
                    "completion_date": "2024-08-31T00:00:00",
                    "project_manager": "Lisa Brown",
                    "tags": ["parks", "recreation", "maintenance", "services"],
                    "keywords": ["parks", "recreation", "maintenance", "services", "facilities", "ongoing"],
                    "tender_type": "tender",
                    "evaluation_method": "MEAT",
                    "compliance_level": "standard"
                },
                {
                    "project_id": "proj_005",
                    "title": "HVAC System Installation - Community Center",
                    "description": "Installation of new HVAC systems for the Blacktown Community Center",
                    "category": "hvac",
                    "status": "completed",
                    "contract_value": 320000.0,
                    "council": "Blacktown City Council",
                    "created_date": "2023-11-01T00:00:00",
                    "last_modified": "2024-02-28T00:00:00",
                    "completion_date": "2024-02-28T00:00:00",
                    "project_manager": "David Wilson",
                    "tags": ["hvac", "community-center", "installation", "climate-control"],
                    "keywords": ["hvac", "community center", "installation", "climate control", "heating", "cooling"],
                    "tender_type": "tender",
                    "evaluation_method": "MEAT",
                    "compliance_level": "standard"
                }
            ]
            
            for project_data in sample_projects:
                project_file = self.projects_dir / f"{project_data['project_id']}.json"
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2, ensure_ascii=False)
    
    def _load_all_projects(self) -> List[Project]:
        """Load all projects from the projects directory"""
        projects = []
        
        for project_file in self.projects_dir.glob("*.json"):
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                # Convert string enums back to enum objects
                project_data['category'] = ProjectCategory(project_data['category'])
                project_data['status'] = ProjectStatus(project_data['status'])
                
                project = Project(**project_data)
                projects.append(project)
                
            except Exception as e:
                print(f"⚠️ Error loading project {project_file}: {e}")
        
        return projects
    
    def get_projects_by_category(self, category: str) -> List[Project]:
        """Get projects filtered by category"""
        if category == "all":
            return self.projects
        
        return [p for p in self.projects if p.category.value == category]
    
    def get_projects_by_status(self, status: str) -> List[Project]:
        """Get projects filtered by status"""
        if status == "all":
            return self.projects
        
        return [p for p in self.projects if p.status.value == status]
    
    def search_projects(self, query: str, category: str = "all", status: str = "all") -> List[Project]:
        """Search projects by keywords, title, or description"""
        query_lower = query.lower()
        
        filtered_projects = self.projects
        
        # Filter by category
        if category != "all":
            filtered_projects = [p for p in filtered_projects if p.category.value == category]
        
        # Filter by status
        if status != "all":
            filtered_projects = [p for p in filtered_projects if p.status.value == status]
        
        # Search in title, description, tags, and keywords
        matching_projects = []
        for project in filtered_projects:
            searchable_text = f"{project.title} {project.description} {' '.join(project.tags)} {' '.join(project.keywords)}".lower()
            
            if query_lower in searchable_text:
                matching_projects.append(project)
        
        return matching_projects
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID"""
        for project in self.projects:
            if project.project_id == project_id:
                return project
        return None
    
    def create_new_project(self, 
                          title: str, 
                          description: str, 
                          category: ProjectCategory, 
                          contract_value: float,
                          council: str,
                          tender_type: str = "tender",
                          project_manager: str = "") -> Project:
        """Create a new project"""
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        # Generate keywords from title and description
        keywords = self._generate_keywords(title, description)
        
        project = Project(
            project_id=project_id,
            title=title,
            description=description,
            category=category,
            status=ProjectStatus.NEW_TENDER if tender_type == "tender" else ProjectStatus.NEW_RFQ,
            contract_value=contract_value,
            council=council,
            created_date=datetime.now().isoformat(),
            project_manager=project_manager,
            keywords=keywords,
            tender_type=tender_type
        )
        
        # Save project
        self._save_project(project)
        self.projects.append(project)
        
        return project
    
    def _generate_keywords(self, title: str, description: str) -> List[str]:
        """Generate keywords from title and description"""
        text = f"{title} {description}".lower()
        
        # Simple keyword extraction (can be enhanced with NLP)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = text.split()
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        return list(set(keywords))[:10]  # Limit to 10 keywords
    
    def _save_project(self, project: Project):
        """Save project to file"""
        project_file = self.projects_dir / f"{project.project_id}.json"
        
        # Convert to dict for JSON serialization
        project_data = asdict(project)
        project_data['category'] = project.category.value
        project_data['status'] = project.status.value
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
    
    def update_project_status(self, project_id: str, new_status: ProjectStatus):
        """Update project status"""
        project = self.get_project_by_id(project_id)
        if project:
            project.status = new_status
            project.last_modified = datetime.now().isoformat()
            self._save_project(project)
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        total_projects = len(self.projects)
        completed = len([p for p in self.projects if p.status == ProjectStatus.COMPLETED])
        ongoing = len([p for p in self.projects if p.status == ProjectStatus.ONGOING])
        new_tenders = len([p for p in self.projects if p.status == ProjectStatus.NEW_TENDER])
        new_rfqs = len([p for p in self.projects if p.status == ProjectStatus.NEW_RFQ])
        
        total_value = sum(p.contract_value for p in self.projects)
        
        return {
            "total_projects": total_projects,
            "completed": completed,
            "ongoing": ongoing,
            "new_tenders": new_tenders,
            "new_rfqs": new_rfqs,
            "total_value": total_value,
            "average_value": total_value / total_projects if total_projects > 0 else 0
        }
    
    def get_recent_projects(self, limit: int = 5) -> List[Project]:
        """Get most recently modified projects"""
        sorted_projects = sorted(self.projects, key=lambda p: p.last_modified, reverse=True)
        return sorted_projects[:limit]
    
    def get_projects_by_council(self, council: str) -> List[Project]:
        """Get projects for a specific council"""
        return [p for p in self.projects if p.council.lower() == council.lower()]
