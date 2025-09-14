#!/usr/bin/env python3

# Test the company name extraction fix
import sys
import os
import re

# Add the app directory to sys.path
sys.path.insert(0, '/home/amir/Desktop/AI-Powered-Procurement-Automation-Platform')

try:
    from app.services.supplier import _is_generic_label, _looks_like_company_name
    
    # Test cases
    test_cases = [
        ("e.g., Pty Ltd", True, False),  # Should be generic, should NOT look like company name
        ("e.g. Pty Ltd", True, False),   # Should be generic, should NOT look like company name  
        ("eg, Pty Ltd", True, False),    # Should be generic, should NOT look like company name
        ("ABC Industries Pty Ltd", False, True),  # Should NOT be generic, should look like company name
        ("Example Company Limited", True, False),  # Should be generic, should NOT look like company name
        ("Real Corp Pty Ltd", False, True),  # Should NOT be generic, should look like company name
        ("sample business", True, False),  # Should be generic, should NOT look like company name
        ("Your Company Name", True, False),  # Should be generic, should NOT look like company name
    ]
    
    print("Testing company name extraction fix:")
    print("=" * 50)
    
    all_passed = True
    for test_text, expect_generic, expect_company in test_cases:
        is_generic = _is_generic_label(test_text)
        looks_like_company = _looks_like_company_name(test_text)
        
        generic_ok = is_generic == expect_generic
        company_ok = looks_like_company == expect_company
        
        status = "✓" if (generic_ok and company_ok) else "✗"
        print(f"{status} '{test_text}':")
        print(f"    is_generic: {is_generic} (expected {expect_generic}) {'✓' if generic_ok else '✗'}")
        print(f"    looks_like_company: {looks_like_company} (expected {expect_company}) {'✓' if company_ok else '✗'}")
        print()
        
        if not (generic_ok and company_ok):
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! The fix is working correctly.")
    else:
        print("❌ Some tests failed. Check the logic above.")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory.")
