/**
 * ============================================================================
 * LOW COST GROCERIES - AI Shopping Assistant
 * Frontend JavaScript
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    API_BASE_URL: 'http://146.190.129.92:8000',  // Droplet 1 API
    DEBOUNCE_DELAY: 1200,  // ms to wait after user stops typing (increased to prevent partial word searches)
    POLL_INTERVAL: 2000,  // ms between result polls
    MAX_ITEMS: 10,
    MIN_ZIP_LENGTH: 5
};

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const state = {
    cart: [],
    currentStep: 1,
    jobId: null,
    pollInterval: null,
    zipCode: null,
    pendingSuggestions: []  // Items waiting for AI suggestions
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Debounce function to limit API calls
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Show toast notification
 */
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

/**
 * Navigate between steps
 */
function goToStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show target step
    document.getElementById(`step${stepNumber}`).classList.add('active');
    state.currentStep = stepNumber;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// STEP 1: CART BUILDING
// ============================================================================

const itemInput = document.getElementById('itemInput');
const addManualBtn = document.getElementById('addManualBtn');
const suggestionsDiv = document.getElementById('suggestions');
const suggestionsContent = document.getElementById('suggestionsContent');
const cartItems = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const continueBtn = document.getElementById('continueBtn');
const clearCartBtn = document.getElementById('clearCartBtn');

/**
 * Fetch AI suggestions for item
 */
async function fetchSuggestions(item) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/clarify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                item: item,
                context: state.cart.map(cartItem => cartItem.name)
            })
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        showToast('Failed to get AI suggestions. Try again!');
        return null;
    }
}

/**
 * Display AI suggestions
 */
function displaySuggestions(data) {
    if (!data || !data.suggested) {
        suggestionsDiv.classList.add('hidden');
        addManualBtn.style.display = 'block';  // Show manual button if no suggestions
        return;
    }
    
    suggestionsContent.innerHTML = '';
    
    // Add main suggestion
    const suggested = data.suggested;
    const mainCard = createSuggestionCard(
        suggested.name,
        true  // is best match
    );
    suggestionsContent.appendChild(mainCard);
    
    // Add alternatives
    if (data.alternatives && data.alternatives.length > 0) {
        data.alternatives.slice(0, 3).forEach(alt => {
            const altCard = createSuggestionCard(
                alt.name,
                false
            );
            suggestionsContent.appendChild(altCard);
        });
    }
    
    suggestionsDiv.classList.remove('hidden');
    addManualBtn.style.display = 'none';  // Hide manual button when suggestions are showing
}

/**
 * Create suggestion card element
 */
function createSuggestionCard(name, isBest, pendingId = null) {
    const card = document.createElement('div');
    card.className = 'suggestion-card';
    card.innerHTML = `
        <span class="suggestion-name">${name}</span>
        ${isBest ? '<span class="suggestion-badge">Best Match</span>' : ''}
    `;
    
    card.addEventListener('click', () => {
        addToCart(name);
        // Remove this pending item from queue after selection
        if (pendingId !== null) {
            removePendingItem(pendingId);
        }
    });
    
    return card;
}

/**
 * Remove a pending suggestion item after user selection
 */
function removePendingItem(pendingId) {
    const index = state.pendingSuggestions.findIndex(p => p.id === pendingId);
    if (index !== -1) {
        state.pendingSuggestions.splice(index, 1);
        renderPendingSuggestions();
    }
}

/**
 * Add item to cart
 */
function addToCart(name) {
    // Check if already in cart
    if (state.cart.some(item => item.name === name)) {
        showToast('Item already in cart!');
        return;
    }
    
    // Check max items
    if (state.cart.length >= CONFIG.MAX_ITEMS) {
        showToast(`Maximum ${CONFIG.MAX_ITEMS} items allowed`);
        return;
    }
    
    // Add to cart
    state.cart.push({ name });
    
    // Update UI
    renderCart();
    showToast('Added to cart!', 1500);
    
    // Keep input focused for next item
    itemInput.focus();
    
    // Focus back on input for next item
    itemInput.focus();
}

/**
 * Remove item from cart
 */
function removeFromCart(index) {
    state.cart.splice(index, 1);
    renderCart();
    showToast('Removed from cart', 1500);
}

/**
 * Render cart UI
 */
