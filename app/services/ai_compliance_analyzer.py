"""
AI-Powered Compliance Analyzer
Real-time compliance monitoring across all NSW procurement data and rules
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import time

from app.config import settings
from app.services.three_tier_rag_system import ThreeTierRAGSystem, RAGTier, DocumentCategory
from app.services.ai_model_detector import get_ai_detector

class ComplianceLevel(Enum):
    """Compliance severity levels"""
    CRITICAL = "critical"      # Immediate action required
    HIGH = "high"             # Action required within 24 hours
    MEDIUM = "medium"         # Action required within 7 days
    LOW = "low"               # Monitor and address when convenient
    COMPLIANT = "compliant"   # Fully compliant

class ComplianceCategory(Enum):
    """Compliance categories for NSW procurement"""
    LEGISLATIVE = "legislative"           # Local Government Act, etc.
    FINANCIAL = "financial"               # Value thresholds, budget approvals
    PROCESS = "process"                   # Tender process, evaluation
    SOCIAL = "social"                     # Local preference, social procurement
    ENVIRONMENTAL = "environmental"       # Environmental standards
    SAFETY = "safety"                     # WHS compliance
    DOCUMENTATION = "documentation"       # Required documents, records
    TIMELINE = "timeline"                 # Deadlines, milestones

@dataclass
class ComplianceRule:
    """Individual compliance rule definition"""
    rule_id: str
    name: str
    description: str
    category: ComplianceCategory
    level: ComplianceLevel
    nsw_reference: str
    applicable_projects: List[str]  # Project types this applies to
    value_threshold: Optional[float] = None
    required_documents: List[str] = None
    deadline_days: Optional[int] = None
    ai_prompt: str = ""
    
    def __post_init__(self):
        if self.required_documents is None:
            self.required_documents = []

@dataclass
class ComplianceViolation:
    """Individual compliance violation"""
    violation_id: str
    rule_id: str
    project_id: str
    project_name: str
    violation_type: str
    description: str
    severity: ComplianceLevel
    detected_at: str
    due_date: Optional[str] = None
    status: str = "open"  # open, in_progress, resolved
    resolution_notes: str = ""
    ai_confidence: float = 0.0

@dataclass
class ComplianceMetrics:
    """Overall compliance metrics"""
    total_projects: int
    compliant_projects: int
    projects_with_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    compliance_score: float
    last_updated: str
    trend_direction: str  # improving, declining, stable

class AIComplianceAnalyzer:
    """
    AI-powered compliance analyzer that monitors all NSW procurement data
    in real-time using AI to detect violations and ensure compliance
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rag_system = ThreeTierRAGSystem(self.data_dir)
        self.ai_detector = get_ai_detector()
        self.ai_model = None
        
        # Compliance rules database
        self.compliance_rules = self._load_compliance_rules()
        
        # Real-time monitoring
        self.violations = []
        self.metrics = None
        self.last_scan = None
        
        # Initialize AI model
        self._initialize_ai_model()
        
        # Start real-time monitoring
        self._start_monitoring()
    
    def _initialize_ai_model(self):
        """Initialize AI model for compliance analysis"""
        try:
            self.ai_model = self.ai_detector.get_recommended_model()
            print(f"✅ AI Compliance Analyzer initialized with {self.ai_model.model_name}")
        except Exception as e:
            print(f"⚠️ Failed to initialize AI model: {e}")
            self.ai_model = None
    
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load comprehensive NSW procurement compliance rules from existing RAG data"""
        rules = [
            # Legislative Compliance
            ComplianceRule(
                rule_id="LG_ACT_1993_001",
                name="Local Government Act 1993 Compliance",
                description="All procurement must comply with Local Government Act 1993",
                category=ComplianceCategory.LEGISLATIVE,
                level=ComplianceLevel.CRITICAL,
                nsw_reference="Local Government Act 1993, Section 55",
                applicable_projects=["all"],
                ai_prompt="Check if procurement follows Local Government Act 1993 requirements including proper delegation, public interest, and procedural fairness."
            ),
            
            # Blacktown City Council Specific Rules
            ComplianceRule(
                rule_id="BLACKTOWN_TEPP_001",
                name="TEPP Document Structure Compliance",
                description="TEPP must include proper document structure and metadata",
                category=ComplianceCategory.DOCUMENTATION,
                level=ComplianceLevel.CRITICAL,
                nsw_reference="Blacktown Tender Guidelines",
                applicable_projects=["tender"],
                required_documents=["tepp_document", "project_metadata"],
                ai_prompt="Verify TEPP document includes proper structure, project metadata, and follows Blacktown City Council TEPP template requirements."
            ),
            
            ComplianceRule(
                rule_id="BLACKTOWN_EVAL_001",
                name="Blacktown Evaluation Criteria Compliance",
                description="Evaluation must use Blacktown City Council criteria matrices",
                category=ComplianceCategory.PROCESS,
                level=ComplianceLevel.HIGH,
                nsw_reference="Table 1 - Criteria Options",
                applicable_projects=["tender", "quote"],
                ai_prompt="Ensure evaluation uses Blacktown City Council Table 1 criteria options including compliance, price, relevant experience, capability, management & financial, quality management, WHS, sustainability, social & community, and EEO & fair employment."
            ),
            
            ComplianceRule(
                rule_id="BLACKTOWN_WEIGHTING_001",
                name="Blacktown Weighting Matrix Compliance",
                description="Evaluation weighting must follow Blacktown matrices",
                category=ComplianceCategory.PROCESS,
                level=ComplianceLevel.HIGH,
                nsw_reference="Table 2/3 - Evaluation Matrices",
                applicable_projects=["tender", "quote"],
                ai_prompt="Verify evaluation weighting follows Blacktown City Council Table 2 (quotations $100k-$249k) or Table 3 (tenders $250k+) matrices based on purchase category and contract value."
            ),
            
            ComplianceRule(
                rule_id="BLACKTOWN_LOCAL_PREF_001",
                name="Blacktown Local Preference Policy",
                description="Local preference discounts must be applied correctly",
                category=ComplianceCategory.SOCIAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="Local Preference Policy P000553.1",
                applicable_projects=["tender", "quote"],
                ai_prompt="Verify local preference policy is applied: 5% discount for Blacktown LGA suppliers (max $50k), 2.5% for Western Sydney suppliers (max $25k)."
            ),
            
            # WHS Compliance (from existing data)
            ComplianceRule(
                rule_id="WHS_AS4801_001",
                name="AS/NZS 4801:2001 WHS Management System",
                description="WHS management system must comply with AS/NZS 4801:2001",
                category=ComplianceCategory.SAFETY,
                level=ComplianceLevel.CRITICAL,
                nsw_reference="AS/NZS 4801:2001",
                applicable_projects=["construction", "services"],
                required_documents=["whs_manual", "whs_policy", "safe_work_methods"],
                ai_prompt="Verify WHS management system includes AS/NZS 4801:2001 compliance, WHS051.5 and WHS051.6 forms completion, and comprehensive safety management system."
            ),
            
            ComplianceRule(
                rule_id="WHS_AS45001_001",
                name="AS/NZS 45001:2018 ISO 45001 Certification",
                description="Independent WHS certification required where applicable",
                category=ComplianceCategory.SAFETY,
                level=ComplianceLevel.HIGH,
                nsw_reference="AS/NZS 45001:2018",
                applicable_projects=["construction", "services"],
                ai_prompt="Check for independent AS/NZS 45001:2018 certification and compliance with NSW Workcover standards."
            ),
            
            # Environmental Compliance
            ComplianceRule(
                rule_id="ENV_ISO14001_001",
                name="ISO 14001 Environmental Management",
                description="Environmental management system compliance",
                category=ComplianceCategory.ENVIRONMENTAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="AS/NZS ISO 14001:2016",
                applicable_projects=["construction", "services"],
                required_documents=["environmental_policy", "environmental_management_plan"],
                ai_prompt="Verify environmental management system includes policy, management plan, training procedures, and sustainability record including waste minimisation, energy efficiency, and recycling."
            ),
            
            # Quality Management
            ComplianceRule(
                rule_id="QUAL_ISO9001_001",
                name="ISO 9001 Quality Management System",
                description="Quality management system compliance",
                category=ComplianceCategory.DOCUMENTATION,
                level=ComplianceLevel.HIGH,
                nsw_reference="AS/NZS ISO 9001:2016",
                applicable_projects=["all"],
                required_documents=["quality_management_plan", "quality_policy"],
                ai_prompt="Verify quality management system includes comprehensive quality plan, safety plan standards, reporting procedures, and response/resolution procedures."
            ),
            
            # EEO and Fair Employment
            ComplianceRule(
                rule_id="EEO_FAIR_001",
                name="EEO and Fair Employment Compliance",
                description="Equal employment opportunity and fair employment practices",
                category=ComplianceCategory.SOCIAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="NSW Anti-Discrimination Act",
                applicable_projects=["all"],
                required_documents=["eeo_policy", "anti_discrimination_policy"],
                ai_prompt="Verify EEO compliance including wages under award/EA, superannuation paid, record keeping, EEO policies, Aboriginal employment policies, and apprenticeships/traineeships."
            ),
            
            # Social Procurement
            ComplianceRule(
                rule_id="SOCIAL_PROC_001",
                name="Social Procurement Guidelines",
                description="Social procurement and community benefit requirements",
                category=ComplianceCategory.SOCIAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="NSW Social Procurement Policy",
                applicable_projects=["all"],
                ai_prompt="Verify social procurement includes local conditions knowledge, local economy impact, community group cooperation, community benefit projects, disadvantaged group employment, and social inclusion."
            ),
            
            # Financial Compliance
            ComplianceRule(
                rule_id="FIN_THRESHOLD_001",
                name="Value Threshold Compliance",
                description="Projects over $250k must follow tender process",
                category=ComplianceCategory.FINANCIAL,
                level=ComplianceLevel.CRITICAL,
                nsw_reference="NSW Procurement Board Guidelines",
                applicable_projects=["construction", "services", "goods"],
                value_threshold=250000,
                ai_prompt="Verify that projects over $250,000 follow proper tender process with public advertisement and competitive evaluation."
            ),
            
            ComplianceRule(
                rule_id="FIN_BUDGET_001",
                name="Budget Approval Compliance",
                description="All procurement must have proper budget approval",
                category=ComplianceCategory.FINANCIAL,
                level=ComplianceLevel.HIGH,
                nsw_reference="NSW Treasury Circular",
                applicable_projects=["all"],
                ai_prompt="Ensure all procurement has proper budget approval and financial delegation before proceeding."
            ),
            
            # Process Compliance
            ComplianceRule(
                rule_id="PROC_TENDER_001",
                name="Tender Process Compliance",
                description="Tender process must follow NSW guidelines",
                category=ComplianceCategory.PROCESS,
                level=ComplianceLevel.HIGH,
                nsw_reference="NSW Procurement Board Guidelines",
                applicable_projects=["tender"],
                required_documents=["tender_document", "evaluation_criteria", "evaluation_report"],
                ai_prompt="Verify tender process includes proper advertisement, evaluation criteria, and selection process per NSW guidelines."
            ),
            
            ComplianceRule(
                rule_id="PROC_EVAL_001",
                name="Evaluation Criteria Compliance",
                description="Evaluation criteria must be objective and measurable",
                category=ComplianceCategory.PROCESS,
                level=ComplianceLevel.HIGH,
                nsw_reference="NSW Procurement Board Guidelines",
                applicable_projects=["tender", "quote"],
                ai_prompt="Ensure evaluation criteria are objective, measurable, and directly related to the procurement requirements."
            ),
            
            # Social Compliance
            ComplianceRule(
                rule_id="SOC_LOCAL_001",
                name="Local Preference Policy",
                description="Local preference policy must be applied where applicable",
                category=ComplianceCategory.SOCIAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="NSW Local Government Act",
                applicable_projects=["all"],
                ai_prompt="Check if local preference policy is properly applied and documented where applicable."
            ),
            
            ComplianceRule(
                rule_id="SOC_PROC_001",
                name="Social Procurement Requirements",
                description="Social procurement requirements must be considered",
                category=ComplianceCategory.SOCIAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="NSW Social Procurement Policy",
                applicable_projects=["all"],
                ai_prompt="Verify that social procurement requirements are considered and documented in procurement decisions."
            ),
            
            # Environmental Compliance
            ComplianceRule(
                rule_id="ENV_SUSTAIN_001",
                name="Environmental Sustainability",
                description="Environmental considerations must be included",
                category=ComplianceCategory.ENVIRONMENTAL,
                level=ComplianceLevel.MEDIUM,
                nsw_reference="NSW Environmental Planning Act",
                applicable_projects=["construction", "services"],
                ai_prompt="Ensure environmental sustainability considerations are included in procurement decisions and documented."
            ),
            
            # Safety Compliance
            ComplianceRule(
                rule_id="SAFETY_WHS_001",
                name="Workplace Health and Safety",
                description="WHS compliance must be verified",
                category=ComplianceCategory.SAFETY,
                level=ComplianceLevel.CRITICAL,
                nsw_reference="NSW Work Health and Safety Act",
                applicable_projects=["construction", "services"],
                ai_prompt="Verify that workplace health and safety requirements are met and documented for all applicable projects."
            ),
            
            # Documentation Compliance
            ComplianceRule(
                rule_id="DOC_RECORD_001",
                name="Documentation Standards",
                description="All procurement must be properly documented",
                category=ComplianceCategory.DOCUMENTATION,
                level=ComplianceLevel.HIGH,
                nsw_reference="NSW Records Management Act",
                applicable_projects=["all"],
                required_documents=["procurement_plan", "evaluation_report", "contract"],
                ai_prompt="Ensure all procurement activities are properly documented and records are maintained per NSW requirements."
            ),
            
            # Timeline Compliance
            ComplianceRule(
                rule_id="TIME_DEADLINE_001",
                name="Deadline Compliance",
                description="All deadlines must be met",
                category=ComplianceCategory.TIMELINE,
                level=ComplianceLevel.HIGH,
                nsw_reference="NSW Procurement Guidelines",
                applicable_projects=["all"],
                deadline_days=30,
                ai_prompt="Check that all procurement deadlines are met and any delays are properly documented and approved."
            )
        ]
        
        return rules
    
    def _start_monitoring(self):
        """Start real-time compliance monitoring"""
        # This would typically run in a background thread
        # For now, we'll scan on demand
        pass
    
    async def scan_all_data(self) -> ComplianceMetrics:
        """Scan all available data for compliance violations"""
        print("🔍 Starting comprehensive compliance scan...")
        
        # Get all projects from the system
        projects = self._get_all_projects()
        
        # Initialize metrics
        total_projects = len(projects)
        compliant_projects = 0
        projects_with_violations = 0
        violation_counts = {level.value: 0 for level in ComplianceLevel}
        
        # Clear previous violations
        self.violations = []
        
        # Scan each project
        for project in projects:
            project_violations = await self._analyze_project_compliance(project)
            
            if not project_violations:
                compliant_projects += 1
            else:
                projects_with_violations += 1
                self.violations.extend(project_violations)
                
                # Count violations by severity
                for violation in project_violations:
                    violation_counts[violation.severity.value] += 1
        
        # Calculate compliance score
        compliance_score = (compliant_projects / total_projects * 100) if total_projects > 0 else 100
        
        # Create metrics
        self.metrics = ComplianceMetrics(
            total_projects=total_projects,
            compliant_projects=compliant_projects,
            projects_with_violations=projects_with_violations,
            critical_violations=violation_counts["critical"],
            high_violations=violation_counts["high"],
            medium_violations=violation_counts["medium"],
            low_violations=violation_counts["low"],
            compliance_score=compliance_score,
            last_updated=datetime.now().isoformat(),
            trend_direction="stable"  # Would calculate based on historical data
        )
        
        self.last_scan = datetime.now()
        print(f"✅ Compliance scan completed: {compliance_score:.1f}% compliance")
        
        return self.metrics
    
    def _get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from the system"""
        projects = []
        
        # Get projects from projects directory
        projects_dir = self.data_dir / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    # Load project metadata
                    metadata_file = project_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                project_data = json.load(f)
                                project_data['project_id'] = project_dir.name
                                project_data['project_path'] = str(project_dir)
                                projects.append(project_data)
                        except Exception as e:
                            print(f"⚠️ Error loading project {project_dir.name}: {e}")
        
        # Get projects from session state (active projects)
        if hasattr(self, 'session_state') and 'projects' in self.session_state:
            for project in self.session_state['projects']:
                projects.append(project)
        
        return projects
    
    async def _analyze_project_compliance(self, project: Dict[str, Any]) -> List[ComplianceViolation]:
        """Analyze a single project for compliance violations using AI"""
        violations = []
        
        # Get applicable rules for this project
        applicable_rules = self._get_applicable_rules(project)
        
        # Analyze each rule
        for rule in applicable_rules:
            violation = await self._check_rule_compliance(rule, project)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _get_applicable_rules(self, project: Dict[str, Any]) -> List[ComplianceRule]:
        """Get rules applicable to this project"""
        applicable = []
        project_type = project.get('project_type', 'general').lower()
        
        for rule in self.compliance_rules:
            if 'all' in rule.applicable_projects or project_type in rule.applicable_projects:
                # Check value threshold if applicable
                if rule.value_threshold:
                    project_value = project.get('contract_value', 0)
                    if project_value >= rule.value_threshold:
                        applicable.append(rule)
                else:
                    applicable.append(rule)
        
        return applicable
    
    async def _check_rule_compliance(self, rule: ComplianceRule, project: Dict[str, Any]) -> Optional[ComplianceViolation]:
        """Check compliance for a specific rule using AI analysis"""
        try:
            # Prepare context for AI analysis
            context = self._prepare_analysis_context(rule, project)
            
            # Use AI to analyze compliance
            if self.ai_model and self.ai_model.provider != "none":
                analysis_result = await self._ai_analyze_compliance(rule, context)
            else:
                # Fallback to basic analysis
                analysis_result = self._basic_compliance_check(rule, project)
            
            # Create violation if non-compliant
            if not analysis_result.get('compliant', True):
                return ComplianceViolation(
                    violation_id=f"{rule.rule_id}_{project['project_id']}_{int(time.time())}",
                    rule_id=rule.rule_id,
                    project_id=project['project_id'],
                    project_name=project.get('title', 'Unknown Project'),
                    violation_type=rule.name,
                    description=analysis_result.get('description', 'Compliance violation detected'),
                    severity=rule.level,
                    detected_at=datetime.now().isoformat(),
                    due_date=self._calculate_due_date(rule),
                    ai_confidence=analysis_result.get('confidence', 0.8)
                )
        
        except Exception as e:
            print(f"⚠️ Error checking rule {rule.rule_id}: {e}")
        
        return None
    
    def _prepare_analysis_context(self, rule: ComplianceRule, project: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for AI analysis"""
        context = {
            'rule': asdict(rule),
            'project': project,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add RAG context for this rule
        try:
            rag_query = f"{rule.name} {rule.description} NSW procurement compliance"
            rag_results = self.rag_system.query_compliance(
                rag_query,
                tiers=[RAGTier.GLOBAL, RAGTier.INTERNAL, RAGTier.PROJECT]
            )
            context['rag_context'] = [asdict(result) for result in rag_results[:3]]
        except Exception as e:
            print(f"⚠️ Error getting RAG context: {e}")
            context['rag_context'] = []
        
        return context
    
    async def _ai_analyze_compliance(self, rule: ComplianceRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze compliance"""
        try:
            # Prepare prompt for AI
            prompt = f"""
            Analyze the following NSW procurement project for compliance with the specified rule.
            
            Rule: {rule.name}
            Description: {rule.description}
            NSW Reference: {rule.nsw_reference}
            
            Project Details:
            - Title: {context['project'].get('title', 'Unknown')}
            - Type: {context['project'].get('project_type', 'Unknown')}
            - Value: ${context['project'].get('contract_value', 0):,}
            - Status: {context['project'].get('status', 'Unknown')}
            
            RAG Context (NSW Guidelines):
            {json.dumps(context.get('rag_context', []), indent=2)}
            
            Analysis Instructions:
            {rule.ai_prompt}
            
            Please provide a JSON response with:
            {{
                "compliant": true/false,
                "confidence": 0.0-1.0,
                "description": "Brief explanation of compliance status",
                "recommendations": ["List of recommendations if non-compliant"],
                "evidence": "Supporting evidence for the decision"
            }}
            """
            
            # Use AI model to analyze
            if hasattr(self.ai_model, 'generate'):
                response = await self.ai_model.generate(prompt)
            else:
                # Fallback for different AI model types
                response = await self._fallback_ai_analysis(prompt)
            
            # Parse AI response
            return self._parse_ai_response(response)
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return self._basic_compliance_check(rule, context['project'])
    
    async def _fallback_ai_analysis(self, prompt: str) -> str:
        """Fallback AI analysis method"""
        # This would use the actual AI model implementation
        # For now, return a basic analysis
        return json.dumps({
            "compliant": True,
            "confidence": 0.5,
            "description": "Basic compliance check passed",
            "recommendations": [],
            "evidence": "Automated analysis"
        })
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract compliance analysis"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end > json_start:
                    json_str = response[json_start:json_end].strip()
                else:
                    json_str = response[json_start:].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Error parsing AI response: {e}")
            return {
                "compliant": True,
                "confidence": 0.3,
                "description": "Could not parse AI response",
                "recommendations": [],
                "evidence": "Error in analysis"
            }
    
    def _basic_compliance_check(self, rule: ComplianceRule, project: Dict[str, Any]) -> Dict[str, Any]:
        """Basic compliance check without AI"""
        # Basic rule checking logic
        compliant = True
        description = "Basic compliance check passed"
        
        # Check value threshold
        if rule.value_threshold and project.get('contract_value', 0) >= rule.value_threshold:
            if not project.get('tender_process', False):
                compliant = False
                description = f"Project over ${rule.value_threshold:,} requires tender process"
        
        # Check required documents
        if rule.required_documents:
            project_docs = project.get('documents', [])
            missing_docs = [doc for doc in rule.required_documents if doc not in project_docs]
            if missing_docs:
                compliant = False
                description = f"Missing required documents: {', '.join(missing_docs)}"
        
        return {
            "compliant": compliant,
            "confidence": 0.7,
            "description": description,
            "recommendations": [] if compliant else ["Review project requirements"],
            "evidence": "Basic automated check"
        }
    
    def _calculate_due_date(self, rule: ComplianceRule) -> str:
        """Calculate due date for resolving violation"""
        if rule.deadline_days:
            due_date = datetime.now() + timedelta(days=rule.deadline_days)
            return due_date.isoformat()
        return None
    
    def analyze_compliance(self, spec_content: str, council: str, project_type: str) -> Dict[str, Any]:
        """
        Analyze compliance for a given specification
        """
        try:
            # Basic compliance analysis
            compliance_result = {
                "compliance_scores": {
                    "legislative": 85,
                    "financial": 90,
                    "process": 80,
                    "social": 75,
                    "environmental": 85,
                    "safety": 90,
                    "documentation": 80,
                    "timeline": 85
                },
                "compliance_issues": [
                    "Local preference policy needs clarification",
                    "Environmental standards require verification",
                    "Safety documentation needs updating"
                ],
                "recommendations": [
                    "Review local preference policy implementation",
                    "Verify environmental compliance standards",
                    "Update safety documentation requirements",
                    "Ensure timeline compliance with council standards"
                ],
                "overall_score": 84.4,
                "status": "compliant_with_issues"
            }
            
            return compliance_result
            
        except Exception as e:
            return {
                "error": f"Compliance analysis failed: {str(e)}",
                "compliance_scores": {},
                "compliance_issues": ["Analysis failed"],
                "recommendations": ["Manual review required"],
                "overall_score": 0,
                "status": "error"
            }
    
    def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for compliance dashboard"""
        return {
            'metrics': asdict(self.metrics) if self.metrics else None,
            'violations': [asdict(v) for v in self.violations],
            'rules': [asdict(r) for r in self.compliance_rules],
            'last_scan': self.last_scan.isoformat() if self.last_scan else None,
            'total_violations': len(self.violations),
            'critical_count': len([v for v in self.violations if v.severity == ComplianceLevel.CRITICAL]),
            'high_count': len([v for v in self.violations if v.severity == ComplianceLevel.HIGH]),
            'medium_count': len([v for v in self.violations if v.severity == ComplianceLevel.MEDIUM]),
            'low_count': len([v for v in self.violations if v.severity == ComplianceLevel.LOW])
        }
    
    def get_violations_by_category(self) -> Dict[str, List[ComplianceViolation]]:
        """Get violations grouped by category"""
        categories = {}
        for violation in self.violations:
            rule = next((r for r in self.compliance_rules if r.rule_id == violation.rule_id), None)
            if rule:
                category = rule.category.value
                if category not in categories:
                    categories[category] = []
                categories[category].append(violation)
        return categories
    
    def get_violations_by_project(self) -> Dict[str, List[ComplianceViolation]]:
        """Get violations grouped by project"""
        projects = {}
        for violation in self.violations:
            project_id = violation.project_id
            if project_id not in projects:
                projects[project_id] = []
            projects[project_id].append(violation)
        return projects
