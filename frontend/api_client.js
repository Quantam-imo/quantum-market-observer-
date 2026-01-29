/**
 * API Client for v2 endpoints
 * Handles authentication headers and API calls to backend
 */

// Build API base compatible with Codespaces
const proto = window.location.protocol;
const host = window.location.hostname;
let apiHost = host;

const m = host.match(/^(.*)-(\d+)\.app\.github\.dev$/);
if (m) {
    apiHost = `${m[1]}-8000.app.github.dev`;
}
if (host === "localhost" || host === "127.0.0.1") {
    apiHost = `${host}:8000`;
}

const API_BASE = `${proto}//${apiHost}`;

/**
 * Get user context from localStorage or defaults
 */
function getUserContext() {
    return {
        tier: localStorage.getItem('user_tier') || 'BASIC',
        phase: localStorage.getItem('user_phase') || 'BEGINNER'
    };
}

/**
 * Set user context in localStorage
 */
function setUserContext(tier, phase) {
    localStorage.setItem('user_tier', tier);
    localStorage.setItem('user_phase', phase);
}

/**
 * Make authenticated API request to v2 endpoints
 */
async function apiRequest(endpoint, options = {}) {
    const user = getUserContext();
    
    const headers = {
        'Content-Type': 'application/json',
        'X-User-Tier': user.tier,
        'X-User-Phase': user.phase,
        ...options.headers
    };
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * API Methods
 */
const API = {
    // Health check
    async health() {
        return await apiRequest('/api/v2/health');
    },
    
    // User profile
    async whoami() {
        return await apiRequest('/api/v2/whoami');
    },
    
    // Mentor signal
    async getMentorSignal() {
        return await apiRequest('/api/v2/mentor/signal');
    },
    
    // Dashboard data
    async getDashboard() {
        return await apiRequest('/api/v2/dashboard');
    },
    
    // Chart overlays
    async getChartOverlays() {
        return await apiRequest('/api/v2/chart/overlays');
    },
    
    // Guards status
    async getGuards() {
        return await apiRequest('/api/v2/guards');
    },
    
    // Log trade
    async logTrade(tradeData) {
        return await apiRequest('/api/v2/trade/log', {
            method: 'POST',
            body: JSON.stringify(tradeData)
        });
    },
    
    // Journal summary
    async getJournalSummary() {
        return await apiRequest('/api/v2/journal/summary');
    },
    
    // Run backtest
    async runBacktest(params) {
        return await apiRequest('/api/v2/backtest/run', {
            method: 'POST',
            body: JSON.stringify(params)
        });
    }
};

// Export for use in other scripts
window.API = API;
window.API_BASE = API_BASE;
window.getUserContext = getUserContext;
window.setUserContext = setUserContext;
