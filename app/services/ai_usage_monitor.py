"""
AI Usage Monitor and Time Estimation System
Provides transparency about which AI provider is being used and expected performance
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """AI Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA_LOCAL = "ollama_local"
    OLLAMA_CLOUD = "ollama_cloud"
    HUGGINGFACE = "huggingface"
    CURSOR_API = "cursor_api"

@dataclass
class AIUsageInfo:
    """Information about AI usage"""
    provider: AIProvider
    model: str
    is_local: bool
    estimated_time_seconds: float
    cost_per_request: float
    reliability_score: float
    description: str

class AIUsageMonitor:
    """Monitor and provide transparency about AI usage"""
    
    def __init__(self):
        self.usage_history = []
        self.provider_info = self._initialize_provider_info()
        self.current_provider = None
    
    def _initialize_provider_info(self) -> Dict[AIProvider, AIUsageInfo]:
        """Initialize information about different AI providers"""
        return {
            AIProvider.OPENAI: AIUsageInfo(
                provider=AIProvider.OPENAI,
                model="gpt-4",
                is_local=False,
                estimated_time_seconds=2.0,
                cost_per_request=0.02,
                reliability_score=0.95,
                description="Cloud-based GPT-4 - Fast response, high quality"
            ),
            AIProvider.ANTHROPIC: AIUsageInfo(
                provider=AIProvider.ANTHROPIC,
                model="claude-3",
                is_local=False,
                estimated_time_seconds=2.5,
                cost_per_request=0.025,
                reliability_score=0.92,
                description="Cloud-based Claude-3 - Excellent reasoning"
            ),
            AIProvider.GOOGLE: AIUsageInfo(
                provider=AIProvider.GOOGLE,
                model="gemini-pro",
                is_local=False,
                estimated_time_seconds=1.8,
                cost_per_request=0.015,
                reliability_score=0.90,
                description="Cloud-based Gemini - Fast and efficient"
            ),
            AIProvider.OLLAMA_LOCAL: AIUsageInfo(
                provider=AIProvider.OLLAMA_LOCAL,
                model="phi3:3.8b",
                is_local=True,
                estimated_time_seconds=8.0,
                cost_per_request=0.0,
                reliability_score=0.85,
                description="Local AI - No cost, complete privacy, slower response"
            ),
            AIProvider.OLLAMA_CLOUD: AIUsageInfo(
                provider=AIProvider.OLLAMA_CLOUD,
                model="llama3:8b",
                is_local=False,
                estimated_time_seconds=4.0,
                cost_per_request=0.01,
                reliability_score=0.88,
                description="Cloud Ollama - Balanced speed and cost"
            ),
            AIProvider.HUGGINGFACE: AIUsageInfo(
                provider=AIProvider.HUGGINGFACE,
                model="microsoft/DialoGPT",
                is_local=False,
                estimated_time_seconds=3.0,
                cost_per_request=0.005,
                reliability_score=0.80,
                description="Hugging Face - Open source models"
            ),
            AIProvider.CURSOR_API: AIUsageInfo(
                provider=AIProvider.CURSOR_API,
                model="cursor-code",
                is_local=False,
                estimated_time_seconds=1.5,
                cost_per_request=0.0,
                reliability_score=0.75,
                description="Cursor API - Code-specific, limited availability"
            )
        }
    
    def get_provider_info(self, provider: AIProvider) -> Optional[AIUsageInfo]:
        """Get information about a specific provider"""
        return self.provider_info.get(provider)
    
    def estimate_time_for_task(self, task_type: str, provider: AIProvider) -> float:
        """Estimate time for a specific task with a provider"""
        base_info = self.get_provider_info(provider)
        if not base_info:
            return 5.0  # Default fallback
        
        # Adjust time based on task complexity
        task_multipliers = {
            "simple_query": 1.0,
            "document_analysis": 1.5,
            "tender_generation": 2.0,
            "compliance_check": 1.8,
            "supplier_evaluation": 2.5,
            "historical_matching": 3.0,
            "complex_analysis": 4.0
        }
        
        multiplier = task_multipliers.get(task_type, 2.0)
        return base_info.estimated_time_seconds * multiplier
    
    def get_user_friendly_time_estimate(self, task_type: str, provider: AIProvider) -> str:
        """Get user-friendly time estimate"""
        estimated_seconds = self.estimate_time_for_task(task_type, provider)
        
        if estimated_seconds < 5:
            return f"~{estimated_seconds:.0f} seconds"
        elif estimated_seconds < 60:
            return f"~{estimated_seconds:.0f} seconds"
        else:
            minutes = estimated_seconds / 60
            return f"~{minutes:.1f} minutes"
    
    def get_provider_benefits(self, provider: AIProvider) -> List[str]:
        """Get benefits of using a specific provider"""
        info = self.get_provider_info(provider)
        if not info:
            return ["Unknown provider"]
        
        benefits = []
        
        if info.is_local:
            benefits.extend([
                "🔒 Complete data privacy",
                "💰 Zero ongoing costs",
                "🏠 Runs on your hardware",
                "🛡️ No external data transmission"
            ])
        else:
            benefits.extend([
                "⚡ Fast response times",
                "🎯 High-quality results",
                "🌐 Reliable cloud infrastructure",
                "🔄 Automatic scaling"
            ])
        
        if info.cost_per_request == 0:
            benefits.append("💵 No per-request charges")
        else:
            benefits.append(f"💵 Low cost: ~${info.cost_per_request:.3f}/request")
        
        return benefits
    
    def get_provider_limitations(self, provider: AIProvider) -> List[str]:
        """Get limitations of using a specific provider"""
        info = self.get_provider_info(provider)
        if not info:
            return ["Unknown provider"]
        
        limitations = []
        
        if info.is_local:
            limitations.extend([
                "⏱️ Slower response times",
                "💻 Requires local hardware",
                "🔧 Setup complexity",
                "📊 Limited model variety"
            ])
        else:
            limitations.extend([
                "🌐 Requires internet connection",
                "💰 Per-request costs",
                "🔒 Data sent to external servers",
                "⚡ Dependent on API availability"
            ])
        
        if info.reliability_score < 0.9:
            limitations.append("⚠️ Lower reliability score")
        
        return limitations
    
    def start_ai_operation(self, provider: AIProvider, task_type: str) -> Dict[str, Any]:
        """Start tracking an AI operation"""
        start_time = time.time()
        self.current_provider = provider
        
        info = self.get_provider_info(provider)
        estimated_time = self.estimate_time_for_task(task_type, provider)
        
        operation_info = {
            "provider": provider,
            "task_type": task_type,
            "start_time": start_time,
            "estimated_time": estimated_time,
            "is_local": info.is_local if info else False,
            "model": info.model if info else "unknown",
            "cost_per_request": info.cost_per_request if info else 0.0
        }
        
        return operation_info
    
    def end_ai_operation(self, operation_info: Dict[str, Any]) -> Dict[str, Any]:
        """End tracking an AI operation and return results"""
        end_time = time.time()
        actual_time = end_time - operation_info["start_time"]
        
        result = {
            **operation_info,
            "end_time": end_time,
            "actual_time": actual_time,
            "time_accuracy": actual_time / operation_info["estimated_time"] if operation_info["estimated_time"] > 0 else 1.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in history
        self.usage_history.append(result)
        
        return result
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        if not self.usage_history:
            return {"message": "No usage data available yet"}
        
        total_operations = len(self.usage_history)
        local_operations = sum(1 for op in self.usage_history if op["is_local"])
        cloud_operations = total_operations - local_operations
        
        avg_time_accuracy = sum(op["time_accuracy"] for op in self.usage_history) / total_operations
        total_cost = sum(op["cost_per_request"] for op in self.usage_history)
        
        return {
            "total_operations": total_operations,
            "local_operations": local_operations,
            "cloud_operations": cloud_operations,
            "local_percentage": (local_operations / total_operations) * 100,
            "avg_time_accuracy": avg_time_accuracy,
            "total_cost": total_cost,
            "cost_savings_from_local": sum(op["cost_per_request"] for op in self.usage_history if op["is_local"])
        }
    
    def get_recommended_provider(self, task_type: str, user_preferences: Dict[str, Any] = None) -> AIProvider:
        """Get recommended provider based on task and user preferences"""
        if user_preferences is None:
            user_preferences = {}
        
        # Default preferences
        prefer_local = user_preferences.get("prefer_local", False)
        prefer_speed = user_preferences.get("prefer_speed", True)
        prefer_cost_efficiency = user_preferences.get("prefer_cost_efficiency", True)
        
        # Score each provider
        provider_scores = {}
        
        for provider, info in self.provider_info.items():
            score = 0
            
            # Time scoring (lower is better)
            time_score = 10 - (info.estimated_time_seconds / 10)
            score += time_score if prefer_speed else 0
            
            # Cost scoring (lower is better)
            cost_score = 10 - (info.cost_per_request * 100)
            score += cost_score if prefer_cost_efficiency else 0
            
            # Local preference bonus
            if info.is_local and prefer_local:
                score += 5
            
            # Reliability scoring
            score += info.reliability_score * 10
            
            provider_scores[provider] = score
        
        # Return provider with highest score
        return max(provider_scores, key=provider_scores.get)

# Global instance
_ai_usage_monitor = None

def get_ai_usage_monitor() -> AIUsageMonitor:
    """Get or create the global AI usage monitor"""
    global _ai_usage_monitor
    if _ai_usage_monitor is None:
        _ai_usage_monitor = AIUsageMonitor()
    return _ai_usage_monitor

def get_ai_provider_info(provider: str) -> Optional[AIUsageInfo]:
    """Get AI provider information"""
    monitor = get_ai_usage_monitor()
    try:
        provider_enum = AIProvider(provider)
        return monitor.get_provider_info(provider_enum)
    except ValueError:
        return None

def estimate_ai_operation_time(task_type: str, provider: str) -> float:
    """Estimate time for an AI operation"""
    monitor = get_ai_usage_monitor()
    try:
        provider_enum = AIProvider(provider)
        return monitor.estimate_time_for_task(task_type, provider_enum)
    except ValueError:
        return 5.0  # Default fallback

def get_user_friendly_time_estimate(task_type: str, provider: str) -> str:
    """Get user-friendly time estimate for an AI operation"""
    monitor = get_ai_usage_monitor()
    try:
        provider_enum = AIProvider(provider)
        return monitor.get_user_friendly_time_estimate(task_type, provider_enum)
    except ValueError:
        return "~5 seconds"
