/**
 * MediBuddy - Enterprise Healthcare Agent
 * Frontend Application Logic
 */

// ============================================
// GLOBAL STATE
// ============================================

const state = {
    currentSection: 'dashboard',
    websocket: null,
    wsConnected: false,
    isSidebarCollapsed: false,
    theme: localStorage.getItem('theme') || 'dark', // Re-added localStorage for theme
    userLocation: localStorage.getItem('userLocation') || 'FL', // Default to Florida
    updates: [],
    unreadUpdates: 0,
    drugs: [], // Retained from original
    payers: [], // Retained from original
    chatHistory: [], // Retained from original
};

// ============================================
// API CLIENT
// ============================================

const API = {
    baseUrl: '',

    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`API GET ${endpoint} failed:`, error);
            throw error;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`API POST ${endpoint} failed:`, error);
            throw error;
        }
    }
};

// ============================================
// WEBSOCKET - REAL-TIME UPDATES
// ============================================

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    state.websocket = new WebSocket(wsUrl);

    state.websocket.onopen = () => {
        console.log('[WS] Connected to MediBuddy Real-Time Engine');
        state.wsConnected = true;
        updateSystemStatus(true);
    };

    state.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    state.websocket.onclose = () => {
        console.log('[WS] Disconnected, reconnecting in 3s...');
        state.wsConnected = false;
        updateSystemStatus(false);
        setTimeout(connectWebSocket, 3000);
    };

    state.websocket.onerror = (error) => {
        console.error('[WS] Error:', error);
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'connected':
            addUpdateToFeed({
                icon: '✓',
                type: 'success',
                text: data.message,
                time: 'Just now'
            });
            break;

        case 'pharma_update':
            state.unreadUpdates++; // Changed from updateCount
            updateUpdatesIndicator();

            // Show toast notification for important updates
            if (data.data.importance >= 7) {
                showToast({
                    title: 'Real-Time Update',
                    message: `${data.data.entity_id}: ${data.data.field} changed`,
                    icon: getImportanceIcon(data.data.importance)
                });
            }

            // Add to feed
            addUpdateToFeed({
                icon: getImportanceIcon(data.data.importance),
                type: getImportanceType(data.data.importance),
                text: `${data.data.entity_id.split(':')[0]}: ${data.data.field} updated`,
                time: new Date().toLocaleTimeString()
            });
            break;

        case 'chat_response':
            addChatMessage('assistant', data.response);
            break;

        case 'price_update':
            // Update pricing UI if the drug is being viewed
            handleRealTimePriceUpdate(data.data);
            break;
    }
}

function handleRealTimePriceUpdate(data) {
    // If we're in the pricing section and searching for this drug
    const pricingInput = document.getElementById('pricing-search-input');
    const currentQuery = pricingInput?.value?.toLowerCase();

    if (state.currentSection === 'pricing' && currentQuery &&
        (data.entity_id.toLowerCase().includes(currentQuery) ||
            currentQuery.includes(data.entity_id.toLowerCase()))) {

        // Refresh the pricing search
        searchPricing(pricingInput.value);

        showToast({
            title: 'Live Price Update',
            message: `${data.entity_id}: ${data.field} is now $${data.value}`,
            icon: '💰'
        });
    }
}

function getImportanceIcon(importance) {
    if (importance >= 9) return '🚨';
    if (importance >= 7) return '⚠️';
    if (importance >= 5) return '📢';
    return '📌';
}

function getImportanceType(importance) {
    if (importance >= 9) return 'danger';
    if (importance >= 7) return 'warning';
    return 'info';
}

// ============================================
// NAVIGATION
// ============================================

function initNavigation() {
    // Sidebar navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            if (section) navigateToSection(section);
        });
    });

    // Quick actions
    document.querySelectorAll('.quick-action').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            handleQuickAction(action);
        });
    });

    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.section) {
            navigateToSection(e.state.section, false);
        }
    });

    // Load initial section from URL hash
    const hash = window.location.hash.slice(1);
    if (hash && document.getElementById(hash)) {
        navigateToSection(hash, false);
    }
}

function navigateToSection(sectionId, pushState = true) {
    // Update state
    state.currentSection = sectionId;

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });

    // Show/hide sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.toggle('active', section.id === sectionId);
    });

    // Update breadcrumb
    const breadcrumb = document.getElementById('breadcrumb');
    if (breadcrumb) {
        const sectionNames = {
            'dashboard': 'Dashboard',
            'drug-lookup': 'Drug Lookup',
            'pricing': 'Pricing Intelligence',
            'coverage': 'Payer Coverage',
            'prior-auth': 'Prior Authorization',
            'interactions': 'Drug Interactions',
            'specialty': 'Specialty Pharmacy',
            'chat': 'AI Chat'
        };
        breadcrumb.innerHTML = `
            <span class="breadcrumb-item">MediBuddy</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item active">${sectionNames[sectionId] || sectionId}</span>
        `;
    }

    // Push to history
    if (pushState) {
        history.pushState({ section: sectionId }, '', `#${sectionId}`);
    }
    refreshSectionContent(); // Refresh content when navigating
}

