// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// State Management
const state = {
    searchResults: [],
    compareSessionId: null,
    compareProducts: [],
    favorites: [],
    currentView: 'categories',
    productCache: {},
    categories: [],
    currentCategory: null
};

// DOM Elements
const searchForm = document.getElementById('searchForm');
const searchResults = document.getElementById('searchResults');
const loadingIndicator = document.getElementById('loadingIndicator');
const compareGrid = document.getElementById('compareGrid');
const favoritesGrid = document.getElementById('favoritesGrid');
const productModal = document.getElementById('productModal');
const modalContent = document.getElementById('modalContent');
const favCount = document.getElementById('favCount');

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    initializeEventListeners();
    await loadFavorites();
    loadCategories();
    populateCategoryDropdown();
    await initComparisonSession();
});

// Event Listeners
function initializeEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const view = e.target.dataset.view;
            switchView(view);
        });
    });

    // Search Form
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await performSearch();
    });

    // Modal Close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === productModal) {
            closeModal();
        }
    });
}

// View Management
function switchView(view) {
    state.currentView = view;
    
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Update views
    document.querySelectorAll('.view').forEach(v => {
        v.classList.remove('active');
    });
    document.getElementById(`${view}View`).classList.add('active');
    
    // Load view-specific content
    if (view === 'categories') {
        loadCategories();
    } else if (view === 'compare') {
        renderCompareView();
    } else if (view === 'favorites') {
        renderFavoritesView();
    }
}

// Categories Functions
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        const data = await response.json();
        state.categories = data.categories;
        renderCategories();
    } catch (error) {
        console.error('Failed to load categories:', error);
        showError('Failed to load categories');
    }
}

function renderCategories() {
    const categoriesGrid = document.getElementById('categoriesGrid');
    const categoryProducts = document.getElementById('categoryProducts');
    
    categoriesGrid.style.display = 'grid';
    categoryProducts.style.display = 'none';
    
    categoriesGrid.innerHTML = state.categories.map(category => `
        <div class="category-card" data-category="${category.category_id}">
            <div class="category-name">${category.name}</div>
            <div class="category-count">${category.product_count} products</div>
            <div class="category-info">
                ${category.avg_rating ? `<span>★ ${category.avg_rating}</span>` : ''}
                ${category.price_range ? `<span>$${category.price_range.min}-$${category.price_range.max}</span>` : ''}
            </div>
        </div>
    `).join('');
    
    // Add click handlers
    categoriesGrid.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', () => {
            const categoryId = card.dataset.category;
            loadCategoryProducts(categoryId);
        });
    });
}

async function populateCategoryDropdown() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        const data = await response.json();
        
        const categorySelect = document.getElementById('category');
        if (categorySelect) {
            // Keep the "All Categories" option and add the rest
            const options = data.categories.map(cat => 
                `<option value="${cat.category_id}">${cat.name}</option>`
            ).join('');
            
            categorySelect.innerHTML = '<option value="">All Categories</option>' + options;
        }
    } catch (error) {
        console.error('Failed to load categories for dropdown:', error);
    }
}

