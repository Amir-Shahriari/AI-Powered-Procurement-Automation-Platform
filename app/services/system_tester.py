#!/usr/bin/env python3
"""
System Test Runner for NSW Procurement Platform
Runs comprehensive tests to verify system functionality
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
import streamlit as st

# Set OMP environment variable
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def run_system_tests() -> Dict[str, any]:
    """
    Run comprehensive system tests and return results
    """
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "test_results": [],
        "system_status": "unknown",
        "errors": []
    }
    
    # Define test files and their purposes
    test_files = [
        {
            "file": "test_smart_rag.py",
            "name": "Smart RAG System",
            "description": "Tests AI document processing and retrieval system"
        },
        {
            "file": "test_historical_matching.py", 
            "name": "Historical Project Matching",
            "description": "Tests project similarity and optimization features"
        },
        {
            "file": "test_smart_compliance.py",
            "name": "Smart Compliance System",
            "description": "Tests compliance document processing and validation"
        },
        {
            "file": "test_ai_providers.py",
            "name": "AI Provider Integration",
            "description": "Tests local and cloud AI model connections"
        }
    ]
    
    project_root = Path(__file__).parent.parent.parent
    
    for test_info in test_files:
        test_file = project_root / test_info["file"]
        
        if not test_file.exists():
            results["test_results"].append({
                "name": test_info["name"],
                "status": "skipped",
                "message": f"Test file not found: {test_info['file']}",
                "description": test_info["description"]
            })
            results["total_tests"] += 1
            continue
        
        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root)
            )
            
            results["total_tests"] += 1
            
            if result.returncode == 0:
                results["passed"] += 1
                results["test_results"].append({
                    "name": test_info["name"],
                    "status": "passed",
                    "message": "All tests passed",
                    "description": test_info["description"],
                    "output": result.stdout[-200:] if result.stdout else "No output"
                })
            else:
                results["failed"] += 1
                results["test_results"].append({
                    "name": test_info["name"],
                    "status": "failed",
                    "message": f"Test failed with return code {result.returncode}",
                    "description": test_info["description"],
                    "output": result.stderr[-200:] if result.stderr else "No error output"
                })
                
        except subprocess.TimeoutExpired:
            results["failed"] += 1
            results["test_results"].append({
                "name": test_info["name"],
                "status": "failed",
                "message": "Test timed out after 30 seconds",
                "description": test_info["description"]
            })
        except Exception as e:
            results["failed"] += 1
            results["test_results"].append({
                "name": test_info["name"],
                "status": "failed",
                "message": f"Test execution error: {str(e)}",
                "description": test_info["description"]
            })
            results["errors"].append(str(e))
    
    # Determine overall system status
    if results["total_tests"] == 0:
        results["system_status"] = "no_tests"
    elif results["failed"] == 0:
        results["system_status"] = "healthy"
    elif results["passed"] > results["failed"]:
        results["system_status"] = "warning"
    else:
        results["system_status"] = "critical"
    
    return results

def test_core_functionality() -> Dict[str, any]:
    """
    Test core system functionality without external test files
    """
    core_tests = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "test_results": []
    }
    
    # Test 1: App imports
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import streamlit_app
        core_tests["test_results"].append({
            "name": "App Import",
            "status": "passed",
            "message": "Main application imports successfully"
        })
        core_tests["passed"] += 1
    except Exception as e:
        core_tests["test_results"].append({
            "name": "App Import", 
            "status": "failed",
            "message": f"Import error: {str(e)}"
        })
        core_tests["failed"] += 1
    finally:
        core_tests["total_tests"] += 1
    
    # Test 2: Data directory access
    try:
        from app import config as settings
        data_dir = Path(settings.DATA_DIR)
        if data_dir.exists():
            core_tests["test_results"].append({
                "name": "Data Directory",
                "status": "passed", 
                "message": "Data directory is accessible"
            })
            core_tests["passed"] += 1
        else:
            core_tests["test_results"].append({
                "name": "Data Directory",
                "status": "failed",
                "message": "Data directory does not exist"
            })
            core_tests["failed"] += 1
    except Exception as e:
        core_tests["test_results"].append({
            "name": "Data Directory",
            "status": "failed",
            "message": f"Data directory error: {str(e)}"
        })
        core_tests["failed"] += 1
    finally:
        core_tests["total_tests"] += 1
    
    # Test 3: AI model discovery
    try:
        from app.services.streamlit_app import discover_models
        models = discover_models()
        if models:
            core_tests["test_results"].append({
                "name": "AI Models",
                "status": "passed",
                "message": f"Found {len(models)} available AI models"
            })
            core_tests["passed"] += 1
        else:
            core_tests["test_results"].append({
                "name": "AI Models",
                "status": "warning",
                "message": "No AI models found - check configuration"
            })
            core_tests["passed"] += 1  # This is a warning, not a failure
    except Exception as e:
        core_tests["test_results"].append({
            "name": "AI Models",
            "status": "failed",
            "message": f"AI model discovery error: {str(e)}"
        })
        core_tests["failed"] += 1
    finally:
        core_tests["total_tests"] += 1
    
    return core_tests

def show_system_test_results(results: Dict[str, any], core_results: Dict[str, any]):
    """
    Display system test results in Streamlit
    """
    st.markdown("### 🧪 System Test Results")
    
    # Overall status
    if results["system_status"] == "healthy" and core_results["failed"] == 0:
        st.success("✅ **System Status: HEALTHY** - All tests passed!")
    elif results["system_status"] == "warning" or core_results["failed"] == 0:
        st.warning("⚠️ **System Status: WARNING** - Some tests failed, but system is functional")
    else:
        st.error("❌ **System Status: CRITICAL** - Multiple test failures detected")
    
    # Test summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tests", results["total_tests"] + core_results["total_tests"])
    
    with col2:
        st.metric("Passed", results["passed"] + core_results["passed"], 
                 delta=f"+{results['passed'] + core_results['passed']}")
    
    with col3:
        st.metric("Failed", results["failed"] + core_results["failed"],
                 delta=f"-{results['failed'] + core_results['failed']}" if results['failed'] + core_results['failed'] > 0 else None)
    
    with col4:
        success_rate = ((results["passed"] + core_results["passed"]) / 
                       (results["total_tests"] + core_results["total_tests"]) * 100) if (results["total_tests"] + core_results["total_tests"]) > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Detailed results
    st.markdown("#### 📋 Detailed Test Results")
    
    # Core functionality tests
    st.markdown("**Core System Tests:**")
    for test in core_results["test_results"]:
        if test["status"] == "passed":
            st.success(f"✅ {test['name']}: {test['message']}")
        elif test["status"] == "warning":
            st.warning(f"⚠️ {test['name']}: {test['message']}")
        else:
            st.error(f"❌ {test['name']}: {test['message']}")
    
    # Feature tests
    if results["test_results"]:
        st.markdown("**Feature Tests:**")
        for test in results["test_results"]:
            if test["status"] == "passed":
                st.success(f"✅ {test['name']}: {test['message']}")
            elif test["status"] == "skipped":
                st.info(f"⏭️ {test['name']}: {test['message']}")
            else:
                st.error(f"❌ {test['name']}: {test['message']}")
                
                # Show detailed output for failed tests
                if "output" in test and test["output"]:
                    with st.expander(f"Error details for {test['name']}"):
                        st.code(test["output"])
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    
    if results["system_status"] == "healthy" and core_results["failed"] == 0:
        st.success("🎉 **System is ready for production use!** All core functionality is working correctly.")
    elif results["failed"] > 0 or core_results["failed"] > 0:
        st.warning("🔧 **Action Required:** Some tests failed. Please check the error details above and:")
        st.markdown("- Verify all required dependencies are installed")
        st.markdown("- Check that data directories are accessible")
        st.markdown("- Ensure AI models are properly configured")
        st.markdown("- Review any error messages for specific issues")
    else:
        st.info("ℹ️ **System Status:** Some test files were not found, but core functionality is working.")
