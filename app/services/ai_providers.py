"""
Multi-Provider AI Model Integration Service
Supports OpenAI, Anthropic, Google AI, Ollama, and Cursor API integration
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CURSOR = "cursor"
    HUGGINGFACE = "huggingface"

@dataclass
class ModelConfig:
    provider: AIProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30

class AIProviderManager:
    """Centralized AI provider management with fallback support"""
    
    def __init__(self):
        self.providers = {}
        self.local_ai = None
        self._initialize_providers()
        self._initialize_local_ai()
    
    def _initialize_providers(self):
        """Initialize all available AI providers from environment variables"""
        
        # OpenAI Configuration
        if os.getenv("OPENAI_API_KEY"):
            self.providers[AIProvider.OPENAI] = ModelConfig(
                provider=AIProvider.OPENAI,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
        
        # Anthropic Configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers[AIProvider.ANTHROPIC] = ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            )
        
        # Google AI Configuration
        if os.getenv("GOOGLE_AI_API_KEY"):
            self.providers[AIProvider.GOOGLE] = ModelConfig(
                provider=AIProvider.GOOGLE,
                model_name=os.getenv("GOOGLE_MODEL", "gemini-pro"),
                api_key=os.getenv("GOOGLE_AI_API_KEY"),
                base_url=os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
            )
        
        # Ollama Configuration (Local)
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.providers[AIProvider.OLLAMA] = ModelConfig(
            provider=AIProvider.OLLAMA,
            model_name=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=ollama_url
        )
        
        # Cursor API Configuration
        if os.getenv("CURSOR_API_KEY"):
            self.providers[AIProvider.CURSOR] = ModelConfig(
                provider=AIProvider.CURSOR,
                model_name=os.getenv("CURSOR_MODEL", "claude-3-sonnet"),
                api_key=os.getenv("CURSOR_API_KEY"),
                base_url=os.getenv("CURSOR_BASE_URL", "https://api.cursor.com/v1")
            )
        
        # Hugging Face Configuration
        if os.getenv("HUGGINGFACE_API_KEY"):
            self.providers[AIProvider.HUGGINGFACE] = ModelConfig(
                provider=AIProvider.HUGGINGFACE,
                model_name=os.getenv("HUGGINGFACE_MODEL", "microsoft/DialoGPT-medium"),
                api_key=os.getenv("HUGGINGFACE_API_KEY"),
                base_url=os.getenv("HUGGINGFACE_BASE_URL", "https://api-inference.huggingface.co")
            )
    
    def _initialize_local_ai(self):
        """Initialize local AI fallback"""
        try:
            from app.services.local_ai import local_ai
            self.local_ai = local_ai
            logger.info("Local AI fallback initialized")
        except Exception as e:
            logger.warning(f"Local AI not available: {e}")
            self.local_ai = None
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available AI providers"""
        return list(self.providers.keys())
    
    def get_provider_config(self, provider: AIProvider) -> Optional[ModelConfig]:
        """Get configuration for a specific provider"""
        return self.providers.get(provider)
    
    async def generate_response(
        self, 
        prompt: str, 
        provider: Optional[AIProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate AI response using specified or best available provider"""
        
        if provider and provider in self.providers:
            return await self._call_provider(provider, prompt, **kwargs)
        
        # Fallback to best available provider
        preferred_order = [
            AIProvider.OPENAI,
            AIProvider.ANTHROPIC, 
            AIProvider.GOOGLE,
            AIProvider.OLLAMA,
            AIProvider.CURSOR,
            AIProvider.HUGGINGFACE
        ]
        
        for preferred_provider in preferred_order:
            if preferred_provider in self.providers:
                try:
                    return await self._call_provider(preferred_provider, prompt, **kwargs)
                except Exception as e:
                    logger.warning(f"Provider {preferred_provider.value} failed: {e}")
                    continue
        
        # Final fallback to local AI
        if self.local_ai and self.local_ai.is_available():
            logger.info("Falling back to local AI")
            return await self.local_ai.generate_response(prompt, **kwargs)
        
        raise Exception("No available AI providers (including local fallback)")
    
    async def _call_provider(self, provider: AIProvider, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call specific AI provider"""
        
        config = self.providers[provider]
        
        if provider == AIProvider.OPENAI:
            return await self._call_openai(config, prompt, **kwargs)
        elif provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(config, prompt, **kwargs)
        elif provider == AIProvider.GOOGLE:
            return await self._call_google(config, prompt, **kwargs)
        elif provider == AIProvider.OLLAMA:
            return await self._call_ollama(config, prompt, **kwargs)
        elif provider == AIProvider.CURSOR:
            return await self._call_cursor(config, prompt, **kwargs)
        elif provider == AIProvider.HUGGINGFACE:
            return await self._call_huggingface(config, prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _call_openai(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call OpenAI API"""
        import openai
        
        client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
        response = await client.chat.completions.create(
            model=config.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", config.max_tokens),
            temperature=kwargs.get("temperature", config.temperature),
            timeout=config.timeout
        )
        
        return {
            "provider": "openai",
            "model": config.model_name,
            "response": response.choices[0].message.content,
            "usage": response.usage.dict() if response.usage else None,
            "cost": self._calculate_openai_cost(response.usage, config.model_name)
        }
    
    async def _call_anthropic(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Anthropic Claude API"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
        response = await client.messages.create(
            model=config.model_name,
            max_tokens=kwargs.get("max_tokens", config.max_tokens),
            temperature=kwargs.get("temperature", config.temperature),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "provider": "anthropic",
            "model": config.model_name,
            "response": response.content[0].text,
            "usage": response.usage.dict() if response.usage else None,
            "cost": self._calculate_anthropic_cost(response.usage, config.model_name)
        }
    
    async def _call_google(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Google AI API"""
        import google.generativeai as genai
        
        genai.configure(api_key=config.api_key)
        model = genai.GenerativeModel(config.model_name)
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature)
            )
        )
        
        return {
            "provider": "google",
            "model": config.model_name,
            "response": response.text,
            "usage": None,  # Google doesn't provide detailed usage info
            "cost": 0.0  # Free tier available
        }
    
    async def _call_ollama(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Ollama local API"""
        url = f"{config.base_url}/api/generate"
        
        payload = {
            "model": config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", config.temperature),
                "num_predict": kwargs.get("max_tokens", config.max_tokens)
            }
        }
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=config.timeout,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "provider": "ollama",
            "model": config.model_name,
            "response": result.get("response", ""),
            "usage": None,
            "cost": 0.0  # Local, no cost
        }
    
    async def _call_cursor(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Cursor API (Code Analysis and AI Assistance)"""
        
        # Note: Cursor API is primarily for code tracking, but we can use it for AI assistance
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Cursor API endpoint for AI assistance
        url = f"{config.base_url}/ai/assist"
        
        payload = {
            "prompt": prompt,
            "model": config.model_name,
            "max_tokens": kwargs.get("max_tokens", config.max_tokens),
            "temperature": kwargs.get("temperature", config.temperature)
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "provider": "cursor",
                "model": config.model_name,
                "response": result.get("response", ""),
                "usage": result.get("usage"),
                "cost": result.get("cost", 0.0)
            }
        else:
            # Fallback: Use Cursor's code analysis capabilities
            return await self._call_cursor_code_analysis(config, prompt)
    
    async def _call_cursor_code_analysis(self, config: ModelConfig, prompt: str) -> Dict[str, Any]:
        """Use Cursor's code analysis API as fallback"""
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use Cursor's code tracking API for analysis
        url = f"{config.base_url}/code/analyze"
        
        payload = {
            "code": prompt,
            "analysis_type": "general"
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "provider": "cursor",
                "model": config.model_name,
                "response": result.get("analysis", "Analysis completed"),
                "usage": None,
                "cost": 0.0
            }
        else:
            raise Exception(f"Cursor API error: {response.status_code}")
    
    async def _call_huggingface(self, config: ModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Hugging Face Inference API"""
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{config.base_url}/models/{config.model_name}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": kwargs.get("max_tokens", config.max_tokens),
                "temperature": kwargs.get("temperature", config.temperature)
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            "provider": "huggingface",
            "model": config.model_name,
            "response": result[0].get("generated_text", "") if result else "",
            "usage": None,
            "cost": 0.0  # Free tier available
        }
    
    def _calculate_openai_cost(self, usage, model_name: str) -> float:
        """Calculate OpenAI API cost"""
        if not usage:
            return 0.0
        
        # OpenAI pricing (as of 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }
        
        model_pricing = pricing.get(model_name, pricing["gpt-3.5-turbo"])
        
        input_cost = (usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def _calculate_anthropic_cost(self, usage, model_name: str) -> float:
        """Calculate Anthropic API cost"""
        if not usage:
            return 0.0
        
        # Anthropic pricing (as of 2024)
        pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
        }
        
        model_pricing = pricing.get(model_name, pricing["claude-3-sonnet-20240229"])
        
        input_cost = (usage.input_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost

# Global instance
ai_manager = AIProviderManager()

# Convenience functions
async def generate_ai_response(prompt: str, provider: Optional[AIProvider] = None, **kwargs) -> Dict[str, Any]:
    """Generate AI response using the best available provider"""
    return await ai_manager.generate_response(prompt, provider, **kwargs)

def get_available_ai_providers() -> List[AIProvider]:
    """Get list of available AI providers"""
    return ai_manager.get_available_providers()

def get_provider_info(provider: AIProvider) -> Dict[str, Any]:
    """Get information about a specific provider"""
    config = ai_manager.get_provider_config(provider)
    if not config:
        return {"available": False}
    
    return {
        "available": True,
        "provider": provider.value,
        "model": config.model_name,
        "base_url": config.base_url,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature
    }