async function loadCategoryProducts(categoryId) {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/${categoryId}/top`);
        const data = await response.json();
        
        state.currentCategory = data.category;
        renderCategoryProducts(data.products);
    } catch (error) {
        console.error('Failed to load category products:', error);
        showError('Failed to load products');
    }
}

function renderCategoryProducts(products) {
    const categoriesGrid = document.getElementById('categoriesGrid');
    const categoryProducts = document.getElementById('categoryProducts');
    const categoryTitle = document.getElementById('categoryTitle');
    const categoryProductsGrid = document.getElementById('categoryProductsGrid');
    
    categoriesGrid.style.display = 'none';
    categoryProducts.style.display = 'block';
    categoryTitle.textContent = `${state.currentCategory.name} - Top Products`;
    
    categoryProductsGrid.innerHTML = products.map(product => createProductCard({
        product_id: product.product_id,
        brand: product.brand,
        model_name: product.model_name,
        price_range: product.price_range || {min: 0, max: 0},
        rating: product.rating,
        category: product.category,
        specs: product.specs || {},
        score: Math.round((product.rating || 0) * 20) || 0,
        popularity_rank: product.popularity_rank
    })).join('');
    
    // Add event listeners
    categoryProductsGrid.querySelectorAll('.product-card').forEach(card => {
        const productId = card.dataset.productId;
        const product = products.find(p => p.product_id === productId);
        
        card.querySelector('.btn-details').addEventListener('click', () => {
            showProductDetails(productId);
        });
        
        card.querySelector('.btn-compare').addEventListener('click', () => {
            toggleCompare(product);
        });
        
        card.querySelector('.btn-favorite').addEventListener('click', async (e) => {
            await toggleFavorite(product);
        });
    });
    
    // Back button
    document.getElementById('backToCategories').onclick = () => {
        renderCategories();
    };
}

// Search Functionality

async function performSearch() {
    const formData = new FormData(searchForm);
    const params = new URLSearchParams();
    
    if (formData.get('budget')) params.append('budget_max', formData.get('budget'));
    if (formData.get('category')) params.append('category', formData.get('category'));
    if (formData.get('brand')) params.append('brand', formData.get('brand'));
    if (formData.get('minRam')) params.append('min_ram', formData.get('minRam'));
    if (formData.get('minStorage')) params.append('min_storage', formData.get('minStorage'));
    if (formData.get('cameraImportance')) params.append('camera_importance', formData.get('cameraImportance'));
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/search?${params}`);
        const data = await response.json();
        
        state.searchResults = data.products;
        renderSearchResults(data.products);
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to search phones. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Render Functions
function renderSearchResults(products) {
    if (products.length === 0) {
        searchResults.innerHTML = `
            <div class="message-box" style="grid-column: 1/-1;">
                <p>No phones found matching your criteria. Try adjusting your filters.</p>
            </div>
        `;
        return;
    }
    
    searchResults.innerHTML = products.map(product => createProductCard(product)).join('');
    
    // Add event listeners to cards
    searchResults.querySelectorAll('.product-card').forEach(card => {
        const productId = card.dataset.productId;
        const product = products.find(p => p.product_id === productId);
        
        // View Details
        card.querySelector('.btn-details').addEventListener('click', () => {
            showProductDetails(productId);
        });
        
        // Add to Compare
        card.querySelector('.btn-compare').addEventListener('click', () => {
            toggleCompare(product);
        });
        
        // Toggle Favorite
        card.querySelector('.btn-favorite').addEventListener('click', async (e) => {
            await toggleFavorite(product);
        });
    });
}

function renderProductSpecs(specs) {
    if (!specs) return '<p class="text-muted">No specifications available</p>';
    
    // Define priority specs to show
    const prioritySpecs = ['brand', 'model_number', 'color', 'product_name'];
    const specsToShow = [];
    
    // Add priority specs first
    prioritySpecs.forEach(key => {
        if (specs[key]) {
            const label = key.replace(/_/g, ' ');
            const value = key === 'product_name' && specs[key].length > 40 
                ? specs[key].substring(0, 40) + '...' 
                : specs[key];
            specsToShow.push({ label, value });
        }
    });
    
    // Add other important specs if they exist and we have room
    const additionalSpecs = ['screen_size', 'memory_storage_capacity', 'wireless_carrier'];
    let specsAdded = specsToShow.length;
    
    for (const key of additionalSpecs) {
        if (specsAdded >= 5) break; // Limit to 5 specs max
        if (specs[key]) {
            const label = key.replace(/_/g, ' ');
            specsToShow.push({ label, value: specs[key] });
            specsAdded++;
        }
    }
    
    // If we still don't have any specs, show the first few available
    if (specsToShow.length === 0) {
        const specKeys = Object.keys(specs).slice(0, 4);
        specKeys.forEach(key => {
            const label = key.replace(/_/g, ' ');
            const value = specs[key].toString().length > 40 
                ? specs[key].toString().substring(0, 40) + '...' 
                : specs[key];
            specsToShow.push({ label, value });
        });
    }
    
    return specsToShow.map(spec => `
        <div class="spec-item">
            <span class="spec-label">${spec.label}:</span>
            <span>${spec.value}</span>
        </div>
    `).join('');
}

