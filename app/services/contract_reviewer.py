"""
AI-Powered Contract Review Service
Comprehensive contract analysis against risks, rules, governance, and compliance
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
from app.services.three_tier_rag_system import ThreeTierRAGSystem
from app.services.ai_model_detector import AIModelDetector


@dataclass
class ContractRisk:
    """Contract risk assessment"""
    risk_type: str
    severity: str  # Low, Medium, High, Critical
    description: str
    recommendation: str
    compliance_impact: str


@dataclass
class ComplianceCheck:
    """Compliance check result"""
    category: str
    status: str  # Compliant, Non-Compliant, Requires Review
    description: str
    evidence: str
    remediation: str


@dataclass
class GovernanceAnalysis:
    """Governance analysis result"""
    aspect: str
    assessment: str
    findings: str
    recommendations: str


@dataclass
class ContractReviewResult:
    """Complete contract review result"""
    contract_id: str
    review_date: str
    ai_model_used: str
    overall_risk_score: str
    compliance_score: str
    governance_score: str
    risks: List[ContractRisk]
    compliance_checks: List[ComplianceCheck]
    governance_analysis: List[GovernanceAnalysis]
    executive_summary: str
    critical_issues: List[str]
    recommendations: List[str]
    next_steps: List[str]


class ContractReviewer:
    """AI-powered contract review system"""
    
    def __init__(self):
        """Initialize the contract reviewer"""
        from pathlib import Path
        self.rag_system = ThreeTierRAGSystem(Path("data"))
        self.ai_detector = AIModelDetector()
        
    def review_contract(self, contract_content: str, contract_type: str = "General", 
                       ai_model: Optional[Any] = None) -> ContractReviewResult:
        """
        Perform comprehensive AI-powered contract review
        
        Args:
            contract_content: The contract text to review
            contract_type: Type of contract (Construction, Services, Supply, etc.)
            ai_model: AI model to use for analysis
            
        Returns:
            ContractReviewResult with comprehensive analysis
        """
        
        # Use provided model or force Gemini if available
        if ai_model is None:
            # Try to get Gemini model first, fallback to recommended
            gemini_model = self._get_gemini_model()
            if gemini_model:
                ai_model = gemini_model
            else:
                ai_model = self.ai_detector.get_recommended_model()
        
        contract_id = f"CONTRACT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get RAG context for compliance and governance
        rag_context = self._get_rag_context(contract_type)
        
        # Perform AI analysis
        ai_analysis = self._analyze_contract_with_ai(
            contract_content, contract_type, rag_context, ai_model
        )
        
        # Structure the results
        result = ContractReviewResult(
            contract_id=contract_id,
            review_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ai_model_used=ai_model.model_name,
            overall_risk_score=ai_analysis.get('overall_risk_score', 'Medium'),
            compliance_score=ai_analysis.get('compliance_score', 'Requires Review'),
            governance_score=ai_analysis.get('governance_score', 'Requires Review'),
            risks=self._parse_risks(ai_analysis.get('risks', [])),
            compliance_checks=self._parse_compliance_checks(ai_analysis.get('compliance_checks', [])),
            governance_analysis=self._parse_governance_analysis(ai_analysis.get('governance_analysis', [])),
            executive_summary=ai_analysis.get('executive_summary', ''),
            critical_issues=ai_analysis.get('critical_issues', []),
            recommendations=ai_analysis.get('recommendations', []),
            next_steps=ai_analysis.get('next_steps', [])
        )
        
        return result
    
    def _get_gemini_model(self):
        """Get Gemini model configuration if available"""
        try:
            from app.config import settings
            if settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY) > 10:
                from app.services.ai_model_detector import AIModelConfig, ModelType
                return AIModelConfig(
                    model_type=ModelType.CLOUD_API,
                    model_name=settings.GEMINI_MODEL,
                    provider="Google",
                    max_tokens=8192,
                    temperature=0.3,
                    description=f"Google {settings.GEMINI_MODEL} - Cloud API",
                    performance_score=9.0,
                    cost_per_token=0.000125
                )
        except Exception:
            pass
        return None
    
    def _get_rag_context(self, contract_type: str) -> str:
        """Get relevant RAG context for contract review"""
        try:
            # Query RAG system for relevant compliance and governance information
            queries = [
                f"contract compliance requirements for {contract_type}",
                f"risk management guidelines for {contract_type} contracts",
                f"governance standards for {contract_type} procurement",
                "supplier evaluation criteria and standards",
                "contract termination and dispute resolution procedures",
                "insurance and liability requirements",
                "environmental and sustainability compliance",
                "work health safety requirements"
            ]
            
            rag_content = []
            for query in queries:
                try:
                    result = self.rag_system.query_compliance(query)
                    if result:
                        rag_content.append(result)
                except:
                    continue
            
            return "\n\n".join(rag_content) if rag_content else ""
            
        except Exception as e:
            st.warning(f"Could not retrieve RAG context: {e}")
            return ""
    
    def _analyze_contract_with_ai(self, contract_content: str, contract_type: str, 
                                rag_context: str, ai_model: Any) -> Dict[str, Any]:
        """Analyze contract using AI with comprehensive prompts"""
        
        # Create comprehensive analysis prompt
        prompt = f"""
