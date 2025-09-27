"""
Local AI Model Integration Service
Provides local AI capabilities using Ollama and other local models
"""

import os
import json
import requests
import subprocess
import time
import platform
import psutil
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LocalAIManager:
    """Local AI model manager with automatic fallback"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.available_models = []
        self.current_model = None
        self.system_info = self._analyze_system()
        self._check_ollama_status()
    
    def _analyze_system(self) -> Dict[str, Any]:
        """Analyze system capabilities for optimal model selection"""
        logger.info("🔍 Analyzing system capabilities...")
        
        system_info = {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "gpu_info": self._detect_gpu(),
            "recommended_models": [],
            "performance_tier": "unknown"
        }
        
        # Determine performance tier
        system_info["performance_tier"] = self._determine_performance_tier(system_info)
        
        # Get recommended models based on system capabilities
        system_info["recommended_models"] = self._get_recommended_models_for_system(system_info)
        
        logger.info(f"System analysis complete: {system_info['performance_tier']} tier")
        return system_info
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU capabilities"""
        gpu_info = {
            "available": False,
            "type": None,
            "memory_gb": 0,
            "cuda_available": False,
            "vram_gb": 0,
            "recommended_for_ai": False
        }
        
        try:
            # Try to detect NVIDIA GPU
            if self._detect_nvidia_gpu():
                gpu_info.update(self._get_nvidia_info())
            # Try to detect AMD GPU
            elif self._detect_amd_gpu():
                gpu_info.update(self._get_amd_info())
            # Try to detect Intel GPU
            elif self._detect_intel_gpu():
                gpu_info.update(self._get_intel_info())
            # Try to detect Apple Silicon GPU
            elif self._detect_apple_gpu():
                gpu_info.update(self._get_apple_info())
                
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
        
        return gpu_info
    
    def _detect_nvidia_gpu(self) -> bool:
        """Detect if NVIDIA GPU is available"""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_nvidia_info(self) -> Dict[str, Any]:
        """Get NVIDIA GPU information"""
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    gpu_name, memory_mb = lines[0].split(', ')
                    memory_gb = round(int(memory_mb) / 1024, 1)
                    
                    return {
                        "available": True,
                        "type": "nvidia",
                        "name": gpu_name.strip(),
                        "memory_gb": memory_gb,
                        "vram_gb": memory_gb,
                        "cuda_available": True,
                        "recommended_for_ai": memory_gb >= 4  # 4GB+ recommended for AI
                    }
        except Exception as e:
            logger.warning(f"NVIDIA GPU info failed: {e}")
        
        return {"available": False}
    
    def _detect_amd_gpu(self) -> bool:
        """Detect if AMD GPU is available"""
        try:
            result = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_amd_info(self) -> Dict[str, Any]:
        """Get AMD GPU information"""
        try:
            result = subprocess.run(["rocm-smi", "--showproductname"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return {
                    "available": True,
                    "type": "amd",
                    "name": result.stdout.strip(),
                    "memory_gb": 8,  # Estimate
                    "vram_gb": 8,
                    "cuda_available": False,
                    "recommended_for_ai": True
                }
        except Exception as e:
            logger.warning(f"AMD GPU info failed: {e}")
        
        return {"available": False}
    
    def _detect_intel_gpu(self) -> bool:
        """Detect if Intel GPU is available"""
        try:
            result = subprocess.run(["intel_gpu_top"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_intel_info(self) -> Dict[str, Any]:
        """Get Intel GPU information"""
        return {
            "available": True,
            "type": "intel",
            "name": "Intel Integrated Graphics",
            "memory_gb": 2,  # Shared memory
            "vram_gb": 0,
            "cuda_available": False,
            "recommended_for_ai": False  # Usually not powerful enough
        }
    
    def _detect_apple_gpu(self) -> bool:
        """Detect if Apple Silicon GPU is available"""
        return platform.system() == "Darwin" and platform.machine() == "arm64"
    
    def _get_apple_info(self) -> Dict[str, Any]:
        """Get Apple Silicon GPU information"""
        try:
            # Try to get memory info
            result = subprocess.run(["system_profiler", "SPHardwareDataType"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout
                if "Apple M" in output:
                    # Estimate based on M-series chip
                    if "M1" in output:
                        memory_gb = 8  # Base M1
                    elif "M1 Pro" in output or "M1 Max" in output:
                        memory_gb = 16
                    elif "M2" in output:
                        memory_gb = 8
                    elif "M2 Pro" in output or "M2 Max" in output:
                        memory_gb = 16
                    else:
                        memory_gb = 8  # Default
                    
                    return {
                        "available": True,
                        "type": "apple",
                        "name": "Apple Silicon GPU",
                        "memory_gb": memory_gb,
                        "vram_gb": memory_gb,  # Unified memory
                        "cuda_available": False,
                        "recommended_for_ai": memory_gb >= 8
                    }
        except Exception as e:
            logger.warning(f"Apple GPU info failed: {e}")
        
        return {"available": False}
    
    def _determine_performance_tier(self, system_info: Dict[str, Any]) -> str:
        """Determine system performance tier"""
        memory_gb = system_info["memory_gb"]
        cpu_count = system_info["cpu_count"]
        gpu = system_info["gpu_info"]
        
        # High-end tier
        if (memory_gb >= 32 and cpu_count >= 8) or (gpu["available"] and gpu["vram_gb"] >= 8):
            return "high_end"
        
        # Mid-tier
        elif (memory_gb >= 16 and cpu_count >= 4) or (gpu["available"] and gpu["vram_gb"] >= 4):
            return "mid_tier"
        
        # Entry tier
        elif memory_gb >= 8 and cpu_count >= 2:
            return "entry_level"
        
        # Low-end
        else:
            return "low_end"
    
    def _get_recommended_models_for_system(self, system_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended models based on system capabilities"""
        tier = system_info["performance_tier"]
        gpu = system_info["gpu_info"]
        memory_gb = system_info["memory_gb"]
        
        recommendations = []
        
        if tier == "high_end":
            recommendations = [
                {
                    "model": "llama3.1:8b",
                    "size_gb": 8,
                    "speed": "fast",
                    "quality": "excellent",
                    "use_cases": ["tender_generation", "compliance_checking", "document_analysis"],
                    "reason": "Best quality for complex tasks"
                },
                {
                    "model": "llama3:8b", 
                    "size_gb": 8,
                    "speed": "fast",
                    "quality": "excellent",
                    "use_cases": ["tender_generation", "supplier_evaluation"],
                    "reason": "Excellent balance of speed and quality"
                },
                {
                    "model": "mistral:7b",
                    "size_gb": 4,
                    "speed": "very_fast",
                    "quality": "very_good",
                    "use_cases": ["document_analysis", "compliance_checking"],
                    "reason": "Fast and accurate for structured tasks"
                }
            ]
        elif tier == "mid_tier":
            recommendations = [
                {
                    "model": "phi3:3.8b",
                    "size_gb": 4,
                    "speed": "very_fast",
                    "quality": "good",
                    "use_cases": ["compliance_checking", "fast_processing"],
                    "reason": "Optimal for your system - fast and efficient"
                },
                {
                    "model": "mistral:7b",
                    "size_gb": 4,
                    "speed": "fast",
                    "quality": "very_good",
                    "use_cases": ["document_analysis", "tender_generation"],
                    "reason": "Good balance for mid-tier systems"
                },
                {
                    "model": "codellama:7b",
                    "size_gb": 4,
                    "speed": "fast",
                    "quality": "good",
                    "use_cases": ["supplier_evaluation", "structured_tasks"],
                    "reason": "Good for structured data processing"
                }
            ]
        elif tier == "entry_level":
            recommendations = [
                {
                    "model": "phi3:3.8b",
                    "size_gb": 4,
                    "speed": "fast",
                    "quality": "good",
                    "use_cases": ["compliance_checking", "fast_processing"],
                    "reason": "Best for entry-level systems - fast and efficient"
                },
                {
                    "model": "gemma:7b",
                    "size_gb": 4,
                    "speed": "fast",
                    "quality": "good",
                    "use_cases": ["general_purpose", "document_analysis"],
                    "reason": "Good performance on limited hardware"
                }
            ]
        else:  # low_end
            recommendations = [
                {
                    "model": "phi3:3.8b",
                    "size_gb": 4,
                    "speed": "moderate",
                    "quality": "good",
                    "use_cases": ["compliance_checking", "basic_tasks"],
                    "reason": "Only recommended model for low-end systems"
                }
            ]
        
        # Filter based on available memory
        available_memory = memory_gb - 4  # Reserve 4GB for system
        recommendations = [r for r in recommendations if r["size_gb"] <= available_memory]
        
        return recommendations
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information"""
        return self.system_info.copy()
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        return self.system_info["gpu_info"].copy()
    
    def get_recommended_models(self) -> List[Dict[str, Any]]:
        """Get recommended models for current system"""
        return self.system_info["recommended_models"].copy()
    
    def get_performance_tier(self) -> str:
        """Get system performance tier"""
        return self.system_info["performance_tier"]
    
    def _check_ollama_status(self) -> bool:
        """Check if Ollama is running and get available models"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.ok:
                models_data = response.json()
                self.available_models = [model["name"] for model in models_data.get("models", [])]
                logger.info(f"Found {len(self.available_models)} local models: {self.available_models}")
                return True
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if local AI is available"""
        return len(self.available_models) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available local models"""
        return self.available_models.copy()
    
    def install_model(self, model_name: str) -> bool:
        """Install a model using Ollama"""
        try:
            logger.info(f"Installing model: {model_name}")
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed model: {model_name}")
                self._check_ollama_status()  # Refresh available models
                return True
            else:
                logger.error(f"Failed to install model {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing model {model_name}")
            return False
        except Exception as e:
            logger.error(f"Error installing model {model_name}: {e}")
            return False
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using local model"""
        
        if not self.is_available():
            raise Exception("No local models available")
        
        # Select model
        selected_model = model or self._get_best_model()
        if not selected_model:
            raise Exception("No suitable local model found")
        
        try:
            response = await self._call_ollama(
                prompt, 
                selected_model, 
                max_tokens, 
                temperature
            )
            
            return {
                "provider": "ollama_local",
                "model": selected_model,
                "response": response.get("response", ""),
                "usage": None,
                "cost": 0.0,  # Local models are free
                "local": True
            }
            
        except Exception as e:
            logger.error(f"Local AI generation failed: {e}")
            raise
    
    def _get_best_model(self) -> Optional[str]:
        """Get the best available local model for the task based on system capabilities"""
        
        # Get recommended models for current system
        recommended = self.get_recommended_models()
        
        # First, try recommended models in order
        for rec in recommended:
            if rec["model"] in self.available_models:
                logger.info(f"Using recommended model for {self.get_performance_tier()} system: {rec['model']}")
                return rec["model"]
        
        # Fallback to general preference order
        preferred_models = [
            "llama3.1:8b",      # Best general purpose
            "llama3:8b",        # Good general purpose
            "mistral:7b",       # Good for code and documents
            "codellama:7b",     # Good for structured tasks
            "phi3:3.8b",        # Fast and efficient
            "gemma:7b",         # Google's model
            "llama2:7b",        # Decent general purpose
            "qwen:7b"           # Alibaba's model
        ]
        
        for preferred in preferred_models:
            if preferred in self.available_models:
                logger.info(f"Using fallback model: {preferred}")
                return preferred
        
        # If no preferred model found, return the first available
        return self.available_models[0] if self.available_models else None
    
    async def _call_ollama(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Call Ollama API"""
        
        url = f"{self.ollama_base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            timeout=120,  # 2 minutes timeout for local generation
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/show",
                json={"name": model_name},
                timeout=10
            )
            
            if response.ok:
                return response.json()
            else:
                return {"error": f"Model {model_name} not found"}
                
        except Exception as e:
            return {"error": str(e)}

# Global instance
local_ai = LocalAIManager()

# Convenience functions
def is_local_ai_available() -> bool:
    """Check if local AI is available"""
    return local_ai.is_available()

def get_local_models() -> List[str]:
    """Get available local models"""
    return local_ai.get_available_models()

async def generate_local_response(
    prompt: str, 
    model: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate response using local AI"""
    return await local_ai.generate_response(prompt, model, **kwargs)

def install_local_model(model_name: str) -> bool:
    """Install a local model"""
    return local_ai.install_model(model_name)

# Convenience functions
def get_system_info() -> Dict[str, Any]:
    """Get detailed system information"""
    return local_ai.get_system_info()

def get_gpu_info() -> Dict[str, Any]:
    """Get GPU information"""
    return local_ai.get_gpu_info()

def get_performance_tier() -> str:
    """Get system performance tier"""
    return local_ai.get_performance_tier()

def get_system_recommendations() -> List[Dict[str, Any]]:
    """Get recommended models for current system"""
    return local_ai.get_recommended_models()

def get_best_model_for_task(task_type: str) -> Optional[str]:
    """Get best available model for specific task type"""
    recommendations = local_ai.get_recommended_models()
    
    # Map task types to model preferences
    task_preferences = {
        "tender_generation": ["llama3.1:8b", "llama3:8b", "mistral:7b"],
        "compliance_checking": ["phi3:3.8b", "mistral:7b", "llama3:8b"],
        "document_analysis": ["mistral:7b", "llama3.1:8b", "phi3:3.8b"],
        "supplier_evaluation": ["codellama:7b", "llama3:8b", "mistral:7b"],
        "general_purpose": ["llama3.1:8b", "llama3:8b", "phi3:3.8b"],
        "fast_processing": ["phi3:3.8b", "gemma:7b", "mistral:7b"]
    }
    
    preferred_models = task_preferences.get(task_type, ["llama3.1:8b", "phi3:3.8b"])
    
    # First try system recommendations
    for rec in recommendations:
        if rec["model"] in preferred_models and rec["model"] in local_ai.available_models:
            return rec["model"]
    
    # Then try preferred models
    for model in preferred_models:
        if model in local_ai.available_models:
            return model
    
    # Fallback to best available
    return local_ai._get_best_model()

def print_system_analysis():
    """Print detailed system analysis"""
    info = get_system_info()
    gpu = info["gpu_info"]
    
    print("🖥️  System Analysis Report")
    print("=" * 50)
    print(f"Platform: {info['platform']} ({info['architecture']})")
    print(f"CPU Cores: {info['cpu_count']}")
    print(f"Memory: {info['memory_gb']} GB")
    print(f"Performance Tier: {info['performance_tier'].upper()}")
    
    print(f"\n🎮 GPU Information:")
    if gpu["available"]:
        print(f"  Type: {gpu['type'].upper()}")
        print(f"  Name: {gpu['name']}")
        print(f"  Memory: {gpu['memory_gb']} GB")
        print(f"  AI Recommended: {'✅ Yes' if gpu['recommended_for_ai'] else '❌ No'}")
        if gpu["cuda_available"]:
            print(f"  CUDA: ✅ Available")
    else:
        print("  ❌ No GPU detected")
    
    print(f"\n🤖 Recommended Models:")
    recommendations = info["recommended_models"]
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['model']} ({rec['size_gb']}GB)")
            print(f"     Quality: {rec['quality']} | Speed: {rec['speed']}")
            print(f"     Use cases: {', '.join(rec['use_cases'])}")
            print(f"     Reason: {rec['reason']}")
    else:
        print("  ❌ No models recommended for this system")
    
    print(f"\n💡 Recommendations:")
    if info["performance_tier"] == "high_end":
        print("  🚀 Your system can handle the best AI models!")
        print("  💰 Consider using llama3.1:8b for maximum quality")
    elif info["performance_tier"] == "mid_tier":
        print("  ⚡ Your system is well-balanced for AI tasks")
        print("  🎯 phi3:3.8b is optimal for speed and efficiency")
    elif info["performance_tier"] == "entry_level":
        print("  🔧 Your system can run basic AI models")
        print("  ⚡ Stick to phi3:3.8b for best performance")
    else:
        print("  ⚠️  Your system may struggle with AI models")
        print("  💡 Consider upgrading RAM or using cloud APIs")
