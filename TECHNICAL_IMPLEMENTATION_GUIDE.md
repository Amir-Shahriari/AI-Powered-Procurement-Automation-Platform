# 🔧 Technical Implementation Guide - NSW Government Procurement Platform

## 📋 **Overview**

This guide provides detailed technical information for developers, IT administrators, and technical stakeholders implementing the AI-Powered Procurement Automation Platform.

---

## 🏗️ **System Architecture**

### **Core Components**
```
┌─────────────────────────────────────────────────────────────┐
│                    NSW Procurement Platform                 │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)     │  Backend (FastAPI)             │
│  ├─ User Interface        │  ├─ API Services               │
│  ├─ Dashboard             │  ├─ Document Processing        │
│  ├─ Forms & Navigation    │  ├─ AI Integration             │
│  └─ Real-time Updates     │  └─ Data Management            │
├─────────────────────────────────────────────────────────────┤
│  AI Processing Layer                                        │
│  ├─ Local AI (Ollama)     │  ├─ Cloud APIs (Fallback)     │
│  ├─ Smart RAG System      │  ├─ Hardware Optimization     │
│  ├─ Compliance Engine     │  └─ Performance Monitoring     │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├─ Document Storage      │  ├─ Vector Stores (FAISS)     │
│  ├─ Compliance Cache      │  ├─ Project Files              │
│  └─ User Data             │  └─ Configuration              │
└─────────────────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Frontend**: Streamlit 1.28+
- **Backend**: FastAPI 0.111+
- **AI Processing**: Ollama (local) + LangChain + OpenAI/Anthropic/Google AI
- **Document Processing**: PyMuPDF, python-docx, docx2txt
- **Vector Storage**: FAISS, ChromaDB
- **Database**: Local file system (JSON)
- **Authentication**: Custom session-based with hashed passwords

---

## 🖥️ **Local AI System Implementation**

### **Hardware Detection & Optimization**

#### **System Analysis Components**
```python
# Automatic hardware detection
system_info = {
    "platform": platform.system(),           # Windows, macOS, Linux
    "architecture": platform.machine(),      # AMD64, ARM64, etc.
    "cpu_count": psutil.cpu_count(),         # Logical CPU cores
    "memory_gb": psutil.virtual_memory(),    # Total RAM
    "gpu_info": detect_gpu(),                # GPU capabilities
    "performance_tier": determine_tier()     # Performance classification
}
```

#### **Performance Tier Classification**
- **High-End**: 32GB+ RAM, 8+ cores, 8GB+ GPU → llama3.1:8b, llama3:8b
- **Mid-Tier**: 16GB+ RAM, 4+ cores, 4GB+ GPU → phi3:3.8b, mistral:7b
- **Entry-Level**: 8GB+ RAM, 2+ cores → phi3:3.8b, gemma:7b
- **Low-End**: <8GB RAM → phi3:3.8b only

#### **GPU Detection Support**
- **NVIDIA**: nvidia-smi detection, CUDA support
- **AMD**: ROCm support detection
- **Intel**: Integrated graphics detection
- **Apple Silicon**: M1/M2 chip detection with unified memory

### **Model Management**

#### **Recommended Models by Task**
```python
TASK_MODELS = {
    "tender_generation": ["llama3.1:8b", "llama3:8b", "mistral:7b"],
    "compliance_checking": ["phi3:3.8b", "mistral:7b", "llama3:8b"],
    "document_analysis": ["mistral:7b", "llama3.1:8b", "phi3:3.8b"],
    "supplier_evaluation": ["codellama:7b", "llama3:8b", "mistral:7b"],
    "general_purpose": ["llama3.1:8b", "llama3:8b", "phi3:3.8b"],
    "fast_processing": ["phi3:3.8b", "gemma:7b", "mistral:7b"]
}
```

#### **Model Installation**
```bash
# Automatic installation via setup script
python setup_local_ai.py

# Manual installation
ollama pull phi3:3.8b      # 4GB - Recommended for entry-level
ollama pull mistral:7b     # 4GB - Good for documents
ollama pull llama3.1:8b    # 8GB - Best quality
ollama pull codellama:7b   # 4GB - Good for structured tasks
```

---

## 🔧 **Installation & Setup**

### **Prerequisites**
```bash
# Python 3.8+ with pip
python --version