function renderCart() {
    // Update count
    cartCount.textContent = `${state.cart.length}/${CONFIG.MAX_ITEMS}`;
    
    // Show/hide clear button
    clearCartBtn.style.display = state.cart.length > 0 ? 'block' : 'none';
    
    // Enable/disable continue button
    continueBtn.disabled = state.cart.length === 0;
    
    // Render items
    if (state.cart.length === 0) {
        cartItems.innerHTML = `
            <div class="empty-cart">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <path d="M8 8H16L20 40H52L56 20H20" stroke="#E0E0E0" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="24" cy="52" r="4" fill="#E0E0E0"/>
                    <circle cx="48" cy="52" r="4" fill="#E0E0E0"/>
                </svg>
                <p class="empty-text">Your list is empty</p>
                <p class="empty-subtext">Start typing above to add items</p>
            </div>
        `;
    } else {
        cartItems.innerHTML = state.cart.map((item, index) => `
            <div class="cart-item">
                <span class="cart-item-name">${item.name}</span>
                <button class="cart-item-remove" onclick="removeFromCart(${index})">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }
}

/**
 * Submit item for AI processing (happens immediately, no debounce)
 */
async function submitItemForAI(originalText) {
    if (originalText.length < 2) {
        return;
    }
    
    // Create pending item
    const pendingId = Date.now();
    const pendingItem = {
        id: pendingId,
        originalText: originalText,
        status: 'loading',
        suggestions: null
    };
    
    state.pendingSuggestions.push(pendingItem);
    renderPendingSuggestions();
    
    // Clear input immediately so user can type next item
    itemInput.value = '';
    itemInput.focus();
    
    // Fetch AI suggestions in background
    try {
        const suggestions = await fetchSuggestions(originalText);
        
        // Update pending item with results
        const item = state.pendingSuggestions.find(p => p.id === pendingId);
        if (item) {
            item.status = 'complete';
            item.suggestions = suggestions;
            renderPendingSuggestions();
        }
    } catch (error) {
        // Update pending item with error
        const item = state.pendingSuggestions.find(p => p.id === pendingId);
        if (item) {
            item.status = 'error';
            renderPendingSuggestions();
        }
    }
}

/**
 * Render all pending suggestion cards
 */
function renderPendingSuggestions() {
    if (state.pendingSuggestions.length === 0) {
        suggestionsDiv.classList.add('hidden');
        return;
    }
    
    suggestionsDiv.classList.remove('hidden');
    suggestionsContent.innerHTML = '';
    
    state.pendingSuggestions.forEach(pending => {
        const pendingCard = document.createElement('div');
        pendingCard.className = 'pending-item-card';
        
        if (pending.status === 'loading') {
            pendingCard.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <div class="pending-text">
                        <strong>"${pending.originalText}"</strong>
                        <div style="font-size: 12px; color: var(--gray-500); margin-top: 4px;">Getting AI suggestions...</div>
                    </div>
                </div>
            `;
        } else if (pending.status === 'complete' && pending.suggestions) {
            const data = pending.suggestions;
            
            // Remove pending item header, show suggestions
            pendingCard.innerHTML = `
                <div class="suggestions-ready">
                    <div style="font-size: 12px; color: var(--gray-600); margin-bottom: 8px; font-weight: 500;">
                        ✨ Suggestions for "${pending.originalText}"
                    </div>
                </div>
            `;
            
            // Add main suggestion
            if (data.suggested) {
                const mainCard = createSuggestionCard(
                    data.suggested.name,
                    true,
                    pending.id
                );
                pendingCard.appendChild(mainCard);
            }
            
            // Add alternatives
            if (data.alternatives && data.alternatives.length > 0) {
                data.alternatives.slice(0, 3).forEach(alt => {
                    const altCard = createSuggestionCard(
                        alt.name,
                        false,
                        pending.id
                    );
                    pendingCard.appendChild(altCard);
                });
            }
        } else if (pending.status === 'error') {
            pendingCard.innerHTML = `
                <div class="error-state">
                    ❌ Failed to get suggestions for "${pending.originalText}"
                    <button onclick="retryPending(${pending.id})" class="retry-btn">Retry</button>
                </div>
            `;
        }
        
        suggestionsContent.appendChild(pendingCard);
    });
}

// Event listeners for Step 1
itemInput.addEventListener('input', (e) => {
    const value = e.target.value.trim();
    // Just enable/disable the button, no AI calls yet
    addManualBtn.disabled = value.length < 2;
    addManualBtn.textContent = value.length >= 2 ? '→ Get AI Suggestions' : '+ Add Item';
});

itemInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const value = itemInput.value.trim();
        if (value.length >= 2) {
            submitItemForAI(value);
        }
    }
});

addManualBtn.addEventListener('click', () => {
    const value = itemInput.value.trim();
    if (value.length >= 2) {
        submitItemForAI(value);
    }
});

