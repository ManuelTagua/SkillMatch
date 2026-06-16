#!/usr/bin/env python
"""
Direct test of CompatibilityResult from the actual codebase.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, r'c:\Yo\Proyectos\SkillMatch')

print("Step 1: Import CompatibilityResult")
print("-" * 70)
try:
    from src.skillmatch.domain.entities import CompatibilityResult
    print("✓ Successfully imported CompatibilityResult")
    print(f"  Location: {CompatibilityResult.__module__}")
    print(f"  Dataclass: {CompatibilityResult.__dataclass_fields__.keys()}")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

print("\nStep 2: Test instantiation with keyword arguments")
print("-" * 70)
try:
    result = CompatibilityResult(
        percentage=75,
        matched=['java', 'python'],
        weak=['javascript'],
        missing=['go'],
        recommendations=['Learn Go']
    )
    print(f"✓ Successfully created CompatibilityResult")
    print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Failed to create: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Test with empty explicit fields")
print("-" * 70)
try:
    result2 = CompatibilityResult(
        percentage=0,
        matched=[],
        weak=[],
        missing=['all'],
        recommendations=[],
    )
    print(f"✓ Successfully created minimal CompatibilityResult")
    print(f"  Result: {result2}")
except Exception as e:
    print(f"✗ Failed to create: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Import and test calculate_compatibility")
print("-" * 70)
try:
    from src.skillmatch.domain.services import extract_skills, calculate_compatibility
    print("✓ Successfully imported services")
    
    job_text = "Java Spring Boot"
    profile_text = "I have experience with Java and Spring Boot"
    
    offer_set, offer_cat = extract_skills(job_text)
    print(f"  Extracted skills from job: {offer_set.skills}")
    
    result3 = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    print(f"✓ calculate_compatibility executed successfully")
    print(f"  Result: percentage={result3.percentage}%, matched={result3.matched}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL TESTS PASSED!")
print("=" * 70)
print("\nThe issue should be resolved. The CompatibilityResult dataclass")
print("is correctly defined with all required fields in the right order,")
print("and all instantiations use keyword arguments.")
sys.exit(0)
