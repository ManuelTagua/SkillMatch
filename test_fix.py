#!/usr/bin/env python
"""Test script to verify the fixes."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.skillmatch.domain.entities import SkillSet, CompatibilityResult
from src.skillmatch.domain.services import extract_skills, calculate_compatibility, _extract_skills_with_context

# Test with the candidate text that should fail for React and TypeScript
candidate_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''

# First, test context-aware extraction
print('=== Context-aware extraction test ===')
strong, weak, negative = _extract_skills_with_context(candidate_text)
print(f'Strong skills: {strong}')
print(f'Weak skills: {weak}')
print(f'Negative skills: {negative}')
print()

# Now test with compatibility calculation
print('=== Compatibility test ===')
job_text = "JavaScript React HTML CSS REST APIs Git TypeScript"
offer_set, offer_cat = extract_skills(job_text)
print(f'Job requires: {offer_set.skills}')
print()

result = calculate_compatibility(offer_set, candidate_text, offer_cat, {})
print(f'Percentage: {result.percentage}%')
print(f'Matched: {result.matched}')
print(f'Weak: {result.weak}')
print(f'Missing: {result.missing}')
print()

# Check the expected behavior
print('=== Validation ===')
try:
    assert 'react' not in result.matched, 'React should NOT be matched'
    print('✓ React is not matched')
    
    assert 'typescript' not in result.matched, 'TypeScript should NOT be matched'
    print('✓ TypeScript is not matched')
    
    assert 'git' in result.matched, 'Git should be matched'
    assert 'restapi' in result.matched, 'REST API should be matched'
    assert 'html' in result.weak, 'HTML should be weak'
    assert 'css' in result.weak, 'CSS should be weak'
    print('✓ HTML handling is correct')
    
    assert 'javascript' in result.missing, 'JavaScript should be missing'
    print('✓ JavaScript is missing')
    
    assert 40 <= result.percentage <= 60, f'Score should be around 40-60%, got {result.percentage}%'
    print(f'✓ Score is reasonable: {result.percentage}%')
    
    print('\n✓ All validation checks passed!')
except AssertionError as e:
    print(f'✗ Validation failed: {e}')
    exit(1)