continueBtn.addEventListener('click', () => {
    goToStep(2);
});

clearCartBtn.addEventListener('click', () => {
    if (confirm('Clear all items from cart?')) {
        state.cart = [];
        renderCart();
    }
});

// ============================================================================
// STEP 2: ZIP CODE
// ============================================================================

const zipInput = document.getElementById('zipInput');
const backBtn = document.getElementById('backBtn');
const findPricesBtn = document.getElementById('findPricesBtn');

zipInput.addEventListener('input', (e) => {
    const value = e.target.value.replace(/\D/g, '');  // Only digits
    e.target.value = value;
    findPricesBtn.disabled = value.length !== CONFIG.MIN_ZIP_LENGTH;
});

zipInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !findPricesBtn.disabled) {
        submitCart();
    }
});

backBtn.addEventListener('click', () => {
    goToStep(1);
});

findPricesBtn.addEventListener('click', () => {
    submitCart();
});

/**
 * Submit cart to API
 */
async function submitCart() {
    state.zipCode = zipInput.value;
    const prioritizeNearby = document.getElementById('prioritizeNearbyToggle').checked;
    goToStep(3);
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/cart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                items: state.cart.map(item => item.name),
                zipcode: state.zipCode,
                prioritize_nearby: prioritizeNearby
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit cart');
        }
        
        const data = await response.json();
        state.jobId = data.job_id;
        
        document.getElementById('jobIdDisplay').textContent = data.job_id.substring(0, 8) + '...';
        document.getElementById('loadingStatus').textContent = 'Job queued, waiting for worker...';
        
        // Start polling for results
        startPolling();
        
    } catch (error) {
        console.error('Error submitting cart:', error);
        showToast('Failed to submit cart. Please try again.');
        goToStep(2);
    }
}

// ============================================================================
// STEP 3: POLLING FOR RESULTS
// ============================================================================

let pollCount = 0;

/**
 * Start polling for results
 */
function startPolling() {
    pollCount = 0;
    state.pollInterval = setInterval(pollResults, CONFIG.POLL_INTERVAL);
    pollResults();  // Poll immediately
}

/**
 * Poll for results
 */
async function pollResults() {
    pollCount++;
    const progressFill = document.getElementById('progressFill');
    const loadingStatus = document.getElementById('loadingStatus');
    
    // Update progress bar (fake progress)
    const progress = Math.min((pollCount * 10), 90);
    progressFill.style.width = `${progress}%`;
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/results/${state.jobId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch results');
        }
        
        const data = await response.json();
        
        if (data.status === 'complete') {
            // Stop polling
            clearInterval(state.pollInterval);
            progressFill.style.width = '100%';
            
            // Display results
            displayResults(data);
            goToStep(4);
            
        } else if (data.status === 'processing') {
            loadingStatus.textContent = 'Processing your items...';
            
        } else if (data.status === 'failed') {
            clearInterval(state.pollInterval);
            showToast('Search failed. Please try again.');
            goToStep(2);
            
        } else if (data.status === 'queued') {
            loadingStatus.textContent = `Queued (position: ${data.queue_position || '?'})`;
        }
        
    } catch (error) {
        console.error('Error polling results:', error);
        clearInterval(state.pollInterval);
        showToast('Error fetching results. Please try again.');
        goToStep(2);
    }
}

// ============================================================================
// STEP 4: DISPLAY RESULTS
// ============================================================================

const resultsTable = document.getElementById('resultsTable');
const itemsFoundCount = document.getElementById('itemsFoundCount');
const zipDisplay = document.getElementById('zipDisplay');
const totalItems = document.getElementById('totalItems');
const totalProducts = document.getElementById('totalProducts');
const processingTime = document.getElementById('processingTime');
const newSearchBtn = document.getElementById('newSearchBtn');

/**
 * Display search results
 */
