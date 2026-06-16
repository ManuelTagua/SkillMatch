#!/usr/bin/env python
"""Comprehensive test to verify all fixes are working."""

import sys
import traceback

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_compatibility_result_construction():
    """Test 1: Verify CompatibilityResult can be constructed with all required fields."""
    try:
        from src.skillmatch.domain.entities import CompatibilityResult
        
        result = CompatibilityResult(
            percentage=50,
            matched=['skill1'],
            weak=['skill2'],
            missing=['skill3'],
            recommendations=['Learn skill3']
        )
        print("✓ Test 1 PASSED: CompatibilityResult construction works")
        return True
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        traceback.print_exc()
        return False


def test_context_aware_extraction():
    """Test 2: Verify context-aware extraction detects React and TypeScript as negative."""
    try:
        from src.skillmatch.domain.services import _extract_skills_with_context
        
        candidate_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''
        
        strong, weak, negative = _extract_skills_with_context(candidate_text)
        
        tests_passed = True
        
        if 'react' not in negative:
            print(f"✗ Test 2a FAILED: React should be negative, got strong={strong}, weak={weak}, negative={negative}")
            tests_passed = False
        else:
            print("✓ Test 2a PASSED: React correctly identified as negative")
        
        if 'typescript' not in negative:
            print(f"✗ Test 2b FAILED: TypeScript should be negative, got negative={negative}")
            tests_passed = False
        else:
            print("✓ Test 2b PASSED: TypeScript correctly identified as negative")
        
        if 'html' not in weak:
            print(f"✗ Test 2c FAILED: HTML should be weak, got weak={weak}")
            tests_passed = False
        else:
            print("✓ Test 2c PASSED: HTML correctly identified as weak")
        
        return tests_passed
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        traceback.print_exc()
        return False


def test_compatibility_calculation():
    """Test 3: Verify full compatibility calculation produces correct results."""
    try:
        from src.skillmatch.domain.services import extract_skills, calculate_compatibility
        
        job_text = "JavaScript React HTML CSS REST APIs Git TypeScript"
        candidate_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''
        
        offer_set, offer_cat = extract_skills(job_text)
        result = calculate_compatibility(offer_set, candidate_text, offer_cat, {})
        
        print(f"  Percentage: {result.percentage}%")
        print(f"  Matched: {result.matched}")
        print(f"  Weak: {result.weak}")
        print(f"  Missing: {result.missing}")
        
        tests_passed = True
        
        if 'react' in result.matched:
            print(f"✗ Test 3a FAILED: React should NOT be matched")
            tests_passed = False
        else:
            print("✓ Test 3a PASSED: React is not matched")
        
        if 'typescript' in result.matched:
            print(f"✗ Test 3b FAILED: TypeScript should NOT be matched")
            tests_passed = False
        else:
            print("✓ Test 3b PASSED: TypeScript is not matched")
        
        if not 40 <= result.percentage <= 60:
            print(f"✗ Test 3c FAILED: Score {result.percentage}% (expected 40-60%)")
            tests_passed = False
        else:
            print(f"✓ Test 3c PASSED: Score is reasonable {result.percentage}%")
        
        if 'javascript' not in result.missing:
            print(f"✗ Test 3d FAILED: JavaScript should be missing")
            tests_passed = False
        else:
            print("✓ Test 3d PASSED: JavaScript is missing")
        
        return tests_passed
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Running SkillMatch Fix Verification Tests")
    print("=" * 60)
    
    all_passed = True
    
    print("\nTest 1: CompatibilityResult construction")
    all_passed &= test_compatibility_result_construction()
    
    print("\nTest 2: Context-aware extraction")
    all_passed &= test_context_aware_extraction()
    
    print("\nTest 3: Full compatibility calculation")
    all_passed &= test_compatibility_calculation()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
