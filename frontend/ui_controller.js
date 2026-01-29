/**
 * UI Controller for v2 API integration
 * Handles button clicks, panel updates, and data refresh
 */

// Store current data
let currentSignal = null;
let currentOverlays = null;
let currentGuards = null;

/**
 * Initialize UI controllers
 */
function initUIControllers() {
    // Load user context and update banner
    updateTierBanner();
    
    // Check user permissions and update UI
    updateUIPermissions();
    
    // Refresh Signal button
    document.getElementById('refreshSignal')?.addEventListener('click', async () => {
        await refreshMentorSignal();
    });
    
    // Copy Signal button
    document.getElementById('copySignal')?.addEventListener('click', () => {
        if (currentSignal) {
            const text = formatSignalForClipboard(currentSignal);
            navigator.clipboard.writeText(text);
            showToast('Signal copied to clipboard!');
        }
    });
    
    // Mark Signal button
    document.getElementById('markSignal')?.addEventListener('click', () => {
        showToast('Signal marked for review!');
    });
    
    // Check Guards button
    document.getElementById('checkGuards')?.addEventListener('click', async () => {
        await refreshGuards();
    });
    
    // Log Trade button
    document.getElementById('logTrade')?.addEventListener('click', () => {
        showLogTradeModal();
    });
    
    // View Journal button
    document.getElementById('viewJournal')?.addEventListener('click', async () => {
        await refreshJournalSummary();
    });
    
    // Run Backtest button
    document.getElementById('runBacktest')?.addEventListener('click', async () => {
        await runBacktest();
    });
    
    // Show panels after a delay
    setTimeout(() => {
        document.getElementById('guardsPanel').style.display = 'block';
        document.getElementById('journalPanel').style.display = 'block';
        document.getElementById('backtestPanel').style.display = 'block';
    }, 1000);
    
    // Auto-refresh signal every 30s
    setInterval(async () => {
        await refreshMentorSignal();
    }, 30000);
}

/**
 * Update tier banner with user context
 */
function updateTierBanner() {
    const user = getUserContext();
    const banner = document.getElementById('tierBanner');
    const info = document.getElementById('tierInfo');
    
    if (banner && info) {
        // Set tier display
        info.textContent = `${user.tier} • ${user.phase}`;
        
        // Color code by tier
        if (user.tier === 'FREE') {
            banner.style.background = 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)';
            info.innerHTML = `${user.tier} • ${user.phase} <small style="opacity: 0.8;">| Upgrade to unlock features</small>`;
        } else if (user.tier === 'BASIC') {
            banner.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        } else if (user.tier === 'PRO') {
            banner.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
            info.innerHTML = `${user.tier} • ${user.phase} <small style="opacity: 0.8;">| Pro features active</small>`;
        } else if (user.tier === 'ELITE') {
            banner.style.background = 'linear-gradient(135deg, #ffd89b 0%, #19547b 100%)';
            info.innerHTML = `${user.tier} • ${user.phase} <small style="opacity: 0.8;">| All features unlocked</small>`;
        }
        
        banner.style.display = 'block';
    }
}

/**
 * Update UI based on user permissions
 */
async function updateUIPermissions() {
    try {
        const data = await API.getMentorSignal();
        const permissions = data.ui_permissions;
        
        if (!permissions) return;
        
        // Update button states based on permissions
        const user = getUserContext();
        
        // Show lock icons on restricted features
        if (!permissions.show_liquidity_map) {
            addLockIcon('liquidity', 'PRO tier required');
        }
        if (!permissions.show_gann_panel) {
            addLockIcon('gann', 'PRO tier required');
        }
        if (!permissions.show_astro_panel) {
            addLockIcon('astro', 'PRO tier required');
        }
        if (!permissions.show_backtest_engine && user.tier === 'BASIC') {
            const backtestBtn = document.getElementById('runBacktest');
            if (backtestBtn) {
                backtestBtn.innerHTML = '🔒 Run Backtest (PRO)';
                backtestBtn.style.opacity = '0.6';
                backtestBtn.title = 'Upgrade to PRO tier to unlock backtesting';
            }
        }
    } catch (err) {
        console.error('Failed to check permissions:', err);
    }
}

/**
 * Add lock icon to indicator button
 */
function addLockIcon(indicator, tooltip) {
    const btn = document.querySelector(`[data-indicator="${indicator}"]`);
    if (btn && !btn.querySelector('.lock-icon')) {
        btn.style.position = 'relative';
        btn.title = tooltip;
        btn.style.opacity = '0.5';
        const lock = document.createElement('span');
        lock.className = 'lock-icon';
        lock.textContent = '🔒';
        lock.style.cssText = 'position: absolute; top: -2px; right: -2px; font-size: 10px;';
        btn.appendChild(lock);
    }
}

