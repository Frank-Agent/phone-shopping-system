const API_BASE = '/api/v1';

document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const params = new URLSearchParams();
    
    formData.forEach((value, key) => {
        if (value) params.append(key, value);
    });
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/search?${params}`);
        const data = await response.json();
        
        displaySearchResults(data);
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
});

function displaySearchResults(data) {
    const resultsDiv = document.getElementById('results');
    
    if (data.products.length === 0) {
        resultsDiv.innerHTML = '<p>No products found matching your criteria.</p>';
        return;
    }
    
    let html = `<h2>Found ${data.total_results} phones</h2>`;
    
    data.products.forEach(product => {
        const priceRange = product.spec_ranges.price;
        html += `
            <div class="product-card">
                <div class="product-header">
                    <div class="product-name">${product.brand} ${product.model_name}</div>
                    <div class="price-range">$${priceRange.min} - $${priceRange.max}</div>
                </div>
                <div class="spec-grid">
                    <div class="spec-item">
                        <div class="spec-label">RAM</div>
                        <div class="spec-value">${product.spec_ranges.ram}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Storage</div>
                        <div class="spec-value">${product.spec_ranges.storage}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Battery</div>
                        <div class="spec-value">${product.spec_ranges.battery}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Display</div>
                        <div class="spec-value">${product.spec_ranges.display}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Charging</div>
                        <div class="spec-value">${product.spec_ranges.charging}</div>
                    </div>
                </div>
                <div class="action-buttons">
                    <button class="btn-small" onclick="viewDetails('${product.product_id}')">View Details</button>
                    <button class="btn-small" onclick="viewReviews('${product.product_id}')">Reviews</button>
                    <button class="btn-small" onclick="findBestPrice('${product.product_id}')">Find Best Price</button>
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

async function viewDetails(productId) {
    const detailsSection = document.getElementById('productDetails');
    const detailsContent = document.getElementById('detailsContent');
    
    detailsSection.style.display = 'block';
    detailsContent.innerHTML = '<div class="loading">Loading details...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/products/${productId}`);
        const data = await response.json();
        
        let html = `
            <h3>${data.product.brand} ${data.product.model_name}</h3>
            <p><strong>Total Variants:</strong> ${data.total_variants}</p>
            <h4>Available Variants:</h4>
            <ul>
        `;
        
        data.variants.forEach(variant => {
            html += `<li>${variant.color} - ${variant.storage_gb}GB</li>`;
        });
        
        html += '</ul>';
        
        const specs = data.product.specs;
        html += `
            <h4>Specifications:</h4>
            <div class="spec-grid">
                <div class="spec-item">
                    <div class="spec-label">OS</div>
                    <div class="spec-value">${specs.os?.value || 'N/A'}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Processor</div>
                    <div class="spec-value">${specs.soc?.value || 'N/A'}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Display</div>
                    <div class="spec-value">${specs.display?.size_in}"  ${specs.display?.tech}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Battery</div>
                    <div class="spec-value">${specs.battery?.capacity_mah}mAh</div>
                </div>
            </div>
        `;
        
        detailsContent.innerHTML = html;
    } catch (error) {
        detailsContent.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

async function viewReviews(productId) {
    const reviewsSection = document.getElementById('reviews');
    const reviewsContent = document.getElementById('reviewsContent');
    
    reviewsSection.style.display = 'block';
    reviewsContent.innerHTML = '<div class="loading">Loading reviews...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/reviews/product/${productId}/summary`);
        const data = await response.json();
        
        let coverageClass = 'coverage-' + data.coverage_level;
        
        let html = `
            <div class="review-summary">
                <h3>${data.model_name}</h3>
                <p>
                    <span class="coverage-indicator ${coverageClass}">
                        Coverage: ${data.coverage_level.toUpperCase()}
                    </span>
                    <strong style="margin-left: 20px;">Average Rating: ${data.average_rating}/10</strong>
                </p>
                <p style="margin: 15px 0;">${data.summary}</p>
        `;
        
        if (data.pro_consensus.length > 0) {
            html += '<h4>Pros:</h4><ul>';
            data.pro_consensus.forEach(pro => {
                html += `<li>${pro}</li>`;
            });
            html += '</ul>';
        }
        
        if (data.con_consensus.length > 0) {
            html += '<h4>Cons:</h4><ul>';
            data.con_consensus.forEach(con => {
                html += `<li>${con}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div>';
        reviewsContent.innerHTML = html;
    } catch (error) {
        reviewsContent.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

async function findBestPrice(productId) {
    const offersSection = document.getElementById('offers');
    const offersContent = document.getElementById('offersContent');
    
    offersSection.style.display = 'block';
    offersContent.innerHTML = '<div class="loading">Finding best prices...</div>';
    
    try {
        const productResponse = await fetch(`${API_BASE}/products/${productId}`);
        const productData = await productResponse.json();
        
        const firstVariant = productData.variants[0];
        
        const offersResponse = await fetch(`${API_BASE}/offers/variant/${firstVariant._id}?country=US`);
        const offersData = await offersResponse.json();
        
        let html = `<h3>Prices for ${productData.product.brand} ${productData.product.model_name}</h3>`;
        html += `<p>Variant: ${firstVariant.color} - ${firstVariant.storage_gb}GB</p>`;
        
        if (offersData.best_new) {
            html += `
                <div class="offer-card">
                    <div class="retailer-name">
                        Best New Price: ${offersData.best_new.retailer.toUpperCase()}
                        <span class="condition new">NEW</span>
                    </div>
                    <div class="offer-price">$${offersData.best_new.price_amount}</div>
                    ${offersData.best_new.discount_pct ? `<p>Discount: ${offersData.best_new.discount_pct}% off</p>` : ''}
                    ${offersData.best_new.store_name ? `<p>Available for pickup at: ${offersData.best_new.store_name}</p>` : ''}
                </div>
            `;
        }
        
        if (offersData.best_refurbished) {
            html += `
                <div class="offer-card">
                    <div class="retailer-name">
                        Best Refurbished Price: ${offersData.best_refurbished.retailer.toUpperCase()}
                        <span class="condition refurbished">REFURBISHED</span>
                    </div>
                    <div class="offer-price">$${offersData.best_refurbished.price_amount}</div>
                </div>
            `;
        }
        
        html += '<h4>All Offers:</h4>';
        offersData.offers.forEach(offer => {
            html += `
                <div class="offer-card">
                    <strong>${offer.retailer}</strong> - 
                    $${offer.price_amount} 
                    (${offer.condition})
                    ${offer.availability === 'in-stock' ? '✓ In Stock' : ''}
                </div>
            `;
        });
        
        offersContent.innerHTML = html;
    } catch (error) {
        offersContent.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}