function handleQuickAction(action) {
    switch (action) {
        case 'drug-search':
            navigateToSection('drug-lookup');
            document.getElementById('drug-search-input')?.focus();
            break;
        case 'check-coverage':
            navigateToSection('coverage');
            document.getElementById('coverage-drug-input')?.focus();
            break;
        case 'interactions':
            navigateToSection('interactions');
            document.getElementById('interactions-input')?.focus();
            break;
        case 'prior-auth':
            navigateToSection('prior-auth');
            document.getElementById('pa-drug-input')?.focus();
            break;
        case 'pricing':
            navigateToSection('pricing');
            document.getElementById('pricing-search-input')?.focus();
            break;
        case 'chat':
            navigateToSection('chat');
            document.getElementById('chat-input')?.focus();
            break;
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar?.classList.toggle('collapsed');
    state.isSidebarCollapsed = sidebar?.classList.contains('collapsed');
}

// ============================================
// COMMAND PALETTE
// ============================================

function initCommandPalette() {
    const palette = document.getElementById('command-palette');
    const input = document.getElementById('command-input');
    const cmdKBtn = document.getElementById('cmd-k-btn');

    // Open with Ctrl+K
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openCommandPalette();
        }

        if (e.key === 'Escape') {
            closeCommandPalette();
        }

        // Quick navigation shortcuts
        if (!e.ctrlKey && !e.metaKey && !e.altKey) {
            if (document.activeElement.tagName !== 'INPUT' &&
                document.activeElement.tagName !== 'TEXTAREA') {
                switch (e.key.toLowerCase()) {
                    case 'd': navigateToSection('dashboard'); break;
                    case 's': navigateToSection('drug-lookup'); break;
                    case 'c': navigateToSection('coverage'); break;
                    case 'i': navigateToSection('interactions'); break;
                    case 'a': navigateToSection('chat'); break;
                    case '[': toggleSidebar(); break;
                }
            }
        }
    });

    cmdKBtn?.addEventListener('click', openCommandPalette);

    // Close on backdrop click
    document.querySelector('.command-palette-backdrop')?.addEventListener('click', closeCommandPalette);

    // Command items
    document.querySelectorAll('.command-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            closeCommandPalette();
            handleQuickAction(action);
        });
    });

    // Search functionality
    input?.addEventListener('input', (e) => {
        searchCommandPalette(e.target.value);
    });
}

function openCommandPalette() {
    const palette = document.getElementById('command-palette');
    palette?.classList.remove('hidden');
    document.getElementById('command-input')?.focus();
}

function closeCommandPalette() {
    const palette = document.getElementById('command-palette');
    palette?.classList.add('hidden');
    document.getElementById('command-input').value = '';
}

async function searchCommandPalette(query) {
    const resultsContainer = document.getElementById('command-results');
    if (!query) {
        // Show default quick actions
        resultsContainer.innerHTML = `
            <div class="command-section">
                <div class="command-section-title">Quick Actions</div>
                <div class="command-item" data-action="drug-search">
                    <span class="command-item-icon">💊</span>
                    <span>Search Drugs</span>
                    <kbd>S</kbd>
                </div>
                <div class="command-item" data-action="check-coverage">
                    <span class="command-item-icon">🏥</span>
                    <span>Check Coverage</span>
                    <kbd>C</kbd>
                </div>
                <div class="command-item" data-action="interactions">
                    <span class="command-item-icon">⚠️</span>
                    <span>Drug Interactions</span>
                    <kbd>I</kbd>
                </div>
                <div class="command-item" data-action="chat">
                    <span class="command-item-icon">🤖</span>
                    <span>AI Chat</span>
                    <kbd>A</kbd>
                </div>
            </div>
        `;
        return;
    }

    // Search drugs
    try {
        const drugs = await API.get(`/api/drugs?search=${encodeURIComponent(query)}&limit=5`);
        let html = '';

        if (drugs.length > 0) {
            html += `<div class="command-section">
                <div class="command-section-title">Drugs</div>
                ${drugs.map(d => `
                    <div class="command-item" data-drug="${d.id}">
                        <span class="command-item-icon">💊</span>
                        <span>${d.brand_name} (${d.generic_name})</span>
                    </div>
                `).join('')}
            </div>`;
        }

        resultsContainer.innerHTML = html || '<div class="command-section"><div class="command-section-title">No results found</div></div>';

        // Add click handlers
        resultsContainer.querySelectorAll('.command-item[data-drug]').forEach(item => {
            item.addEventListener('click', () => {
                closeCommandPalette();
                navigateToSection('drug-lookup');
                document.getElementById('drug-search-input').value = item.dataset.drug;
                searchDrugs(item.dataset.drug);
            });
        });
    } catch (error) {
        console.error('Command search failed:', error);
    }
}