/**
 * Refresh mentor signal from API
 */
async function refreshMentorSignal() {
    try {
        const data = await API.getMentorSignal();
        currentSignal = data;
        
        // Update mentor text
        const mentorText = document.getElementById('mentorText');
        const drawerContainer = document.getElementById('drawerContainer');
        // If chart.v4 already manages the mentor drawers/content, avoid overwriting it
        if (mentorText && !drawerContainer) {
            const signal = data.signal || data;
            mentorText.innerHTML = formatMentorSignal(signal);
        }
        
        // Update confidence
        const confidenceDiv = document.getElementById('confidence');
        const signal = data.signal || data;
        if (confidenceDiv && signal && signal.confidence !== undefined) {
            const conf = signal.confidence;
            const color = conf >= 80 ? '#3fb950' : conf >= 60 ? '#ff9f1c' : '#f85149';
            confidenceDiv.innerHTML = `<div style="margin-top: 8px; font-size: 11px;"><b>Confidence:</b> <span style="color: ${color}; font-weight: 600;">${conf}%</span></div>`;
        }
        
        // Note: Removed repetitive "Some features require PRO tier" toast
        // Tier information is already shown in the banner at the top
        
    } catch (err) {
        console.error('Failed to refresh signal:', err);
        showToast('Failed to refresh signal', 'error');
    }
}

/**
 * Format signal for display
 */
function formatMentorSignal(signal) {
    if (!signal || typeof signal !== 'object') {
        return '<div style="color: #888;">No signal available</div>';
    }
    
    let html = '';
    
    if (signal.action) {
        html += `<div style="margin-bottom: 8px;"><b>Action:</b> <span style="color: #ff9f1c; font-weight: 600;">${signal.action}</span></div>`;
    }
    
    if (signal.reason) {
        html += `<div style="margin-bottom: 8px; font-size: 11px; color: #888;">${signal.reason}</div>`;
    }
    
    if (signal.entry_zone) {
        html += `<div style="margin-bottom: 6px; font-size: 11px;"><b>Entry:</b> ${signal.entry_zone.min} - ${signal.entry_zone.max}</div>`;
    }
    
    if (signal.stops) {
        html += `<div style="margin-bottom: 6px; font-size: 11px;"><b>Stop:</b> ${signal.stops.conservative}</div>`;
    }
    
    if (signal.targets && signal.targets.length > 0) {
        html += `<div style="margin-bottom: 6px; font-size: 11px;"><b>Targets:</b> ${signal.targets.join(', ')}</div>`;
    }
    
    if (signal.confidence !== undefined) {
        const conf = signal.confidence;
        const color = conf >= 80 ? '#3fb950' : conf >= 60 ? '#ff9f1c' : '#f85149';
        html += `<div style="margin-top: 8px; font-size: 11px;"><b>Confidence:</b> <span style="color: ${color}; font-weight: 600;">${conf}%</span></div>`;
    }
    
    return html || '<div style="color: #888;">No signal available</div>';
}

/**
 * Format signal for clipboard
 */
function formatSignalForClipboard(data) {
    if (!data || typeof data !== 'object') {
        return 'No signal data available';
    }
    
    const s = data.signal || data;
    let text = `AI MENTOR SIGNAL\n`;
    text += `================\n`;
    if (s && s.action) text += `Action: ${s.action}\n`;
    if (s && s.reason) text += `Reason: ${s.reason}\n`;
    if (s && s.entry_zone) text += `Entry: ${s.entry_zone.min} - ${s.entry_zone.max}\n`;
    if (s && s.stops) text += `Stop: ${s.stops.conservative}\n`;
    if (s && s.targets) text += `Targets: ${s.targets.join(', ')}\n`;
    if (s && s.confidence) text += `Confidence: ${s.confidence}%\n`;
    if (data.timestamp) text += `\nTimestamp: ${data.timestamp}`;
    return text;
}

/**
 * Refresh guards status
 */
async function refreshGuards() {
    try {
        const data = await API.getGuards();
        currentGuards = data;
        
        const statusDiv = document.getElementById('guardsStatus');
        if (statusDiv) {
            statusDiv.innerHTML = formatGuardsStatus(data);
        }
        
        const btn = document.getElementById('checkGuards');
        if (btn) {
            btn.textContent = data.trading_allowed ? '✅ Trading Allowed' : '🚫 Trading Blocked';
            btn.style.background = data.trading_allowed ? 'linear-gradient(135deg, #3fb950 0%, #2ea043 100%)' : 'linear-gradient(135deg, #f85149 0%, #da3633 100%)';
        }
        
    } catch (err) {
        console.error('Failed to refresh guards:', err);
        showToast('Failed to check guards', 'error');
    }
}

