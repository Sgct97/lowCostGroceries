"""
AI Product Clarification Service using GPT-5-mini

This module uses OpenAI's GPT-5-mini model to convert vague grocery items
into specific, searchable products.

Example:
    "milk" → "Whole Milk, 1 Gallon"
    "eggs" → "Large Eggs, 12 Count"
"""

import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Emoji mapping for common grocery categories
EMOJI_MAP = {
    'milk': '🥛',
    'eggs': '🥚',
    'bread': '🍞',
    'cheese': '🧀',
    'butter': '🧈',
    'yogurt': '🥛',
    'chicken': '🍗',
    'beef': '🥩',
    'pork': '🥓',
    'fish': '🐟',
    'apple': '🍎',
    'banana': '🍌',
    'orange': '🍊',
    'lettuce': '🥬',
    'tomato': '🍅',
    'potato': '🥔',
    'onion': '🧅',
    'carrot': '🥕',
    'rice': '🍚',
    'pasta': '🍝',
    'cereal': '🥣',
    'coffee': '☕',
    'tea': '🍵',
    'juice': '🧃',
    'water': '💧',
    'soda': '🥤',
    'beer': '🍺',
    'wine': '🍷',
    'chips': '🥔',
    'cookies': '🍪',
    'ice cream': '🍦',
    'chocolate': '🍫',
}


def get_emoji(product_name: str) -> str:
    """
    Get appropriate emoji for a product based on keywords.
    
    Args:
        product_name: The product name to match
        
    Returns:
        Emoji string or default 🛒
    """
    product_lower = product_name.lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in product_lower:
            return emoji
    return '🛒'


def build_system_prompt() -> str:
    """
    Build the system prompt for GPT-5-mini.
    
    Returns:
        System prompt string
    """
    return """You are a grocery shopping assistant that helps users specify vague grocery items into specific, searchable products.

CRITICAL RULES:
1. ALWAYS include specific size/quantity/volume
2. For BEVERAGES (juice, soda, water, etc): MUST specify volume (64 fl oz, 1 liter, half gallon, etc)
3. For FOOD: Specify weight or count
4. For NON-FOOD (shampoo, soap, etc): Specify volume or count
5. NEVER say "1 unit" - that's unacceptable
6. Default to most common grocery store sizes
7. Consider context from previous items

COMMON SIZES (use these):
Beverages:
- Juice → 64 fl oz (half gallon) or 1 gallon
- Soda → 2 liter or 12 pack cans
- Water → 1 gallon or 24 pack bottles
- Milk → 1 gallon

Food:
- Eggs → 12 count, large
- Bread → 20-24 oz loaf
- Meat → 1 lb packages
- Produce → by lb or count

Personal Care:
- Shampoo → 12-16 fl oz bottle
- Soap → bar soap 4 pack or body wash 18 oz
- Toothpaste → 4-6 oz tube

EXAMPLES (good):
- "orange juice" → "Orange Juice, 64 fl oz"
- "apple juice" → "Apple Juice, Half Gallon"
- "shampoo" → "Shampoo, 12 fl oz Bottle"
- "body wash" → "Body Wash, 18 fl oz"
- "water" → "Bottled Water, 24 Pack"

EXAMPLES (bad - NEVER do this):
- "Orange Juice, 1 Unit" ❌
- "Shampoo, 1 Unit" ❌
- "Milk" (no size) ❌

Return your response as valid JSON in this exact format:
{
  "suggested": {
    "name": "Product Name with Size",
    "confidence": 0.95
  },
  "alternatives": [
    {"name": "Alternative 1"},
    {"name": "Alternative 2"},
    {"name": "Alternative 3"}
  ]
}

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no extra text."""


def build_user_prompt(item: str, context: Optional[List[str]] = None) -> str:
    """
    Build the user prompt with item and context.
    
    Args:
        item: The vague grocery item
        context: List of previously clarified items for context-awareness
        
    Returns:
        User prompt string
    """
    context_str = ""
    if context and len(context) > 0:
        context_str = f"\n\nContext (user's previous items):\n" + "\n".join([f"- {item}" for item in context])
        context_str += "\n\nConsider this context when making suggestions (e.g., if they picked organic, suggest organic)."
    
    return f"""Clarify this grocery item: "{item}"{context_str}

Return suggestions as JSON."""


async def clarify_item(item: str, context: Optional[List[str]] = None) -> Dict:
    """
    Convert a vague grocery item into specific product suggestions using GPT-5-mini.
    
    Args:
        item: The vague grocery item (e.g., "milk", "eggs")
        context: Optional list of previously clarified items for context-aware suggestions
        
    Returns:
        Dictionary with suggested product and alternatives:
        {
            "suggested": {
                "name": "Whole Milk, 1 Gallon",
                "confidence": 0.95,
                "emoji": "🥛"
            },
            "alternatives": [
                {"name": "2% Milk, 1 Gallon", "emoji": "🥛"},
                {"name": "Skim Milk, 1 Gallon", "emoji": "🥛"},
                {"name": "Organic Whole Milk, Half Gal", "emoji": "🥛"}
            ]
        }
        
    Raises:
        Exception: If OpenAI API call fails, returns fallback suggestion
    """
    try:
        # Build prompts
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(item, context)
        
        # Call GPT-5-mini using Chat Completions API
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Note: GPT-5-mini only supports default temperature (1.0)
            max_completion_tokens=1000,   # GPT-5-mini needs more tokens for JSON output
            response_format={"type": "json_object"}  # Enforce JSON output
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        if not content:
            raise ValueError("Empty response from GPT-5-mini")
        
        result = json.loads(content)
        
        # Add emojis to all suggestions
        if 'suggested' in result and 'name' in result['suggested']:
            result['suggested']['emoji'] = get_emoji(result['suggested']['name'])
        
        if 'alternatives' in result:
            for alt in result['alternatives']:
                if 'name' in alt:
                    alt['emoji'] = get_emoji(alt['name'])
        
        return result
        
    except Exception as e:
        print(f"❌ GPT-5-mini API error: {e}")
        
        # Fallback: Return simple suggestion
        fallback_name = f"{item.title()}, 1 Unit"
        return {
            "suggested": {
                "name": fallback_name,
                "confidence": 0.5,
                "emoji": get_emoji(item)
            },
            "alternatives": []
        }


def clarify_item_sync(item: str, context: Optional[List[str]] = None) -> Dict:
    """
    Synchronous version of clarify_item for non-async contexts.
    
    Args:
        item: The vague grocery item
        context: Optional list of previously clarified items
        
    Returns:
        Same as clarify_item()
    """
    import asyncio
    return asyncio.run(clarify_item(item, context))


# Testing function
if __name__ == "__main__":
    print("🧪 Testing GPT-5-mini Product Clarification\n")
    
    # Test 1: Simple item
    print("Test 1: milk")
    result = clarify_item_sync("milk")
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    print(f"   Alternatives: {len(result.get('alternatives', []))}")
    print()
    
    # Test 2: With context (organic preference)
    print("Test 2: eggs (with organic context)")
    result = clarify_item_sync("eggs", context=["Organic Whole Milk, 1 Gallon"])
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    print(f"   Alternatives:")
    for alt in result.get('alternatives', []):
        print(f"   - {alt['name']} {alt.get('emoji', '')}")
    print()
    
    # Test 3: Less common item
    print("Test 3: chicken")
    result = clarify_item_sync("chicken")
    print(f"✅ Suggested: {result['suggested']['name']} {result['suggested']['emoji']}")
    print()
    
    print("🎉 All tests complete!")

