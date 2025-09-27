"""
AI Providers Management UI for Streamlit
Provides interface to manage, test, and configure AI providers
"""

import streamlit as st
import asyncio
import json
from typing import Dict, List, Any
from app.services.ai_providers import AIProvider, ai_manager, generate_ai_response, get_available_ai_providers, get_provider_info

def render_ai_providers_page():
    """Render the AI Providers management page"""
    
    st.markdown("## 🤖 AI Providers Management")
    st.markdown("Configure and test different AI providers for your procurement platform")
    
    # Provider status overview
    render_provider_status()
    
    st.divider()
    
    # Provider configuration
    render_provider_configuration()
    
    st.divider()
    
    # Provider testing
    render_provider_testing()
    
    st.divider()
    
    # Cost tracking
    render_cost_tracking()

def render_provider_status():
    """Show status of all AI providers"""
    
    st.subheader("📊 Provider Status Overview")
    
    available_providers = get_available_ai_providers()
    
    if not available_providers:
        st.warning("⚠️ No AI providers configured. Please set up API keys in your environment variables.")
        return
    
    # Create columns for provider cards
    cols = st.columns(min(len(available_providers), 3))
    
    for i, provider in enumerate(available_providers):
        with cols[i % 3]:
            render_provider_card(provider)

def render_provider_card(provider: AIProvider):
    """Render a provider status card"""
    
    info = get_provider_info(provider)
    
    if not info["available"]:
        st.error(f"❌ {provider.value.upper()}")
        st.caption("Not configured")
        return
    
    # Provider icon and name
    provider_icons = {
        AIProvider.OPENAI: "🤖",
        AIProvider.ANTHROPIC: "🧠", 
        AIProvider.GOOGLE: "🔍",
        AIProvider.OLLAMA: "🏠",
        AIProvider.CURSOR: "⌨️",
        AIProvider.HUGGINGFACE: "🤗"
    }
    
    icon = provider_icons.get(provider, "🤖")
    
    st.markdown(f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <strong>{provider.value.upper()}</strong>
        </div>
        <div style="font-size: 0.9rem; color: #666;">
            <div>Model: {info['model']}</div>
            <div>Max Tokens: {info['max_tokens']:,}</div>
            <div>Temperature: {info['temperature']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_provider_configuration():
    """Render provider configuration interface"""
    
    st.subheader("⚙️ Provider Configuration")
    
    selected_provider = st.selectbox(
        "Select Provider to Configure",
        options=[p.value for p in AIProvider],
        format_func=lambda x: f"{x.upper()} - {get_provider_info(AIProvider(x))['model'] if get_provider_info(AIProvider(x))['available'] else 'Not configured'}"
    )
    
    provider = AIProvider(selected_provider)
    info = get_provider_info(provider)
    
    if info["available"]:
        st.success(f"✅ {provider.value.upper()} is configured and ready to use")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Model**: {info['model']}")
            st.info(f"**Base URL**: {info['base_url']}")
        
        with col2:
            st.info(f"**Max Tokens**: {info['max_tokens']:,}")
            st.info(f"**Temperature**: {info['temperature']}")
    else:
        st.warning(f"⚠️ {provider.value.upper()} is not configured")
        
        # Show configuration instructions
        render_configuration_instructions(provider)

def render_configuration_instructions(provider: AIProvider):
    """Show configuration instructions for a provider"""
    
    instructions = {
        AIProvider.OPENAI: {
            "title": "OpenAI Configuration",
            "steps": [
                "1. Get your API key from https://platform.openai.com/api-keys",
                "2. Set environment variable: `OPENAI_API_KEY=your_key_here`",
                "3. Optionally set: `OPENAI_MODEL=gpt-4` (default: gpt-4)"
            ],
            "cost": "Paid service - ~$0.03 per 1K tokens"
        },
        AIProvider.ANTHROPIC: {
            "title": "Anthropic Claude Configuration", 
            "steps": [
                "1. Get your API key from https://console.anthropic.com/",
                "2. Set environment variable: `ANTHROPIC_API_KEY=your_key_here`",
                "3. Optionally set: `ANTHROPIC_MODEL=claude-3-sonnet-20240229`"
            ],
            "cost": "Paid service - ~$0.003 per 1K input tokens"
        },
        AIProvider.GOOGLE: {
            "title": "Google AI Configuration",
            "steps": [
                "1. Get your API key from https://aistudio.google.com/app/apikey",
                "2. Set environment variable: `GOOGLE_AI_API_KEY=your_key_here`",
                "3. Optionally set: `GOOGLE_MODEL=gemini-pro`"
            ],
            "cost": "Free tier available, then paid"
        },
        AIProvider.OLLAMA: {
            "title": "Ollama Configuration (Local)",
            "steps": [
                "1. Install Ollama from https://ollama.ai/",
                "2. Run: `ollama pull llama3.1:8b`",
                "3. Set environment variable: `OLLAMA_BASE_URL=http://localhost:11434`"
            ],
            "cost": "Free - runs locally on your machine"
        },
        AIProvider.CURSOR: {
            "title": "Cursor API Configuration",
            "steps": [
                "1. Ensure you have Cursor Pro or Team subscription",
                "2. Get API key from Cursor settings",
                "3. Set environment variable: `CURSOR_API_KEY=your_key_here`"
            ],
            "cost": "Included in Cursor subscription"
        },
        AIProvider.HUGGINGFACE: {
            "title": "Hugging Face Configuration",
            "steps": [
                "1. Get your API key from https://huggingface.co/settings/tokens",
                "2. Set environment variable: `HUGGINGFACE_API_KEY=your_key_here`",
                "3. Optionally set: `HUGGINGFACE_MODEL=microsoft/DialoGPT-medium`"
            ],
            "cost": "Free tier available"
        }
    }
    
    config = instructions.get(provider, {})
    
    if config:
        st.markdown(f"### {config['title']}")
        
        for step in config["steps"]:
            st.markdown(step)
        
        st.info(f"**Cost**: {config['cost']}")

def render_provider_testing():
    """Render provider testing interface"""
    
    st.subheader("🧪 Provider Testing")
    
    available_providers = get_available_ai_providers()
    
    if not available_providers:
        st.warning("No providers available for testing")
        return
    
    # Test prompt
    test_prompt = st.text_area(
        "Test Prompt",
        value="Generate a professional tender title for: 'Supply and Installation of HVAC Systems for Blacktown Leisure Centre'",
        height=100
    )
    
    # Provider selection
    selected_provider = st.selectbox(
        "Select Provider to Test",
        options=[None] + [p.value for p in available_providers],
        format_func=lambda x: "Auto-select best provider" if x is None else f"{x.upper()}"
    )
    
    # Test parameters
    col1, col2 = st.columns(2)
    
    with col1:
        max_tokens = st.slider("Max Tokens", 100, 4000, 1000)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
    
    with col2:
        timeout = st.number_input("Timeout (seconds)", 10, 120, 30)
    
    # Test button
    if st.button("🚀 Test Provider", type="primary"):
        if not test_prompt.strip():
            st.error("Please enter a test prompt")
            return
        
        provider = AIProvider(selected_provider) if selected_provider else None
        
        with st.spinner(f"Testing {selected_provider or 'auto-selected provider'}..."):
            try:
                # Run async function
                result = asyncio.run(generate_ai_response(
                    test_prompt,
                    provider,
                    max_tokens=max_tokens,
                    temperature=temperature
                ))
                
                # Display results
                st.success("✅ Test completed successfully!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Provider", result["provider"].upper())
                
                with col2:
                    st.metric("Model", result["model"])
                
                with col3:
                    cost = result.get("cost", 0.0)
                    st.metric("Cost", f"${cost:.4f}")
                
                # Response
                st.subheader("🤖 AI Response")
                st.write(result["response"])
                
                # Usage details
                if result.get("usage"):
                    st.subheader("📊 Usage Details")
                    st.json(result["usage"])
                
                # Store test result in session state
                if "ai_test_results" not in st.session_state:
                    st.session_state["ai_test_results"] = []
                
                st.session_state["ai_test_results"].append({
                    "timestamp": st.session_state.get("test_timestamp", "unknown"),
                    "provider": result["provider"],
                    "model": result["model"],
                    "cost": cost,
                    "response_length": len(result["response"]),
                    "prompt": test_prompt
                })
                
            except Exception as e:
                st.error(f"❌ Test failed: {str(e)}")
                st.exception(e)

def render_cost_tracking():
    """Render cost tracking interface"""
    
    st.subheader("💰 Cost Tracking")
    
    if "ai_test_results" not in st.session_state or not st.session_state["ai_test_results"]:
        st.info("No test results available. Run some provider tests to see cost tracking.")
        return
    
    results = st.session_state["ai_test_results"]
    
    # Cost summary
    total_cost = sum(r["cost"] for r in results)
    total_requests = len(results)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Cost", f"${total_cost:.4f}")
    
    with col2:
        st.metric("Total Requests", total_requests)
    
    with col3:
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        st.metric("Avg Cost/Request", f"${avg_cost:.4f}")
    
    # Provider breakdown
    st.subheader("📊 Provider Usage Breakdown")
    
    provider_stats = {}
    for result in results:
        provider = result["provider"]
        if provider not in provider_stats:
            provider_stats[provider] = {"count": 0, "cost": 0.0}
        provider_stats[provider]["count"] += 1
        provider_stats[provider]["cost"] += result["cost"]
    
    for provider, stats in provider_stats.items():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**{provider.upper()}**")
        
        with col2:
            st.write(f"Requests: {stats['count']}")
        
        with col3:
            st.write(f"Cost: ${stats['cost']:.4f}")
    
    # Detailed results table
    if st.checkbox("Show Detailed Results"):
        st.subheader("📋 Detailed Test Results")
        
        import pandas as pd
        
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # Export results
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Results as CSV",
            data=csv,
            file_name=f"ai_provider_test_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Clear results button
    if st.button("🗑️ Clear All Results"):
        st.session_state["ai_test_results"] = []
        st.rerun()

def render_provider_recommendations():
    """Render provider recommendations based on use case"""
    
    st.subheader("💡 Provider Recommendations")
    
    use_case = st.selectbox(
        "Select Your Use Case",
        [
            "Tender Document Generation",
            "Compliance Checking", 
            "Supplier Evaluation",
            "Cost Optimization",
            "General Text Processing"
        ]
    )
    
    recommendations = {
        "Tender Document Generation": {
            "best": "OpenAI GPT-4",
            "reason": "Excellent for complex document generation with high quality output",
            "alternatives": ["Anthropic Claude", "Google Gemini"]
        },
        "Compliance Checking": {
            "best": "Anthropic Claude",
            "reason": "Superior reasoning and accuracy for compliance analysis",
            "alternatives": ["OpenAI GPT-4", "Local Ollama"]
        },
        "Supplier Evaluation": {
            "best": "OpenAI GPT-4",
            "reason": "Best for structured data extraction and scoring",
            "alternatives": ["Google Gemini", "Hugging Face"]
        },
        "Cost Optimization": {
            "best": "Local Ollama",
            "reason": "No API costs, good for high-volume processing",
            "alternatives": ["Hugging Face", "Google Gemini (free tier)"]
        },
        "General Text Processing": {
            "best": "Auto-select",
            "reason": "Let the system choose the best available provider",
            "alternatives": ["Any configured provider"]
        }
    }
    
    rec = recommendations.get(use_case, {})
    
    if rec:
        st.success(f"**Recommended**: {rec['best']}")
        st.info(f"**Why**: {rec['reason']}")
        
        st.write("**Alternatives**:")
        for alt in rec["alternatives"]:
            st.write(f"• {alt}")

# Integration function for main app
def add_ai_providers_to_sidebar():
    """Add AI providers management to sidebar"""
    
    if st.sidebar.button("🤖 AI Providers"):
        st.session_state["current_page"] = "ai_providers"
        st.rerun()

def render_ai_providers_in_main_app():
    """Render AI providers page in main app"""
    
    if st.session_state.get("current_page") == "ai_providers":
        render_ai_providers_page()
        return True
    return False
