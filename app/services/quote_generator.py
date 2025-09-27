#!/usr/bin/env python3
"""
AI Quote Generator Service
AI-powered quotation generation system for suppliers and contractors
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

class QuoteType(Enum):
    """Types of quotes"""
    TENDER_RESPONSE = "tender_response"
    QUOTATION = "quotation"
    PROPOSAL = "proposal"
    ESTIMATE = "estimate"
    BUDGET_QUOTE = "budget_quote"

class QuoteStatus(Enum):
    """Quote status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class QuoteCategory(Enum):
    """Quote categories"""
    CONSTRUCTION = "construction"
    MAINTENANCE = "maintenance"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    CONSULTING = "consulting"
    TECHNOLOGY = "technology"
    LANDSCAPING = "landscaping"
    CLEANING = "cleaning"
    SECURITY = "security"
    TRANSPORT = "transport"

@dataclass
class QuoteItem:
    """Quote line item"""
    item_id: str
    description: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    category: str
    specifications: List[str]
    notes: str

@dataclass
class Quote:
    """Quote data structure"""
    quote_id: str
    title: str
    description: str
    quote_type: QuoteType
    category: QuoteCategory
    status: QuoteStatus
    client_name: str
    client_email: str
    client_phone: str
    project_reference: str
    quote_date: str
    valid_until: str
    items: List[QuoteItem]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    terms_conditions: List[str]
    payment_terms: str
    delivery_terms: str
    warranty_terms: str
    special_requirements: List[str]
    attachments: List[str]
    metadata: Dict[str, Any]
    created_date: str
    updated_date: str

