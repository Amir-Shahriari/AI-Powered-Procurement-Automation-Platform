#!/usr/bin/env python3
"""
Local AI Setup Script for NSW Government Procurement Platform
Automatically installs and configures local AI models using Ollama
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

def check_ollama_installation():
    """Check if Ollama is installed and running"""
    print("🔍 Checking Ollama installation...")
    
    try:
        # Check if ollama command exists
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not found in PATH")
            return False
    except FileNotFoundError:
        print("❌ Ollama not installed")
        return False

def check_ollama_running():
    """Check if Ollama service is running"""
    print("🔍 Checking if Ollama is running...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.ok:
            print("✅ Ollama service is running")
            return True
        else:
            print(f"❌ Ollama service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama service not accessible: {e}")
        return False

def install_ollama():
    """Install Ollama if not present"""
    print("📥 Installing Ollama...")
    
    if sys.platform == "win32":
        print("Please download and install Ollama from: https://ollama.ai/download")
        print("After installation, restart your terminal and run this script again.")
        return False
    elif sys.platform == "darwin":
        # macOS
        try:
            subprocess.run(["brew", "install", "ollama"], check=True)
            print("✅ Ollama installed via Homebrew")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install via Homebrew. Please install manually from https://ollama.ai/download")
            return False
    else:
        # Linux
        try:
            subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh"], check=True)
            print("✅ Ollama installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Ollama. Please install manually from https://ollama.ai/download")
            return False

def start_ollama_service():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    
    try:
        if sys.platform == "win32":
            # On Windows, Ollama usually starts automatically
            print("ℹ️ On Windows, Ollama should start automatically")
            return True
        else:
            # On macOS/Linux, start ollama serve
            subprocess.Popen(["ollama", "serve"])
            time.sleep(3)  # Wait for service to start
            return check_ollama_running()
    except Exception as e:
        print(f"❌ Failed to start Ollama service: {e}")
        return False

def get_available_models():
    """Get list of currently available models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.ok:
            models_data = response.json()
            return [model["name"] for model in models_data.get("models", [])]
        return []
    except Exception:
        return []

def install_model(model_name: str) -> bool:
    """Install a specific model"""
    print(f"📥 Installing model: {model_name}")
    
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully installed {model_name}")
            return True
        else:
            print(f"❌ Failed to install {model_name}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout installing {model_name} (this can take a while for large models)")
        return False
    except Exception as e:
        print(f"❌ Error installing {model_name}: {e}")
        return False

def analyze_system_and_get_recommendations():
    """Analyze system and get recommended models"""
    print("🔍 Analyzing your system capabilities...")
    
    try:
        from services.local_ai import print_system_analysis, get_system_recommendations
        
        # Print system analysis
        print_system_analysis()
        
        # Get recommended models
        recommendations = get_system_recommendations()
        
        if not recommendations:
            print("\n⚠️ No models recommended for your system.")
            print("💡 Consider upgrading your hardware or using cloud APIs.")
            return []
        
        print(f"\n🎯 System recommends {len(recommendations)} models for optimal performance:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['model']} - {rec['reason']}")
        
        return [rec["model"] for rec in recommendations]
        
    except Exception as e:
        print(f"⚠️ Could not analyze system: {e}")
        print("📦 Using default model recommendations...")
        
        # Fallback to default recommendations
        return [
            "phi3:3.8b",        # Fast and efficient (4GB)
            "mistral:7b",       # Good for documents (4GB)
            "llama3.1:8b",      # Best general purpose (8GB)
        ]

def install_recommended_models():
    """Install recommended models based on system analysis"""
    
    print("🎯 Getting model recommendations for your system...")
    recommended_models = analyze_system_and_get_recommendations()
    
    if not recommended_models:
        print("❌ No models could be recommended for your system.")
        return []
    
    print(f"\n📦 Installing {len(recommended_models)} recommended models...")
    print("This may take a while depending on your internet connection.")
    
    installed_models = []
    
    for model in recommended_models:
        print(f"\n📦 Installing {model}...")
        if install_model(model):
            installed_models.append(model)
        else:
            print(f"⚠️ Skipping {model} due to installation failure")
    
    return installed_models

def test_model(model_name: str) -> bool:
    """Test a model with a simple prompt"""
    print(f"🧪 Testing model: {model_name}")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Generate a professional tender title for: 'Supply and Installation of HVAC Systems'",
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 100}
            },
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            response_text = result.get("response", "")
            print(f"✅ Model test successful")
            print(f"Response: {response_text[:100]}...")
            return True
        else:
            print(f"❌ Model test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def create_env_file():
    """Create .env file with local AI configuration"""
    env_content = """# Local AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Uncomment and add your API keys if you want to use cloud providers
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_AI_API_KEY=your_google_ai_api_key_here
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file with local AI configuration")
    else:
        print("ℹ️ .env file already exists, skipping creation")

def main():
    """Main setup function"""
    print("🏛️ NSW Government Procurement Platform - Local AI Setup")
    print("=" * 60)
    
    # Step 1: Check Ollama installation
    if not check_ollama_installation():
        print("\n📥 Ollama not found. Installing...")
        if not install_ollama():
            print("\n❌ Please install Ollama manually and run this script again.")
            print("Download from: https://ollama.ai/download")
            return False
        print("✅ Ollama installed successfully")
    
    # Step 2: Check if Ollama is running
    if not check_ollama_running():
        print("\n🚀 Starting Ollama service...")
        if not start_ollama_service():
            print("\n❌ Failed to start Ollama service")
            print("Please start Ollama manually and run this script again")
            return False
        print("✅ Ollama service started")
    
    # Step 3: Check existing models
    existing_models = get_available_models()
    if existing_models:
        print(f"\n✅ Found {len(existing_models)} existing models:")
        for model in existing_models:
            print(f"  - {model}")
    else:
        print("\n📦 No models found. Installing recommended models...")
    
    # Step 4: Install recommended models
    installed_models = install_recommended_models()
    
    if not installed_models:
        print("\n❌ No models were installed successfully")
        return False
    
    # Step 5: Test models
    print(f"\n🧪 Testing installed models...")
    working_models = []
    for model in installed_models:
        if test_model(model):
            working_models.append(model)
    
    # Step 6: Create configuration
    create_env_file()
    
    # Step 7: Summary
    print("\n" + "=" * 60)
    print("🎉 Local AI Setup Complete!")
    print(f"✅ {len(working_models)} models ready for use:")
    for model in working_models:
        print(f"  - {model}")
    
    print(f"\n💡 Your procurement platform will now use local AI models")
    print(f"   No API costs, complete privacy, works offline!")
    
    print(f"\n🚀 To test the integration, run:")
    print(f"   python test_ai_providers.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