function createProductCard(product) {
    // All endpoints now use product_id consistently
    const productId = product.product_id;
    const isFavorite = state.favorites.some(f => f.product_id === productId);
    const isInCompare = state.compareProducts.some(c => c.product_id === productId);
    
    return `
        <div class="product-card" data-product-id="${productId}">
            ${product.image_url ? `
                <div class="product-image">
                    <img src="${product.image_url}" alt="${product.model_name || product.name}" style="width: 100%; max-height: 150px; object-fit: contain;">
                </div>
            ` : ''}
            <div class="product-header">
                <div class="product-score">${Math.round(product.score || 0)}</div>
                <h3 class="product-title">${product.model_name || product.name || 'Unknown'}</h3>
                <p class="product-brand">${product.brand || 'Unknown Brand'}</p>
            </div>
            <div class="product-body">
                <div class="price-range">
                    ${product.price_range ? 
                        `$${product.price_range.min} - $${product.price_range.max}` :
                        (product.spec_ranges?.price ? 
                            `$${product.spec_ranges.price.min} - $${product.spec_ranges.price.max}` : 
                            'Price N/A')}
                </div>
                ${product.specs && Object.keys(product.specs).length > 0 ? `
                    <div class="specs-title">Product Details</div>
                    <div class="specs-grid">
                        ${renderProductSpecs(product.specs)}
                    </div>
                ` : ''}
            </div>
            <div class="product-actions">
                <button class="btn btn-primary btn-sm btn-details">View Details</button>
                <button class="btn btn-outline btn-sm btn-compare ${isInCompare ? 'active' : ''}">
                    ${isInCompare ? 'In Compare' : 'Compare'}
                </button>
                <button class="btn-icon btn-favorite ${isFavorite ? 'active' : ''}">
                    ${isFavorite ? '❤️' : '🤍'}
                </button>
            </div>
        </div>
    `;
}

// Product Details
async function showProductDetails(productId) {
    showLoading(true);
    
    try {
        // Fetch product details
        const productResponse = await fetch(`${API_BASE_URL}/products/${productId}`);
        if (!productResponse.ok) {
            throw new Error('Failed to fetch product details');
        }
        const productData = await productResponse.json();
        
        // Try to fetch reviews, but don't fail if unavailable
        let reviewsData = null;
        try {
            const reviewsResponse = await fetch(`${API_BASE_URL}/reviews/product/${productId}/summary`);
            if (reviewsResponse.ok) {
                reviewsData = await reviewsResponse.json();
            }
        } catch (reviewError) {
            console.warn('Reviews not available for this product');
        }
        
        renderProductModal(productData.product, reviewsData);
        productModal.classList.add('show');
    } catch (error) {
        console.error('Error fetching product details:', error);
        showError('Failed to load product details.');
    } finally {
        showLoading(false);
    }
}

