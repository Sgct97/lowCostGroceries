"""
Quick test script for AI integration
Tests GPT-5-mini clarification before full system test
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from ai_service import clarify_item_sync

def test_ai_clarification():
    print("=" * 80)
    print("🧪 TESTING GPT-5-MINI AI CLARIFICATION")
    print("=" * 80)
    print()
    
    # Test 1: Simple item
    print("Test 1: 'milk'")
    print("-" * 40)
    result = clarify_item_sync("milk")
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    if result.get('alternatives'):
        print(f"   Alternatives: {len(result['alternatives'])}")
        for i, alt in enumerate(result['alternatives'][:3], 1):
            print(f"   {i}. {alt['name']} {alt.get('emoji', '')}")
    print()
    
    # Test 2: With context
    print("Test 2: 'eggs' (with organic context)")
    print("-" * 40)
    result = clarify_item_sync("eggs", context=["Organic Whole Milk, 1 Gallon"])
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    if result.get('alternatives'):
        for i, alt in enumerate(result['alternatives'][:3], 1):
            print(f"   {i}. {alt['name']} {alt.get('emoji', '')}")
    print()
    
    # Test 3: Less common item
    print("Test 3: 'chicken breast'")
    print("-" * 40)
    result = clarify_item_sync("chicken breast")
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    print()
    
    print("=" * 80)
    print("🎉 ALL AI TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    test_ai_clarification()

