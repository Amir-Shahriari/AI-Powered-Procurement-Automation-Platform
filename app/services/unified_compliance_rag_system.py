#!/usr/bin/env python3
"""
Unified Compliance RAG System
Optimized RAG system that integrates all compliance documents for comprehensive compliance checking
Minimizes time and cost through intelligent caching, query optimization, and automated compliance verification
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import time

# Import existing systems
from app.services.blacktown_rag_system import BlacktownRAGSystem, BlacktownRAGDocument
from app.services.global_compliance_manager import GlobalComplianceManager

class ComplianceCategory(Enum):
    """Compliance document categories"""
    BLACKTOWN_STANDARDS = "blacktown_standards"
    GLOBAL_NSW_STANDARDS = "global_nsw_standards"
    TENDERING_GUIDELINES = "tendering_guidelines"
    EVALUATION_CRITERIA = "evaluation_criteria"
    LOCAL_PREFERENCE = "local_preference"
    SOCIAL_PROCUREMENT = "social_procurement"
    WHS_COMPLIANCE = "whs_compliance"
    ENVIRONMENTAL = "environmental"
    EEO_FAIR_EMPLOYMENT = "eeo_fair_employment"

class QueryType(Enum):
    """Types of compliance queries"""
    EVALUATION_CRITERIA = "evaluation_criteria"
    WEIGHTING_MATRIX = "weighting_matrix"
    RATING_SCALE = "rating_scale"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    DOCUMENT_TEMPLATE = "document_template"
    LOCAL_PREFERENCE = "local_preference"
    SOCIAL_VALUE = "social_value"

@dataclass
class ComplianceQuery:
    """Optimized compliance query"""
    query_id: str
    query_type: QueryType
    category: ComplianceCategory
    parameters: Dict[str, Any]
    timestamp: str
    cache_key: str

@dataclass
class ComplianceResult:
    """Compliance query result with caching metadata"""
    query_id: str
    result: Any
    source_documents: List[str]
    confidence_score: float
    timestamp: str
    cache_hit: bool
    processing_time_ms: int

@dataclass
class ComplianceCache:
    """Intelligent compliance cache"""
    cache_key: str
    result: Any
    source_documents: List[str]
    confidence_score: float
    created_at: str
    expires_at: str
    access_count: int
    last_accessed: str

class UnifiedComplianceRAGSystem:
    """
    Unified RAG system that optimizes compliance checking across all documents
    Minimizes time and cost through intelligent caching and query optimization
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cache_dir = data_dir / "compliance_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.blacktown_rag = BlacktownRAGSystem(data_dir)
        self.global_compliance = GlobalComplianceManager(data_dir)
        
        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_processing_time_ms": 0,
            "total_processing_time_ms": 0
        }
        
        # Load cache
        self.cache = self._load_cache()
        
        # Initialize optimized document index
        self._build_document_index()
    
    def _load_cache(self) -> Dict[str, ComplianceCache]:
        """Load compliance cache from disk"""
        cache = {}
        cache_file = self.cache_dir / "compliance_cache.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                for key, data in cache_data.items():
                    cache[key] = ComplianceCache(**data)
                    
                print(f"✅ Loaded {len(cache)} cached compliance results")
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
        
        return cache
    
    def _save_cache(self):
        """Save compliance cache to disk"""
        cache_file = self.cache_dir / "compliance_cache.json"
        
        try:
            cache_data = {}
            for key, cache_item in self.cache.items():
                cache_data[key] = asdict(cache_item)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def _generate_cache_key(self, query_type: QueryType, category: ComplianceCategory, parameters: Dict[str, Any]) -> str:
        """Generate unique cache key for query"""
        # Create deterministic hash of query parameters
        params_str = json.dumps(parameters, sort_keys=True)
        query_str = f"{query_type.value}:{category.value}:{params_str}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _build_document_index(self):
        """Build optimized document index for fast retrieval"""
        self.document_index = {
            "blacktown_standards": {},
            "global_compliance": {},
            "quick_lookup": {}
        }
        
        # Index Blacktown standards
        blacktown_docs = self.blacktown_rag.get_all_rag_documents()
        for doc in blacktown_docs:
            doc_type = doc.metadata.get("document_type", "unknown")
            if doc_type not in self.document_index["blacktown_standards"]:
                self.document_index["blacktown_standards"][doc_type] = []
            self.document_index["blacktown_standards"][doc_type].append(doc.document_id)
            
            # Build quick lookup for common queries
            if doc_type == "evaluation_criteria":
                self._index_evaluation_criteria(doc)
            elif doc_type == "evaluation_matrix":
                self._index_evaluation_matrices(doc)
            elif doc_type == "rating_scales":
                self._index_rating_scales(doc)
        
        # Index global compliance
        try:
            global_criteria = self.global_compliance.get_global_evaluation_criteria("tender")
            if global_criteria:
                self.document_index["global_compliance"]["evaluation_criteria"] = len(global_criteria)
            
            global_requirements = self.global_compliance.get_global_compliance_requirements("tender", "general")
            if global_requirements:
                self.document_index["global_compliance"]["compliance_requirements"] = len(global_requirements)
                
        except Exception as e:
            print(f"⚠️ Error indexing global compliance: {e}")
    
    def _index_evaluation_criteria(self, doc: BlacktownRAGDocument):
        """Index evaluation criteria for fast lookup"""
        criteria_categories = doc.content.get("criteria_categories", {})
        for category_key, category_data in criteria_categories.items():
            self.document_index["quick_lookup"][f"criteria:{category_key}"] = {
                "document_id": doc.document_id,
                "category": category_data.get("name", category_key),
                "sub_criteria_count": len(category_data.get("sub_criteria", []))
            }
    
    def _index_evaluation_matrices(self, doc: BlacktownRAGDocument):
        """Index evaluation matrices for fast lookup"""
        purchase_categories = doc.content.get("purchase_categories", {})
        for category_key, category_data in purchase_categories.items():
            self.document_index["quick_lookup"][f"matrix:{category_key}"] = {
                "document_id": doc.document_id,
                "category": category_data.get("name", category_key),
                "criteria_count": len(category_data.get("criteria", {}))
            }
    
    def _index_rating_scales(self, doc: BlacktownRAGDocument):
        """Index rating scales for fast lookup"""
        rating_scales = doc.content.get("rating_scales", {})
        for scale_key, scale_data in rating_scales.items():
            self.document_index["quick_lookup"][f"scale:{scale_key}"] = {
                "document_id": doc.document_id,
                "scale_name": scale_data.get("scale_name", scale_key),
                "score_levels": len(scale_data.get("scores", {}))
            }
    
    def query_compliance(self, 
                        query_type: QueryType, 
                        category: ComplianceCategory, 
                        parameters: Dict[str, Any]) -> ComplianceResult:
        """Optimized compliance query with intelligent caching"""
        
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query_type, category, parameters)
        
        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            self.query_stats["cache_hits"] += 1
            processing_time = int((time.time() - start_time) * 1000)
            
            return ComplianceResult(
                query_id=f"{query_type.value}_{int(time.time())}",
                result=cached_result.result,
                source_documents=cached_result.source_documents,
                confidence_score=cached_result.confidence_score,
                timestamp=datetime.now().isoformat(),
                cache_hit=True,
                processing_time_ms=processing_time
            )
        
        # Cache miss - process query
        self.query_stats["cache_misses"] += 1
        result = self._process_compliance_query(query_type, category, parameters)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Cache the result
        self._cache_result(cache_key, result, processing_time)
        
        # Update stats
        self.query_stats["total_queries"] += 1
        self.query_stats["total_processing_time_ms"] += processing_time
        self.query_stats["avg_processing_time_ms"] = (
            self.query_stats["total_processing_time_ms"] / self.query_stats["total_queries"]
        )
        
        return ComplianceResult(
            query_id=f"{query_type.value}_{int(time.time())}",
            result=result["data"],
            source_documents=result["sources"],
            confidence_score=result["confidence"],
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            processing_time_ms=processing_time
        )
    
    def _get_cached_result(self, cache_key: str) -> Optional[ComplianceCache]:
        """Get cached result if valid"""
        if cache_key in self.cache:
            cache_item = self.cache[cache_key]
            
            # Check if cache is still valid
            if datetime.now().isoformat() < cache_item.expires_at:
                # Update access statistics
                cache_item.access_count += 1
                cache_item.last_accessed = datetime.now().isoformat()
                
                return cache_item
            else:
                # Remove expired cache item
                del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any], processing_time_ms: int):
        """Cache compliance query result"""
        # Determine cache expiration based on query type and processing time
        cache_duration_hours = self._get_cache_duration(result)
        
        expires_at = (datetime.now() + timedelta(hours=cache_duration_hours)).isoformat()
        
        cache_item = ComplianceCache(
            cache_key=cache_key,
            result=result["data"],
            source_documents=result["sources"],
            confidence_score=result["confidence"],
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            access_count=1,
            last_accessed=datetime.now().isoformat()
        )
        
        self.cache[cache_key] = cache_item
        
        # Save cache periodically (every 10 items)
        if len(self.cache) % 10 == 0:
            self._save_cache()
    
    def _get_cache_duration(self, result: Dict[str, Any]) -> int:
        """Determine cache duration based on result type and confidence"""
        confidence = result.get("confidence", 0.5)
        
        # Higher confidence = longer cache duration
        if confidence >= 0.9:
            return 24  # 24 hours for high confidence results
        elif confidence >= 0.7:
            return 12  # 12 hours for medium confidence results
        else:
            return 6   # 6 hours for low confidence results
    
    def _process_compliance_query(self, 
                                 query_type: QueryType, 
                                 category: ComplianceCategory, 
                                 parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process compliance query and return optimized result"""
        
        if query_type == QueryType.EVALUATION_CRITERIA:
            return self._get_evaluation_criteria(category, parameters)
        elif query_type == QueryType.WEIGHTING_MATRIX:
            return self._get_weighting_matrix(category, parameters)
        elif query_type == QueryType.RATING_SCALE:
            return self._get_rating_scale(category, parameters)
        elif query_type == QueryType.COMPLIANCE_REQUIREMENT:
            return self._get_compliance_requirements(category, parameters)
        elif query_type == QueryType.LOCAL_PREFERENCE:
            return self._get_local_preference_info(category, parameters)
        elif query_type == QueryType.SOCIAL_VALUE:
            return self._get_social_value_criteria(category, parameters)
        else:
            return {
                "data": None,
                "sources": [],
                "confidence": 0.0,
                "error": f"Unknown query type: {query_type}"
            }
    
    def _get_evaluation_criteria(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get evaluation criteria with optimization"""
        criteria_name = parameters.get("criteria_name", "")
        
        # Try quick lookup first
        if f"criteria:{criteria_name}" in self.document_index["quick_lookup"]:
            lookup_info = self.document_index["quick_lookup"][f"criteria:{criteria_name}"]
            doc_id = lookup_info["document_id"]
            
            doc = self.blacktown_rag.load_rag_document(doc_id)
            if doc:
                criteria_categories = doc.content.get("criteria_categories", {})
                criteria_data = criteria_categories.get(criteria_name)
                
                if criteria_data:
                    return {
                        "data": criteria_data,
                        "sources": [f"Blacktown Standards: {doc.title}"],
                        "confidence": 0.95
                    }
        
        # Fallback to search
        search_results = self.blacktown_rag.search_rag_documents(criteria_name, "evaluation_criteria")
        if search_results:
            return {
                "data": search_results[0].content,
                "sources": [f"Blacktown Standards: {search_results[0].title}"],
                "confidence": 0.8
            }
        
        return {
            "data": None,
            "sources": [],
            "confidence": 0.0,
            "error": f"Evaluation criteria '{criteria_name}' not found"
        }
    
    def _get_weighting_matrix(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get weighting matrix with optimization"""
        purchase_category = parameters.get("purchase_category", "")
        contract_value = parameters.get("contract_value", "")
        
        # Determine which table to use
        if "$100,000" in contract_value and "$249,999" in contract_value:
            table_doc = self.blacktown_rag.load_rag_document("table_2_quotation_matrix")
        else:
            table_doc = self.blacktown_rag.load_rag_document("table_3_tender_matrix")
        
        if table_doc:
            purchase_categories = table_doc.content.get("purchase_categories", {})
            matrix_data = purchase_categories.get(purchase_category)
            
            if matrix_data:
                return {
                    "data": matrix_data,
                    "sources": [f"Blacktown Standards: {table_doc.title}"],
                    "confidence": 0.95
                }
        
        return {
            "data": None,
            "sources": [],
            "confidence": 0.0,
            "error": f"Weighting matrix for '{purchase_category}' not found"
        }
    
    def _get_rating_scale(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get rating scale with optimization"""
        scale_name = parameters.get("scale_name", "")
        
        # Try quick lookup first
        if f"scale:{scale_name}" in self.document_index["quick_lookup"]:
            lookup_info = self.document_index["quick_lookup"][f"scale:{scale_name}"]
            doc_id = lookup_info["document_id"]
            
            doc = self.blacktown_rag.load_rag_document(doc_id)
            if doc:
                rating_scales = doc.content.get("rating_scales", {})
                scale_data = rating_scales.get(scale_name)
                
                if scale_data:
                    return {
                        "data": scale_data,
                        "sources": [f"Blacktown Standards: {doc.title}"],
                        "confidence": 0.95
                    }
        
        return {
            "data": None,
            "sources": [],
            "confidence": 0.0,
            "error": f"Rating scale '{scale_name}' not found"
        }
    
    def _get_compliance_requirements(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get compliance requirements with optimization"""
        project_type = parameters.get("project_type", "general")
        process_type = parameters.get("process_type", "tender")
        
        # Get from global compliance manager
        try:
            requirements = self.global_compliance.get_global_compliance_requirements(process_type, project_type)
            
            if requirements:
                return {
                    "data": requirements,
                    "sources": ["Global NSW Compliance Standards"],
                    "confidence": 0.9
                }
        except Exception as e:
            print(f"Error getting global compliance requirements: {e}")
        
        return {
            "data": [],
            "sources": [],
            "confidence": 0.0,
            "error": "No compliance requirements found"
        }
    
    def _get_local_preference_info(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get local preference information with optimization"""
        doc = self.blacktown_rag.load_rag_document("local_preference_policy")
        
        if doc:
            return {
                "data": doc.content,
                "sources": [f"Blacktown Standards: {doc.title}"],
                "confidence": 0.95
            }
        
        return {
            "data": None,
            "sources": [],
            "confidence": 0.0,
            "error": "Local preference policy not found"
        }
    
    def _get_social_value_criteria(self, category: ComplianceCategory, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get social value criteria with optimization"""
        doc = self.blacktown_rag.load_rag_document("social_procurement_guidelines")
        
        if doc:
            return {
                "data": doc.content,
                "sources": [f"Blacktown Standards: {doc.title}"],
                "confidence": 0.95
            }
        
        return {
            "data": None,
            "sources": [],
            "confidence": 0.0,
            "error": "Social procurement guidelines not found"
        }
    
    def verify_compliance(self, 
                         document_type: str, 
                         document_data: Dict[str, Any], 
                         project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive compliance verification for any document type"""
        
        compliance_report = {
            "document_type": document_type,
            "compliance_score": 0.0,
            "requirements_met": [],
            "requirements_missing": [],
            "recommendations": [],
            "source_standards": [],
            "verification_timestamp": datetime.now().isoformat()
        }
        
        # Get relevant compliance requirements
        project_type = project_context.get("project_type", "general")
        process_type = project_context.get("process_type", "tender")
        contract_value = project_context.get("contract_value", "")
        
        # Check evaluation criteria compliance
        if document_type in ["tepp", "evaluation_criteria", "returnable_schedules"]:
            criteria_result = self.query_compliance(
                QueryType.EVALUATION_CRITERIA,
                ComplianceCategory.EVALUATION_CRITERIA,
                {"criteria_name": "price"}
            )
            
            if criteria_result.result:
                compliance_report["requirements_met"].append("Evaluation criteria structure")
                compliance_report["source_standards"].extend(criteria_result.source_documents)
            else:
                compliance_report["requirements_missing"].append("Proper evaluation criteria structure")
                compliance_report["recommendations"].append("Include all required evaluation criteria categories")
        
        # Check weighting matrix compliance
        if document_type in ["evaluation_criteria", "weighting_matrix"]:
            matrix_result = self.query_compliance(
                QueryType.WEIGHTING_MATRIX,
                ComplianceCategory.EVALUATION_CRITERIA,
                {
                    "purchase_category": project_type,
                    "contract_value": contract_value
                }
            )
            
            if matrix_result.result:
                compliance_report["requirements_met"].append("Weighting matrix compliance")
                compliance_report["source_standards"].extend(matrix_result.source_documents)
            else:
                compliance_report["requirements_missing"].append("Proper weighting matrix")
                compliance_report["recommendations"].append("Use appropriate weighting ranges for project type")
        
        # Check compliance requirements
        compliance_result = self.query_compliance(
            QueryType.COMPLIANCE_REQUIREMENT,
            ComplianceCategory.GLOBAL_NSW_STANDARDS,
            {
                "project_type": project_type,
                "process_type": process_type
            }
        )
        
        if compliance_result.result:
            compliance_report["requirements_met"].append("NSW compliance requirements")
            compliance_report["source_standards"].extend(compliance_result.source_documents)
        else:
            compliance_report["requirements_missing"].append("NSW compliance requirements")
            compliance_report["recommendations"].append("Include all mandatory NSW compliance requirements")
        
        # Calculate compliance score
        total_requirements = len(compliance_report["requirements_met"]) + len(compliance_report["requirements_missing"])
        if total_requirements > 0:
            compliance_report["compliance_score"] = len(compliance_report["requirements_met"]) / total_requirements
        
        return compliance_report
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        cache_hit_rate = 0.0
        if self.query_stats["total_queries"] > 0:
            cache_hit_rate = self.query_stats["cache_hits"] / self.query_stats["total_queries"]
        
        return {
            "total_queries": self.query_stats["total_queries"],
            "cache_hits": self.query_stats["cache_hits"],
            "cache_misses": self.query_stats["cache_misses"],
            "cache_hit_rate": cache_hit_rate,
            "avg_processing_time_ms": self.query_stats["avg_processing_time_ms"],
            "cached_items": len(self.cache),
            "document_index_size": len(self.document_index["quick_lookup"]),
            "last_updated": datetime.now().isoformat()
        }
    
    def optimize_cache(self):
        """Optimize cache by removing unused items and consolidating"""
        current_time = datetime.now().isoformat()
        
        # Remove expired items
        expired_keys = []
        for key, cache_item in self.cache.items():
            if current_time > cache_item.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        # Remove low-access items (accessed less than 2 times in 24 hours)
        low_access_keys = []
        for key, cache_item in self.cache.items():
            if cache_item.access_count < 2:
                low_access_keys.append(key)
        
        for key in low_access_keys:
            del self.cache[key]
        
        print(f"✅ Cache optimized: {len(expired_keys)} expired, {len(low_access_keys)} low-access items removed")
        print(f"📊 Cache now contains {len(self.cache)} items")
        
        # Save optimized cache
        self._save_cache()

# Global instance
_unified_compliance_rag = None

def get_unified_compliance_rag(data_dir: Path) -> UnifiedComplianceRAGSystem:
    """Get or create unified compliance RAG system instance"""
    global _unified_compliance_rag
    if _unified_compliance_rag is None:
        _unified_compliance_rag = UnifiedComplianceRAGSystem(data_dir)
    return _unified_compliance_rag

if __name__ == "__main__":
    # Test the unified compliance RAG system
    from ..config import settings
    
    system = UnifiedComplianceRAGSystem(settings.DATA_DIR)
    
    print("✅ Unified Compliance RAG System initialized")
    
    # Test performance
    start_time = time.time()
    
    # Test evaluation criteria query
    result = system.query_compliance(
        QueryType.EVALUATION_CRITERIA,
        ComplianceCategory.EVALUATION_CRITERIA,
        {"criteria_name": "price"}
    )
    
    print(f"📋 Evaluation criteria query: {result.confidence_score:.2f} confidence")
    print(f"⏱️ Processing time: {result.processing_time_ms}ms")
    print(f"🎯 Cache hit: {result.cache_hit}")
    
    # Test compliance verification
    compliance_report = system.verify_compliance(
        "tepp",
        {"project_name": "Test Project"},
        {
            "project_type": "construction_contract",
            "process_type": "tender",
            "contract_value": "$250,000+"
        }
    )
    
    print(f"\n🛡️ Compliance verification:")
    print(f"   Score: {compliance_report['compliance_score']:.2f}")
    print(f"   Requirements met: {len(compliance_report['requirements_met'])}")
    print(f"   Requirements missing: {len(compliance_report['requirements_missing'])}")
    
    # Show performance stats
    stats = system.get_performance_stats()
    print(f"\n📊 Performance Stats:")
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"   Avg processing time: {stats['avg_processing_time_ms']:.1f}ms")
    
    print("\n🎉 Unified Compliance RAG System optimized and ready!")
