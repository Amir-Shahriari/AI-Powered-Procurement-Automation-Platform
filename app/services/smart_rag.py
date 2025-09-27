"""
Smart RAG System for NSW Government Procurement Platform
======================================================

This module provides an intelligent RAG system that optimizes performance and cost by:
1. Determining when RAG is necessary vs when direct LLM calls are sufficient
2. Using cached results for similar queries
3. Implementing smart context selection
4. Providing fallback mechanisms for reliability

Key Features:
- Intelligent query classification
- Context-aware retrieval
- Cost optimization
- Performance monitoring
- Caching and memoization
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.services.llm import rag_json, _llm
from app.services.vectorstores import get_vs, build_index
from app.services.textio import chunks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryClassification:
    """Classification of a query for RAG optimization."""
    needs_rag: bool
    confidence: float
    reasoning: str
    suggested_context_limit: int
    estimated_cost: str  # "LOW", "MEDIUM", "HIGH"

@dataclass
class RAGResult:
    """Result from smart RAG processing."""
    content: Any
    used_rag: bool
    context_sources: List[str]
    processing_time: float
    cost_category: str
    cache_hit: bool = False

class SmartRAGSystem:
    """
    Intelligent RAG system that optimizes performance and cost.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.performance_metrics = {
            "rag_calls": 0,
            "direct_calls": 0,
            "cache_hits": 0,
            "total_time": 0.0
        }
        
        # Query classification patterns
        self.rag_required_patterns = [
            "compliance", "regulation", "standard", "policy", "guideline",
            "requirement", "mandatory", "legal", "statutory", "act",
            "whs", "adr", "as/nzs", "iso", "privacy", "environmental"
        ]
        
        self.simple_patterns = [
            "title", "name", "date", "time", "location", "contact",
            "phone", "email", "address", "number", "id", "reference"
        ]
        
        self.complex_patterns = [
            "evaluation", "criteria", "weighting", "scoring", "assessment",
            "analysis", "comparison", "ranking", "selection", "decision"
        ]
    
    def classify_query(self, prompt: str, field_queries: List[str]) -> QueryClassification:
        """
        Classify whether a query needs RAG or can use direct LLM processing.
        """
        prompt_lower = prompt.lower()
        queries_lower = [q.lower() for q in field_queries]
        all_text = prompt_lower + " " + " ".join(queries_lower)
        
        # Check for RAG-required patterns
        rag_score = sum(1 for pattern in self.rag_required_patterns if pattern in all_text)
        simple_score = sum(1 for pattern in self.simple_patterns if pattern in all_text)
        complex_score = sum(1 for pattern in self.complex_patterns if pattern in all_text)
        
        # Decision logic
        needs_rag = rag_score > 0 or complex_score > 2
        confidence = min(1.0, (rag_score + complex_score) / max(1, len(field_queries)))
        
        if needs_rag:
            reasoning = f"RAG required: {rag_score} regulatory patterns, {complex_score} complex patterns"
            context_limit = min(12, 4 + rag_score + complex_score)
            cost_category = "HIGH" if rag_score > 2 else "MEDIUM"
        else:
            reasoning = f"Direct LLM sufficient: {simple_score} simple patterns, low complexity"
            context_limit = 4
            cost_category = "LOW"
        
        return QueryClassification(
            needs_rag=needs_rag,
            confidence=confidence,
            reasoning=reasoning,
            suggested_context_limit=context_limit,
            estimated_cost=cost_category
        )
    
    def get_cache_key(self, prompt: str, field_queries: List[str], vs_id: str) -> str:
        """Generate cache key for query."""
        content = f"{prompt}|{sorted(field_queries)}|{vs_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False
        age = time.time() - cache_entry.get("timestamp", 0)
        return age < self.cache_ttl
    
    def smart_rag_json(self, 
                      vs, 
                      prompt: str, 
                      field_queries: List[str],
                      max_ctx: int = 8,
                      min_chars: int = 2500,
                      allow_synthesis: bool = False,
                      force_rag: bool = False) -> RAGResult:
        """
        Smart RAG processing that decides whether to use RAG or direct LLM.
        """
        start_time = time.time()
        vs_id = getattr(vs, 'index_name', 'unknown') if hasattr(vs, 'index_name') else 'unknown'
        
        # Check cache first
        cache_key = self.get_cache_key(prompt, field_queries, vs_id)
        if cache_key in self.cache and self.is_cache_valid(self.cache[cache_key]):
            self.performance_metrics["cache_hits"] += 1
            cached_result = self.cache[cache_key]["result"]
            return RAGResult(
                content=cached_result,
                used_rag=cached_result.get("used_rag", False),
                context_sources=cached_result.get("context_sources", []),
                processing_time=time.time() - start_time,
                cost_category=cached_result.get("cost_category", "LOW"),
                cache_hit=True
            )
        
        # Classify query
        classification = self.classify_query(prompt, field_queries)
        
        # Decide processing method
        if force_rag or classification.needs_rag:
            # Use RAG
            result = self._process_with_rag(
                vs, prompt, field_queries, 
                classification.suggested_context_limit, min_chars, allow_synthesis
            )
            used_rag = True
            self.performance_metrics["rag_calls"] += 1
        else:
            # Use direct LLM
            result = self._process_direct_llm(prompt, field_queries)
            used_rag = False
            self.performance_metrics["direct_calls"] += 1
        
        processing_time = time.time() - start_time
        self.performance_metrics["total_time"] += processing_time
        
        # Prepare result
        rag_result = RAGResult(
            content=result,
            used_rag=used_rag,
            context_sources=[f"vs_{vs_id}"] if used_rag else [],
            processing_time=processing_time,
            cost_category=classification.estimated_cost
        )
        
        # Cache result
        self.cache[cache_key] = {
            "result": {
                "content": result,
                "used_rag": used_rag,
                "context_sources": rag_result.context_sources,
                "cost_category": classification.estimated_cost
            },
            "timestamp": time.time()
        }
        
        logger.info(f"Smart RAG: {'RAG' if used_rag else 'Direct'} processing, "
                   f"time: {processing_time:.2f}s, cost: {classification.estimated_cost}")
        
        return rag_result
    
    def _process_with_rag(self, vs, prompt: str, field_queries: List[str], 
                         max_ctx: int, min_chars: int, allow_synthesis: bool) -> Any:
        """Process query using RAG."""
        try:
            return rag_json(
                vs, prompt, field_queries,
                max_ctx=max_ctx, min_chars=min_chars, allow_synthesis=allow_synthesis
            )
        except Exception as e:
            logger.warning(f"RAG processing failed, falling back to direct LLM: {e}")
            return self._process_direct_llm(prompt, field_queries)
    
    def _process_direct_llm(self, prompt: str, field_queries: List[str]) -> Any:
        """Process query using direct LLM without RAG."""
        try:
            # Create a simplified prompt for direct processing
            simplified_prompt = f"""
            {prompt}
            
            Available information fields: {', '.join(field_queries)}
            
            Return ONLY the JSON object. If information is not available, set to null or [].
            Use NSW/Australian standards and best practices where appropriate.
            """
            
            messages = [
                {"role": "system", "content": simplified_prompt.strip()},
                {"role": "user", "content": "Please provide the requested information in JSON format."}
            ]
            
            response = _llm(json_mode=True).invoke(messages).content
            
            # Try to parse JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback to basic structure
                return self._create_fallback_response(field_queries)
                
        except Exception as e:
            logger.error(f"Direct LLM processing failed: {e}")
            return self._create_fallback_response(field_queries)
    
    def _create_fallback_response(self, field_queries: List[str]) -> Dict[str, Any]:
        """Create a fallback response when all processing fails."""
        fallback = {}
        for query in field_queries:
            if "title" in query.lower():
                fallback["title"] = None
            elif "date" in query.lower() or "time" in query.lower():
                fallback["closing_datetime"] = None
            elif "contact" in query.lower():
                fallback["contact"] = {"name": None, "email": None, "phone": None}
            elif "scope" in query.lower():
                fallback["scope"] = []
            elif "location" in query.lower():
                fallback["location"] = None
            elif "safety" in query.lower() or "standard" in query.lower():
                fallback["safety_standards"] = []
        return fallback
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_calls = self.performance_metrics["rag_calls"] + self.performance_metrics["direct_calls"]
        avg_time = self.performance_metrics["total_time"] / max(1, total_calls)
        
        return {
            **self.performance_metrics,
            "total_calls": total_calls,
            "average_time": avg_time,
            "rag_percentage": (self.performance_metrics["rag_calls"] / max(1, total_calls)) * 100,
            "cache_hit_rate": (self.performance_metrics["cache_hits"] / max(1, total_calls)) * 100
        }
    
    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def optimize_for_category(self, category: str):
        """Optimize RAG settings for specific procurement categories."""
        if category.lower() in ["construction", "infrastructure"]:
            # More RAG needed for complex construction projects
            self.rag_required_patterns.extend(["construction", "building", "infrastructure"])
        elif category.lower() in ["services", "consultancy"]:
            # Moderate RAG for service contracts
            self.rag_required_patterns.extend(["service", "consultancy", "professional"])
        elif category.lower() in ["goods", "equipment"]:
            # Less RAG for simple goods procurement
            self.simple_patterns.extend(["goods", "equipment", "product"])
        
        logger.info(f"Optimized RAG settings for category: {category}")

# Global smart RAG instance
smart_rag = SmartRAGSystem()

def smart_rag_json(vs, prompt: str, field_queries: List[str], 
                  max_ctx: int = 8, min_chars: int = 2500, 
                  allow_synthesis: bool = False, force_rag: bool = False) -> Any:
    """
    Convenience function for smart RAG processing.
    
    Args:
        vs: Vector store
        prompt: LLM prompt
        field_queries: List of field queries
        max_ctx: Maximum context chunks
        min_chars: Minimum character threshold
        allow_synthesis: Allow synthesis when context is insufficient
        force_rag: Force RAG usage even for simple queries
    
    Returns:
        JSON result from processing
    """
    result = smart_rag.smart_rag_json(
        vs, prompt, field_queries, max_ctx, min_chars, allow_synthesis, force_rag
    )
    return result.content

def get_rag_performance_metrics() -> Dict[str, Any]:
    """Get RAG performance metrics."""
    return smart_rag.get_performance_metrics()

def optimize_rag_for_category(category: str):
    """Optimize RAG for specific procurement category."""
    smart_rag.optimize_for_category(category)

def clear_rag_cache():
    """Clear RAG cache."""
    smart_rag.clear_cache()
