# AI-Powered Procurement Automation Platform

A comprehensive NSW Local Government procurement automation platform with AI-enhanced tender generation, evaluation, and compliance management.

## 🚀 Features

### Core Functionality
- **🤖 AI-Enhanced TEPP Generator** - Generate comprehensive Tender Evaluation and Probity Plans with AI assistance
- **📋 AI Tender Creation** - Create detailed tender packages with AI-powered content generation
- **💰 AI Quote Generator** - Generate professional quotes with intelligent pricing and specifications
- **🔍 Unified Evaluation System** - Collaborative evaluation with AI pre-scoring and human consensus
- **📚 RAG & Document Management** - Three-tier document management with compliance, internal, and external categories
- **🛡️ Compliance Dashboard** - Real-time compliance monitoring and analysis
- **📊 Progress Dashboard** - Development progress tracking and reporting
- **🔍 Historical Matching** - AI-powered historical project matching and analysis

### AI Integration
- **Multiple AI Models** - Support for Ollama (local) and Google Gemini (cloud) models
- **Intelligent Model Selection** - Automatic model detection and recommendation
- **RAG-Enhanced Generation** - Context-aware content generation using retrieval-augmented generation
- **Real-time Enhancement** - AI-powered section enhancement based on user edits and real factors

### Test Examples
- **🚛 Fleet Test Examples** - Ready-to-use specifications for fleet procurement
- **💼 Services Test Examples** - HVAC, building maintenance, and equipment service specifications
- **📋 Copy-Paste Ready** - Easy-to-use test specifications for AI generators

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Streamlit
- Ollama (for local AI models)
- Google API Key (for Gemini models)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI-Powered-Procurement-Automation-Platform.git
cd AI-Powered-Procurement-Automation-Platform
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp ai_providers_config.env.example .env
# Edit .env with your API keys
```

4. Start the application:
```bash
streamlit run app/main.py
```

## 📁 Project Structure

```
├── app/                          # Main application
│   ├── components/              # UI components
│   ├── pages/                   # Application pages
│   ├── services/                # Business logic services
│   ├── core/                    # Core functionality
│   └── ui/                      # UI assets and styling
├── data/                        # Data storage
├── projects/                    # Project files
├── docs/                        # Documentation
└── requirements.txt             # Python dependencies
```

## 🔧 Configuration

### AI Models
- **Local Models**: Ollama (Phi3, Llama, etc.)
- **Cloud Models**: Google Gemini 1.5 Flash/Pro
- **Model Selection**: Automatic detection and recommendation

### RAG System
- **Three-Tier Structure**: Compliance, Internal, External documents
- **Document Types**: PDF, DOCX, TXT, MD
- **Categories**: Project-specific document organization

## 📊 Usage

### 1. Sign In
- Use any email format for registration
- Simple authentication system

### 2. Choose Procurement Type
- Select from available procurement types
- Access AI generators and tools

### 3. Generate TEPP
- Use AI-Enhanced TEPP Generator
- Edit sections with AI enhancement
- Download and save documents

### 4. Create Tenders
- Use AI Tender Creation
- Upload specifications or paste text
- Generate comprehensive tender packages

### 5. Evaluate Submissions
- Use Unified Evaluation System
- AI pre-scoring with human consensus
- Comprehensive evaluation reports

## 🧪 Testing

### Test Examples
- **Fleet Specifications**: Sweeper Truck, Garbage Truck, Fire Truck
- **Services Specifications**: HVAC, Building Maintenance, Equipment Service
- **Usage**: Copy-paste ready specifications for testing AI generators

### Test Process
1. Go to Test Examples in sidebar
2. Select specification type
3. Copy content (Ctrl+A, Ctrl+C)
4. Paste into AI generator
5. Test and validate results

## 📚 Documentation

- [AI Providers Integration Guide](AI_PROVIDERS_INTEGRATION_GUIDE.md)
- [Local AI Setup Guide](LOCAL_AI_SETUP_GUIDE.md)
- [Technical Implementation Guide](TECHNICAL_IMPLEMENTATION_GUIDE.md)
- [Compliance System Guide](INTEGRATED_COMPLIANCE_SYSTEM.md)
- [Historical Project Matching Guide](HISTORICAL_PROJECT_MATCHING_GUIDE.md)

## 🔒 Compliance

- **NSW Local Government Standards** - Full compliance with local government requirements
- **TEPP Framework** - Standardized Tender Evaluation and Probity Plans
- **Probity Requirements** - Comprehensive probity and accountability measures
- **Audit Trail** - Complete audit trail for all evaluations and decisions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the test examples
- Use the built-in help system
- Contact the development team

## 🚀 Development Status

- ✅ Core functionality implemented
- ✅ AI integration complete
- ✅ RAG system operational
- ✅ Test examples available
- ✅ Documentation updated
- 🔄 Continuous improvement in progress

---

**Built for NSW Local Government Procurement Excellence**