class AIQuoteGenerator:
    """AI-powered quote generation service"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.quotes_dir = data_dir / "quotes"
        self.quotes_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI model
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Load existing quotes
        self.quotes = self._load_quotes()
    
    def _load_quotes(self) -> List[Quote]:
        """Load quotes from storage"""
        quotes = []
        
        if self.quotes_dir.exists():
            for quote_file in self.quotes_dir.glob("*.json"):
                try:
                    with open(quote_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Convert items back to QuoteItem objects
                        items = [QuoteItem(**item) for item in data.get('items', [])]
                        data['items'] = items
                        
                        # Convert string enums back to enum objects
                        if 'quote_type' in data and isinstance(data['quote_type'], str):
                            data['quote_type'] = QuoteType(data['quote_type'])
                        if 'category' in data and isinstance(data['category'], str):
                            data['category'] = QuoteCategory(data['category'])
                        if 'status' in data and isinstance(data['status'], str):
                            data['status'] = QuoteStatus(data['status'])
                        
                        quotes.append(Quote(**data))
                except Exception as e:
                    print(f"⚠️ Error loading quote {quote_file}: {e}")
        
        return quotes
    
    def _save_quote(self, quote: Quote):
        """Save quote to storage"""
        try:
            # Convert to serializable format
            quote_data = {
                "quote_id": quote.quote_id,
                "title": quote.title,
                "description": quote.description,
                "quote_type": quote.quote_type.value,
                "category": quote.category.value,
                "status": quote.status.value,
                "client_name": quote.client_name,
                "client_email": quote.client_email,
                "client_phone": quote.client_phone,
                "project_reference": quote.project_reference,
                "quote_date": quote.quote_date,
                "valid_until": quote.valid_until,
                "items": [asdict(item) for item in quote.items],
                "subtotal": quote.subtotal,
                "tax_rate": quote.tax_rate,
                "tax_amount": quote.tax_amount,
                "total_amount": quote.total_amount,
                "terms_conditions": quote.terms_conditions,
                "payment_terms": quote.payment_terms,
                "delivery_terms": quote.delivery_terms,
                "warranty_terms": quote.warranty_terms,
                "special_requirements": quote.special_requirements,
                "attachments": quote.attachments,
                "metadata": quote.metadata,
                "created_date": quote.created_date,
                "updated_date": quote.updated_date
            }
            
            quote_file = self.quotes_dir / f"{quote.quote_id}.json"
            with open(quote_file, 'w', encoding='utf-8') as f:
                json.dump(quote_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving quote: {e}")
    
    def generate_quote(self,
                     title: str,
                     description: str,
                     quote_type: QuoteType,
                     category: QuoteCategory,
                     client_name: str,
                     client_email: str,
                     client_phone: str = "",
                     project_reference: str = "",
                     requirements: List[str] = None,
                     budget_range: Tuple[float, float] = None,
                     timeline_days: int = None) -> Quote:
        """Generate AI-powered quote"""
        
        try:
            # Generate quote using AI
            ai_response = self._generate_quote_with_ai(
                title, description, quote_type, category, 
                requirements or [], budget_range, timeline_days
            )
            
            # Create quote ID
            quote_id = hashlib.md5(f"{title}_{client_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Calculate totals
            subtotal = sum(item.total_price for item in ai_response['items'])
            tax_rate = 0.10  # 10% GST
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            # Create quote
            quote = Quote(
                quote_id=quote_id,
                title=title,
                description=description,
                quote_type=quote_type,
                category=category,
                status=QuoteStatus.DRAFT,
                client_name=client_name,
                client_email=client_email,
                client_phone=client_phone,
                project_reference=project_reference,
                quote_date=datetime.now().strftime("%Y-%m-%d"),
                valid_until=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                items=ai_response['items'],
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total_amount,
                terms_conditions=ai_response['terms_conditions'],
                payment_terms=ai_response['payment_terms'],
                delivery_terms=ai_response['delivery_terms'],
                warranty_terms=ai_response['warranty_terms'],
                special_requirements=ai_response['special_requirements'],
                attachments=[],
                metadata={
                    "ai_generated": True,
                    "generation_confidence": ai_response['confidence'],
                    "budget_range": budget_range,
                    "timeline_days": timeline_days
                },
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat()
            )
            
            # Save quote
            self._save_quote(quote)
            self.quotes.append(quote)
            
            return quote
            
        except Exception as e:
            print(f"⚠️ Error generating quote: {e}")
            raise
    
    def _generate_quote_with_ai(self,
                               title: str,
                               description: str,
                               quote_type: QuoteType,
                               category: QuoteCategory,
                               requirements: List[str],
                               budget_range: Optional[Tuple[float, float]],
                               timeline_days: Optional[int]) -> Dict[str, Any]:
        """Generate quote content using AI"""
        
        try:
            prompt = f"""
            Generate a professional quote for a {category.value} project.
            
            PROJECT DETAILS:
            Title: {title}
            Description: {description}
            Quote Type: {quote_type.value}
            Category: {category.value}
            Requirements: {', '.join(requirements) if requirements else 'Standard requirements'}
            Budget Range: ${budget_range[0]:,.0f} - ${budget_range[1]:,.0f} if budget_range else 'Not specified'
            Timeline: {timeline_days} days if timeline_days else 'Standard timeline'
            
            Generate a detailed quote with:
            1. Line items with descriptions, quantities, units, and prices
            2. Professional terms and conditions
            3. Payment terms
            4. Delivery terms
            5. Warranty terms
            6. Special requirements
            
            Return in JSON format:
            {{
                "items": [
                    {{
                        "item_id": "item_1",
                        "description": "Item description",
                        "quantity": 1.0,
                        "unit": "each",
                        "unit_price": 1000.0,
                        "total_price": 1000.0,
                        "category": "Labor",
                        "specifications": ["spec1", "spec2"],
                        "notes": "Additional notes"
                    }}
                ],
                "terms_conditions": ["term1", "term2"],
                "payment_terms": "Payment terms text",
                "delivery_terms": "Delivery terms text",
                "warranty_terms": "Warranty terms text",
                "special_requirements": ["req1", "req2"],
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
                
                result = json.loads(json_text)
                
                # Convert items to QuoteItem objects
                items = []
                for item_data in result.get('items', []):
                    items.append(QuoteItem(
                        item_id=item_data.get('item_id', ''),
                        description=item_data.get('description', ''),
                        quantity=float(item_data.get('quantity', 1.0)),
                        unit=item_data.get('unit', 'each'),
                        unit_price=float(item_data.get('unit_price', 0.0)),
                        total_price=float(item_data.get('total_price', 0.0)),
                        category=item_data.get('category', 'General'),
                        specifications=item_data.get('specifications', []),
                        notes=item_data.get('notes', '')
                    ))
                
                result['items'] = items
                return result
                
            except Exception as e:
                print(f"⚠️ Error parsing AI response: {e}")
                return self._fallback_quote_generation(category, budget_range)
                
        except Exception as e:
            print(f"⚠️ Error generating quote with AI: {e}")
            return self._fallback_quote_generation(category, budget_range)
    
    def _fallback_quote_generation(self, category: QuoteCategory, budget_range: Optional[Tuple[float, float]]) -> Dict[str, Any]:
        """Fallback quote generation when AI fails"""
        
        # Default items based on category
        default_items = {
            QuoteCategory.CONSTRUCTION: [
                {"description": "Labor costs", "quantity": 1.0, "unit": "project", "unit_price": 5000.0},
                {"description": "Materials", "quantity": 1.0, "unit": "project", "unit_price": 3000.0},
                {"description": "Equipment rental", "quantity": 1.0, "unit": "project", "unit_price": 1000.0}
            ],
            QuoteCategory.MAINTENANCE: [
                {"description": "Maintenance labor", "quantity": 1.0, "unit": "hour", "unit_price": 80.0},
                {"description": "Replacement parts", "quantity": 1.0, "unit": "lot", "unit_price": 200.0}
            ],
            QuoteCategory.SERVICES: [
                {"description": "Service delivery", "quantity": 1.0, "unit": "service", "unit_price": 500.0},
                {"description": "Consultation", "quantity": 1.0, "unit": "hour", "unit_price": 150.0}
            ]
        }
        
        items_data = default_items.get(category, default_items[QuoteCategory.SERVICES])
        
        # Create QuoteItem objects
        items = []
        for i, item_data in enumerate(items_data):
            total_price = item_data['quantity'] * item_data['unit_price']
            items.append(QuoteItem(
                item_id=f"item_{i+1}",
                description=item_data['description'],
                quantity=item_data['quantity'],
                unit=item_data['unit'],
                unit_price=item_data['unit_price'],
                total_price=total_price,
                category="General",
                specifications=[],
                notes="Standard service"
            ))
        
        return {
            "items": items,
            "terms_conditions": [
                "All prices are exclusive of GST",
                "Payment due within 30 days",
                "Work to be completed as per specifications"
            ],
            "payment_terms": "Payment due within 30 days of invoice date",
            "delivery_terms": "Delivery as per agreed schedule",
            "warranty_terms": "12 months warranty on workmanship",
            "special_requirements": ["Compliance with all relevant standards"],
            "confidence": 0.6
        }
    
    def get_quotes_by_status(self, status: QuoteStatus) -> List[Quote]:
        """Get quotes by status"""
        return [q for q in self.quotes if q.status == status]
    
    def get_quotes_by_category(self, category: QuoteCategory) -> List[Quote]:
        """Get quotes by category"""
        return [q for q in self.quotes if q.category == category]
    
    def get_quote_statistics(self) -> Dict[str, Any]:
        """Get quote statistics"""
        if not self.quotes:
            return {
                "total_quotes": 0,
                "total_value": 0,
                "average_value": 0,
                "status_breakdown": {},
                "category_breakdown": {}
            }
        
        total_value = sum(q.total_amount for q in self.quotes)
        average_value = total_value / len(self.quotes)
        
        # Status breakdown
        status_breakdown = {}
        for quote in self.quotes:
            status = quote.status.value
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Category breakdown
        category_breakdown = {}
        for quote in self.quotes:
            category = quote.category.value
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        return {
            "total_quotes": len(self.quotes),
            "total_value": total_value,
            "average_value": average_value,
            "status_breakdown": status_breakdown,
            "category_breakdown": category_breakdown
        }
    
    def update_quote_status(self, quote_id: str, new_status: QuoteStatus) -> bool:
        """Update quote status"""
        for quote in self.quotes:
            if quote.quote_id == quote_id:
                quote.status = new_status
                quote.updated_date = datetime.now().isoformat()
                self._save_quote(quote)
                return True
        return False
    
    def get_quote_by_id(self, quote_id: str) -> Optional[Quote]:
        """Get quote by ID"""
        for quote in self.quotes:
            if quote.quote_id == quote_id:
                return quote
        return None