// ============================================
// THEME
// ============================================

function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);

    const themeToggle = document.getElementById('theme-toggle');
    themeToggle?.addEventListener('click', () => {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', state.theme);
        localStorage.setItem('theme', state.theme);
    });
}

// ============================================
// DRUG LOOKUP
// ============================================

function initDrugLookup() {
    const searchInput = document.getElementById('drug-search-input');

    let debounceTimer;
    searchInput?.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchDrugs(e.target.value);
        }, 300);
    });
}

async function searchDrugs(query) {
    const resultsContainer = document.getElementById('drug-results');

    if (!query || query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    try {
        const drugs = await API.get(`/api/drugs?search=${encodeURIComponent(query)}`);

        resultsContainer.innerHTML = drugs.map(drug => `
            <div class="drug-card" data-drug-id="${drug.id}">
                <div class="drug-card-header">
                    <div>
                        <div class="drug-card-title">${drug.brand_name}</div>
                        <div class="drug-card-generic">${drug.generic_name}</div>
                    </div>
                    <div class="drug-card-badges">
                        ${drug.has_black_box ? '<span class="badge danger">Black Box</span>' : ''}
                        ${drug.schedule !== 'None' ? `<span class="badge schedule">${drug.schedule}</span>` : ''}
                    </div>
                </div>
                <div class="drug-card-info">
                    <span>📦 ${drug.drug_class}</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        resultsContainer.querySelectorAll('.drug-card').forEach(card => {
            card.addEventListener('click', () => {
                loadDrugDetails(card.dataset.drugId);
            });
        });
    } catch (error) {
        resultsContainer.innerHTML = '<p>Error loading drugs</p>';
    }
}

async function loadDrugDetails(drugId) {
    try {
        const data = await API.get(`/api/drugs/${drugId}`);
        const drug = data.drug;
        const panel = document.getElementById('drug-detail-panel');

        panel.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>${drug.brand_name} (${drug.generic_name})</h3>
                    <button class="btn" onclick="document.getElementById('drug-detail-panel').classList.add('hidden')">✕ Close</button>
                </div>
                <div class="card-body">
                    <div class="drug-detail-grid">
                        <div class="drug-detail-section">
                            <h4>Identifiers</h4>
                            <p><strong>NDC:</strong> ${drug.identifiers.ndc}</p>
                            <p><strong>GPI:</strong> ${drug.identifiers.gpi}</p>
                            <p><strong>AHFS:</strong> ${drug.identifiers.ahfs}</p>
                        </div>
                        <div class="drug-detail-section">
                            <h4>Safety</h4>
                            <p><strong>Schedule:</strong> ${drug.schedule}</p>
                            <p><strong>Pregnancy:</strong> ${drug.pregnancy_category}</p>
                            <p><strong>REMS:</strong> ${drug.rems_required ? 'Yes' : 'No'}</p>
                        </div>
                    </div>
                    ${drug.warnings.length > 0 ? `
                        <div class="drug-warnings">
                            <h4>⚠️ Warnings</h4>
                            ${drug.warnings.map(w => `
                                <div class="warning-item ${w.type === 'Black Box' ? 'danger' : ''}">
                                    <strong>[${w.type}] ${w.title}</strong>
                                    <p>${w.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    <div class="drug-indications">
                        <h4>Indications</h4>
                        <ul>
                            ${drug.indications.map(ind => `
                                <li>${ind.condition} ${ind.fda_approved ? '✓' : '(Off-label)'}</li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;

        panel.classList.remove('hidden');
    } catch (error) {
        console.error('Failed to load drug details:', error);
    }
}

// ============================================
// PRICING
// ============================================

function initPricing() {
    const searchInput = document.getElementById('pricing-search-input');
    const searchBtn = document.getElementById('pricing-search-btn');
    const locationSelect = document.getElementById('pricing-location-select');

    // Sync with global location
    if (locationSelect) {
        locationSelect.value = state.userLocation;
    }

    let debounceTimer;
    searchInput?.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchPricing(e.target.value);
        }, 500);
    });

    searchBtn?.addEventListener('click', () => {
        searchPricing(searchInput.value);
    });

    locationSelect?.addEventListener('change', () => {
        if (searchInput.value) searchPricing(searchInput.value);
    });

    // Enter key support
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchPricing(searchInput.value);
    });
}

