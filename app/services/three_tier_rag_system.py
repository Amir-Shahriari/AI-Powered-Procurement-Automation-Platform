#!/usr/bin/env python3
"""
Three-Tier RAG System for NSW Local Government Procurement
Implements comprehensive document categorization and compliance alignment

Tier 1: Global RAG - NSW Local Government external standards, rules, regulations
Tier 2: Internal RAG - Council-specific internal rules, regulations, policies
Tier 3: Project RAG - Project-specific compliance (WHS, ADR, ISO, etc.)
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import time

# Import existing systems
from app.services.blacktown_rag_system import BlacktownRAGSystem
from app.services.global_compliance_manager import GlobalComplianceManager
from app.services.smart_rag import SmartRAGSystem

class RAGTier(Enum):
    """Three-tier RAG system categories"""
    GLOBAL = "global"           # NSW Local Government external standards
    INTERNAL = "internal"       # Council-specific internal rules
    PROJECT = "project"         # Project-specific compliance (WHS, ADR, ISO)

class DocumentCategory(Enum):
    """Document categories within each tier"""
    # Global Tier
    NSW_LEGISLATION = "nsw_legislation"
    LOCAL_GOVT_ACT = "local_govt_act"
    PROCUREMENT_GUIDELINES = "procurement_guidelines"
    TENDERING_STANDARDS = "tendering_standards"
    EVALUATION_CRITERIA = "evaluation_criteria"
    
    # Internal Tier
    COUNCIL_POLICIES = "council_policies"
    INTERNAL_PROCEDURES = "internal_procedures"
    COUNCIL_STANDARDS = "council_standards"
    LOCAL_PREFERENCE = "local_preference"
    SOCIAL_PROCUREMENT = "social_procurement"
    
    # Project Tier
    WHS_COMPLIANCE = "whs_compliance"
    ADR_STANDARDS = "adr_standards"
    ISO_STANDARDS = "iso_standards"
    ENVIRONMENTAL = "environmental"
    EEO_FAIR_EMPLOYMENT = "eeo_fair_employment"
    SAFETY_STANDARDS = "safety_standards"
    QUALITY_MANAGEMENT = "quality_management"

@dataclass
class RAGDocument:
    """Standardized RAG document structure"""
    document_id: str
    title: str
    content: str
    tier: RAGTier
    category: DocumentCategory
    council: Optional[str] = None
    project_type: Optional[str] = None
    version: str = "1.0"
    upload_date: str = ""
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_date: str = ""
    updated_date: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.upload_date:
            self.upload_date = datetime.now().isoformat()
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.updated_date:
            self.updated_date = datetime.now().isoformat()

@dataclass
class RAGQueryResult:
    """Result from RAG query across all tiers"""
    tier: RAGTier
    category: DocumentCategory
    document_id: str
    title: str
    content: str
    relevance_score: float
    source_section: str
    compliance_requirements: List[str]
    metadata: Dict[str, Any]

class ThreeTierRAGSystem:
    """
    Comprehensive three-tier RAG system for NSW Local Government procurement
    Ensures all documents (TEPP, Returnable Schedules, RFT/RFQ) are aligned with all compliance tiers
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.rag_dir = data_dir / "three_tier_rag"
        self.rag_dir.mkdir(exist_ok=True)
        
        # Create tier-specific directories
        self.global_dir = self.rag_dir / "global"
        self.internal_dir = self.rag_dir / "internal"
        self.project_dir = self.rag_dir / "project"
        
        for tier_dir in [self.global_dir, self.internal_dir, self.project_dir]:
            tier_dir.mkdir(exist_ok=True)
        
        # Initialize RAG systems for each tier
        self.global_rag = SmartRAGSystem()
        self.internal_rag = SmartRAGSystem()
        self.project_rag = SmartRAGSystem()
        
        # Document index for fast retrieval
        self.document_index = {
            RAGTier.GLOBAL: {},
            RAGTier.INTERNAL: {},
            RAGTier.PROJECT: {}
        }
        
        # Load existing documents
        self._load_existing_documents()
        
        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "tier_queries": {tier.value: 0 for tier in RAGTier},
            "avg_processing_time_ms": 0,
            "total_processing_time_ms": 0
        }
    
    def _load_existing_documents(self):
        """Load existing documents from all tiers"""
        for tier in RAGTier:
            tier_dir = self.rag_dir / tier.value
            if tier_dir.exists():
                for doc_file in tier_dir.glob("*.json"):
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                        
                        doc = RAGDocument(**doc_data)
                        self._index_document(doc)
                        
                    except Exception as e:
                        print(f"⚠️ Error loading document {doc_file}: {e}")
    
    def _index_document(self, doc: RAGDocument):
        """Index document for fast retrieval"""
        tier = doc.tier
        category = doc.category
        
        if category not in self.document_index[tier]:
            self.document_index[tier][category] = []
        
        self.document_index[tier][category].append(doc.document_id)
    
    def upload_document(self, 
                       file_path: Path, 
                       title: str, 
                       tier: RAGTier, 
                       category: DocumentCategory,
                       council: Optional[str] = None,
                       project_type: Optional[str] = None,
                       content: Optional[str] = None) -> str:
        """
        Upload document to appropriate tier with automatic categorization
        """
        # Generate unique document ID
        doc_id = f"{tier.value}_{category.value}_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        
        # Extract content if not provided
        if not content:
            content = self._extract_text_from_file(file_path)
        
        # Create RAG document
        doc = RAGDocument(
            document_id=doc_id,
            title=title,
            content=content,
            tier=tier,
            category=category,
            council=council,
            project_type=project_type,
            file_path=str(file_path),
            metadata={
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "file_type": file_path.suffix,
                "upload_timestamp": datetime.now().isoformat()
            }
        )
        
        # Save document
        self._save_document(doc)
        
        # Index document
        self._index_document(doc)
        
        # Add to appropriate RAG system
        self._add_to_rag_system(doc)
        
        return doc_id
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from various file types"""
        try:
            if file_path.suffix.lower() == '.pdf':
                # TODO: Implement PDF text extraction
                return f"PDF content from {file_path.name}"
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # TODO: Implement DOCX text extraction
                return f"DOCX content from {file_path.name}"
            elif file_path.suffix.lower() == '.txt':
                return file_path.read_text(encoding='utf-8')
            else:
                return f"Content from {file_path.name}"
        except Exception as e:
            print(f"⚠️ Error extracting text from {file_path}: {e}")
            return f"Content from {file_path.name}"
    
    def _save_document(self, doc: RAGDocument):
        """Save document to appropriate tier directory"""
        tier_dir = self.rag_dir / doc.tier.value
        doc_file = tier_dir / f"{doc.document_id}.json"
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(doc), f, indent=2, ensure_ascii=False)
    
    def _add_to_rag_system(self, doc: RAGDocument):
        """Add document to appropriate RAG system"""
        try:
            if doc.tier == RAGTier.GLOBAL:
                self.global_rag.add_document(doc.content, doc.metadata)
            elif doc.tier == RAGTier.INTERNAL:
                self.internal_rag.add_document(doc.content, doc.metadata)
            elif doc.tier == RAGTier.PROJECT:
                self.project_rag.add_document(doc.content, doc.metadata)
        except Exception as e:
            print(f"⚠️ Error adding document to RAG system: {e}")
    
    def query(self, 
              query_text: str, 
              tier: str = "internal", 
              max_results: int = 5) -> str:
        """
        Simple query method for backward compatibility
        Returns a string response from the RAG system
        """
        try:
            # Convert tier string to RAGTier enum
            if tier == "global":
                rag_tier = RAGTier.GLOBAL
            elif tier == "internal":
                rag_tier = RAGTier.INTERNAL
            elif tier == "project":
                rag_tier = RAGTier.PROJECT
            else:
                rag_tier = RAGTier.INTERNAL
            
            # Query the compliance system
            results = self.query_compliance(
                query=query_text,
                tiers=[rag_tier],
                max_results=max_results
            )
            
            # Convert results to string
            if results:
                response_parts = []
                for result in results[:max_results]:
                    response_parts.append(f"**{result.document_title}**\n{result.relevant_content}\n")
                return "\n".join(response_parts)
            else:
                return f"No relevant documents found for query: {query_text}"
                
        except Exception as e:
            return f"Error querying RAG system: {str(e)}"
    
    def query_compliance(self, 
                        query: str, 
                        tiers: Optional[List[RAGTier]] = None,
                        categories: Optional[List[DocumentCategory]] = None,
                        council: Optional[str] = None,
                        project_type: Optional[str] = None,
                        max_results: int = 5) -> List[RAGQueryResult]:
        """
        Query compliance across specified tiers and categories
        Returns comprehensive results from all relevant sources
        """
        start_time = time.time()
        self.query_stats["total_queries"] += 1
        
        # Default to all tiers if not specified
        if not tiers:
            tiers = list(RAGTier)
        
        results = []
        
        # Query each tier
        for tier in tiers:
            self.query_stats["tier_queries"][tier.value] += 1
            
            # Get relevant categories for this tier
            tier_categories = self._get_relevant_categories(tier, categories)
            
            for category in tier_categories:
                tier_results = self._query_tier_category(
                    query, tier, category, council, project_type
                )
                results.extend(tier_results)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update performance stats
        processing_time = (time.time() - start_time) * 1000
        self.query_stats["total_processing_time_ms"] += processing_time
        self.query_stats["avg_processing_time_ms"] = (
            self.query_stats["total_processing_time_ms"] / 
            self.query_stats["total_queries"]
        )
        
        return results
    
    def _get_relevant_categories(self, 
                                tier: RAGTier, 
                                categories: Optional[List[DocumentCategory]]) -> List[DocumentCategory]:
        """Get relevant categories for a tier"""
        if not categories:
            # Return all categories for the tier
            if tier == RAGTier.GLOBAL:
                return [DocumentCategory.NSW_LEGISLATION, DocumentCategory.LOCAL_GOVT_ACT, 
                       DocumentCategory.PROCUREMENT_GUIDELINES, DocumentCategory.TENDERING_STANDARDS,
                       DocumentCategory.EVALUATION_CRITERIA]
            elif tier == RAGTier.INTERNAL:
                return [DocumentCategory.COUNCIL_POLICIES, DocumentCategory.INTERNAL_PROCEDURES,
                       DocumentCategory.COUNCIL_STANDARDS, DocumentCategory.LOCAL_PREFERENCE,
                       DocumentCategory.SOCIAL_PROCUREMENT]
            elif tier == RAGTier.PROJECT:
                return [DocumentCategory.WHS_COMPLIANCE, DocumentCategory.ADR_STANDARDS,
                       DocumentCategory.ISO_STANDARDS, DocumentCategory.ENVIRONMENTAL,
                       DocumentCategory.EEO_FAIR_EMPLOYMENT, DocumentCategory.SAFETY_STANDARDS,
                       DocumentCategory.QUALITY_MANAGEMENT]
        
        # Filter categories by tier
        tier_categories = []
        for category in categories:
            if self._is_category_for_tier(category, tier):
                tier_categories.append(category)
        
        return tier_categories
    
    def _is_category_for_tier(self, category: DocumentCategory, tier: RAGTier) -> bool:
        """Check if category belongs to tier"""
        global_categories = [DocumentCategory.NSW_LEGISLATION, DocumentCategory.LOCAL_GOVT_ACT,
                           DocumentCategory.PROCUREMENT_GUIDELINES, DocumentCategory.TENDERING_STANDARDS,
                           DocumentCategory.EVALUATION_CRITERIA]
        
        internal_categories = [DocumentCategory.COUNCIL_POLICIES, DocumentCategory.INTERNAL_PROCEDURES,
                             DocumentCategory.COUNCIL_STANDARDS, DocumentCategory.LOCAL_PREFERENCE,
                             DocumentCategory.SOCIAL_PROCUREMENT]
        
        project_categories = [DocumentCategory.WHS_COMPLIANCE, DocumentCategory.ADR_STANDARDS,
                            DocumentCategory.ISO_STANDARDS, DocumentCategory.ENVIRONMENTAL,
                            DocumentCategory.EEO_FAIR_EMPLOYMENT, DocumentCategory.SAFETY_STANDARDS,
                            DocumentCategory.QUALITY_MANAGEMENT]
        
        if tier == RAGTier.GLOBAL:
            return category in global_categories
        elif tier == RAGTier.INTERNAL:
            return category in internal_categories
        elif tier == RAGTier.PROJECT:
            return category in project_categories
        
        return False
    
    def _query_tier_category(self, 
                           query: str, 
                           tier: RAGTier, 
                           category: DocumentCategory,
                           council: Optional[str] = None,
                           project_type: Optional[str] = None) -> List[RAGQueryResult]:
        """Query specific tier and category"""
        results = []
        
        # Get documents for this tier and category
        if category in self.document_index[tier]:
            for doc_id in self.document_index[tier][category]:
                doc = self._load_document(tier, doc_id)
                if doc:
                    # Check if document matches filters
                    if council and doc.council and doc.council != council:
                        continue
                    if project_type and doc.project_type and doc.project_type != project_type:
                        continue
                    
                    # Query document content
                    relevance_score = self._calculate_relevance(query, doc.content)
                    
                    if relevance_score > 0.1:  # Threshold for relevance
                        result = RAGQueryResult(
                            tier=tier,
                            category=category,
                            document_id=doc.document_id,
                            title=doc.title,
                            content=doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                            relevance_score=relevance_score,
                            source_section=self._extract_relevant_section(query, doc.content),
                            compliance_requirements=self._extract_compliance_requirements(doc.content),
                            metadata=doc.metadata
                        )
                        results.append(result)
        
        return results
    
    def _load_document(self, tier: RAGTier, doc_id: str) -> Optional[RAGDocument]:
        """Load document from tier directory"""
        try:
            doc_file = self.rag_dir / tier.value / f"{doc_id}.json"
            if doc_file.exists():
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                return RAGDocument(**doc_data)
        except Exception as e:
            print(f"⚠️ Error loading document {doc_id}: {e}")
        return None
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        # Simple keyword matching - can be enhanced with semantic similarity
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
    
    def _extract_relevant_section(self, query: str, content: str) -> str:
        """Extract most relevant section of content"""
        # Simple implementation - find sentences containing query words
        sentences = content.split('.')
        query_words = set(query.lower().split())
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if query_words.intersection(sentence_words):
                return sentence.strip()[:200] + "..."
        
        return content[:200] + "..."
    
    def _extract_compliance_requirements(self, content: str) -> List[str]:
        """Extract compliance requirements from content"""
        # Simple keyword-based extraction
        requirements = []
        compliance_keywords = [
            "must", "shall", "required", "mandatory", "compliance",
            "standard", "criteria", "evaluation", "assessment"
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in compliance_keywords):
                requirements.append(sentence.strip())
        
        return requirements[:5]  # Limit to top 5 requirements
    
    def get_compliance_summary(self, 
                             council: Optional[str] = None,
                             project_type: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive compliance summary across all tiers"""
        summary = {
            "global_compliance": {
                "documents_count": len(self.document_index[RAGTier.GLOBAL]),
                "categories_covered": list(self.document_index[RAGTier.GLOBAL].keys()),
                "last_updated": datetime.now().isoformat()
            },
            "internal_compliance": {
                "documents_count": len(self.document_index[RAGTier.INTERNAL]),
                "categories_covered": list(self.document_index[RAGTier.INTERNAL].keys()),
                "council": council,
                "last_updated": datetime.now().isoformat()
            },
            "project_compliance": {
                "documents_count": len(self.document_index[RAGTier.PROJECT]),
                "categories_covered": list(self.document_index[RAGTier.PROJECT].keys()),
                "project_type": project_type,
                "last_updated": datetime.now().isoformat()
            },
            "query_stats": self.query_stats
        }
        
        return summary
    
    def validate_document_alignment(self, 
                                  document_type: str,  # "TEPP", "Returnable_Schedule", "RFT", "RFQ"
                                  content: str) -> Dict[str, Any]:
        """
        Validate that document is aligned with all three RAG tiers
        Returns compliance status and recommendations
        """
        validation_results = {
            "document_type": document_type,
            "overall_compliance": True,
            "tier_validations": {},
            "recommendations": [],
            "missing_requirements": []
        }
        
        # Validate against each tier
        for tier in RAGTier:
            tier_results = self._validate_tier_compliance(document_type, content, tier)
            validation_results["tier_validations"][tier.value] = tier_results
            
            if not tier_results["compliant"]:
                validation_results["overall_compliance"] = False
                validation_results["missing_requirements"].extend(tier_results["missing_requirements"])
        
        # Generate recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results)
        
        return validation_results
    
    def _validate_tier_compliance(self, 
                                document_type: str, 
                                content: str, 
                                tier: RAGTier) -> Dict[str, Any]:
        """Validate compliance against specific tier"""
        # Query relevant compliance requirements
        query = f"{document_type} compliance requirements {tier.value}"
        results = self.query_compliance(query, tiers=[tier])
        
        compliance_score = 0
        missing_requirements = []
        
        for result in results:
            # Check if content addresses the compliance requirement
            if self._content_addresses_requirement(content, result.content):
                compliance_score += result.relevance_score
            else:
                missing_requirements.append({
                    "requirement": result.content,
                    "source": result.title,
                    "tier": tier.value,
                    "category": result.category.value
                })
        
        return {
            "compliant": compliance_score > 0.5,  # Threshold for compliance
            "compliance_score": compliance_score,
            "missing_requirements": missing_requirements,
            "sources_checked": len(results)
        }
    
    def _content_addresses_requirement(self, content: str, requirement: str) -> bool:
        """Check if content addresses a specific requirement"""
        # Simple keyword matching - can be enhanced with semantic analysis
        requirement_keywords = set(requirement.lower().split())
        content_keywords = set(content.lower().split())
        
        # Check for significant overlap
        overlap = requirement_keywords.intersection(content_keywords)
        return len(overlap) / len(requirement_keywords) > 0.3
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if not validation_results["overall_compliance"]:
            recommendations.append("Document needs to address missing compliance requirements from all tiers")
        
        for tier, results in validation_results["tier_validations"].items():
            if not results["compliant"]:
                recommendations.append(f"Enhance {tier} tier compliance - add requirements for {results['missing_requirements'][0]['category']}")
        
        return recommendations
    
    def get_documents_by_tier(self, tier: RAGTier) -> List[RAGDocument]:
        """Get all documents for a specific tier"""
        documents = []
        for category in self.document_index[tier]:
            for doc_id in self.document_index[tier][category]:
                doc = self._load_document(tier, doc_id)
                if doc:
                    documents.append(doc)
        return documents
    
    def add_document(self, doc: RAGDocument) -> bool:
        """Add a new document to the system"""
        try:
            # Save document
            self._save_document(doc)
            
            # Index document
            self._index_document(doc)
            
            # Add to appropriate RAG system
            self._add_to_rag_system(doc)
            
            return True
        except Exception as e:
            print(f"⚠️ Error adding document: {e}")
            return False
    
    def get_document_by_id(self, doc_id: str) -> Optional[RAGDocument]:
        """Get document by ID across all tiers"""
        for tier in RAGTier:
            doc = self._load_document(tier, doc_id)
            if doc:
                return doc
        return None
    
    def get_all_documents(self) -> List[RAGDocument]:
        """Get all documents across all tiers"""
        all_documents = []
        for tier in RAGTier:
            tier_docs = self.get_documents_by_tier(tier)
            all_documents.extend(tier_docs)
        return all_documents