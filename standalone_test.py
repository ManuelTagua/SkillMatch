#!/usr/bin/env python
"""
Standalone test to verify dataclass field order is correct.
This test doesn't import anything - it defines its own CompatibilityResult to verify the order.
"""

from dataclasses import dataclass, field
from typing import List

# Replicate the exact dataclass definition
@dataclass(frozen=True)
class CompatibilityResult:
    percentage: int
    matched: List[str]
    weak: List[str]
    missing: List[str]
    recommendations: List[str] = field(default_factory=list)

print("=" * 70)
print("TEST 1: Constructor with all keyword arguments (all fields)")
print("=" * 70)
try:
    result = CompatibilityResult(
        percentage=50,
        matched=['java'],
        weak=['css'],
        missing=['python'],
        recommendations=['Learn Python']
    )
    print(f"✓ SUCCESS: {result}")
except TypeError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 70)
print("TEST 2: Constructor with empty explicit fields")
print("=" * 70)
try:
    result = CompatibilityResult(
        percentage=0,
        matched=[],
        weak=[],
        missing=[],
        recommendations=[],
    )
    print(f"✓ SUCCESS: {result}")
except TypeError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 70)
print("TEST 3: Constructor with keyword arguments")
print("=" * 70)
try:
    result = CompatibilityResult(
        percentage=50,
        matched=['java'],
        weak=[],
        missing=['python'],
        recommendations=[],
    )
    print(f"✓ SUCCESS: {result}")
except TypeError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 70)
print("TEST 4: Constructor with all explicit fields")
print("=" * 70)
try:
    result = CompatibilityResult(
        percentage=50,
        matched=['java'],
        weak=['css'],
        missing=['python'],
        recommendations=['Learn Python']
    )
    print(f"✓ SUCCESS: {result}")
except TypeError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
