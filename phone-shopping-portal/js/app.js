// API Configuration
// Determine API base automatically based on the current host
const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

// State Management
const state = {
    searchResults: [],
    compareList: [],
    favorites: JSON.parse(localStorage.getItem('favorites') || '[]'),
    currentView: 'search',
    productCache: {}
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
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateFavoritesCount();
    performInitialSearch();
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
    if (view === 'compare') {
        renderCompareView();
    } else if (view === 'favorites') {
        renderFavoritesView();
    }
}

// Search Functionality
async function performInitialSearch() {
    await performSearch();
}

async function performSearch() {
    const formData = new FormData(searchForm);
    const params = new URLSearchParams();
    
    if (formData.get('budget')) params.append('budget_max', formData.get('budget'));
    if (formData.get('os')) params.append('os', formData.get('os'));
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
        card.querySelector('.btn-favorite').addEventListener('click', (e) => {
            toggleFavorite(product);
            e.currentTarget.classList.toggle('active');
        });
    });
}

function createProductCard(product) {
    const isFavorite = state.favorites.some(f => f.product_id === product.product_id);
    const isInCompare = state.compareList.some(c => c.product_id === product.product_id);
    
    return `
        <div class="product-card" data-product-id="${product.product_id}">
            <div class="product-header">
                <div class="product-score">${Math.round(product.score)}</div>
                <h3 class="product-title">${product.model_name}</h3>
                <p class="product-brand">${product.brand}</p>
            </div>
            <div class="product-body">
                <div class="price-range">
                    $${product.spec_ranges.price.min} - $${product.spec_ranges.price.max}
                </div>
                <div class="specs-grid">
                    <div class="spec-item">
                        <span class="spec-label">RAM:</span>
                        <span>${product.spec_ranges.ram}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Storage:</span>
                        <span>${product.spec_ranges.storage}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Display:</span>
                        <span>${product.spec_ranges.display}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Battery:</span>
                        <span>${product.spec_ranges.battery}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Charging:</span>
                        <span>${product.spec_ranges.charging}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">OS:</span>
                        <span>${product.specs.os.value}</span>
                    </div>
                </div>
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
        const productData = await productResponse.json();
        
        // Fetch reviews
        const reviewsResponse = await fetch(`${API_BASE_URL}/reviews/product/${productId}/summary`);
        const reviewsData = await reviewsResponse.json();
        
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
    const cameras = product.specs.cameras;
    const rearCameras = cameras.rear.map(cam => 
        `${cam.mp}MP ${cam.role}${cam.ois ? ' (OIS)' : ''}`
    ).join(', ');
    
    modalContent.innerHTML = `
        <div class="modal-header">
            <h2>${product.brand} ${product.model_name}</h2>
            <p>Released: ${new Date(product.release_date).toLocaleDateString()}</p>
        </div>
        <div class="modal-body">
            <div class="specs-section">
                <h3>Specifications</h3>
                <div class="specs-grid">
                    <div class="spec-item">
                        <span class="spec-label">OS:</span>
                        <span>${product.specs.os.value}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Processor:</span>
                        <span>${product.specs.soc.value}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">RAM:</span>
                        <span>${product.specs.ram_gb.value} GB</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Storage:</span>
                        <span>${product.specs.storage_gb.min}-${product.specs.storage_gb.max} GB</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Display:</span>
                        <span>${product.specs.display.size_in}" ${product.specs.display.tech}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Refresh Rate:</span>
                        <span>${product.specs.display.refresh_hz}Hz</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Battery:</span>
                        <span>${product.specs.battery.capacity_mah} mAh</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Charging:</span>
                        <span>${product.specs.battery.wired_charging_w}W wired${product.specs.battery.wireless_charging_w ? `, ${product.specs.battery.wireless_charging_w}W wireless` : ''}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Rear Cameras:</span>
                        <span>${rearCameras}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Front Camera:</span>
                        <span>${cameras.front.mp}MP</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">IP Rating:</span>
                        <span>${product.specs.ip_rating}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Weight:</span>
                        <span>${product.specs.weight_g}g</span>
                    </div>
                </div>
            </div>
            
            <div class="reviews-section mt-3">
                <h3>Reviews Summary</h3>
                <div class="review-summary">
                    <p><strong>Average Rating:</strong> ${reviews.average_rating}/10</p>
                    <p><strong>Coverage:</strong> ${reviews.coverage_level}</p>
                    <p><strong>Sources:</strong> ${reviews.credibility_breakdown.pro_reviews} professional reviews</p>
                    
                    <div class="mt-2">
                        <h4>Pros:</h4>
                        <ul>
                            ${reviews.pro_consensus.map(pro => `<li>${pro}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="mt-2">
                        <h4>Cons:</h4>
                        <ul>
                            ${reviews.con_consensus.map(con => `<li>${con}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <p class="mt-2">${reviews.summary}</p>
                </div>
            </div>
        </div>
    `;
}

// Compare Functionality
function toggleCompare(product) {
    const index = state.compareList.findIndex(p => p.product_id === product.product_id);
    
    if (index > -1) {
        state.compareList.splice(index, 1);
    } else {
        if (state.compareList.length >= 4) {
            showError('You can compare up to 4 phones at a time.');
            return;
        }
        state.compareList.push(product);
    }
    
    if (state.currentView === 'compare') {
        renderCompareView();
    }
}

function renderCompareView() {
    if (state.compareList.length === 0) {
        compareGrid.innerHTML = '';
        document.getElementById('compareMessage').style.display = 'block';
        return;
    }
    
    document.getElementById('compareMessage').style.display = 'none';
    
    compareGrid.innerHTML = `
        <table class="compare-table" style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="padding: 1rem; text-align: left; border-bottom: 2px solid var(--border);">Feature</th>
                    ${state.compareList.map(p => `
                        <th style="padding: 1rem; text-align: center; border-bottom: 2px solid var(--border);">
                            ${p.brand} ${p.model_name}
                            <button onclick="removeFromCompare('${p.product_id}')" style="margin-left: 0.5rem; color: var(--danger); border: none; background: none; cursor: pointer;">✕</button>
                        </th>
                    `).join('')}
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Price Range</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            $${p.spec_ranges.price.min} - $${p.spec_ranges.price.max}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Score</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${Math.round(p.score)}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>OS</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.specs.os.value}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Processor</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.specs.soc.value}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>RAM</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.spec_ranges.ram}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Storage</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.spec_ranges.storage}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Display</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.spec_ranges.display}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Battery</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.spec_ranges.battery}
                        </td>
                    `).join('')}
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid var(--border);"><strong>Charging</strong></td>
                    ${state.compareList.map(p => `
                        <td style="padding: 0.75rem; text-align: center; border-bottom: 1px solid var(--border);">
                            ${p.spec_ranges.charging}
                        </td>
                    `).join('')}
                </tr>
            </tbody>
        </table>
    `;
}

window.removeFromCompare = function(productId) {
    state.compareList = state.compareList.filter(p => p.product_id !== productId);
    renderCompareView();
};

// Favorites Functionality
function toggleFavorite(product) {
    const index = state.favorites.findIndex(f => f.product_id === product.product_id);
    
    if (index > -1) {
        state.favorites.splice(index, 1);
    } else {
        state.favorites.push(product);
    }
    
    localStorage.setItem('favorites', JSON.stringify(state.favorites));
    updateFavoritesCount();
    
    if (state.currentView === 'favorites') {
        renderFavoritesView();
    }
}

function updateFavoritesCount() {
    favCount.textContent = state.favorites.length;
    favCount.style.display = state.favorites.length > 0 ? 'flex' : 'none';
}

function renderFavoritesView() {
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
        
        card.querySelector('.btn-favorite').addEventListener('click', () => {
            toggleFavorite(product);
            renderFavoritesView();
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