async function searchPricing(query) {
    const resultsContainer = document.getElementById('pricing-results');
    const location = document.getElementById('pricing-location-select')?.value || state.userLocation; // Use global state if local not set

    if (!query || query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    try {
        // First, search for drugs to find the correct ID
        const drugs = await API.get(`/api/drugs?search=${encodeURIComponent(query)}&limit=5`);

        if (drugs.length === 0) {
            resultsContainer.innerHTML = `<p class="error">No drugs found matching "${query}"</p>`;
            return;
        }

        let html = '';
        for (const drug of drugs) {
            try {
                const url = `/api/drugs/${drug.id}/pricing${location ? `?location=${location}` : ''}`;
                const data = await API.get(url);
                const p = data.pricing;
                const symbol = p.location_adjustment?.symbol || '$';
                const formatPrice = (price) => price ? `${symbol}${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : 'N/A';

                const locationBadge = data.location ? `
                    <div style="font-size: 11px; background: rgba(0, 217, 255, 0.1); color: var(--accent-primary); padding: 4px 10px; border-radius: 100px; display: inline-flex; align-items: center; gap: 4px; margin-top: 8px;">
                        📍 ${p.location_adjustment?.name || data.location} (${p.location_adjustment?.currency || 'USD'})
                    </div>
                ` : '';

                html += `
                    <div class="card pricing-card" data-drug-id="${drug.id}" style="margin-bottom: 24px;">
                        <div class="card-header">
                            <div>
                                <h3 style="margin: 0;">💰 ${data.drug_name} (${data.generic_name})</h3>
                                ${locationBadge}
                            </div>
                            <span class="card-badge">Live Market Data</span>
                        </div>
                        <div class="card-body">
                            <div class="pricing-grid">
                                <div class="pricing-item">
                                    <div class="pricing-label">AWP</div>
                                    <div class="pricing-value">${formatPrice(p.awp)}</div>
                                    <div class="pricing-desc">Average Wholesale Price</div>
                                </div>
                                <div class="pricing-item">
                                    <div class="pricing-label">WAC</div>
                                    <div class="pricing-value">${formatPrice(p.wac)}</div>
                                    <div class="pricing-desc">Wholesale Acquisition Cost</div>
                                </div>
                                <div class="pricing-item">
                                    <div class="pricing-label">NADAC</div>
                                    <div class="pricing-value">${formatPrice(p.nadac)}</div>
                                    <div class="pricing-desc">National Average acquisition</div>
                                </div>
                                <div class="pricing-item">
                                    <div class="pricing-label">340B</div>
                                    <div class="pricing-value">${formatPrice(p.price_340b)}</div>
                                    <div class="pricing-desc">340B Ceiling Price</div>
                                </div>
                                <div class="pricing-item highlight">
                                    <div class="pricing-label">GoodRx Low</div>
                                    <div class="pricing-value">${formatPrice(p.goodrx_low)}</div>
                                    <div class="pricing-desc">Best Cash Price</div>
                                </div>
                                <div class="pricing-item highlight">
                                    <div class="pricing-label">Cost Plus</div>
                                    <div class="pricing-value">${formatPrice(p.costplus_price)}</div>
                                    <div class="pricing-desc">Mark Cuban Cost Plus</div>
                                </div>
                            </div>
                            ${p.awp && p.goodrx_low ? `
                                <div class="savings-callout">
                                    💰 <strong>Potential Savings:</strong> Up to ${Math.round(((p.awp - p.goodrx_low) / p.awp) * 100)}% off AWP with cash pay options
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            } catch (innerError) {
                console.warn(`Failed to load pricing for ${drug.id}`, innerError);
            }
        }

        resultsContainer.innerHTML = html || '<p class="error">Pricing data unavailable</p>';
    } catch (error) {
        console.error('Pricing search failed:', error);
        resultsContainer.innerHTML = '<p class="error">Error loading pricing information</p>';
    }
}

// ============================================
// COVERAGE
// ============================================

function initCoverage() {
    const searchBtn = document.getElementById('coverage-search-btn');
    searchBtn?.addEventListener('click', searchCoverage);

    // Enter key support
    ['coverage-drug-input', 'coverage-payer-input'].forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchCoverage();
        });
    });
}

async function searchCoverage() {
    const drugInput = document.getElementById('coverage-drug-input');
    const payerInput = document.getElementById('coverage-payer-input');
    const resultsContainer = document.getElementById('coverage-results');

    const drugName = drugInput?.value?.trim();
    if (!drugName) {
        resultsContainer.innerHTML = '<p>Please enter a drug name</p>';
        return;
    }

    try {
        let url = `/api/coverage/${encodeURIComponent(drugName)}`;
        const payerName = payerInput?.value?.trim();
        if (payerName) {
            url += `?payer=${encodeURIComponent(payerName)}`;
        }
        // Add location to coverage search
        url += `${payerName ? '&' : '?'}location=${encodeURIComponent(state.userLocation)}`;


        const coverages = await API.get(url);

        const tierNames = {
            0: 'Tier 0 (Preferred Generic)',
            1: 'Tier 1 (Generic)',
            2: 'Tier 2 (Preferred Brand)',
            3: 'Tier 3 (Non-Preferred)',
            4: 'Tier 4 (Specialty)',
            5: 'Tier 5 (Specialty High)',
            6: 'Not Covered'
        };

        resultsContainer.innerHTML = coverages.map(item => `
            <div class="coverage-card">
                <div class="coverage-card-header">
                    <div>
                        <div class="coverage-payer-name">${item.payer.name}</div>
                        <div class="coverage-plan-name">${item.payer.plan_name}</div>
                    </div>
                    <span class="coverage-tier tier-${item.coverage.tier}">${tierNames[item.coverage.tier]}</span>
                </div>
                <div class="coverage-card-body">
                    <div class="coverage-detail">
                        <div class="coverage-detail-label">Copay</div>
                        <div class="coverage-detail-value">${item.coverage.copay !== null ? `$${item.coverage.copay}` : 'N/A'}</div>
                    </div>
                    <div class="coverage-detail">
                        <div class="coverage-detail-label">Coinsurance</div>
                        <div class="coverage-detail-value">${item.coverage.coinsurance !== null ? `${item.coverage.coinsurance}%` : 'N/A'}</div>
                    </div>
                    <div class="coverage-detail">
                        <div class="coverage-detail-label">Prior Auth</div>
                        <div class="coverage-detail-value ${item.coverage.prior_auth_required ? 'pa-required' : 'no-pa'}">
                            ${item.coverage.prior_auth_required ? '⚠️ Required' : '✓ Not Required'}
                        </div>
                    </div>
                    <div class="coverage-detail">
                        <div class="coverage-detail-label">Step Therapy</div>
                        <div class="coverage-detail-value">${item.coverage.step_therapy_required ? 'Required' : 'No'}</div>
                    </div>
                    ${item.coverage.quantity_limit ? `
                        <div class="coverage-detail">
                            <div class="coverage-detail-label">Quantity Limit</div>
                            <div class="coverage-detail-value">${item.coverage.quantity_limit}</div>
                        </div>
                    ` : ''}
                    ${item.coverage.pa_criteria ? `
                        <div class="coverage-detail" style="grid-column: span 2;">
                            <div class="coverage-detail-label">PA Criteria</div>
                            <div class="coverage-detail-value">${item.coverage.pa_criteria}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        resultsContainer.innerHTML = '<p class="error">No coverage found</p>';
    }
}

// ============================================
// DRUG INTERACTIONS
// ============================================

function initInteractions() {
    const checkBtn = document.getElementById('check-interactions-btn');
    checkBtn?.addEventListener('click', checkInteractions);

    const input = document.getElementById('interactions-input');
    input?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') checkInteractions();
    });
}

async function checkInteractions() {
    const input = document.getElementById('interactions-input');
    const resultsContainer = document.getElementById('interactions-results');
    const chipsContainer = document.getElementById('interaction-chips');

    const drugsStr = input?.value?.trim();
    if (!drugsStr) {
        resultsContainer.innerHTML = '<p>Please enter at least 2 drugs</p>';
        return;
    }

    const drugs = drugsStr.split(',').map(d => d.trim()).filter(d => d);

    if (drugs.length < 2) {
        resultsContainer.innerHTML = '<p>Please enter at least 2 drugs (comma-separated)</p>';
        return;
    }

    // Show chips
    chipsContainer.innerHTML = drugs.map(d => `
        <span class="drug-chip">💊 ${d}</span>
    `).join('');

    try {
        const data = await API.post('/api/interactions/check', { drugs });

        if (data.interactions.length === 0) {
            resultsContainer.innerHTML = `
                <div class="card" style="background: rgba(16, 185, 129, 0.1); border-color: var(--success);">
                    <div class="card-body">
                        <h3 style="color: var(--success);">✅ No Significant Interactions Found</h3>
                        <p>No major drug-drug interactions detected between: ${drugs.join(', ')}</p>
                    </div>
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = `
            <div style="margin-bottom: 16px;">
                <h3>${data.has_major_interaction ? '🔴 Major Interactions Detected!' : '⚠️ Interactions Found'}</h3>
                <p>${data.summary}</p>
            </div>
            ${data.interactions.map(i => `
                <div class="interaction-card ${i.severity.toLowerCase()}">
                    <div class="interaction-header">
                        <div class="interaction-drugs">${i.drug_a} + ${i.drug_b}</div>
                        <span class="interaction-severity ${i.severity.toLowerCase()}">${i.severity}</span>
                    </div>
                    <div class="interaction-body">
                        <p><strong>Clinical Effect:</strong> ${i.clinical_effect}</p>
                        <p><strong>Management:</strong> ${i.management}</p>
                    </div>
                </div>
            `).join('')}
        `;
    } catch (error) {
        resultsContainer.innerHTML = '<p class="error">Error checking interactions</p>';
    }
}

// ============================================
// PRIOR AUTHORIZATION
// ============================================

function initPriorAuth() {
    const generateBtn = document.getElementById('generate-pa-btn');
    generateBtn?.addEventListener('click', generatePA);
}

async function generatePA() {
    const drugInput = document.getElementById('pa-drug-input');
    const payerInput = document.getElementById('pa-payer-input');
    const diagnosisInput = document.getElementById('pa-diagnosis-input');
    const resultContainer = document.getElementById('pa-result');

    const drug = drugInput?.value?.trim();
    const payer = payerInput?.value?.trim();
    const diagnosis = diagnosisInput?.value?.trim();

    if (!drug || !payer || !diagnosis) {
        alert('Please fill in all fields');
        return;
    }

    try {
        const data = await API.post('/api/prior-auth/generate', {
            drug_name: drug,
            payer_name: payer,
            diagnosis: diagnosis,
            location: state.userLocation // Add location to PA request
        });

        resultContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>📋 Generated PA Form</h3>
                    <span class="card-badge">Auto-Generated</span>
                </div>
                <div class="card-body">
                    <div class="pa-content">${formatMarkdown(data.form)}</div>
                    <div style="margin-top: 20px; display: flex; gap: 12px;">
                        <button class="btn primary" onclick="navigator.clipboard.writeText(document.querySelector('.pa-content').innerText)">📋 Copy to Clipboard</button>
                        <button class="btn" onclick="window.print()">🖨️ Print</button>
                    </div>
                </div>
            </div>
        `;

        resultContainer.classList.remove('hidden');
    } catch (error) {
        alert('Failed to generate PA form');
    }
}

// ============================================
// SPECIALTY PHARMACY
// ============================================

function initSpecialty() {
    const searchInput = document.getElementById('specialty-search-input');
    const searchBtn = document.getElementById('specialty-search-btn');

    let debounceTimer;
    searchInput?.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchSpecialty(e.target.value);
        }, 500);
    });

    searchBtn?.addEventListener('click', () => {
        searchSpecialty(searchInput.value);
    });
}

async function searchSpecialty(query) {
    const resultsContainer = document.getElementById('specialty-results');

    if (!query || query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    try {
        // First, search for drug
        const drug = await API.get(`/api/drugs/${encodeURIComponent(query)}`);

        // Find pharmacies for this drug
        const pharmacies = await API.get('/api/status').then(r => {
            // In production we'd have a dedicated endpoint, 
            // for now we'll simulate finding pharmacies that cover this drug
            return [
                { name: "CVS Specialty", phone: "1-800-237-2767", notes: "Authorized distributor for this medication." },
                { name: "Accredo", phone: "1-800-803-2523", notes: "Requires prior authorization before shipping." }
            ];
        });

        resultsContainer.innerHTML = `
            <div class="card" style="margin-bottom: 24px;">
                <div class="card-header">
                    <h3>🏪 Specialty Care: ${drug.drug.brand_name}</h3>
                </div>
                <div class="card-body">
                    <p style="margin-bottom: 16px; color: var(--text-secondary);">
                        The following specialty pharmacies are authorized to dispense ${drug.drug.brand_name}. 
                        Coordination of benefits and prior authorization are required.
                    </p>
                    <div class="specialty-grid">
                        ${pharmacies.map(p => `
                            <div class="specialty-item" style="background: var(--bg-tertiary); padding: 16px; border-radius: var(--radius-md); margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div>
                                        <div style="font-weight: 600; font-size: 16px;">${p.name}</div>
                                        <div style="color: var(--accent-primary); font-size: 14px; margin-top: 4px;">📞 ${p.phone}</div>
                                    </div>
                                    <button class="btn secondary sm" onclick="window.location.href='tel:${p.phone}'">Call</button>
                                </div>
                                <div style="font-size: 13px; color: var(--text-tertiary); margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color);">
                                    ${p.notes}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        resultsContainer.innerHTML = '<p class="error">No specialty pharmacy data found for this medication</p>';
    }
}

function formatMarkdown(text) {
    // Basic markdown formatting
    return text
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^- (.*$)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        .replace(/\n/g, '<br>');
}

// ============================================
// CHAT
// ============================================

function initChat() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');

    sendBtn?.addEventListener('click', sendChatMessage);

    input?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Auto-resize textarea
    input?.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    });

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.textContent;
            sendChatMessage();
        });
    });
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value?.trim();

    if (!message) return;

    // Add user message
    addChatMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Hide suggestions after first message
    document.getElementById('chat-suggestions')?.remove();

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        // Send via WebSocket if connected, otherwise use REST
        if (state.wsConnected && state.websocket?.readyState === WebSocket.OPEN) {
            state.websocket.send(JSON.stringify({
                type: 'chat',
                message: message,
                location: state.userLocation // Add location to chat message
            }));
        } else {
            const response = await API.post('/api/chat', { message, location: state.userLocation });
            removeTypingIndicator(typingId);
            addChatMessage('assistant', response.response);
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addChatMessage('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
    }
}

function addChatMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // Remove typing indicator if this is an assistant response
    document.querySelector('.message.typing')?.remove();

    messageDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">
            <div class="message-text">${formatChatContent(content)}</div>
        </div>
    `;

    container?.appendChild(messageDiv);
    container?.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

function formatChatContent(content) {
    // Format markdown-like content
    return content
        .replace(/^# (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h4>$1</h4>')
        .replace(/^### (.*$)/gm, '<h5>$1</h5>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^- (.*$)/gm, '• $1')
        .replace(/\n/g, '<br>');
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing';
    typingDiv.id = id;
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-text">
                <span class="typing-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        </div>
    `;

    container?.appendChild(typingDiv);
    container?.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });

    return id;
}

function removeTypingIndicator(id) {
    document.getElementById(id)?.remove();
}

// ============================================
// UPDATES FEED
// ============================================

function addUpdateToFeed(update) {
    const feed = document.getElementById('updates-feed');
    if (!feed) return;

    const item = document.createElement('div');
    item.className = 'update-item';
    item.innerHTML = `
        <div class="update-icon ${update.type}">${update.icon}</div>
        <div class="update-content">
            <div class="update-text">${update.text}</div>
            <div class="update-time">${update.time}</div>
        </div>
    `;

    feed.insertBefore(item, feed.firstChild);

    // Keep only last 20 updates
    while (feed.children.length > 20) {
        feed.removeChild(feed.lastChild);
    }
}

function updateUpdatesIndicator() {
    const countEl = document.querySelector('.updates-count');
    if (countEl) {
        countEl.textContent = state.unreadUpdates; // Changed from updateCount
    }
}

// ============================================
// SYSTEM STATUS
// ============================================

function updateSystemStatus(online) {
    const statusDot = document.querySelector('.system-status .status-dot');
    const statusText = document.getElementById('sidebar-region-text');

    if (statusDot) {
        statusDot.classList.toggle('online', online);
    }
    if (statusText) {
        if (online) {
            statusText.textContent = `Region: ${state.userLocation}`;
        } else {
            statusText.textContent = 'Reconnecting...';
        }
    }
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast({ title, message, icon = '📢', duration = 5000 }) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, duration);
}

// ============================================
// LOAD INITIAL DATA
// ============================================

async function loadInitialData() {
    try {
        // Load popular drugs for dashboard
        const drugs = await API.get('/api/drugs?limit=5');
        const drugsList = document.getElementById('popular-drugs');

        if (drugsList) {
            drugsList.innerHTML = drugs.map(d => `
                <div class="drug-list-item" data-drug="${d.id}">
                    <div class="drug-info">
                        <span class="drug-name">${d.brand_name}</span>
                        <span class="drug-generic">${d.generic_name}</span>
                    </div>
                    <span class="drug-class-badge">${d.drug_class}</span>
                </div>
            `).join('');

            drugsList.querySelectorAll('.drug-list-item').forEach(item => {
                item.addEventListener('click', () => {
                    navigateToSection('drug-lookup');
                    document.getElementById('drug-search-input').value = item.dataset.drug;
                    searchDrugs(item.dataset.drug);
                });
            });
        }

        // Update stats
        const status = await API.get('/api/status');
        document.getElementById('stat-drugs').textContent = status.database.drugs + '+';

    } catch (error) {
        console.error('Failed to load initial data:', error);
    }
}

// ============================================
// DASHBOARD
// ============================================
function initDashboard() {
    // This function can be expanded to load dashboard-specific data
    // based on the current state.userLocation if needed.
    loadInitialData(); // Re-load popular drugs, etc.
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🏥 MediBuddy Initializing...');

    function initApp() {
        // Global Location Handling
        const globalLocationSelect = document.getElementById('global-location-select');
        if (globalLocationSelect) {
            globalLocationSelect.value = state.userLocation;
            globalLocationSelect.addEventListener('change', (e) => {
                updateGlobalLocation(e.target.value);
            });
        }

        // Initialize modules
        initTheme();
        initNavigation(); // Renamed from initNavigafunction
        initCommandPalette();
        initDrugLookup();
        initPricing();
        initCoverage();
        initInteractions();
        initPriorAuth();
        initSpecialty();
        initChat();
        initDashboard(); // Ensure dashboard is updated for location

        // Connect WebSocket
        connectWebSocket();

        // Initial data load
        refreshData(); // This function was not defined, assuming it's meant to be loadInitialData() or a new function.
        // For now, I'll call loadInitialData() and define refreshData() to call it.
    }

    function updateGlobalLocation(location) {
        state.userLocation = location;
        localStorage.setItem('userLocation', location);

        // Sync local selectors if they exist
        const pricingLoc = document.getElementById('pricing-location-select');
        if (pricingLoc) pricingLoc.value = location;

        // Notify user of personalization
        showToast({
            title: 'Region Updated',
            message: `MediBuddy content is now personalized for ${location}`,
            icon: '🌍'
        });

        // Refresh content for current section
        refreshSectionContent();
    }

    function refreshSectionContent() {
        switch (state.currentSection) {
            case 'dashboard':
                initDashboard();
                break;
            case 'pricing':
                const pricingInput = document.getElementById('pricing-search-input');
                if (pricingInput.value) searchPricing(pricingInput.value);
                break;
            case 'coverage':
                const coverageDrugInput = document.getElementById('coverage-drug-input'); // Corrected ID
                if (coverageDrugInput && coverageDrugInput.value) searchCoverage(); // Call searchCoverage directly
                break;
            case 'drug-lookup': // Corrected from 'lookup'
                // Search again if query exists
                const drugLookupInput = document.getElementById('drug-search-input');
                if (drugLookupInput && drugLookupInput.value) searchDrugs(drugLookupInput.value);
                break;
            case 'specialty':
                const specialtyInput = document.getElementById('specialty-search-input');
                if (specialtyInput && specialtyInput.value) searchSpecialty(specialtyInput.value);
                break;
            case 'prior-auth':
                // No automatic refresh needed for PA as it's form-driven
                break;
            case 'interactions':
                // No automatic refresh needed for interactions as it's form-driven
                break;
            case 'chat':
                // No automatic refresh needed for chat
                break;
        }
    }

    // Define refreshData if it's a new function, otherwise call loadInitialData directly
    function refreshData() {
        loadInitialData();
    }

    initApp(); // Call the new initApp function

    console.log('✅ MediBuddy Ready!');
});

// Add CSS for pricing and some missing styles
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    .pricing-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
    }
    
    .pricing-item {
        background: var(--bg-tertiary);
        padding: 16px;
        border-radius: var(--radius-md);
        text-align: center;
    }
    
    .pricing-item.highlight {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success);
    }
    
    .pricing-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-tertiary);
        margin-bottom: 8px;
    }
    
    .pricing-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .pricing-desc {
        font-size: 11px;
        color: var(--text-tertiary);
        margin-top: 4px;
    }
    
    .savings-callout {
        margin-top: 20px;
        padding: 16px;
        background: rgba(16, 185, 129, 0.1);
        border-radius: var(--radius-md);
        color: var(--success);
    }
    
    .coverage-plan-name {
        font-size: 13px;
        color: var(--text-secondary);
    }
    
    .error {
        color: var(--danger);
        padding: 20px;
        text-align: center;
    }
    
    .drug-detail-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .drug-detail-section h4 {
        margin-bottom: 12px;
        color: var(--accent-primary);
    }
    
    .drug-detail-section p {
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .drug-warnings {
        background: rgba(239, 68, 68, 0.1);
        padding: 16px;
        border-radius: var(--radius-md);
        margin-bottom: 20px;
    }
    
    .drug-warnings h4 {
        margin-bottom: 12px;
    }
    
    .warning-item {
        padding: 12px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: var(--radius-sm);
        margin-bottom: 8px;
    }
    
    .warning-item.danger {
        border-left: 3px solid var(--danger);
    }
    
    .warning-item p {
        margin-top: 8px;
        font-size: 13px;
        color: var(--text-secondary);
    }
    
    .drug-indications h4 {
        margin-bottom: 12px;
    }
    
    .drug-indications ul {
        margin-left: 20px;
    }
    
    .drug-indications li {
        margin-bottom: 6px;
    }
    
    .typing-dots span {
        animation: blink 1.4s infinite both;
        font-size: 24px;
    }
    
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes blink {
        0%, 20% { opacity: 0.2; }
        50% { opacity: 1; }
        80%, 100% { opacity: 0.2; }
    }
`;
document.head.appendChild(additionalStyles);

// Re-expose updateGlobalLocation to window for index.html access if needed
window.updateGlobalLocation = updateGlobalLocation;
window.refreshSectionContent = refreshSectionContent;
