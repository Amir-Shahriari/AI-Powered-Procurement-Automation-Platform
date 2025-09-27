"""
AI Model Detection and Selection System
Automatically detects PC capabilities and selects the best AI model
"""
import streamlit as st
import torch
import platform
import psutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ModelType(Enum):
    """Available AI model types"""
    LOCAL_CPU = "local_cpu"
    LOCAL_GPU = "local_gpu"
    CLOUD_API = "cloud_api"
    HYBRID = "hybrid"

@dataclass
class SystemCapabilities:
    """System hardware capabilities"""
    has_gpu: bool
    gpu_memory_gb: float
    cpu_cores: int
    ram_gb: float
    platform: str
    cuda_available: bool
    cuda_version: Optional[str]
    gpu_name: Optional[str]

@dataclass
class AIModelConfig:
    """AI Model configuration"""
    model_type: ModelType
    model_name: str
    provider: str
    max_tokens: int
    temperature: float
    description: str
    performance_score: float
    cost_per_token: float = 0.0

class AIModelDetector:
    """Detects system capabilities and recommends optimal AI model"""
    
    def __init__(self):
        self.capabilities = self._detect_system_capabilities()
        self.available_models = self._get_available_models()
    
    def _detect_system_capabilities(self) -> SystemCapabilities:
        """Detect system hardware capabilities"""
        try:
            # GPU Detection
            has_gpu = torch.cuda.is_available()
            gpu_memory_gb = 0.0
            gpu_name = None
            cuda_version = None
            
            if has_gpu:
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
            
            # CPU and RAM
            cpu_cores = psutil.cpu_count(logical=False)
            ram_gb = psutil.virtual_memory().total / (1024**3)
            
            return SystemCapabilities(
                has_gpu=has_gpu,
                gpu_memory_gb=gpu_memory_gb,
                cpu_cores=cpu_cores,
                ram_gb=ram_gb,
                platform=platform.system(),
                cuda_available=has_gpu,
                cuda_version=cuda_version,
                gpu_name=gpu_name
            )
        except Exception as e:
            st.warning(f"Error detecting system capabilities: {e}")
            return SystemCapabilities(
                has_gpu=False,
                gpu_memory_gb=0.0,
                cpu_cores=4,
                ram_gb=8.0,
                platform=platform.system(),
                cuda_available=False,
                cuda_version=None,
                gpu_name=None
            )
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available and running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _get_available_models(self) -> List[AIModelConfig]:
        """Get list of available AI models based on system capabilities"""
        models = []
        ollama_available = self._check_ollama_available()
        
        # Local GPU models (if GPU available) - lowered threshold
        if self.capabilities.has_gpu and self.capabilities.gpu_memory_gb >= 4:
            models.extend([
                AIModelConfig(
                    model_type=ModelType.LOCAL_GPU,
                    model_name="llama-3.1-8b-instruct",
                    provider="Ollama",
                    max_tokens=4096,
                    temperature=0.7,
                    description="High-performance local GPU model (8B parameters)",
                    performance_score=9.0,
                    cost_per_token=0.0
                ),
                AIModelConfig(
                    model_type=ModelType.LOCAL_GPU,
                    model_name="mistral-7b-instruct",
                    provider="Ollama",
                    max_tokens=4096,
                    temperature=0.7,
                    description="Efficient local GPU model (7B parameters)",
                    performance_score=8.5,
                    cost_per_token=0.0
                )
            ])
        
        # Local CPU models - Ollama (if available and running)
        if self.capabilities.ram_gb >= 8 and ollama_available:
            models.extend([
                AIModelConfig(
                    model_type=ModelType.LOCAL_CPU,
                    model_name="llama3.2:3b",
                    provider="Ollama",
                    max_tokens=2048,
                    temperature=0.7,
                    description="Fast local CPU model (3B parameters) - Ollama",
                    performance_score=7.5,
                    cost_per_token=0.0
                ),
                AIModelConfig(
                    model_type=ModelType.LOCAL_CPU,
                    model_name="llama3.2:1b",
                    provider="Ollama",
                    max_tokens=2048,
                    temperature=0.7,
                    description="Ultra-fast local CPU model (1B parameters) - Ollama",
                    performance_score=6.5,
                    cost_per_token=0.0
                ),
                AIModelConfig(
                    model_type=ModelType.LOCAL_CPU,
                    model_name="phi3:mini",
                    provider="Ollama",
                    max_tokens=2048,
                    temperature=0.7,
                    description="Efficient local CPU model (3.8B parameters) - Ollama",
                    performance_score=7.0,
                    cost_per_token=0.0
                ),
                AIModelConfig(
                    model_type=ModelType.LOCAL_CPU,
                    model_name="gemma2:2b",
                    provider="Ollama",
                    max_tokens=2048,
                    temperature=0.7,
                    description="Google Gemma 2B model - Ollama",
                    performance_score=6.8,
                    cost_per_token=0.0
                )
            ])
        elif self.capabilities.ram_gb >= 8:
            # Add a note that Ollama is not running
            models.append(AIModelConfig(
                model_type=ModelType.LOCAL_CPU,
                model_name="ollama-not-running",
                provider="Ollama",
                max_tokens=0,
                temperature=0.7,
                description="⚠️ Ollama not running - Install and start Ollama to use local models",
                performance_score=0.0,
                cost_per_token=0.0
            ))
        
        # Note: Cloud API models removed - only Gemini and local models are available
        # Gemini models are added dynamically via _get_gemini_model() method
        
        return models
    
    def get_recommended_model(self) -> AIModelConfig:
        """Get the recommended AI model - prioritize Gemini 1.5 Flash"""
        # First, try to get Gemini model if available
        gemini_model = self._get_gemini_model()
        if gemini_model:
            return gemini_model
        
        # If no Gemini available, fallback to local models
        if not self.available_models:
            # Fallback to basic local model (no API dependency)
            return AIModelConfig(
                model_type=ModelType.LOCAL_CPU,
                model_name="basic-fallback",
                provider="none",
                max_tokens=512,
                temperature=0.7,
                description="Basic fallback model (no AI capabilities)",
                performance_score=1.0,
                cost_per_token=0.0
            )
        
        # Sort by performance score (highest first)
        sorted_models = sorted(self.available_models, key=lambda x: x.performance_score, reverse=True)
        
        # Prefer local GPU if available and powerful enough
        if self.capabilities.has_gpu and self.capabilities.gpu_memory_gb >= 4:
            for model in sorted_models:
                if model.model_type == ModelType.LOCAL_GPU:
                    return model
        
        # Prefer local CPU if sufficient RAM
        if self.capabilities.ram_gb >= 8:
            for model in sorted_models:
                if model.model_type == ModelType.LOCAL_CPU:
                    return model
        
        # Fallback to first available model
        return sorted_models[0]
    
    def _get_gemini_model(self):
        """Get Gemini model configuration if available"""
        try:
            from app.config import settings
            if settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY) > 10:
                return AIModelConfig(
                    model_type=ModelType.CLOUD_API,
                    model_name=settings.GEMINI_MODEL,
                    provider="Google",
                    max_tokens=8192,
                    temperature=0.3,
                    description=f"Google {settings.GEMINI_MODEL} - Cloud API",
                    performance_score=9.5,  # High priority
                    cost_per_token=0.000125
                )
        except Exception:
            pass
        return None
    
    def _get_fallback_model(self):
        """Get fallback model when no cloud models are available"""
        return AIModelConfig(
            model_type=ModelType.LOCAL_CPU,
            model_name="fallback",
            provider="none",
            max_tokens=512,
            temperature=0.7,
            description="Fallback model (no AI capabilities)",
            performance_score=1.0,
            cost_per_token=0.0
        )
    
    def get_model_options(self) -> List[AIModelConfig]:
        """Get available model options - prioritize Gemini, then local models only"""
        options = []
        
        # Add Gemini first if available
        gemini_model = self._get_gemini_model()
        if gemini_model:
            options.append(gemini_model)
        
        # Add only local models (no other cloud APIs)
        for model in self.available_models:
            if model.model_type in [ModelType.LOCAL_CPU, ModelType.LOCAL_GPU]:
                options.append(model)
        
        return sorted(options, key=lambda x: x.performance_score, reverse=True)
    
    def display_system_info(self) -> None:
        """Display system capabilities in sidebar"""
        with st.sidebar:
            st.subheader("🖥️ System Capabilities")
            
            # GPU Info
            if self.capabilities.has_gpu:
                st.success(f"🎮 GPU: {self.capabilities.gpu_name}")
                st.info(f"💾 GPU Memory: {self.capabilities.gpu_memory_gb:.1f} GB")
                if self.capabilities.cuda_version:
                    st.info(f"🔧 CUDA: {self.capabilities.cuda_version}")
            else:
                st.warning("🎮 No GPU detected")
            
            # CPU Info
            st.info(f"⚙️ CPU Cores: {self.capabilities.cpu_cores}")
            st.info(f"💾 RAM: {self.capabilities.ram_gb:.1f} GB")
            st.info(f"🖥️ Platform: {self.capabilities.platform}")
    
    def display_model_selector(self) -> AIModelConfig:
        """Display model selector in sidebar"""
        with st.sidebar:
            st.subheader("🤖 AI Mode Selection")
            
            # AI Mode Selection
            ai_mode = st.radio(
                "Choose AI Mode:",
                ["🌐 Cloud API", "🖥️ Local Ollama", "📝 Manual Mode"],
                help="Select how you want to generate AI content"
            )
            
            # Model selection based on mode
            if ai_mode == "🌐 Cloud API":
                return self.display_cloud_model_selector()
            elif ai_mode == "🖥️ Local Ollama":
                return self.display_ollama_model_selector()
            else:  # Manual Mode
                return self.display_manual_mode()
    
    def display_cloud_model_selector(self) -> AIModelConfig:
        """Display cloud API model selector - only Gemini available"""
        with st.sidebar:
            st.subheader("☁️ Cloud API Models")
            
            # Get Gemini model if available
            gemini_model = self._get_gemini_model()
            
            if not gemini_model:
                st.warning("No cloud models available - Gemini API key not configured")
                return self._get_fallback_model()
            
            # Display Gemini model info
            st.info(f"🤖 **{gemini_model.model_name}**")
            st.caption(f"Provider: {gemini_model.provider}")
            st.caption(f"Max Tokens: {gemini_model.max_tokens:,}")
            st.caption(f"Performance: {gemini_model.performance_score}/10")
            st.caption(f"Cost: ${gemini_model.cost_per_token:.6f}/token")
            
            # Since only Gemini is available, return it directly
            return gemini_model
    
    def display_ollama_model_selector(self) -> AIModelConfig:
        """Display Ollama model selector"""
        with st.sidebar:
            st.subheader("🖥️ Local Ollama Models")
            
            # Check if Ollama is running
            ollama_available = self._check_ollama_available()
            
            if not ollama_available:
                st.error("⚠️ Ollama is not running!")
                st.markdown("""
                **To use local models:**
                1. Install Ollama from https://ollama.ai
                2. Start Ollama: `ollama serve`
                3. Pull a model: `ollama pull llama3.2:3b`
                """)
                return self._get_fallback_model()
            
            # Get available Ollama models
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    ollama_models = response.json().get("models", [])
                    
                    if not ollama_models:
                        st.warning("No models found in Ollama. Pull a model first:")
                        st.code("ollama pull llama3.2:3b")
                        return self._get_fallback_model()
                    
                    # Create model options
                    model_options = []
                    model_dict = {}
                    
                    for model_info in ollama_models:
                        model_name = model_info.get("name", "")
                        model_label = f"{model_name}"
                        model_options.append(model_label)
                        
                        # Create AIModelConfig for Ollama model
                        ollama_model = AIModelConfig(
                            model_type=ModelType.LOCAL_CPU,
                            model_name=model_name,
                            provider="Ollama",
                            max_tokens=2048,
                            temperature=0.7,
                            description=f"Local Ollama model: {model_name}",
                            performance_score=7.0,
                            cost_per_token=0.0
                        )
                        model_dict[model_label] = ollama_model
                    
                    # Model selector
                    selected_label = st.selectbox(
                        "Select Ollama Model:",
                        model_options,
                        index=0
                    )
                    
                    selected_model = model_dict[selected_label]
                    
                    # Display model info
                    st.success(f"✅ **Model:** {selected_model.model_name}")
                    st.info(f"**Provider:** {selected_model.provider}")
                    st.info(f"**Type:** Local CPU")
                    st.info(f"**Cost:** Free")
                    
                    return selected_model
                else:
                    st.error(f"Ollama API error: {response.status_code}")
                    return self._get_fallback_model()
                    
            except Exception as e:
                st.error(f"Error connecting to Ollama: {e}")
                return self._get_fallback_model()
    
    def display_manual_mode(self) -> AIModelConfig:
        """Display manual mode (no AI)"""
        with st.sidebar:
            st.subheader("📝 Manual Mode")
            st.info("No AI processing - uses template-based generation")
            
            return AIModelConfig(
                model_type=ModelType.LOCAL_CPU,
                model_name="manual-mode",
                provider="none",
                max_tokens=0,
                temperature=0.7,
                description="Manual mode - no AI processing",
                performance_score=1.0,
                cost_per_token=0.0
            )

# Global detector instance
@st.cache_resource
def get_ai_detector() -> AIModelDetector:
    """Get cached AI detector instance"""
    return AIModelDetector()