/**
 * Format guards status
 */
function formatGuardsStatus(data) {
    const g = data.guards;
    let html = '';
    
    // News guard
    const newsIcon = g.news.allow_trade ? '✅' : '🚫';
    html += `<div style="margin-bottom: 6px; font-size: 11px;">${newsIcon} <b>News:</b> ${g.news.risk_level}</div>`;
    
    // Session guard
    const sessionIcon = g.session.allowed ? '✅' : '🚫';
    html += `<div style="margin-bottom: 6px; font-size: 11px;">${sessionIcon} <b>Session:</b> ${g.session.current_session}</div>`;
    
    // Risk guard
    const riskIcon = g.risk.can_trade ? '✅' : '🚫';
    html += `<div style="margin-bottom: 6px; font-size: 11px;">${riskIcon} <b>Risk:</b> ${g.risk.daily_loss_pct.toFixed(1)}% / ${g.risk.max_daily_loss_pct}%</div>`;
    
    return html;
}

/**
 * Show log trade modal (simplified for now)
 */
function showLogTradeModal() {
    const data = {
        entry_time: new Date().toISOString(),
        direction: 'LONG',
        entry_price: 2650.0,
        stop_loss: 2645.0,
        take_profit_1: 2660.0,
        setup_type: 'ICEBERG_ABSORPTION',
        ai_confidence: 85.0,
        execution_notes: 'Manual test trade'
    };
    
    API.logTrade(data)
        .then(() => {
            showToast('Trade logged successfully!');
        })
        .catch(err => {
            console.error('Failed to log trade:', err);
            showToast('Failed to log trade', 'error');
        });
}

/**
 * Refresh journal summary
 */
async function refreshJournalSummary() {
    try {
        const data = await API.getJournalSummary();
        
        const summaryDiv = document.getElementById('journalSummary');
        if (summaryDiv) {
            if (data.status === 'empty') {
                summaryDiv.innerHTML = '<div style="color: #888;">No trades logged today</div>';
            } else {
                summaryDiv.innerHTML = formatJournalSummary(data.summary);
            }
        }
        
    } catch (err) {
        console.error('Failed to refresh journal:', err);
        showToast('Failed to load journal', 'error');
    }
}

/**
 * Format journal summary
 */
function formatJournalSummary(summary) {
    let html = `<div style="font-size: 11px;">`;
    html += `<div><b>Trades:</b> ${summary.total_trades || 0}</div>`;
    html += `<div><b>Win Rate:</b> ${summary.win_rate || 0}%</div>`;
    html += `<div><b>Avg R:</b> ${summary.avg_r_multiple || 0}R</div>`;
    html += `</div>`;
    return html;
}

/**
 * Run backtest
 */
async function runBacktest() {
    const startInput = document.getElementById('backtestStart');
    const endInput = document.getElementById('backtestEnd');
    
    if (!startInput.value || !endInput.value) {
        showToast('Please select date range', 'warning');
        return;
    }
    
    try {
        showToast('Running backtest...', 'info');
        
        const data = await API.runBacktest({
            instrument: 'GC',
            start_date: startInput.value,
            end_date: endInput.value,
            data_source: 'simulation'
        });
        
        const resultsDiv = document.getElementById('backtestResults');
        if (resultsDiv) {
            resultsDiv.innerHTML = formatBacktestResults(data);
        }
        
        showToast('Backtest completed!');
        
    } catch (err) {
        console.error('Failed to run backtest:', err);
        showToast('Backtest failed', 'error');
    }
}

/**
 * Format backtest results
 */
function formatBacktestResults(data) {
    const r = data.results;
    let html = `<div style="font-size: 11px; margin-top: 8px;">`;
    html += `<div><b>Candles:</b> ${data.backtest.candles_processed}</div>`;
    html += `<div><b>Win Rate:</b> ${r.win_rate || 0}%</div>`;
    html += `<div><b>Avg R:</b> ${r.avg_r_multiple || 0}R</div>`;
    html += `<div><b>Profit Factor:</b> ${r.profit_factor || 0}</div>`;
    html += `</div>`;
    return html;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const colors = {
        success: '#3fb950',
        warning: '#ff9f1c',
        error: '#f85149',
        info: '#58a6ff'
    };
    
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.success};
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
    .mentor-btn {
        padding: 6px 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .mentor-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .mentor-btn:active {
        transform: translateY(0);
    }
`;
document.head.appendChild(style);

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUIControllers);
} else {
    initUIControllers();
}

// Export for use in other scripts
window.refreshMentorSignal = refreshMentorSignal;
window.refreshGuards = refreshGuards;
