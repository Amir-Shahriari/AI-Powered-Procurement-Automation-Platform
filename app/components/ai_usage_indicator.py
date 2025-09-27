"""
AI Usage Indicator Component
Shows users which AI provider is being used and expected performance
"""

import streamlit as st
from typing import Optional, Dict, Any
from ..services.ai_usage_monitor import (
    get_ai_usage_monitor, 
    AIProvider, 
    get_user_friendly_time_estimate,
    get_ai_provider_info
)

def show_ai_usage_indicator(provider: str, task_type: str, show_details: bool = True):
    """Show AI usage indicator with time estimate"""
    
    try:
        # Get provider information
        provider_info = get_ai_provider_info(provider)
        if not provider_info:
            st.warning("⚠️ Unknown AI provider")
            return
        
        # Get time estimate
        time_estimate = get_user_friendly_time_estimate(task_type, provider)
        
        # Create indicator based on provider type
        if provider_info.is_local:
            # Local AI indicator
            st.info(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; color: white;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">🏠</span>
                    <div>
                        <strong>Local AI Processing</strong><br>
                        <small>Using {provider_info.model} • {time_estimate} • Zero Cost</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if show_details:
                with st.expander("🏠 Local AI Details", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**✅ Benefits:**")
                        benefits = [
                            "🔒 Complete data privacy",
                            "💰 Zero ongoing costs",
                            "🏠 Runs on your hardware",
                            "🛡️ No external data transmission"
                        ]
                        for benefit in benefits:
                            st.markdown(f"• {benefit}")
                    
                    with col2:
                        st.markdown("**⚠️ Considerations:**")
                        limitations = [
                            "⏱️ Slower response times",
                            "💻 Requires local hardware",
                            "🔧 Setup complexity",
                            "📊 Limited model variety"
                        ]
                        for limitation in limitations:
                            st.markdown(f"• {limitation}")
                    
                    st.info(f"**Expected Time:** {time_estimate} for {task_type.replace('_', ' ').title()}")
        
        else:
            # Cloud AI indicator
            st.success(f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 1rem; border-radius: 8px; color: white;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">☁️</span>
                    <div>
                        <strong>Cloud AI Processing</strong><br>
                        <small>Using {provider_info.model} • {time_estimate} • ${provider_info.cost_per_request:.3f}/request</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if show_details:
                with st.expander("☁️ Cloud AI Details", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**✅ Benefits:**")
                        benefits = [
                            "⚡ Fast response times",
                            "🎯 High-quality results",
                            "🌐 Reliable cloud infrastructure",
                            "🔄 Automatic scaling"
                        ]
                        for benefit in benefits:
                            st.markdown(f"• {benefit}")
                    
                    with col2:
                        st.markdown("**⚠️ Considerations:**")
                        limitations = [
                            "🌐 Requires internet connection",
                            "💰 Per-request costs",
                            "🔒 Data sent to external servers",
                            "⚡ Dependent on API availability"
                        ]
                        for limitation in limitations:
                            st.markdown(f"• {limitation}")
                    
                    st.info(f"**Expected Time:** {time_estimate} for {task_type.replace('_', ' ').title()}")
                    if provider_info.cost_per_request > 0:
                        st.warning(f"**Cost:** Approximately ${provider_info.cost_per_request:.3f} per request")

    except Exception as e:
        st.error(f"❌ Error displaying AI usage indicator: {e}")

def show_ai_processing_status(provider: str, task_type: str, progress_text: str = "Processing..."):
    """Show AI processing status with progress"""
    
    try:
        provider_info = get_ai_provider_info(provider)
        time_estimate = get_user_friendly_time_estimate(task_type, provider)
        
        if provider_info and provider_info.is_local:
            # Local AI processing status
            st.info(f"""
            <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 1rem; border-radius: 4px;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">🏠</span>
                    <div>
                        <strong>Local AI Processing</strong><br>
                        <small>{progress_text} • Expected: {time_estimate}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Cloud AI processing status
            st.success(f"""
            <div style="background: #e8f5e8; border-left: 4px solid #4caf50; padding: 1rem; border-radius: 4px;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">☁️</span>
                    <div>
                        <strong>Cloud AI Processing</strong><br>
                        <small>{progress_text} • Expected: {time_estimate}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.warning(f"⚠️ Processing with {provider}...")

def show_ai_provider_comparison():
    """Show comparison between different AI providers"""
    
    st.markdown("## 🤖 AI Provider Comparison")
    
    # Get monitor instance
    monitor = get_ai_usage_monitor()
    
    # Create comparison table
    comparison_data = []
    
    for provider in AIProvider:
        info = monitor.get_provider_info(provider)
        if info:
            comparison_data.append({
                "Provider": provider.value.replace("_", " ").title(),
                "Type": "🏠 Local" if info.is_local else "☁️ Cloud",
                "Model": info.model,
                "Avg Time": f"{info.estimated_time_seconds:.1f}s",
                "Cost/Request": f"${info.cost_per_request:.3f}" if info.cost_per_request > 0 else "Free",
                "Reliability": f"{info.reliability_score:.1%}",
                "Description": info.description
            })
    
    # Display as table
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Provider": st.column_config.TextColumn("Provider", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "Avg Time": st.column_config.TextColumn("Avg Time", width="small"),
            "Cost/Request": st.column_config.TextColumn("Cost", width="small"),
            "Reliability": st.column_config.TextColumn("Reliability", width="small"),
            "Description": st.column_config.TextColumn("Description", width="large")
        }
    )
    
    # Add recommendations
    st.markdown("### 💡 Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏠 Use Local AI when:**")
        st.markdown("""
        • Data privacy is critical
        • Cost reduction is important
        • You have powerful hardware
        • Processing can wait (non-urgent)
        """)
    
    with col2:
        st.markdown("**☁️ Use Cloud AI when:**")
        st.markdown("""
        • Speed is critical
        • You need the latest models
        • Limited local hardware
        • High-volume processing
        """)

def show_ai_usage_statistics():
    """Show AI usage statistics"""
    
    monitor = get_ai_usage_monitor()
    stats = monitor.get_usage_statistics()
    
    if "message" in stats:
        st.info("📊 No AI usage data available yet. Start using AI features to see statistics.")
        return
    
    st.markdown("## 📊 AI Usage Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Operations", stats["total_operations"])
    
    with col2:
        st.metric("Local Usage", f"{stats['local_percentage']:.1f}%")
    
    with col3:
        st.metric("Time Accuracy", f"{stats['avg_time_accuracy']:.1%}")
    
    with col4:
        st.metric("Cost Savings", f"${stats['cost_savings_from_local']:.3f}")
    
    # Usage breakdown
    if stats["total_operations"] > 0:
        st.markdown("### 📈 Usage Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**🏠 Local Operations:** {stats['local_operations']}")
            st.markdown(f"**☁️ Cloud Operations:** {stats['cloud_operations']}")
        
        with col2:
            st.markdown(f"**💰 Total Cost:** ${stats['total_cost']:.3f}")
            st.markdown(f"**💵 Savings from Local:** ${stats['cost_savings_from_local']:.3f}")
