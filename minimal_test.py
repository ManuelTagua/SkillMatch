#!/usr/bin/env python
"""Minimal test to verify dataclass field order."""

from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class TestResult:
    percentage: int
    matched: List[str]
    weak: List[str]
    missing: List[str]
    recommendations: List[str] = field(default_factory=list)

# Test with keyword arguments
print("Test 1: All fields")
r1 = TestResult(
    percentage=50,
    matched=['java'],
    weak=['css'],
    missing=['python'],
    recommendations=['Learn Python']
)
print(f"OK: {r1}")

# Test with empty explicit fields
print("\nTest 2: Empty explicit fields")
r2 = TestResult(
    percentage=0,
    matched=[],
    weak=[],
    missing=[],
    recommendations=[],
)
print(f"OK: {r2}")

# Test with keyword arguments
print("\nTest 3: Keyword arguments")
r3 = TestResult(
    percentage=50,
    matched=['java'],
    weak=[],
    missing=['python'],
    recommendations=[],
)
print(f"OK: {r3}")

print("\nAll tests passed!")
