#!/usr/bin/env python3

import re

def _is_generic_label(s: str) -> bool:
    s_l = (s or "").strip().lower()
    if not s_l:
        return True
    generic = {
        "name","company name","organisation name","organization name","business name",
        "legal name","trading name","details legal name","details trading name",
        "enter company name","enter legal name"
    }
    # Check for example/placeholder text patterns
    # Only match these if they appear to be standalone or with minimal context
    if any(phrase in s_l for phrase in ["e.g.", "e.g.,", "example", "sample", "placeholder", "your company", "eg.", "eg,"]):
        return True
    
    # If it's a generic label or starts with common prefixes
    if s_l in generic or s_l.startswith("details ") or s_l.startswith("enter "):
        return True
    
    # Check for standalone business entity types (without a proper company name)
    standalone_patterns = ["pty ltd", "ltd", "limited", "inc", "llc", "corp", "company name", "business name"]
    if s_l in standalone_patterns:
        return True
    
    # Check for specific example patterns like "e.g., Pty Ltd"
    if re.match(r"^e\.?g\.?,?\s+(pty|ltd|limited|inc|corp|llc)", s_l, re.IGNORECASE):
        return True
    
    # If it's very short and looks like a placeholder
    if len(s_l) < 8 and any(standalone in s_l for standalone in ["company name", "business name", "legal name"]):
        return True
        
    return False

def _looks_like_company_name(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s_clean = re.sub(r"\s+", " ", s).strip()
    if not s_clean:
        return False
    
    # Reject obvious placeholder/example text FIRST, before any other validation
    if _is_generic_label(s_clean):
        return False
    
    # Must be at least 5 characters long
    if len(s_clean) < 5:
        return False
    
    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', s_clean):
        return False
    
    # Check for company suffixes - this is a strong indicator
    if re.search(r"\b(pty|pte|ltd|limited|inc|llc|llp|gmbh|s\.a\.|s\.r\.l\.|plc|corp|corporation)\b", s_clean, re.IGNORECASE):
        # Extract the part before the suffix
        before_suffix = re.split(r'\b(?:pty|pte|ltd|limited|inc|llc|llp|gmbh|s\.a\.|s\.r\.l\.|plc|corp|corporation)\b', s_clean, flags=re.IGNORECASE)[0].strip()
        # Additional check: make sure the part before suffix isn't generic either
        if _is_generic_label(before_suffix):
            return False
        # Must have at least 1 substantial word before the suffix (relaxed from 2)
        words_before = [w for w in re.split(r'[^A-Za-z]+', before_suffix) if w and len(w) >= 2]
        if len(words_before) >= 1 and len(before_suffix) >= 3:
            return True
    
    # For names without suffixes, require at least 2 substantial words (relaxed from 3)
    words = [w for w in re.split(r"[^A-Za-z]+", s_clean) if w and len(w) >= 2]
    return len(words) >= 2 and len(s_clean) >= 8

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