# Ollama installation
# Windows: Download from https://ollama.ai/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
```

### **Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd AI-Powered-Procurement-Automation-Platform

# Create conda environment
conda env create -f environment.yml
conda activate AI

# Install dependencies
pip install -r requirements.txt

# Set up local AI
python setup_local_ai.py

# Test installation
python test_ai_providers.py
```

### **Configuration Files**

#### **Environment Variables (.env)**
```bash
# Local AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:3.8b

# Optional: Cloud API Keys (for fallback)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_AI_API_KEY=your_google_ai_key_here

# Application Settings
APP_THEME_CSS=app/ui/theme.css
DATA_DIR=./data
```

#### **System Configuration**
```python
# app/config.py
class Settings:
    DATA_DIR = Path("./data")
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "phi3:3.8b"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    SUPPORTED_FORMATS = ["pdf", "docx", "txt", "doc"]
```

---

## 🚀 **Deployment Options**

### **Option 1: Local Development**
```bash
# Start Ollama service
ollama serve

# Run application
python start_app.py
# or
python -m streamlit run app/streamlit_app.py
```

### **Option 2: Production Deployment**

#### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Start services
CMD ["sh", "-c", "ollama serve & python start_app.py"]
```

#### **Systemd Service**
```ini
[Unit]
Description=NSW Procurement Platform
After=network.target

[Service]
Type=simple
User=procurement
WorkingDirectory=/opt/procurement-platform
ExecStart=/opt/procurement-platform/start_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### **Option 3: Cloud Deployment**

#### **AWS/Azure/GCP**
- **Compute**: EC2/Azure VM/GCP Compute Engine
- **Storage**: S3/Azure Blob/GCP Storage
- **Networking**: VPC with security groups
- **Monitoring**: CloudWatch/Azure Monitor/GCP Monitoring

#### **Container Orchestration**
- **Kubernetes**: For scalable deployments
- **Docker Compose**: For simple multi-container setups
- **Helm Charts**: For Kubernetes package management

---

## 🔒 **Security Implementation**

### **Authentication System**
```python
# Password hashing with scrypt
def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    import hashlib, binascii
    if salt is None:
        salt_bytes = os.urandom(16)
    else:
        salt_bytes = binascii.unhexlify(salt)
    
    h = hashlib.scrypt(
        password.encode("utf-8"), 
        salt=salt_bytes, 
        n=2**14, r=8, p=1, dklen=32
    )
    return binascii.hexlify(salt_bytes).decode(), binascii.hexlify(h).decode()
```

### **Data Protection**
- **Local Processing**: All AI processing happens locally
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive input sanitization

### **Access Control**
```python
# Role-based access control
USER_ROLES = {
    "admin": ["read", "write", "delete", "admin"],
    "officer": ["read", "write"],
    "viewer": ["read"]
}
```

---

## 📊 **Performance Optimization**

### **Local AI Optimization**
```python
# Model selection based on system capabilities
def get_optimal_model(system_info: Dict[str, Any]) -> str:
    if system_info["performance_tier"] == "high_end":
        return "llama3.1:8b"
    elif system_info["performance_tier"] == "mid_tier":
        return "phi3:3.8b"
    else:
        return "phi3:3.8b"
```

### **Caching Strategy**
```python
# Smart caching for compliance documents
compliance_cache = {
    "hvac": cached_documents,
    "fleet": cached_documents,
    "service": cached_documents,
    "maintenance": cached_documents
}
```

### **Memory Management**
- **Model Loading**: Lazy loading of AI models
- **Cache Management**: Automatic cache cleanup
- **Resource Monitoring**: Real-time resource usage tracking

---

## 🔍 **Monitoring & Logging**

### **Performance Metrics**
```python
# Real-time performance monitoring
metrics = {
    "total_calls": 0,
    "rag_percentage": 0.0,
    "cache_hit_rate": 0.0,
    "average_time": 0.0,
    "total_time": 0.0,
    "cost_savings": 0.0
}
```

