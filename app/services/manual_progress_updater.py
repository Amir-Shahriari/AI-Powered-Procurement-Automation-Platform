#!/usr/bin/env python3
"""
Manual Progress Updater for LGP Council Reports
Only adds major steps when explicitly requested by user
"""

from app.services.progress_tracker import add_feature, get_recent_features, load_progress_data
from typing import Dict, Any, Optional

def add_major_step(
    title: str,
    description: str,
    impact: str,
    category: str = "Major Update",
    explanation: str = None
) -> bool:
    """
    Add a major step to the progress tracker
    Only use this for significant updates that should be reported to LGP Council
    """
    if not explanation:
        explanation = f"Major update: {title}"
    
    return add_feature(
        title=title,
        description=description,
        impact=impact,
        status="✅ Complete",
        category=category,
        explanation=explanation
    )

def add_major_feature(
    title: str,
    description: str,
    impact: str,
    category: str = "Feature",
    explanation: str = None
) -> bool:
    """
    Add a major feature to the progress tracker
    Only use this for significant features that should be reported to LGP Council
    """
    if not explanation:
        explanation = f"Major feature implementation: {title}"
    
    return add_feature(
        title=title,
        description=description,
        impact=impact,
        status="✅ Complete",
        category=category,
        explanation=explanation
    )

def add_major_system(
    title: str,
    description: str,
    impact: str,
    category: str = "System",
    explanation: str = None
) -> bool:
    """
    Add a major system to the progress tracker
    Only use this for significant systems that should be reported to LGP Council
    """
    if not explanation:
        explanation = f"Major system implementation: {title}"
    
    return add_feature(
        title=title,
        description=description,
        impact=impact,
        status="✅ Complete",
        category=category,
        explanation=explanation
    )

def get_council_report_features() -> list:
    """
    Get features that should be included in LGP Council reports
    These are the major steps, features, and systems that matter for progress reporting
    """
    data = load_progress_data()
    
    # Filter for major updates only
    major_features = []
    for feature in data["features"]:
        category = feature.get("category", "")
        if category in ["Major Update", "Feature", "System", "Core System", "AI System", "Compliance"]:
            major_features.append(feature)
    
    return major_features

def remove_technical_details():
    """
    Remove technical details and small updates from progress tracker
    Keep only major steps that matter for LGP Council reports
    """
    data = load_progress_data()
    
    # Keep only major categories
    major_categories = ["Major Update", "Feature", "System", "Core System", "AI System", "Compliance", "UI/UX"]
    
    # Filter features
    data["features"] = [
        feature for feature in data["features"] 
        if feature.get("category", "") in major_categories
    ]
    
    # Save updated data
    from app.services.progress_tracker import save_progress_data
    save_progress_data(data)
    
    return len(data["features"])

if __name__ == "__main__":
    # Test the manual progress updater
    print("Manual Progress Updater Test")
    
    # Example: Add a major step
    success = add_major_step(
        "📊 LGP Council Progress Report System",
        "Automated progress reporting system for LGP Council and teams",
        "100% automated reporting, real-time progress visibility",
        "Major Update",
        "System for generating progress reports for LGP Council and team updates"
    )
    
    print(f"Added major step: {success}")
    
    # Show council report features
    features = get_council_report_features()
    print(f"Council report features: {len(features)}")
    for feature in features:
        print(f"  - {feature['title']} ({feature.get('category', 'Unknown')})")
