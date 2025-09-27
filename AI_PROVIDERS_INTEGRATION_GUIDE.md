# 🤖 AI Providers Integration Guide

## Overview
This guide shows you how to integrate multiple AI providers into your NSW Government Procurement Automation Platform, including Cursor API integration.

## 🏷️ **Cursor API Pricing & Access**

### **Current Cursor API Status:**
- **Cursor Pro/Team Plans**: Include API access for code tracking and analysis
- **No Additional Cost**: API usage is included in your subscription
- **Rate Limits**: Subject to your plan's rate limits
- **Primary Use**: Code analysis, not general AI inference

### **Important Note:**
Cursor's API is primarily for **code tracking and analysis**, not for general AI model inference. For actual AI model usage in your app, use the other providers in this integration.

---

## 🚀 **Quick Setup**

### **1. Install Additional Dependencies**
```bash
pip install openai anthropic google-generativeai
```

### **2. Set Up API Keys**
Copy `ai_providers_config.env.example` to `.env` and add your API keys:

```bash
# OpenAI (Recommended for tender generation)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Claude (Great for compliance checking)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI (Free tier available)
GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Cursor API (If you have Cursor Pro/Team)
CURSOR_API_KEY=your_cursor_api_key_here

# Ollama (Local - No API key needed)
OLLAMA_BASE_URL=http://localhost:11434
```

### **3. Test Your Setup**
```python
from app.services.ai_providers import generate_ai_response, get_available_ai_providers

# Check available providers
providers = get_available_ai_providers()
print(f"Available providers: {[p.value for p in providers]}")

# Test AI generation
import asyncio
result = asyncio.run(generate_ai_response("Generate a professional tender title for HVAC installation"))
print(result["response"])
```

---

## 🎯 **Provider Recommendations by Use Case**

### **🏗️ Tender Document Generation**
- **Best**: OpenAI GPT-4
- **Why**: Excellent for complex document generation with high quality output
- **Cost**: ~$0.03 per 1K tokens

### **📋 Compliance Checking**
- **Best**: Anthropic Claude
- **Why**: Superior reasoning and accuracy for compliance analysis
- **Cost**: ~$0.003 per 1K input tokens

### **🏆 Supplier Evaluation**
- **Best**: OpenAI GPT-4
- **Why**: Best for structured data extraction and scoring
- **Cost**: ~$0.03 per 1K tokens

### **💰 Cost Optimization**
- **Best**: Local Ollama
- **Why**: No API costs, good for high-volume processing
- **Cost**: Free (runs locally)

### **🔍 General Text Processing**
- **Best**: Auto-select
- **Why**: Let the system choose the best available provider
- **Cost**: Varies by provider

---

## 🔧 **Integration Examples**

### **1. Basic AI Generation**
```python
from app.services.ai_providers import generate_ai_response, AIProvider

# Auto-select best provider
result = await generate_ai_response("Your prompt here")

# Use specific provider
result = await generate_ai_response(
    "Your prompt here", 
    provider=AIProvider.OPENAI
)
```

### **2. Cost-Optimized Generation**
```python
# Use local Ollama for high-volume, low-cost processing
result = await generate_ai_response(
    "Process supplier data",
    provider=AIProvider.OLLAMA,
    max_tokens=2000,
    temperature=0.3
)
```

### **3. High-Quality Generation**
```python
# Use premium provider for critical documents
result = await generate_ai_response(
    "Generate tender evaluation criteria",
    provider=AIProvider.OPENAI,
    max_tokens=4000,
    temperature=0.7
)
```

### **4. Cursor API Integration**
```python
# Use Cursor API for code analysis (if available)
result = await generate_ai_response(
    "Analyze this procurement code",
    provider=AIProvider.CURSOR
)
```

---

## 📊 **Cost Management**

### **Cost Tracking**
The system automatically tracks costs for each provider:

```python
result = await generate_ai_response("Your prompt")
print(f"Cost: ${result['cost']:.4f}")
print(f"Usage: {result['usage']}")
```

### **Cost Optimization Strategies**
1. **Use Local Models**: Ollama for high-volume processing
2. **Free Tiers**: Google AI and Hugging Face offer free tiers
3. **Smart Routing**: System automatically chooses most cost-effective provider
4. **Caching**: Implement caching to reduce repeated API calls

---

## 🛠️ **Advanced Configuration**

### **Custom Provider Configuration**
```python
from app.services.ai_providers import ai_manager, ModelConfig, AIProvider

# Add custom provider configuration
ai_manager.providers[AIProvider.OPENAI] = ModelConfig(
    provider=AIProvider.OPENAI,
    model_name="gpt-4-turbo",
    api_key="your_key",
    max_tokens=8000,
    temperature=0.5
)
```

### **Fallback Chain**
The system automatically falls back through providers:
1. OpenAI GPT-4
2. Anthropic Claude
3. Google Gemini
4. Ollama (Local)
5. Cursor API
6. Hugging Face

---

## 🎮 **Streamlit UI Integration**

### **Add to Your App**
```python
# In your streamlit_app.py
from app.services.ai_providers_ui import render_ai_providers_page

def page_ai_providers():
    _topbar()
    render_ai_providers_page()
    _footer()

# Add to navigation
if view == "ai_providers":
    page_ai_providers()
```

### **UI Features**
- ✅ Provider status overview
- ✅ Configuration management
- ✅ Live testing interface
- ✅ Cost tracking dashboard
- ✅ Usage analytics
- ✅ Provider recommendations

---

## 🔒 **Security Best Practices**

### **API Key Management**
1. **Environment Variables**: Never hardcode API keys
2. **Separate Keys**: Use different keys for different environments
3. **Rotation**: Regularly rotate API keys
4. **Monitoring**: Monitor API usage and costs

### **Rate Limiting**
```python
# Implement rate limiting for cost control
import time

class RateLimiter:
    def __init__(self, max_requests_per_minute=60):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    async def wait_if_needed(self):
        now = time.time()
        self.requests = [req for req in self.requests if now - req < 60]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = 60 - (now - self.requests[0])
            await asyncio.sleep(sleep_time)
        
        self.requests.append(now)
```

---

## 📈 **Performance Optimization**

### **Async Processing**
```python
import asyncio

# Process multiple requests concurrently
async def process_multiple_requests(prompts):
    tasks = [generate_ai_response(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    return results
```

### **Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_ai_response(prompt_hash: str, provider: str):
    # Cache responses for repeated queries
    pass
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. No Providers Available**
```
Solution: Check your environment variables and API keys
```

#### **2. Rate Limit Exceeded**
```
Solution: Implement rate limiting or use different provider
```

#### **3. High Costs**
```
Solution: Use local Ollama or free-tier providers
```

#### **4. Poor Response Quality**
```
Solution: Adjust temperature, max_tokens, or try different model
```

### **Debug Mode**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for AI providers
```

---

## 📞 **Support**

### **Getting Help**
1. Check provider documentation
2. Review API key configuration
3. Test with simple prompts first
4. Monitor costs and usage

### **Provider Documentation**
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)
- [Google AI](https://ai.google.dev/docs)
- [Ollama](https://ollama.ai/docs)
- [Cursor API](https://docs.cursor.com/)

---

## 🎉 **Next Steps**

1. **Set up your preferred providers**
2. **Test with sample prompts**
3. **Integrate into your procurement workflows**
4. **Monitor costs and performance**
5. **Optimize based on usage patterns**

This integration gives you access to the best AI models for your procurement platform while maintaining cost control and flexibility!
