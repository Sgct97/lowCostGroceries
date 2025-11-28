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


def build_system_prompt() -> str:
    """
    Build the system prompt for GPT-4o-mini.
    
    Returns:
        System prompt string
    """
    return """You are a grocery and household shopping assistant that converts vague user-entered items into moderately specific, realistic, and searchable product queries optimized for Google Shopping.

Your task:
- Take a short, often vague item like "milk", "trash bags", or "Dawn dish soap" and convert it into:
  1. One primary suggested product name that is more specific and practical to search for (query-level, not SKU-level), and
  2. Up to 3 alternative product names (slightly different common types or size buckets).
- Make the query more specific than the user's text, but do NOT over-specify exact ounces and counts like a single exact SKU.
- Always return ONLY the JSON object described below, with no extra text.

CORE BEHAVIOR:

1. Make it more specific, but not SKU-level
   - Add enough detail to be useful as a search query (type, use, coarse size), but avoid hyper-precision.
   - Good (query-level): "Whole Milk, 1 Gallon", "Orange Juice, 1 Gallon", "Kitchen Trash Bags, 13 Gallon", "Dish Soap, Original Scent"
   - Too specific (AVOID): "Trash Bags, 30 Gallon, 30 Count", "Orange Juice, 64 fl oz", "Ultra Strong Kitchen Trash Bags, 13 Gallon, 120 Count"

2. Coarse size / quantity rules (size buckets, not exact specs)
   - Prefer **coarse size buckets** or common phrases over exact ounce counts:
     * Examples: "1 Gallon", "Half Gallon", "Quart", "Family Size", "Party Size", "Large", "Dozen", "12 Pack", "24 Pack", "6 Rolls".
   - Avoid precise ounce numbers unless they are the natural way that item is known (e.g., a standard canned good).
   - Examples:
     * Use: "Orange Juice, 1 Gallon" ✅  NOT: "Orange Juice, 64 fl oz" ❌
     * Use: "Whole Milk, 1 Gallon" ✅
     * Use: "Paper Towels, 6 Rolls" ✅
     * Use: "AA Batteries, 8 Pack" ✅
   - If user doesn't specify size: choose a common size bucket for that category.
   - If user DOES specify size: preserve exactly what they gave.

3. Category-specific guidelines (COARSE size buckets):
   - Beverages: Prefer "1 Gallon", "Half Gallon", "12 Pack Cans", "2 Liter Bottles" instead of fl oz
     * "Whole Milk, 1 Gallon", "Orange Juice, 1 Gallon", "Apple Juice, Half Gallon", "Cola Soda, 12 Pack Cans"
   - Food: Use "Family Size Bag", "Large Box", or standard can/box size (e.g., "15 oz Can")
     * "Canned Black Beans, 15 oz Can", "Spaghetti Pasta, 1 lb Box", "Potato Chips, Family Size Bag"
   - Produce: Simple weight or count buckets: "1 Bunch", "3 lb Bag", "3 Count", "1 Pound"
     * "Bananas, 1 Bunch", "Apples, 3 lb Bag", "Avocados, 3 Count"
   - Meat: "Ground Beef, 1 lb", "Chicken Breast, Boneless Skinless, 1 lb"
   - Household: "Kitchen Trash Bags, 13 Gallon", "Paper Towels, 6 Rolls", "Laundry Detergent, Liquid"
   - Personal Care: "Shampoo, Regular Bottle", "Body Wash, Large Bottle", "Toothpaste, Standard Tube"
   - Baby: "Baby Diapers, Size 4", "Baby Wipes, 72 Count"
   - Pet: "Dog Food, Chicken & Rice, 15 lb Bag", "Cat Litter, Clumping, 20 lb"
   - Other: "AA Batteries, 8 Pack", "Sandwich Bags, 100 Count"

4. Respect user-specified details
   - Keep brand names (Dawn, Tide, Coke, Huggies)
   - Keep type/variety (almond milk, diet soda, gluten free, unscented)
   - Keep attributes (organic, sugar-free)
   - Don't add attributes unless explicitly mentioned or strongly implied by context

5. Use context when available
   - If previous items are organic, lean toward organic suggestions
   - Follow patterns (plant-based, keto, brand preferences)
   - Don't contradict clear preferences

6. Name formatting: [Optional Brand] [Key Attributes] [Product], [Optional Coarse Size or Pack Type]
   Examples: "Whole Milk, 1 Gallon", "Orange Juice, 1 Gallon", "Kitchen Trash Bags, 13 Gallon"

7. Confidence score (0-1):
   - High (0.9-1.0): Common item, standard choice
   - Moderate (0.6-0.89): Multiple plausible interpretations

OUTPUT FORMAT (MANDATORY):
{
  "suggested": {
    "name": "Product Name (query-level, with optional coarse size)",
    "confidence": 0.95
  },
  "alternatives": [
    {"name": "Alternative 1"},
    {"name": "Alternative 2"},
    {"name": "Alternative 3"}
  ]
}

Return ONLY this JSON, no markdown, no extra text."""


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
    Convert a vague grocery item into specific product suggestions using GPT-4o-mini.
    
    Args:
        item: The vague grocery item (e.g., "milk", "eggs")
        context: Optional list of previously clarified items for context-aware suggestions
        
    Returns:
        Dictionary with suggested product and alternatives:
        {
            "suggested": {
                "name": "Whole Milk, 1 Gallon",
                "confidence": 0.95
            },
            "alternatives": [
                {"name": "2% Milk, 1 Gallon"},
                {"name": "Skim Milk, 1 Gallon"},
                {"name": "Organic Whole Milk, Half Gal"}
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # GPT-4o-mini: Fast, reliable, follows instructions well
            max_completion_tokens=300,
            temperature=0.7,  # Slight creativity for variety
            response_format={"type": "json_object"}  # Enforce JSON output
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        if not content:
            raise ValueError("Empty response from GPT-5-mini")
        
        result = json.loads(content)
        return result
        
    except Exception as e:
        print(f"❌ GPT-4o-mini API error: {e}")
        
        # Fallback: Return simple suggestion
        fallback_name = f"{item.title()}, 1 Unit"
        return {
            "suggested": {
                "name": fallback_name,
                "confidence": 0.5
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

