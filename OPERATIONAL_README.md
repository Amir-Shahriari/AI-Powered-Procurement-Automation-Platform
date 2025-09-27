# NSW Government Procurement Automation Platform - Operational Guide

## 🚀 Quick Start

### Option 1: Windows Batch File (Recommended)
```bash
# Double-click or run:
start_app.bat
```

### Option 2: Python Script
```bash
python start_app.py
```

### Option 3: Direct Streamlit
```bash
# Set environment variable first
set KMP_DUPLICATE_LIB_OK=TRUE
python -m streamlit run app/streamlit_app.py --server.port 8501
```

## 🌐 Access the Application

Once started, the application will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://192.168.20.9:8501 (accessible from other devices on your network)

## 🔐 Professional Login System

### First Time Setup
1. Open the application in your browser
2. You'll see the professional NSW Government login page
3. For new councils: Contact LGP at procurement@lgp.nsw.gov.au or (02) 9248 5000
4. For LGP administrators: Use the "Administrator Access" section with admin key: `5661`

### User Management
- **LGP Administrators**: Can create council accounts and manage access
- **Council Users**: Can access their council's procurement dashboard
- **User database**: Stored securely in `app/users/users.json`
- **Professional Interface**: Government-appropriate design for council confidence

## 🏛️ Features Available

### 1. **Document Upload & Processing**
- Upload tender specifications (PDF, DOCX, TXT)
- AI-powered document analysis and extraction
- Automatic TEPP and Returnable Schedules generation

### 2. **Compliance Checking**
- NSW Local Government procurement guidelines compliance
- WHS, ADR, and standards verification
- Real-time compliance dashboard

### 3. **Supplier Evaluation**
- Upload supplier responses
- AI-powered scoring and ranking
- Comprehensive evaluation reports

### 4. **Document Export**
- Generate TEPP documents (DOCX)
- Export Returnable Schedules (DOCX)
- Download evaluation results (JSON)

## 🔧 Technical Details

### System Requirements
- Python 3.8+
- Windows 10/11 (tested)
- 8GB RAM minimum
- 2GB free disk space

### Dependencies
All required packages are installed via `requirements.txt`:
- Streamlit (web interface)
- FastAPI (API backend)
- LangChain (AI processing)
- Python-docx (document generation)
- And many more...

### File Structure
```
AI-Powered-Procurement-Automation-Platform/
├── app/
│   ├── streamlit_app.py          # Main application
│   ├── services/                 # AI and processing services
│   ├── ui/theme.css             # Professional styling
│   └── users/users.json         # User database
├── data/                        # Generated documents and data
├── start_app.py                 # Python startup script
├── start_app.bat               # Windows batch file
└── requirements.txt            # Python dependencies
```

## 🛠️ Troubleshooting

### OMP Library Conflict
If you see "OMP: Error #15" messages, this is normal and doesn't affect functionality. The app automatically sets `KMP_DUPLICATE_LIB_OK=TRUE` to resolve this.

### App Won't Start
1. Ensure Python is installed and in PATH
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 8501 is not in use by another application

### Login Issues
1. Delete `app/users/users.json` to reset user database
2. Restart the app to create a new admin account

### Performance Issues
- Close other applications to free up memory
- Ensure stable internet connection for AI processing
- Large documents may take longer to process

## 📊 Usage Workflow

### 1. **Create Tender Documents**
1. Login to the platform
2. Go to "Upload Specification"
3. Upload your tender specification document
4. Select procurement category and model
5. Generate TEPP and Returnable Schedules

### 2. **Check Compliance**
1. Navigate to "Check Compliance"
2. Enter procurement details
3. Review compliance status
4. Generate compliance reports

### 3. **Evaluate Suppliers**
1. Go to "Supplier Evaluation"
2. Upload supplier response documents
3. Run AI-powered evaluation
4. Review scores and rankings
5. Export evaluation reports

## 🔒 Security Features

- **User Authentication**: Secure login system with password hashing
- **Session Management**: Automatic logout after inactivity
- **Data Protection**: All data stored locally on your system
- **Admin Controls**: Restricted user creation and management

## 📞 Support

For technical support or questions:
1. Check this README first
2. Review the application logs in the terminal
3. Ensure all dependencies are properly installed
4. Contact your IT administrator

## 🎯 Production Deployment

For production deployment:
1. Use a dedicated server with sufficient resources
2. Set up proper backup procedures for the `data/` directory
3. Configure firewall rules for network access
4. Set up monitoring and logging
5. Regular security updates

---

**© 2024 NSW Government. All rights reserved.**
