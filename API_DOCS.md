# Low Cost Groceries API

**Base URL:** `http://146.190.129.92:8000`

Hey! This is a simple API that finds the cheapest groceries near a user's location. Here's everything you need to know.

---

## How It Works (The Simple Version)

**The Two-Step Flow:**

1. **AI Layer** - Turns vague input like "milk" into specific products like "Whole Milk, 1 Gallon"
2. **Search API** - Finds real prices at nearby stores

**Why two steps?** Because searching for "milk" returns garbage results, but "Whole Milk, 1 Gallon" returns 10-20 actual products with real prices and store locations.

---

## Quick Start

**Step 1: Get AI suggestions**
```bash
POST /api/clarify
{
  "item": "milk"
}
```

**Response:**
```json
{
  "status": "success",
  "suggested": {
    "name": "Whole Milk, 1 Gallon",
    "emoji": "🥛"
  },
  "alternatives": [
    {"name": "2% Reduced-Fat Milk, 1 Gallon"},
    {"name": "Skim Milk, 1 Gallon"}
  ]
}
```

**Step 2: User picks one, you search for prices**
```bash
POST /api/cart
{
  "items": ["Whole Milk, 1 Gallon", "Large Eggs, 12 Count"],
  "zipcode": "33773"
}
```

**Response (instant):**
```json
{
  "job_id": "abc-123",
  "status": "queued",
  "estimated_time_seconds": 2
}
```

**Step 3: Poll for results**
```bash
GET /api/results/abc-123
```

**Response (when done):**
```json
{
  "status": "complete",
  "results": {
    "Whole Milk, 1 Gallon": [
      {
        "name": "Great Value Whole Milk",
        "price": 2.62,
        "merchant": "Walmart",
        "location": "In store, Clearwater",
        "rating": 3.5,
        "review_count": 19000
      }
    ]
  },
  "zip_code": "33773",
  "total_time": 1.5
}
```

That's it. Three simple calls.

---

## The AI Layer (Important!)

**What it does:**
- Takes vague input → Returns specific product names
- Uses GPT-5-mini under the hood
- Makes your search results WAY better

**When to use it:**
- User types anything in a search box
- You want to show helpful suggestions
- Before searching for prices

**Example Flow:**
```
User types: "bread"
   ↓
Call /api/clarify with "bread"
   ↓
Show user: "Whole Wheat Bread, 24 oz Loaf"
              "White Sandwich Bread, 20 oz"
   ↓
User picks one
   ↓
Search for prices with /api/cart
```

**Pro tip:** You CAN skip the AI and search for "bread" directly, but you'll get worse results. The AI makes everything better.

---

## API Endpoints

### 1. POST `/api/clarify`

**What it does:** Turns vague items into specific product names

**Request:**
```json
{
  "item": "orange juice"
}
```

**Response:**
```json
{
  "status": "success",
  "suggested": {
    "name": "Orange Juice, 64 oz",
    "confidence": 0.9,
    "emoji": "🍊"
  },
  "alternatives": [
    {"name": "Tropicana Pure Premium Orange Juice, 52 oz"},
    {"name": "Simply Orange Juice, 89 oz"}
  ],
  "processing_time": 0.8
}
```

---

### 2. POST `/api/cart`

**What it does:** Searches for products and returns prices at nearby stores

**Request:**
```json
{
  "items": ["Whole Milk, 1 Gallon", "Large Eggs, 12 Count"],
  "zipcode": "33773",
  "prioritize_nearby": true
}
```

**Required:**
- `items` - Array of product names (use AI-clarified names for best results)
- `zipcode` - 5-digit ZIP code

**Optional:**
- `prioritize_nearby` (default: true) - Only show in-store products

**Response :**
```json
{
  "job_id": "abc-123",
  "status": "queued",
  "estimated_time_seconds": 2,
  "message": "Job queued. Poll GET /results/abc-123 for results."
}
```

**Important:** This endpoint returns quickly. The actual searching happens in the background.

---

### 3. GET `/api/results/{job_id}`

**What it does:** Gets the results from your search

**Response (while processing):**
```json
{
  "status": "processing",
  "worker_id": "worker-123"
}
```

**Response (when done):**
```json
{
  "status": "complete",
  "results": {
    "Whole Milk, 1 Gallon": [
      {
        "name": "Great Value Whole Milk",
        "price": 2.62,
        "merchant": "Walmart",
        "location": "In store, Clearwater",
        "rating": 3.5,
        "review_count": 19000
      },
      {
        "name": "Organic Valley Whole Milk",
        "price": 4.99,
        "merchant": "Target",
        "location": "In store, Tampa"
      }
    ],
    "Large Eggs, 12 Count": [...]
  },
  "zip_code": "33773",
  "total_time": 2.3
}
```

**How to poll:**
```javascript
async function getResults(jobId) {
  while (true) {
    const response = await fetch(`/api/results/${jobId}`);
    const data = await response.json();
    
    if (data.status === 'complete') {
      return data.results;
    }
    
    await sleep(1000);  // Wait 1 second, try again
  }
}
```



---

## Important Notes

### ZIP Code is Required
Without a ZIP code, you get random/national results. With a ZIP, you get local stores nearby. Always collect the user's ZIP.

### Use AI-Clarified Names
- ❌ Searching for "milk" → 0-5 results
- ✅ Searching for "Whole Milk, 1 Gallon" → 10-20 results



### Rate Limits
Be reasonable. Don't spam the API. If you need to make 1000s of requests, let me know so I can optimize for your usage.

