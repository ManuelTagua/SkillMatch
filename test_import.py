#!/usr/bin/env python
import sys
import traceback

try:
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    from src.skillmatch.domain.entities import CompatibilityResult
    print("[OK] CompatibilityResult imported")
    
    from src.skillmatch.domain.services import calculate_compatibility, extract_skills
    print("[OK] Services imported")
    
    print("\nTesting instantiation with all fields...")
    result = CompatibilityResult(
        percentage=50,
        matched=['java'],
        weak=['css'],
        missing=['python'],
        recommendations=['Learn Python']
    )
    print(f"[OK] Created: {result}")
    
    print("\nTesting instantiation with empty explicit fields...")
    result2 = CompatibilityResult(
        percentage=0,
        matched=[],
        weak=[],
        missing=[],
        recommendations=[],
    )
    print(f"[OK] Created: {result2}")
    
    print("\nTesting calculate_compatibility...")
    job_text = "Java Spring Boot"
    profile_text = "I have Java"
    offer_set, offer_cat = extract_skills(job_text)
    result3 = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    print(f"[OK] Result: {result3}")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

except Exception as e:
    print("\n" + "=" * 60)
    print(f"ERROR: {e}")
    print("=" * 60)
    traceback.print_exc()
    sys.exit(1)