function displayResults(data) {
    const results = data.results || {};
    const itemsWithResults = Object.keys(results).filter(item => results[item].length > 0);
    
    // DEBUG: Log raw API response
    console.log('=== RAW API RESPONSE ===');
    console.log('Full data:', JSON.stringify(data, null, 2));
    console.log('First item products:', results[Object.keys(results)[0]]?.slice(0, 3));
    
    // Update summary
    itemsFoundCount.textContent = itemsWithResults.length;
    zipDisplay.textContent = data.zip_code || state.zipCode;
    totalItems.textContent = state.cart.length;
    
    let totalProductsCount = 0;
    Object.values(results).forEach(products => {
        totalProductsCount += products.length;
    });
    totalProducts.textContent = totalProductsCount;
    
    processingTime.textContent = data.total_time ? `${data.total_time.toFixed(1)}s` : '-';
    
    // Render results
    resultsTable.innerHTML = '';
    
    state.cart.forEach((cartItem, cartIndex) => {
        const products = results[cartItem.name] || [];
        
        if (products.length === 0) {
            // No results found
            resultsTable.innerHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-item-name">${cartItem.name}</span>
                    </div>
                    <div class="result-products">
                        <p style="text-align: center; color: #9E9E9E; padding: 20px;">No products found</p>
                    </div>
                </div>
            `;
        } else {
            // Sort by price (cheapest first)
            const sortedProducts = [...products].sort((a, b) => a.price - b.price);
            
            // Get best price
            const bestPrice = sortedProducts[0].price;
            
            // Group stores by same price
            const bestPriceProducts = sortedProducts.filter(p => p.price === bestPrice);
            const otherProducts = sortedProducts.filter(p => p.price !== bestPrice);
            
            // Create best price display
            let bestPriceHTML = '';
            if (bestPriceProducts.length === 1) {
                // Single store at best price
                const product = bestPriceProducts[0];
                const locationText = product.location ? `<div class="product-location">📍 ${product.location}</div>` : '';
                bestPriceHTML = `
                    <div class="product-row best">
                        <div class="product-name">
                            <span class="best-badge">⭐ BEST PRICE</span>
                            ${product.name || product.title || 'Product'}
                        </div>
                        <div class="product-price">$${bestPrice.toFixed(2)}</div>
                        <div class="product-merchant">
                            ${product.merchant}
                            ${locationText}
                        </div>
                    </div>
                `;
            } else {
                // Multiple stores at best price
                const firstStore = bestPriceProducts[0].merchant;
                const firstLocation = bestPriceProducts[0].location ? `<div class="product-location">📍 ${bestPriceProducts[0].location}</div>` : '';
                const otherCount = bestPriceProducts.length - 1;
                const cardId = `card-${cartIndex}`;
                
                bestPriceHTML = `
                    <div class="product-row best">
                        <div class="product-name">
                            <span class="best-badge">⭐ BEST PRICE</span>
                            ${bestPriceProducts[0].name || bestPriceProducts[0].title || 'Product'}
                        </div>
                        <div class="product-price">$${bestPrice.toFixed(2)}</div>
                        <div class="product-merchant">
                            ${firstStore}
                            ${firstLocation}
                            <button class="btn-expand" onclick="toggleStores('${cardId}')" id="btn-${cardId}">
                                + ${otherCount} other store${otherCount > 1 ? 's' : ''}
                            </button>
                        </div>
                    </div>
                    <div id="${cardId}" class="other-stores hidden">
                        ${bestPriceProducts.slice(1).map(p => {
                            const loc = p.location ? `<div class="product-location">📍 ${p.location}</div>` : '';
                            return `
                                <div class="product-row">
                                    <div class="product-name">${p.name || p.title || 'Product'}</div>
                                    <div class="product-price">$${p.price.toFixed(2)}</div>
                                    <div class="product-merchant">
                                        ${p.merchant}
                                        ${loc}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            
            resultsTable.innerHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-item-name">${cartItem.name}</span>
                    </div>
                    <div class="result-products">
                        ${bestPriceHTML}
                    </div>
                </div>
            `;
        }
    });
}

/**
 * Toggle visibility of other stores
 */
window.toggleStores = function(cardId) {
    const storesDiv = document.getElementById(cardId);
    const btn = document.getElementById(`btn-${cardId}`);
    
    if (storesDiv.classList.contains('hidden')) {
        storesDiv.classList.remove('hidden');
        btn.textContent = '- Hide other stores';
    } else {
        storesDiv.classList.add('hidden');
        const count = storesDiv.querySelectorAll('.product-row').length;
        btn.textContent = `+ ${count} other store${count > 1 ? 's' : ''}`;
    }
};

newSearchBtn.addEventListener('click', () => {
    // Reset state
    state.cart = [];
    state.jobId = null;
    state.zipCode = null;
    
    // Reset inputs
    itemInput.value = '';
    zipInput.value = '';
    
    // Reset UI
    renderCart();
    suggestionsDiv.classList.add('hidden');
    
    // Go back to step 1
    goToStep(1);
});

// ============================================================================
// INITIALIZE
// ============================================================================

// Make functions available globally (for onclick handlers)
window.removeFromCart = removeFromCart;

// Initial render
renderCart();

console.log('🚀 Low Cost Groceries - AI Shopping Assistant loaded');
console.log('📡 API URL:', CONFIG.API_BASE_URL);