### **Logging Configuration**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('procurement_platform.log'),
        logging.StreamHandler()
    ]
)
```

### **Health Checks**
```python
# System health monitoring
def health_check():
    return {
        "ollama_status": check_ollama_status(),
        "model_availability": check_models(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }
```

---

## 🧪 **Testing Framework**

### **Unit Tests**
```python
# Test local AI functionality
def test_local_ai_generation():
    response = generate_local_response(
        "Generate a professional tender title",
        model="phi3:3.8b"
    )
    assert response["cost"] == 0.0
    assert "response" in response
```

### **Integration Tests**
```python
# Test complete workflow
def test_procurement_workflow():
    # Upload specification
    # Generate tender documents
    # Check compliance
    # Evaluate suppliers
    # Verify results
```

### **Performance Tests**
```python
# Load testing
def test_concurrent_users():
    # Simulate multiple users
    # Monitor performance
    # Verify system stability
```

---

## 🛠️ **Troubleshooting Guide**

### **Common Issues**

#### **Ollama Not Starting**
```bash
# Check Ollama installation
ollama --version

# Start Ollama service
ollama serve

# Check if service is running
curl http://localhost:11434/api/tags
```

#### **Model Installation Issues**
```bash
# Check available models
ollama list

# Install specific model
ollama pull phi3:3.8b

# Check model status
ollama show phi3:3.8b
```

#### **Memory Issues**
```bash
# Check system memory
free -h  # Linux
system_profiler SPHardwareDataType  # macOS
Get-ComputerInfo | Select-Object TotalPhysicalMemory  # Windows

# Use smaller models if needed
ollama pull phi3:3.8b  # 4GB instead of 8GB
```

#### **Performance Issues**
```bash
# Check CPU usage
htop  # Linux/macOS
Task Manager  # Windows

# Optimize model selection
python analyze_system.py
```

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug flags
python start_app.py --debug
```

---

## 📚 **API Documentation**

### **Local AI API**
```python
# Generate response using local AI
async def generate_local_response(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate AI response using local models
    
    Args:
        prompt: Input text for AI processing
        model: Specific model to use (optional)
        max_tokens: Maximum tokens to generate
        temperature: Response creativity (0.0-1.0)
    
    Returns:
        Dict containing response, model, cost, and metadata
    """
```

### **System Analysis API**
```python
# Get system information
def get_system_info() -> Dict[str, Any]:
    """
    Get detailed system analysis
    
    Returns:
        Dict containing platform, CPU, memory, GPU info
    """

# Get recommended models
def get_system_recommendations() -> List[Dict[str, Any]]:
    """
    Get AI model recommendations for current system
    
    Returns:
        List of recommended models with reasons
    """
```

---

## 🔄 **Maintenance & Updates**

### **Regular Maintenance Tasks**
```bash
# Update Ollama models
ollama pull phi3:3.8b

# Update application dependencies
pip install -r requirements.txt --upgrade

# Clean up old data
python cleanup_old_data.py

# Backup configuration
cp .env .env.backup
```

### **Version Updates**
```bash
# Update application
git pull origin main
pip install -r requirements.txt

# Update models
ollama pull phi3:3.8b:latest

# Test updates
python test_ai_providers.py
```

### **Backup Strategy**
```bash
# Backup data directory
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Backup configuration
cp .env config_backup_$(date +%Y%m%d).env

# Backup models (if needed)
ollama list > models_backup_$(date +%Y%m%d).txt
```

---

## 📞 **Support & Resources**

### **Documentation**
- **User Guide**: `USER_GUIDE.md`
- **API Reference**: `API_DOCUMENTATION.md`
- **Troubleshooting**: `TROUBLESHOOTING_GUIDE.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`

### **Community Support**
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides and examples
- **Community Forum**: User discussions and support

### **Professional Support**
- **Technical Support**: Available for enterprise deployments
- **Custom Development**: Tailored solutions for specific needs
- **Training Services**: User and administrator training

---

*This technical implementation guide provides comprehensive information for deploying, configuring, and maintaining the NSW Government Procurement Automation Platform in various environments.*