function renderProductModal(product, reviews) {
    // Build specs HTML dynamically based on available specs
    let specsHtml = '';
    const specLabels = {
        os: 'Operating System',
        soc: 'Processor',
        processor: 'Processor',
        ram_gb: 'RAM',
        storage_gb: 'Storage',
        display_size: 'Display Size',
        display: 'Display',
        battery: 'Battery',
        camera_mp: 'Camera',
        cameras: 'Cameras',
        ip_rating: 'IP Rating',
        weight_g: 'Weight',
        connectivity: 'Connectivity',
        bands_5g: '5G Bands',
        wifi: 'WiFi',
        bluetooth: 'Bluetooth'
    };
    
    // Generate spec items dynamically
    for (const [key, value] of Object.entries(product.specs || {})) {
        if (value !== null && value !== undefined) {
            const label = specLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            let displayValue = value;
            
            // Format specific values
            if (key === 'ram_gb' || key === 'storage_gb') {
                displayValue = `${value} GB`;
            } else if (key === 'weight_g') {
                displayValue = `${value}g`;
            } else if (key === 'camera_mp') {
                displayValue = `${value} MP`;
            } else if (key === 'display_size') {
                displayValue = `${value}"`;
            } else if (typeof value === 'object') {
                displayValue = JSON.stringify(value);
            }
            
            specsHtml += `
                <div class="spec-item">
                    <span class="spec-label">${label}:</span>
                    <span>${displayValue}</span>
                </div>
            `;
        }
    }
    
    // If no specs, show a message
    if (!specsHtml) {
        specsHtml = '<p>No specifications available</p>';
    }
    
    modalContent.innerHTML = `
        <div class="modal-header">
            <h2>${product.brand || ''} ${product.model_name || product.name || ''}</h2>
            ${product.release_date ? `<p>Released: ${new Date(product.release_date).toLocaleDateString()}</p>` : ''}
        </div>
        <div class="modal-body">
            ${product.images && product.images.length > 0 ? `
            <div class="product-images" style="margin-bottom: 20px;">
                <div style="display: flex; gap: 10px; overflow-x: auto; padding: 10px 0;">
                    ${product.images.slice(0, 5).map(img => `
                        <img src="${img}" style="height: 100px; object-fit: contain; cursor: pointer;" 
                             onclick="this.style.height = this.style.height === '100px' ? '300px' : '100px'">
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${product.description ? `
            <div class="description-section" style="margin-bottom: 20px;">
                <h3>Description</h3>
                <p>${product.description.substring(0, 500)}${product.description.length > 500 ? '...' : ''}</p>
            </div>
            ` : ''}
            
            ${product.feature_bullets && product.feature_bullets.length > 0 ? `
            <div class="features-section" style="margin-bottom: 20px;">
                <h3>Key Features</h3>
                <ul>
                    ${product.feature_bullets.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${product.variant_options && product.variant_options.length > 0 ? `
            <div class="variants-section" style="margin-bottom: 20px;">
                <h3>Available Variants</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px;">
                    ${product.variant_options.slice(0, 12).map(variant => `
                        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                            <div style="font-weight: 600; margin-bottom: 5px;">${variant.title || 'Variant'}</div>
                            ${variant.dimensions ? `
                                <div style="font-size: 0.9em; color: #666;">
                                    ${variant.dimensions.color ? `Color: ${variant.dimensions.color}<br>` : ''}
                                    ${variant.dimensions.size ? `Storage: ${variant.dimensions.size}<br>` : ''}
                                </div>
                            ` : ''}
                            ${variant.link ? `
                                <a href="${variant.link}" target="_blank" style="color: #007bff; text-decoration: none; font-size: 0.9em;">
                                    View on Amazon →
                                </a>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            <div class="specs-section">
                <h3>Specifications</h3>
                <div class="specs-grid">
                    ${specsHtml}
                </div>
            </div>
            
            ${reviews && reviews.average_rating ? `
            <div class="reviews-section mt-3">
                <h3>Reviews Summary</h3>
                <div class="review-summary">
                    <p><strong>Average Rating:</strong> ${reviews.average_rating}/10</p>
                    <p><strong>Coverage:</strong> ${reviews.coverage_level || 'N/A'}</p>
                    ${reviews.credibility_breakdown ? 
                        `<p><strong>Sources:</strong> ${reviews.credibility_breakdown.pro_reviews || 0} professional reviews</p>` : ''}
                    
                    ${reviews.pro_consensus && reviews.pro_consensus.length > 0 ? `
                    <div class="mt-2">
                        <h4>Pros:</h4>
                        <ul>
                            ${reviews.pro_consensus.map(pro => `<li>${pro}</li>`).join('')}
                        </ul>
                    </div>` : ''}
                    
                    ${reviews.con_consensus && reviews.con_consensus.length > 0 ? `
                    <div class="mt-2">
                        <h4>Cons:</h4>
                        <ul>
                            ${reviews.con_consensus.map(con => `<li>${con}</li>`).join('')}
                        </ul>
                    </div>` : ''}
                    
                    ${reviews.summary ? `<p class="mt-2">${reviews.summary}</p>` : ''}
                </div>
            </div>` : ''}
        </div>
    `;
}

// Compare Functionality
async function initComparisonSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/compare/session`, {
            method: 'POST'
        });
        const data = await response.json();
        state.compareSessionId = data.session_id;
    } catch (error) {
        console.error('Failed to create comparison session:', error);
    }
}

async function toggleCompare(product) {
    if (!state.compareSessionId) {
        await initComparisonSession();
    }
    
    const productId = product.product_id;
    const isInCompare = state.compareProducts.some(p => p.product_id === productId);
    
    try {
        if (isInCompare) {
            // Remove from comparison
            const response = await fetch(
                `${API_BASE_URL}/compare/session/${state.compareSessionId}/remove/${productId}`,
                { method: 'DELETE' }
            );
            
            if (response.ok) {
                state.compareProducts = state.compareProducts.filter(
                    p => p.product_id !== productId
                );
                updateCompareButtons();
            }
        } else {
            // Add to comparison
            const response = await fetch(
                `${API_BASE_URL}/compare/session/${state.compareSessionId}/add`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: productId })
                }
            );
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            state.compareProducts.push(product);
            updateCompareButtons();
        }
        
        if (state.currentView === 'compare') {
            await renderCompareView();
        }
    } catch (error) {
        console.error('Compare error:', error);
        showError('Failed to update comparison');
    }
}

function updateCompareButtons() {
    document.querySelectorAll('.btn-compare').forEach(btn => {
        const card = btn.closest('.product-card');
        if (card) {
            const productId = card.dataset.productId;
            const isInCompare = state.compareProducts.some(
                p => p.product_id === productId
            );
            
            btn.classList.toggle('active', isInCompare);
            btn.textContent = isInCompare ? 'In Compare' : 'Compare';
        }
    });
}

async function renderCompareView() {
    if (!state.compareSessionId || state.compareProducts.length === 0) {
        compareGrid.innerHTML = '';
        document.getElementById('compareMessage').style.display = 'block';
        return;
    }
    
    try {
        // Fetch comparison data from server
        const response = await fetch(
            `${API_BASE_URL}/compare/session/${state.compareSessionId}`
        );
        const data = await response.json();
        
        if (!data.products || data.products.length === 0) {
            compareGrid.innerHTML = '';
            document.getElementById('compareMessage').style.display = 'block';
            return;
        }
        
        document.getElementById('compareMessage').style.display = 'none';
        
        const comparison = data.comparison;
        const products = data.products;
        
        // Build comparison table
        let tableHTML = `
            <div class="comparison-container">
                <table class="compare-table" style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="padding: 1rem; text-align: left; border-bottom: 2px solid var(--border); width: 200px;">Feature</th>
                            ${products.map(p => `
                                <th style="padding: 1rem; text-align: center; border-bottom: 2px solid var(--border);">
                                    <div>${p.brand || ''} ${p.model_name || p.name || ''}</div>
                                    <button onclick="removeFromCompare('${p.product_id}')" style="margin-top: 0.5rem; color: var(--danger); border: none; background: none; cursor: pointer;">✕ Remove</button>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Basic Info Section
        tableHTML += `
            <tr class="section-header">
                <td colspan="${products.length + 1}" style="padding: 0.75rem; background: var(--light); font-weight: bold;">Basic Information</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Category</strong></td>
                ${products.map(p => `
                    <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                        ${comparison.basic_info[p.product_id]?.category || '—'}
                    </td>
                `).join('')}
            </tr>
        `;
        
        // Pricing Section
        tableHTML += `
            <tr class="section-header">
                <td colspan="${products.length + 1}" style="padding: 0.75rem; background: var(--light); font-weight: bold;">Pricing</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Price Range</strong></td>
                ${products.map(p => {
                    const pricing = comparison.pricing[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            $${pricing?.min || 0} - $${pricing?.max || 0}
                        </td>
                    `;
                }).join('')}
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Best Price</strong></td>
                ${products.map(p => {
                    const pricing = comparison.pricing[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${pricing?.best_price ? `$${pricing.best_price}` : '—'}
                            ${pricing?.retailer ? `<br><small>${pricing.retailer}</small>` : ''}
                        </td>
                    `;
                }).join('')}
            </tr>
        `;
        
        // Ratings Section
        tableHTML += `
            <tr class="section-header">
                <td colspan="${products.length + 1}" style="padding: 0.75rem; background: var(--light); font-weight: bold;">Ratings & Reviews</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Average Rating</strong></td>
                ${products.map(p => {
                    const rating = comparison.ratings[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${rating?.average ? `★ ${rating.average}` : '—'}
                        </td>
                    `;
                }).join('')}
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Reviews</strong></td>
                ${products.map(p => {
                    const rating = comparison.ratings[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${rating?.review_count || 0} reviews
                        </td>
                    `;
                }).join('')}
            </tr>
        `;
        
        // Specifications Section
        if (comparison.specs) {
            const specKeys = new Set();
            Object.values(comparison.specs).forEach(specs => {
                Object.keys(specs).forEach(key => specKeys.add(key));
            });
            
            tableHTML += `
                <tr class="section-header">
                    <td colspan="${products.length + 1}" style="padding: 0.75rem; background: var(--light); font-weight: bold;">Specifications</td>
                </tr>
            `;
            
            specKeys.forEach(key => {
                const label = comparison.spec_labels?.[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                tableHTML += `
                    <tr>
                        <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>${label}</strong></td>
                        ${products.map(p => `
                            <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                                ${comparison.specs[p.product_id]?.[key] || '—'}
                            </td>
                        `).join('')}
                    </tr>
                `;
            });
        }
        
        // Availability Section
        tableHTML += `
            <tr class="section-header">
                <td colspan="${products.length + 1}" style="padding: 0.75rem; background: var(--light); font-weight: bold;">Availability</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Variants</strong></td>
                ${products.map(p => {
                    const avail = comparison.availability[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${avail?.variants || 0} options
                        </td>
                    `;
                }).join('')}
            </tr>
            <tr>
                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Offers</strong></td>
                ${products.map(p => {
                    const avail = comparison.availability[p.product_id];
                    return `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${avail?.offers || 0} retailers
                        </td>
                    `;
                }).join('')}
            </tr>
        `;
        
        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;
        
        compareGrid.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Failed to render comparison:', error);
        showError('Failed to load comparison data');
    }
}

window.removeFromCompare = async function(productId) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/compare/session/${state.compareSessionId}/remove/${productId}`,
            { method: 'DELETE' }
        );
        
        if (response.ok) {
            state.compareProducts = state.compareProducts.filter(
                p => (p._id || p.product_id) !== productId
            );
            updateCompareButtons();
            await renderCompareView();
        }
    } catch (error) {
        console.error('Failed to remove from comparison:', error);
    }
};

// Favorites Functionality
async function loadFavorites() {
    try {
        const response = await fetch(`${API_BASE_URL}/favorites/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        state.favorites = data.favorites.map(f => f.product);
        updateFavoritesCount();
    } catch (error) {
        console.error('Failed to load favorites:', error);
        state.favorites = [];
        updateFavoritesCount();
    }
}

async function toggleFavorite(product) {
    const productId = product.product_id;
    
    try {
        const response = await fetch(`${API_BASE_URL}/favorites/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ product_id: productId })
        });
        
        const data = await response.json();
        
        if (data.is_favorite) {
            // Add to local state
            if (!state.favorites.some(f => f.product_id === productId)) {
                state.favorites.push(product);
            }
        } else {
            // Remove from local state
            state.favorites = state.favorites.filter(
                f => f.product_id !== productId
            );
        }
        
        updateFavoritesCount();
        updateFavoriteButtons();
        
        if (state.currentView === 'favorites') {
            renderFavoritesView();
        }
    } catch (error) {
        console.error('Failed to toggle favorite:', error);
        showError('Failed to update favorites');
    }
}

function updateFavoriteButtons() {
    document.querySelectorAll('.btn-favorite').forEach(btn => {
        const card = btn.closest('.product-card');
        if (card) {
            const productId = card.dataset.productId;
            const isFavorite = state.favorites.some(
                f => f.product_id === productId
            );
            
            btn.classList.toggle('active', isFavorite);
            btn.innerHTML = isFavorite ? '❤️' : '🤍';
        }
    });
}

async function updateFavoritesCount() {
    try {
        const response = await fetch(`${API_BASE_URL}/favorites/count`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        favCount.textContent = data.count;
        favCount.style.display = data.count > 0 ? 'flex' : 'none';
    } catch (error) {
        // Fallback to local state
        favCount.textContent = state.favorites.length;
        favCount.style.display = state.favorites.length > 0 ? 'flex' : 'none';
    }
}

async function renderFavoritesView() {
    // Reload favorites from server
    await loadFavorites();
    
    if (state.favorites.length === 0) {
        favoritesGrid.innerHTML = '';
        document.getElementById('favoritesMessage').style.display = 'block';
        return;
    }
    
    document.getElementById('favoritesMessage').style.display = 'none';
    favoritesGrid.innerHTML = state.favorites.map(product => createProductCard(product)).join('');
    
    // Add event listeners
    favoritesGrid.querySelectorAll('.product-card').forEach(card => {
        const productId = card.dataset.productId;
        const product = state.favorites.find(p => p.product_id === productId);
        
        card.querySelector('.btn-details').addEventListener('click', () => {
            showProductDetails(productId);
        });
        
        card.querySelector('.btn-compare').addEventListener('click', () => {
            toggleCompare(product);
        });
        
        card.querySelector('.btn-favorite').addEventListener('click', async () => {
            await toggleFavorite(product);
        });
    });
}

// Utility Functions
function showLoading(show) {
    loadingIndicator.style.display = show ? 'block' : 'none';
    if (show) {
        searchResults.innerHTML = '';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message-box';
    errorDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; background: var(--danger); color: white; z-index: 1000;';
    errorDiv.innerHTML = `<p>${message}</p>`;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

function closeModal() {
    productModal.classList.remove('show');
    modalContent.innerHTML = '';
}