You are an expert contract reviewer and risk analyst. Analyze the following contract against comprehensive risk, compliance, and governance standards.

CONTRACT TYPE: {contract_type}
CONTRACT CONTENT:
{contract_content[:8000]}  # Limit content for token management

RELEVANT REGULATIONS AND STANDARDS:
{rag_context}

Please provide a comprehensive analysis in JSON format with the following structure:

{{
    "overall_risk_score": "Low/Medium/High/Critical",
    "compliance_score": "Compliant/Non-Compliant/Requires Review",
    "governance_score": "Good/Adequate/Poor/Requires Review",
    "executive_summary": "Brief executive summary of key findings",
    "critical_issues": ["List of critical issues that need immediate attention"],
    "risks": [
        {{
            "risk_type": "Risk category (e.g., Legal, Financial, Operational, Compliance)",
            "severity": "Low/Medium/High/Critical",
            "description": "Detailed description of the risk",
            "recommendation": "Specific recommendation to mitigate risk",
            "compliance_impact": "Impact on compliance requirements"
        }}
    ],
    "compliance_checks": [
        {{
            "category": "Compliance area (e.g., WHS, Environmental, Legal, Financial)",
            "status": "Compliant/Non-Compliant/Requires Review",
            "description": "Description of compliance status",
            "evidence": "Evidence found in contract",
            "remediation": "Required actions to achieve compliance"
        }}
    ],
    "governance_analysis": [
        {{
            "aspect": "Governance aspect (e.g., Transparency, Accountability, Oversight)",
            "assessment": "Assessment of current state",
            "findings": "Specific findings",
            "recommendations": "Recommendations for improvement"
        }}
    ],
    "recommendations": ["List of specific recommendations"],
    "next_steps": ["List of immediate next steps"]
}}

Focus on:
1. Legal and regulatory compliance
2. Financial risks and exposure
3. Operational risks
4. Governance and accountability
5. Environmental and sustainability compliance
6. Work health and safety requirements
7. Supplier capability and reliability
8. Contract termination and dispute resolution
9. Insurance and liability coverage
10. Performance monitoring and KPIs

