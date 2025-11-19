# FINDING THE REAL GOOGLE SHOPPING API ENDPOINT

## Critical Steps (Follow This EXACTLY)

### 1. Open Chrome DevTools FIRST
- Open Chrome
- Press F12 (DevTools)
- Go to **Network** tab
- ✅ Check **"Preserve log"** (IMPORTANT!)
- Clear existing requests (trash icon)
- Filter: **Fetch/XHR**

### 2. Navigate to Google Shopping
- In the address bar: `https://www.google.com/search?q=milk&tbm=shop`
- Press Enter
- **WAIT 3-5 seconds** for page to fully load

### 3. INTERACT with the page (This is KEY!)
- **Scroll down** slowly
- **Click on a product**
- **Change the filters** (if any)
- **Click "Load More"** or "Next Page" (if visible)

### 4. Watch Network Tab for NEW requests
Look for requests that appear AFTER you interact:
- URLs containing: `shopping`, `product`, `search`, `rpc`, `async`
- Requests that return **large amounts of data** (> 10kb)
- Requests with **Response Type: json** or **xhr**

### 5. Identify the Product Data Request
For each promising request:
1. Click on it
2. Click **"Preview"** or **"Response"** tab
3. Look for:
   - Product names
   - Prices
   - Merchant/store names
   - Image URLs
   
### 6. Copy the RIGHT Request
Once you find it:
- Right-click on the request
- Copy → Copy as cURL (bash)
- Paste it back here

---

## What You're Looking For

### ✅ GOOD - Product Data Request
```
Response contains:
{
  "products": [
    {
      "title": "Organic Milk 1 Gallon",
      "price": "$6.99",
      "merchant": "Walmart",
      ...
    }
  ]
}
```

### ❌ BAD - Not Product Data
```
- Just JavaScript files (.js)
- Analytics/tracking (gen_204, collect)
- The /async/bgasy we found (initialization only)
- Empty or very small responses
```

---

## Common Google Shopping API Patterns

Based on other Google services, look for:

### Pattern 1: RPC Style
```
/shopping/rpc/...
/maps/shopping/...
/_/shopping/_/rpc/...
```

### Pattern 2: Async/AJAX
```
/async/shopping?...
/async/search?tbm=shop&...
```

### Pattern 3: BatchExecute
```
/_/shopping/_/batchexecute?...
(Google often uses this for multiple API calls)
```

### Pattern 4: Mobile API
```
shopping.google.com/m/...
(Mobile endpoints are often cleaner)
```

---

## Pro Tips

1. **Try Mobile Site**: Visit `shopping.google.com` on mobile or with mobile user-agent
2. **Check "Type" column**: Look for "xhr" or "fetch" types
3. **Sort by Size**: Largest responses usually have the data
4. **Look for JSON**: In the Response tab, look for formatted JSON
5. **Paginate**: Click "Next Page" and see what request fires

---

## Alternative: Check Page Source for API Hints

Sometimes the API endpoint is embedded in the page JavaScript:

```javascript
// Look for patterns like:
window._apiEndpoint = "...";
fetch("https://www.google.com/shopping/...");
```

---

## Once You Find It:

Send me:
1. The cURL command
2. Or just the URL and what parameters it has
3. A sample of what the response looks like

I'll build the scraper immediately!

