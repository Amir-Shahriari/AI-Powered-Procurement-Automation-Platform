# 🏠 Local AI Setup Guide for NSW Government Procurement Platform

## 🎯 **Quick Answer: Cursor API vs Local AI**

### **❌ Cursor API Limitations:**
- **Cannot use Cursor subscription** for document generation/tendering
- **Cursor API is for code analysis only**, not general AI inference
- **No LLM access** through Cursor's current APIs

### **✅ Local AI Solution (Recommended):**
- **Zero API costs** - runs completely on your machine
- **Complete privacy** - no data leaves your system
- **Works offline** - no internet required after setup
- **Government-compliant** - perfect for sensitive procurement data

---

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Run the Setup Script**
```bash
python setup_local_ai.py
```

This script will:
- ✅ Check if Ollama is installed
- ✅ Install Ollama if needed
- ✅ Download recommended AI models
- ✅ Test the models
- ✅ Configure your environment

### **Step 2: Test Your Setup**
```bash
python test_ai_providers.py
```

### **Step 3: Run Your App**
```bash
python start_app.py
```

**That's it!** Your procurement platform now uses local AI models.

---

## 📋 **What Models Are Installed?**

### **Recommended Models (Automatically Installed):**

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| **llama3.1:8b** | 8GB | General purpose, tender generation | ⭐⭐⭐⭐ |
| **phi3:3.8b** | 4GB | Fast processing, compliance checking | ⭐⭐⭐⭐⭐ |
| **mistral:7b** | 4GB | Document analysis, structured tasks | ⭐⭐⭐⭐ |
| **codellama:7b** | 4GB | Supplier evaluation, scoring | ⭐⭐⭐ |

### **Model Selection by Task:**

- **🏗️ Tender Generation**: `llama3.1:8b` (best quality)
- **📋 Compliance Checking**: `phi3:3.8b` (fast and accurate)
- **🏆 Supplier Evaluation**: `codellama:7b` (structured data)
- **📄 Document Analysis**: `mistral:7b` (document understanding)

---

## 💻 **System Requirements**

### **Minimum Requirements:**
- **RAM**: 8GB (for 3.8B models)
- **Storage**: 20GB free space
- **CPU**: Modern multi-core processor
- **OS**: Windows 10+, macOS 10.15+, or Linux

### **Recommended for Best Performance:**
- **RAM**: 16GB+ (for 8B models)
- **Storage**: 50GB+ free space
- **CPU**: 8+ cores
- **GPU**: Optional (will use CPU if no GPU)

---

## 🔧 **Manual Setup (If Script Fails)**

### **1. Install Ollama**
```bash
# Windows
# Download from: https://ollama.ai/download

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### **2. Start Ollama Service**
```bash
ollama serve
```

### **3. Install Models**
```bash
# Install recommended models
ollama pull llama3.1:8b
ollama pull phi3:3.8b
ollama pull mistral:7b
ollama pull codellama:7b
```

### **4. Test Installation**
```bash
ollama run llama3.1:8b "Generate a professional tender title for HVAC installation"
```

---

## 🎮 **Using Local AI in Your App**

### **Automatic Fallback:**
Your app automatically uses local AI when:
- ✅ No API keys are configured
- ✅ API providers are unavailable
- ✅ You want zero-cost processing

### **Manual Selection:**
```python
from app.services.ai_providers import generate_ai_response, AIProvider

# Use local AI specifically
result = await generate_ai_response(
    "Generate tender evaluation criteria",
    provider=AIProvider.OLLAMA
)

# Or let the system auto-select (local AI as fallback)
result = await generate_ai_response(
    "Generate tender evaluation criteria"
)
```

### **Task-Specific Models:**
```python
from app.services.local_ai import get_recommended_model, generate_local_response

# Get best model for specific task
model = get_recommended_model("tender_generation")

# Use that model
result = await generate_local_response(
    "Generate professional tender title",
    model=model
)
```

---

## 📊 **Performance Comparison**

### **Local AI vs Cloud APIs:**

| Feature | Local AI | Cloud APIs |
|---------|----------|------------|
| **Cost** | Free | $0.01-0.10 per request |
| **Privacy** | 100% Private | Data sent to provider |
| **Speed** | 2-10 seconds | 1-3 seconds |
| **Availability** | Always works | Requires internet |
| **Customization** | Full control | Limited |

### **Typical Response Times:**
- **phi3:3.8b**: 2-5 seconds (fast)
- **llama3.1:8b**: 5-10 seconds (high quality)
- **mistral:7b**: 3-7 seconds (balanced)

---

## 🔒 **Security & Compliance Benefits**

### **Perfect for Government Use:**
- ✅ **No data leaves your system**
- ✅ **Complies with data sovereignty requirements**
- ✅ **No API rate limits or costs**
- ✅ **Works in air-gapped environments**
- ✅ **Full audit trail and control**

### **Privacy Advantages:**
- ✅ **Sensitive procurement data stays local**
- ✅ **No third-party data processing**
- ✅ **No risk of data breaches via APIs**
- ✅ **Complete control over model behavior**

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **1. "Ollama not found"**
```bash
# Solution: Install Ollama
# Windows: Download from https://ollama.ai/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
```

#### **2. "No models available"**
```bash
# Solution: Install models
ollama pull llama3.1:8b
ollama pull phi3:3.8b
```

#### **3. "Model generation too slow"**
```bash
# Solution: Use smaller, faster models
ollama pull phi3:3.8b  # Fastest model
```

#### **4. "Out of memory"**
```bash
# Solution: Use smaller models or increase RAM
ollama pull phi3:3.8b  # Uses only 4GB RAM
```

#### **5. "Models not responding"**
```bash
# Solution: Restart Ollama service
ollama serve
```

---

## 📈 **Optimization Tips**

### **For Best Performance:**
1. **Use appropriate model size** for your hardware
2. **Keep models in memory** (Ollama does this automatically)
3. **Use smaller models** for high-volume tasks
4. **Use larger models** for complex document generation

### **For Cost Optimization:**
1. **Local AI is always free** - no API costs
2. **Use phi3:3.8b** for most tasks (fastest)
3. **Use llama3.1:8b** only for critical documents
4. **Cache responses** for repeated queries

### **For Quality:**
1. **Use llama3.1:8b** for tender generation
2. **Use codellama:7b** for structured tasks
3. **Use mistral:7b** for document analysis
4. **Adjust temperature** (0.7 for creativity, 0.3 for accuracy)

---

## 🎉 **Next Steps**

1. **Run the setup script**: `python setup_local_ai.py`
2. **Test your installation**: `python test_ai_providers.py`
3. **Start using local AI**: Your app will automatically use local models
4. **Monitor performance**: Check response times and quality
5. **Optimize as needed**: Adjust models based on your usage patterns

---

## 💡 **Pro Tips**

### **For Procurement Officers:**
- Use **phi3:3.8b** for quick compliance checks
- Use **llama3.1:8b** for important tender documents
- Local AI ensures your sensitive data never leaves your system

### **For IT Administrators:**
- Set up on a dedicated server for better performance
- Monitor disk space (models can be large)
- Consider GPU acceleration for faster processing
- Implement regular model updates

### **For Cost Control:**
- Local AI eliminates all API costs
- No surprise bills or usage limits
- Predictable performance and availability
- Perfect for high-volume government procurement

---

**🎯 Bottom Line**: Local AI gives you enterprise-grade AI capabilities with zero ongoing costs, complete privacy, and government-compliant data handling. Perfect for your NSW Government Procurement Platform!
