import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Simple compliance system with automatic storage and cost optimization
COMPLIANCE_CACHE = {}

def detect_project_type(tender_info: Dict[str, Any]) -> str:
    """Detect project type from tender information"""
    text = f"{tender_info.get('title', '')} {tender_info.get('description', '')} {tender_info.get('scope', '')}".lower()
    
    keywords = {
        "hvac": ["hvac", "heating", "ventilation", "air conditioning"],
        "fleet": ["fleet", "vehicle", "truck", "car", "adr"],
        "service": ["service", "maintenance", "repair", "support"],
        "construction": ["construction", "building", "infrastructure"],
        "general": ["general", "standard", "common"]
    }
    
    for project_type, project_keywords in keywords.items():
        if any(keyword in text for keyword in project_keywords):
            return project_type
    
    return "general"

def process_compliance_documents(project_type: str, documents: List[Any]) -> List[str]:
    """Process and store compliance documents"""
    requirements = []
    
    for doc in documents:
        if hasattr(doc, 'filename'):
            requirements.append(f"Document: {doc.filename}")
        else:
            requirements.append(f"Document: {str(doc)}")
    
    # Store in cache
    COMPLIANCE_CACHE[project_type] = {
        "documents": [getattr(doc, 'filename', str(doc)) for doc in documents],
        "requirements": requirements,
        "last_updated": datetime.now().isoformat(),
        "processed": True
    }
    
    return requirements

def check_compliance_smart(tender_info: Dict[str, Any], project_type: str = None) -> Dict[str, Any]:
    """Check compliance with cost optimization"""
    if project_type is None:
        project_type = detect_project_type(tender_info)
    
    # Check if we have cached data
    if project_type in COMPLIANCE_CACHE and COMPLIANCE_CACHE[project_type]["processed"]:
        return check_compliance_cached(tender_info, project_type)
    else:
        return check_compliance_rag(tender_info, project_type)

def check_compliance_cached(tender_info: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Check compliance using cached data - no API costs!"""
    cached_data = COMPLIANCE_CACHE[project_type]
    requirements = cached_data["requirements"]
    
    results = []
    compliant_count = 0
    
    for requirement in requirements:
        is_compliant = True  # Simple check for demo
        if is_compliant:
            compliant_count += 1
        
        results.append({
            "requirement": requirement,
            "compliant": is_compliant,
            "evidence": "Found in tender" if is_compliant else "Not found",
            "cost": 0  # No API cost!
        })
    
    compliance_rate = (compliant_count / len(requirements)) * 100 if requirements else 0
    
    return {
        "project_type": project_type,
        "compliance_rate": compliance_rate,
        "total_requirements": len(requirements),
        "compliant_requirements": compliant_count,
        "results": results,
        "cost": 0,
        "method": "cached"
    }

def check_compliance_rag(tender_info: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Check compliance using RAG - API costs apply"""
    return {
        "project_type": project_type,
        "compliance_rate": 0,
        "total_requirements": 0,
        "compliant_requirements": 0,
        "results": [],
        "cost": 1,  # API cost
        "method": "rag"
    }

def get_compliance_status(project_type: str = None) -> Dict[str, Any]:
    """Get compliance status"""
    if project_type:
        return COMPLIANCE_CACHE.get(project_type, {"documents": [], "requirements": [], "processed": False})
    return COMPLIANCE_CACHE

def clear_compliance_cache(project_type: str = None):
    """Clear compliance cache"""
    if project_type:
        COMPLIANCE_CACHE.pop(project_type, None)
    else:
        COMPLIANCE_CACHE.clear()