Be thorough, specific, and actionable in your analysis.
"""
        
        # Call AI model directly using Gemini API
        try:
            import google.generativeai as genai
            from app.config import settings
            
            # Configure Gemini API
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            # Create the model
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            # Prepare the full prompt with contract content
            full_prompt = f"{prompt}\n\nContract Content:\n{contract_content[:4000]}..."
            
            # Generate response
            response_obj = model.generate_content(full_prompt)
            response = response_obj.text
            
            # AI analysis completed successfully
            
        except Exception as e:
            print(f"❌ AI analysis failed: {str(e)}")
            # Fallback to basic analysis
            response = self._get_basic_analysis(contract_content, contract_type)
            return response
        
        if response:
            try:
                # Clean the response to extract JSON
                if "```json" in response:
                    # Extract JSON from markdown code block
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    if json_end > json_start:
                        json_str = response[json_start:json_end].strip()
                    else:
                        json_str = response[json_start:].strip()
                else:
                    json_str = response.strip()
                
                parsed_response = json.loads(json_str)
                return parsed_response
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, return structured basic analysis
                return self._get_basic_analysis(contract_content, contract_type)
        else:
            return self._get_basic_analysis(contract_content, contract_type)
    
    def _call_ollama(self, model_name: str, prompt: str) -> str:
        """Call Ollama API for contract analysis"""
        try:
            import requests
            
            # Check if model exists first
            try:
                models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if models_response.status_code == 200:
                    available_models = [model.get("name", "") for model in models_response.json().get("models", [])]
                    if model_name not in available_models:
                        st.error(f"❌ Model '{model_name}' not found in Ollama!")
                        st.info("Available models:")
                        for model in available_models:
                            st.code(f"• {model}")
                        return None
            except:
                st.warning("⚠️ Could not check available models")
            
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "top_p": 0.9,
                    "max_tokens": 4096  # Larger context for comprehensive analysis
                }
            }
            
            # Show progress for long-running requests
            with st.spinner(f"🔍 AI is analyzing contract with '{model_name}'... This comprehensive analysis may take several minutes."):
                response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            elif response.status_code == 404:
                st.warning(f"Model '{model_name}' not found in Ollama. Available models:")
                return None
            else:
                st.warning(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error(f"🔌 Cannot connect to Ollama. Make sure Ollama is running:")
            st.code("ollama serve")
            return None
        except Exception as e:
            st.warning(f"Contract analysis failed: {e}")
            return None
    
    def _get_basic_analysis(self, contract_content: str, contract_type: str) -> Dict[str, Any]:
        """Fallback basic analysis when AI is not available"""
        return {
            "overall_risk_score": "Medium",
            "compliance_score": "Requires Review",
            "governance_score": "Requires Review",
            "executive_summary": f"Basic analysis of {contract_type} contract. AI analysis not available - manual review recommended.",
            "critical_issues": [
                "Manual review required - AI analysis not available",
                "Verify compliance with relevant regulations",
                "Assess financial and operational risks"
            ],
            "risks": [
                {
                    "risk_type": "General",
                    "severity": "Medium",
                    "description": "Contract requires comprehensive manual review",
                    "recommendation": "Engage legal and compliance experts for detailed analysis",
                    "compliance_impact": "Compliance status unknown - verification required"
                }
            ],
            "compliance_checks": [
                {
                    "category": "General Compliance",
                    "status": "Requires Review",
                    "description": "Manual compliance verification required",
                    "evidence": "AI analysis not available",
                    "remediation": "Conduct manual compliance review"
                }
            ],
            "governance_analysis": [
                {
                    "aspect": "Governance Review",
                    "assessment": "Requires Manual Review",
                    "findings": "AI analysis not available",
                    "recommendations": "Engage governance experts for comprehensive review"
                }
            ],
            "recommendations": [
                "Conduct manual legal review",
                "Verify compliance with relevant regulations",
                "Assess governance and accountability measures",
                "Review risk management provisions"
            ],
            "next_steps": [
                "Engage legal counsel",
                "Schedule compliance review",
                "Conduct risk assessment",
                "Review governance framework"
            ]
        }
    
    def _parse_risks(self, risks_data: List[Dict]) -> List[ContractRisk]:
        """Parse risk data into ContractRisk objects"""
        risks = []
        for risk_data in risks_data:
            risk = ContractRisk(
                risk_type=risk_data.get('risk_type', 'Unknown'),
                severity=risk_data.get('severity', 'Medium'),
                description=risk_data.get('description', ''),
                recommendation=risk_data.get('recommendation', ''),
                compliance_impact=risk_data.get('compliance_impact', '')
            )
            risks.append(risk)
        return risks
    
    def _parse_compliance_checks(self, compliance_data: List[Dict]) -> List[ComplianceCheck]:
        """Parse compliance data into ComplianceCheck objects"""
        checks = []
        for check_data in compliance_data:
            check = ComplianceCheck(
                category=check_data.get('category', 'Unknown'),
                status=check_data.get('status', 'Requires Review'),
                description=check_data.get('description', ''),
                evidence=check_data.get('evidence', ''),
                remediation=check_data.get('remediation', '')
            )
            checks.append(check)
        return checks
    
    def _parse_governance_analysis(self, governance_data: List[Dict]) -> List[GovernanceAnalysis]:
        """Parse governance data into GovernanceAnalysis objects"""
        analysis = []
        for gov_data in governance_data:
            gov = GovernanceAnalysis(
                aspect=gov_data.get('aspect', 'Unknown'),
                assessment=gov_data.get('assessment', 'Requires Review'),
                findings=gov_data.get('findings', ''),
                recommendations=gov_data.get('recommendations', '')
            )
            analysis.append(gov)
        return analysis
    
    def generate_review_report(self, result: ContractReviewResult) -> str:
        """Generate a comprehensive review report"""
        
        report = f"""
# CONTRACT REVIEW REPORT

**Contract ID:** {result.contract_id}  
**Review Date:** {result.review_date}  
**AI Model Used:** {result.ai_model_used}  

## EXECUTIVE SUMMARY

{result.executive_summary}

## RISK ASSESSMENT

**Overall Risk Score:** {result.overall_risk_score}  
**Compliance Score:** {result.compliance_score}  
**Governance Score:** {result.governance_score}  

### Risk Analysis
"""
        
        for risk in result.risks:
            severity_emoji = {
                'Low': '🟢',
                'Medium': '🟡', 
                'High': '🟠',
                'Critical': '🔴'
            }.get(risk.severity, '⚪')
            
            report += f"""
#### {severity_emoji} {risk.risk_type} - {risk.severity}
**Description:** {risk.description}  
**Recommendation:** {risk.recommendation}  
**Compliance Impact:** {risk.compliance_impact}  

"""
        
        report += """
## COMPLIANCE REVIEW

"""
        
        for check in result.compliance_checks:
            status_emoji = {
                'Compliant': '✅',
                'Non-Compliant': '❌',
                'Requires Review': '⚠️'
            }.get(check.status, '❓')
            
            report += f"""
#### {status_emoji} {check.category} - {check.status}
**Description:** {check.description}  
**Evidence:** {check.evidence}  
**Remediation:** {check.remediation}  

"""
        
        report += """
## GOVERNANCE ANALYSIS

"""
        
        for gov in result.governance_analysis:
            report += f"""
#### {gov.aspect} - {gov.assessment}
**Findings:** {gov.findings}  
**Recommendations:** {gov.recommendations}  

"""
        
        report += """
## CRITICAL ISSUES

"""
        for issue in result.critical_issues:
            report += f"• {issue}\n"
        
        report += """
## RECOMMENDATIONS

"""
        for rec in result.recommendations:
            report += f"• {rec}\n"
        
        report += """
## NEXT STEPS

"""
        for step in result.next_steps:
            report += f"• {step}\n"
        
        return report
