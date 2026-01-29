console.log("🎬 chart.v4.js loading...");
console.log("📍 Canvas element:", document.getElementById("chart"));
console.log("📍 Mini canvas element:", document.getElementById("miniChart"));

const canvas = document.getElementById("chart");
if (!canvas) {
    console.error("❌ CRITICAL: Canvas element #chart not found!");
    throw new Error("Canvas element not found");
}
const ctx = canvas.getContext("2d");

const miniCanvas = document.getElementById("miniChart");
if (!miniCanvas) {
    console.error("❌ CRITICAL: Canvas element #miniChart not found!");
    throw new Error("Mini canvas element not found");
}
const miniCtx = miniCanvas.getContext("2d");

// ========== ASTRO HEADER DISPLAY - REMOVED ==========
// Astro indicators have been permanently removed from header/toolbar
// function updateAstroHeaderDisplay() - DELETED

let dpiScale = window.devicePixelRatio || 1; // Global DPI scale factor

function resizeCanvases() {
    dpiScale = window.devicePixelRatio || 1;
    const dpr = dpiScale;

    const layout = document.getElementById("layout");
    const layoutRect = layout ? layout.getBoundingClientRect() : null;
    const chartRect = canvas.getBoundingClientRect();
    const cssWidth = Math.floor(chartRect.width || (layoutRect ? layoutRect.width * 0.75 : window.innerWidth * 0.75));
    const cssHeight = Math.floor(chartRect.height || (layoutRect ? layoutRect.height : window.innerHeight * 0.9));
    canvas.style.width = `${cssWidth}px`;
    canvas.style.height = `${cssHeight}px`;
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    
    console.log("📐 Canvas resized:", cssWidth, "x", cssHeight, "DPR:", dpr);

    const miniRect = miniCanvas.getBoundingClientRect();
    const miniCssWidth = Math.floor(miniRect.width || 180);
    const miniCssHeight = Math.floor(miniRect.height || 60);
    miniCanvas.style.width = `${miniCssWidth}px`;
    miniCanvas.style.height = `${miniCssHeight}px`;
    miniCanvas.width = Math.round(miniCssWidth * dpr);
    miniCanvas.height = Math.round(miniCssHeight * dpr);
    miniCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

resizeCanvases();

let ohlcBars = []; // Store OHLC data like TradingView
let dataSource = "Demo";  // Track data source
let currentTimeframe = "5m"; // Current selected timeframe
let previousPrice = 0; // For price change animation
let priceHistory = []; // Store last 30 prices for mini chart
let icebergZones = []; // Absorption zones from backend
let rawOrders = []; // Raw tick-level orders before candle formation
let orderflowVisible = false; // Floating orderflow panel state
let rawOrdersVisible = false; // Raw orders table panel state (default OFF)

// Multi-timeframe support
const timeframes = ['1m', '5m', '15m', '1H', '4H', '1D'];
let timeframeCache = {};  // {timeframe: [candles]}
timeframes.forEach(tf => timeframeCache[tf] = []);  // Initialize empty
let timeframeZoomState = {};  // {timeframe: {zoomLevel, barPan, pricePan}}
let timeframeLastUpdate = {};  // Track last update per timeframe
let isDraggingOrderflow = false;
let orderflowDragOffset = { x: 0, y: 0 };

// New candle tracking for auto-scroll
let lastCandleCount = 0;  // Track number of candles
let newCandleAdded = false;  // Flag for new candle animation
let newCandleFlashTime = 0;  // Timestamp for flash effect
let autoScrollEnabled = false;  // Auto-scroll to latest candle

// Chart panning state (TradingView-like)
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let barPan = 0;          // persistent bar offset (horizontal)
let tempBarPan = 0;      // live drag offset before mouseup
let pricePan = 0;        // persistent price offset (vertical)
let tempPricePan = 0;    // live drag offset before mouseup
let zoomLevel = 1.0;     // zoom multiplier (0.5 to 3.0)
let visibleCandles = 100; // number of candles to display

// Price scale locking
let priceScaleLocked = false;  // When true, price scale stays fixed
let lockedPriceMin = null;     // Locked minimum price
let lockedPriceMax = null;     // Locked maximum price

// Databento usage tracking
let databentoUsage = {
    apiCalls: 0,
    dataConsumed: 0, // in MB
    planLimit: 1000, // MB per month (example limit)
    resetDate: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1)
};

// Drawing tools state
let drawingMode = null;  // 'trendline', 'horizontal', 'fibonacci', or null
let drawings = [];       // Array of {type, points, color, label}
let currentDrawing = {points: [], color: '#FFD700'}; // In-progress drawing
let mouseX = 0;
let mouseY = 0;

// Indicator states (default OFF for clean chart load)
let volumeVisible = false;
let vwapVisible = false;
let vwapValues = [];
let volumeProfileVisible = false;
let volumeProfileData = null;
let volumeProfileLegendVisible = false;  // Legend panel toggle
let sessionMarkersVisible = false;  // Session open markers
let isVolumeProfileUpdating = false;  // Update indicator
let lastVolumeProfileUpdate = null;  // Track last update time
let previousPOC = null;  // Track POC movement for animation
let isDarkTheme = true;  // Theme toggle (dark by default)
let icebergVisible = false;
let gannCyclesVisible = false;  // Toggle for Gann cycle visualization
let gannLevelsVisible = false;   // Toggle for Gann horizontal levels (Cardinal Cross, Clusters)
let astroCyclesVisible = false; // Toggle for Astro cycle visualization
let astroIndicatorsVisible = false; // Toggle for Astro canvas displays (Moon, Warning, Mercury Rx)
let sweepsVisible = false;
let fvgVisible = false;
let liquidityVisible = false;
let htfVisible = false;

// STEP 7: Position Management State
let positionsVisible = false;  // Show positions on chart
let activePositions = [];     // {id, type, entryPrice, entryTime, entryIndex, stopLoss, takeProfit, size, pnl}
let closedTrades = [];        // Historical closed trades
let positionIdCounter = 1;    // Auto-increment ID
let isAddingPosition = false; // Position input mode
let positionPanelVisible = false; // Position control panel
let selectedPosition = null;  // Currently selected position for editing

// Cursor OHLC Display State
let cursorOHLCVisible = false;   // Show OHLC tooltip on cursor (disabled by default)

// Orderflow visualization state
let orderflowVisualization = false;  // Legacy orderflow toggle (unused)
let ictVisible = false;  // ICT indicator toggle
let lastChartState = null;
let ictMemory = (() => {
    try {
        return JSON.parse(localStorage.getItem('ictMemory') || '[]');
    } catch {
        return [];
    }
})();
let lastIctSignalKey = null;
let domLadderVisible = false;   // Show DOM ladder panel
let footprintVisible = false;   // Show footprint in candles
let heatmapVisible = false;     // Show bid/ask heatmap
let orderflowData = {};         // {candleIndex: {bids: [], asks: []}}
let domLadderData = [];         // Current DOM ladder data
let institutionalAlerts = [];   // Sweep, absorption, large order alerts
let lastOrderflowUpdate = 0;    // Prevent excessive updates

// HTF overlay cache from mentor
let htfOverlay = { trend: 'N/A', bias: 'NEUTRAL' };

// Cached layout metrics for panning calculations
let lastCandleSpacing = 8;
let lastChartHeight = 300;
let lastPriceRange = 10;

// Session times (UTC) - for COMEX Gold futures
const SESSION_TIMES = {
    ASIA: { open: 0, close: 8, name: 'ASIA', color: 'rgba(99, 102, 241, 0.15)' },      // 12am - 8am UTC
    LONDON: { open: 8, close: 17, name: 'LONDON', color: 'rgba(34, 197, 94, 0.15)' },  // 8am - 5pm UTC
    NEWYORK: { open: 13, close: 21, name: 'NY', color: 'rgba(239, 68, 68, 0.15)' }      // 1pm - 9pm UTC
};

function getSessionName(hour) {
    if (hour >= SESSION_TIMES.NEWYORK.open && hour < SESSION_TIMES.NEWYORK.close) return SESSION_TIMES.NEWYORK.name;
    if (hour >= SESSION_TIMES.LONDON.open && hour < SESSION_TIMES.LONDON.close) return SESSION_TIMES.LONDON.name;
    return SESSION_TIMES.ASIA.name;
}

// ========== VOLUME PROFILE LEGEND PANEL ==========
function drawVolumeProfileLegend(ctx, profile, chartRight, chartTop) {
    if (!volumeProfileLegendVisible || !profile) return;
    
    const panelWidth = 220;
    const panelHeight = isVolumeProfileUpdating ? 180 : 160;  // Extra space when updating
    const panelX = chartRight - panelWidth - 10;
    const panelY = chartTop + 10;
    
    // Panel background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(panelX, panelY, panelWidth, panelHeight);
    
    // Panel border
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 1;
    ctx.strokeRect(panelX, panelY, panelWidth, panelHeight);
    
    // Title
    ctx.fillStyle = 'rgba(234, 179, 8, 1)';
    ctx.font = "bold 12px 'Segoe UI', Arial, sans-serif";
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('VOLUME PROFILE', panelX + 10, panelY + 8);
    
    const lineHeight = 22;
    let y = panelY + 32;
    
    // POC
    ctx.fillStyle = 'rgba(234, 179, 8, 1)';
    ctx.font = "bold 10px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(`POC: ${profile.poc.toFixed(2)}`, panelX + 10, y);
    y += lineHeight;
    
    // VAH/VAL Range
    const vaRange = (profile.vah - profile.val).toFixed(2);
    ctx.fillStyle = 'rgba(156, 163, 175, 0.9)';
    ctx.fillText(`VA Range: ${vaRange}`, panelX + 10, y);
    y += lineHeight;
    
    // Buy/Sell Ratio
    const totalVol = profile.total_buy_volume + profile.total_sell_volume;
    const buyPct = totalVol > 0 ? ((profile.total_buy_volume / totalVol) * 100).toFixed(1) : 0;
    ctx.fillStyle = 'rgba(34, 197, 94, 1)';
    ctx.font = "10px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(`▲ Buy: ${buyPct}%`, panelX + 10, y);
    
    ctx.fillStyle = 'rgba(239, 68, 68, 1)';
    ctx.fillText(`▼ Sell: ${(100 - buyPct).toFixed(1)}%`, panelX + 110, y);
    y += lineHeight;
    
    // VWAP Deviation from POC
    const vwapDev = (profile.vwap - profile.poc).toFixed(2);
    const devColor = vwapDev >= 0 ? 'rgba(34, 197, 94, 1)' : 'rgba(239, 68, 68, 1)';
    ctx.fillStyle = devColor;
    ctx.fillText(`VWAP Dev: ${vwapDev}`, panelX + 10, y);
    y += lineHeight;
    
    // Volume summary
    const volLabel = profile.total_volume > 999999 
        ? (profile.total_volume / 1000000).toFixed(2) + 'M'
        : profile.total_volume > 999
        ? (profile.total_volume / 1000).toFixed(1) + 'K'
        : profile.total_volume.toString();
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.font = "9px 'Segoe UI', Arial, sans-serif";
    ctx.fillText(`Total Vol: ${volLabel}`, panelX + 10, y);
    y += lineHeight;
    ctx.fillText(`Bars: ${profile.bars_analyzed}`, panelX + 10, y);
    y += lineHeight;
    
    // Update indicator
    if (isVolumeProfileUpdating) {
        ctx.fillStyle = '#f0883e';
        ctx.font = "bold 10px 'Segoe UI', Arial, sans-serif";
        ctx.fillText('⟳ UPDATING...', panelX + 10, y);
    } else if (lastVolumeProfileUpdate) {
        const elapsed = Math.floor((new Date() - lastVolumeProfileUpdate) / 1000);
        const timeText = elapsed < 60 ? `${elapsed}s ago` : `${Math.floor(elapsed/60)}m ago`;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = "9px 'Segoe UI', Arial, sans-serif";
        ctx.fillText(`Updated ${timeText}`, panelX + 10, y);
    }
}

// ========== THEMES ==========
const THEMES = {
    dark: {
        background: '#0e0e0e',
        text: '#e0e0e0',
        grid: '#1a1a1a',
        gridBg: '#0a0a0a',
        up: '#26a69a',
        down: '#ef5350',
        volume: 'rgba(120, 120, 120, 0.3)',
        volumeDown: 'rgba(239, 83, 80, 0.35)',
        crosshair: '#888',
        tooltip: 'rgba(20, 20, 20, 0.95)'
    },
    light: {
        background: '#ffffff',
        text: '#333333',
        grid: '#e0e0e0',
        gridBg: '#f5f5f5',
        up: '#089981',
        down: '#f23645',
        volume: 'rgba(180, 180, 180, 0.4)',
        volumeDown: 'rgba(242, 54, 69, 0.35)',
        crosshair: '#666',
        tooltip: 'rgba(255, 255, 255, 0.95)'
    }
};

// API_BASE is now provided by api_client.js
// No need to redefine here

// Draw mini price chart
function drawMiniChart() {
    if (priceHistory.length < 2) return;
    
    const dpr = window.devicePixelRatio || 1;
    const width = miniCanvas.width / dpr;
    const height = miniCanvas.height / dpr;
    const padding = 4;
    
    // Clear canvas
    miniCtx.fillStyle = '#161b22';
    miniCtx.fillRect(0, 0, width, height);
    
    // Calculate min/max for scaling
    const prices = priceHistory.slice(-30); // Last 30 data points
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    
    // Draw line
    miniCtx.beginPath();
    miniCtx.strokeStyle = priceHistory[priceHistory.length - 1] > priceHistory[priceHistory.length - 2] ? '#3fb950' : '#f85149';
    miniCtx.lineWidth = 1.5;
    
    prices.forEach((price, i) => {
        const x = (i / (prices.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((price - min) / range) * (height - padding * 2);
        
        if (i === 0) {
            miniCtx.moveTo(x, y);
        } else {
            miniCtx.lineTo(x, y);
        }
    });
    
    miniCtx.stroke();
    
    // Draw gradient fill
    miniCtx.lineTo(width - padding, height - padding);
    miniCtx.lineTo(padding, height - padding);
    miniCtx.closePath();
    
    const gradient = miniCtx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, priceHistory[priceHistory.length - 1] > priceHistory[priceHistory.length - 2] ? 'rgba(63, 185, 80, 0.2)' : 'rgba(248, 81, 73, 0.2)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    miniCtx.fillStyle = gradient;
    miniCtx.fill();
}

// Update live price ticker
function updatePriceTicker(price, source) {
    const livePriceEl = document.getElementById("livePrice");
    const priceChangeEl = document.getElementById("priceChange");
    const dataSourceEl = document.getElementById("dataSource");
    
    // Add to price history
    priceHistory.push(price);
    if (priceHistory.length > 60) {
        priceHistory.shift(); // Keep only last 60 points
    }
    
    // Draw mini chart
    drawMiniChart();
    
    // Only update DOM elements if they exist (removed from toolbar)
    if (livePriceEl) {
        // Animate price update
        livePriceEl.style.animation = 'none';
        setTimeout(() => {
            livePriceEl.style.animation = '';
        }, 10);
        
        livePriceEl.textContent = `$${price.toFixed(2)}`;
    }
    
    // Calculate and display change
    if (priceChangeEl && previousPrice > 0) {
        const change = price - previousPrice;
        const changePercent = ((change / previousPrice) * 100).toFixed(2);
        const changeText = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent}%)`;
        priceChangeEl.textContent = changeText;
        priceChangeEl.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
    }
    
    // Update source indicator
    if (dataSourceEl) {
        dataSourceEl.textContent = source === 'Yahoo Finance' ? '● LIVE' : '● DEMO';
        dataSourceEl.style.color = source === 'Yahoo Finance' ? '#3fb950' : '#f0883e';
        dataSourceEl.className = 'live-indicator';
    }
    
    previousPrice = price;
}

async function fetchData() {
    try {
        console.log(`🔄 Fetching chart data (${currentTimeframe})...`);
        console.log(`📡 Fetch URL: ${API_BASE}/api/v1/chart`);
        
        const res = await fetch(`${API_BASE}/api/v1/chart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bars: 100, interval: currentTimeframe })
        });
        
        // Track Databento usage
        updateDatabentoUsage(res);
        
        console.log(`📡 Response status: ${res.status} ${res.statusText}`);
        
        if (!res.ok) {
            console.error(`❌ HTTP Error: ${res.status} - Failed to fetch ${currentTimeframe} data`);
            const mentorEl = document.getElementById("mentorText");
            if (mentorEl) {
                mentorEl.innerText = `⚠️ API Error ${res.status}. Using demo data.`;
            }
            
            // Use demo/cached data if available
            if (ohlcBars.length === 0) {
                console.log("⚠️ No cached data, chart will show loading state");
            }
            return;
        }
        
        const data = await res.json();
        console.log("📊 API Response received:", {
            symbol: data.symbol,
            interval: data.interval,
            barCount: data.bars ? data.bars.length : 0
        });

        if (!data.bars || data.bars.length === 0) {
            console.error("❌ No chart data received from API");
            const mentorEl = document.getElementById("mentorText");
            if (mentorEl) {
                mentorEl.innerText = "⚠️ No data received from API";
            }
            return;
        }

        // Update data source indicator
        dataSource = data.source || "Live";
        console.log(`✅ Chart data loaded: ${data.bars.length} candles (${dataSource})`);
        console.log(`📈 First candle:`, data.bars[0]);
        console.log(`📈 Last candle:`, data.bars[data.bars.length - 1]);

        // Replace OHLC bars with live/demo data
        const previousCandleCount = ohlcBars.length;
        ohlcBars = data.bars.map((bar, idx) => {
            const obj = {
                open: parseFloat(bar.open),
                high: parseFloat(bar.high),
                low: parseFloat(bar.low),
                close: parseFloat(bar.close),
                volume: parseInt(bar.volume) || 0,
                timestamp: bar.timestamp,  // Keep original timestamp string
                icebergDetected: !!bar.iceberg_detected
            };
            if (idx === 0) console.log("🔍 Parsed candle 0:", obj);
            return obj;
        });
        
        // Detect new candle and trigger animation
        if (ohlcBars.length > previousCandleCount && previousCandleCount > 0) {
            newCandleAdded = true;
            newCandleFlashTime = Date.now();
            const newCandle = ohlcBars[ohlcBars.length - 1];
            const isBullish = newCandle.close >= newCandle.open;
            console.log(`🆕 New candle detected! Count: ${previousCandleCount} → ${ohlcBars.length}`);
            
            // Show toast notification
            const candleIcon = isBullish ? '🟢' : '🔴';
            const candleType = isBullish ? 'Bullish' : 'Bearish';
            showToast(`${candleIcon} New ${candleType} Candle | $${newCandle.close.toFixed(2)}`, 3000);
            
            // Auto-scroll to show new candle if enabled
            if (autoScrollEnabled) {
                barPan = 0;  // Reset pan to show latest candles
                tempBarPan = 0;
                console.log("📜 Auto-scrolled to latest candle");
            }
        }

        // Compute VWAP values once after data load
        vwapValues = computeVWAP(ohlcBars);

        icebergZones = (data.iceberg_zones || []).map(z => ({
            price_top: parseFloat(z.price_top),
            price_bottom: parseFloat(z.price_bottom),
            volume: parseFloat(z.volume_indicator),
            color: z.color || "rgba(255,159,28,0.18)"
        }));
        console.log(`🧊 Iceberg zones updated from API: ${icebergZones.length} zones received`);

        // Fetch raw orders (tick-level data before candle formation)
        try {
            const ordersRes = await fetch(`${API_BASE}/api/v1/orders/recent?limit=50`);
            updateDatabentoUsage(ordersRes); // Track usage
            const ordersData = await ordersRes.json();
            rawOrders = ordersData.orders || [];
            console.log(`📊 Fetched ${rawOrders.length} raw orders`);
        } catch (error) {
            console.warn("⚠️ Could not fetch raw orders:", error);
            rawOrders = [];
        }

        console.log(`✅ Parsed ${ohlcBars.length} candles and ${icebergZones.length} iceberg zones`);
        
        // Update live price ticker with latest price
        if (ohlcBars.length > 0) {
            const latestBar = ohlcBars[ohlcBars.length - 1];
            updatePriceTicker(latestBar.close, dataSource);
        }

        // Also fetch mentor data for the AI panel
        try {
            console.log("🔄 Fetching mentor data...");
            const mentorRes = await fetch(`${API_BASE}/api/v1/mentor`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: 'XAUUSD', refresh: true })
            });
            const mentorData = await mentorRes.json();
            console.log("✅ Mentor data received:", mentorData);
            updateMentor(mentorData);
        } catch (error) {
            console.error("❌ Failed to fetch mentor data:", error);
        }

        // Always render both tables (keeps data fresh even if hidden)
        renderIcebergOrderflow(icebergZones, ohlcBars);
        renderRawOrders(rawOrders);
        draw();
    } catch (error) {
        console.error("❌ Failed to fetch chart data:", error);
        const mentorEl = document.getElementById("mentorText");
        if (mentorEl) {
            mentorEl.innerText = "⚠️ Connection error. Retrying...";
        }
    }
}

// ========== VOLUME PROFILE FETCHER WITH AUTO-REFRESH ==========
async function fetchVolumeProfile() {
    try {
        isVolumeProfileUpdating = true;
        draw(); // Show updating indicator
        
        console.log(`🔄 Fetching Volume Profile (${currentTimeframe})...`);
        const res = await fetch(`${API_BASE}/api/v1/indicators/volume-profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                symbol: 'GCG6', 
                interval: currentTimeframe, 
                bars: 100,
                tick_size: 0.10,
                value_area_pct: 0.70
            })
        });
        
        if (!res.ok) {
            console.error(`❌ Volume Profile HTTP Error: ${res.status}`);
            isVolumeProfileUpdating = false;
            return;
        }
        
        const newData = await res.json();
        
        // Track POC movement for animation
        if (volumeProfileData && volumeProfileData.poc !== newData.poc) {
            previousPOC = volumeProfileData.poc;
            console.log(`📊 POC moved: ${previousPOC.toFixed(2)} → ${newData.poc.toFixed(2)}`);
        }
        
        volumeProfileData = newData;
        lastVolumeProfileUpdate = new Date();
        
        console.log("✅ Volume Profile updated:", volumeProfileData);
        console.log(`   POC: ${volumeProfileData.poc}, VAH: ${volumeProfileData.vah}, VAL: ${volumeProfileData.val}, VWAP: ${volumeProfileData.vwap}`);
        
        // Clear updating flag after a brief delay to show the indicator
        setTimeout(() => {
            isVolumeProfileUpdating = false;
            previousPOC = null; // Clear animation after 1 second
            draw();
        }, 1000);
        
        draw();
    } catch (error) {
        console.error("❌ Failed to fetch Volume Profile:", error);
        isVolumeProfileUpdating = false;
        draw();
    }
}

// Compute Volume-Weighted Average Price series
function computeVWAP(bars) {
    let cumulativePV = 0; // price * volume sum
    let cumulativeVolume = 0;
    const values = [];

    bars.forEach(bar => {
        const typicalPrice = (bar.high + bar.low + bar.close) / 3;
        cumulativePV += typicalPrice * (bar.volume || 0);
        cumulativeVolume += (bar.volume || 0);
        const vwap = cumulativeVolume > 0 ? cumulativePV / cumulativeVolume : typicalPrice;
        values.push(vwap);
    });

    return values;
}

function updateMentor(data) {
    console.log("📊 updateMentor called with data:", data);
    
    // Store Gann data globally for chart rendering
    window.gannData = {
        gann_square_of_9: data.gann_square_of_9,
        gann_cardinal_cross: data.gann_cardinal_cross,
        gann_angles: data.gann_angles,
        gann_clusters: data.gann_clusters,
        gann_levels: data.gann_levels,
        gann_cycles: data.gann_cycles || []  // Store cycles for visualization
    };
    
    // Store Astro data globally
    window.astroData = {
        astro_aspects: data.astro_aspects,
        astro_outlook: data.astro_outlook,
        moon_phase: data.moon_phase,
        mercury_retrograde: data.mercury_retrograde,
        active_aspects: data.active_aspects,
        astro_cycles: data.astro_cycles || []  // Store cycles for visualization
    };
    
    // Astro header display removed - no longer called
    
    console.log("🔄 Cycles data received:", window.gannData.gann_cycles);
    
    const htfTrend = data.htf_structure?.trend || 'N/A';
    const bias = data.htf_structure?.bias || 'NEUTRAL';
    const confidence = data.confidence_percent || 0;
    const verdict = data.ai_verdict || 'WAIT';
    const risk = data.risk_assessment || {};
    const conf = data.confirmation_status || {};
    const bullets = data.context_bullets || [];
    const story = data.context_story || '';
    const longStory = data.context_long_story || '';
    const mtfBullets = data.mtf_summary_bullets || [];
    const tradeSummary = data.trade_summary || '';
    const entryPlan = data.entry_plan || '';
    const stopPlan = data.stop_plan || '';
    const targetPlan = data.target_plan || '';
    const sessionNarr = data.session_narrative || '';
    const invalidations = data.invalidations || [];

    // cache for HTF overlay badge
    htfOverlay = { trend: htfTrend, bias };
    
    const icebergInfo = data.iceberg_activity?.detected 
        ? `🧊 ACTIVE: ${data.iceberg_activity?.absorption_count || 0} zones | $${data.iceberg_activity?.price_from?.toFixed(2) || 'N/A'}-$${data.iceberg_activity?.price_to?.toFixed(2) || 'N/A'} | ${(data.iceberg_activity?.volume_spike_ratio || 1).toFixed(1)}x vol` 
        : '✅ Clear';
    
    console.log("🧊 Iceberg info:", icebergInfo);
    console.log("🎯 Verdict:", verdict, "HTF:", htfTrend, "Confidence:", confidence);
    
    const bulletsHTML = bullets.length
        ? `<ul style="margin: 6px 0 4px 16px; padding: 0;">${bullets.map(b => `<li style="margin-bottom:2px;">${b}</li>`).join('')}</ul>`
        : '';

    const mentorHTML = `
        <strong>HTF Trend:</strong> ${htfTrend} (${bias})<br>
        <strong>Session:</strong> ${data.session || 'N/A'} | <strong>Price:</strong> $${data.current_price?.toFixed(2) || '0.00'}<br>
        <strong>Gann:</strong> ${data.gann_signal || 'NEUTRAL'} | <strong>Clusters:</strong> ${data.gann_clusters?.length || 0} zones<br>
        <strong>Astro:</strong> ${data.astro_signal || 'N/A'} | <strong>Moon:</strong> ${data.moon_phase?.phase || 'N/A'}<br>
        <strong>Iceberg:</strong> ${icebergInfo}<br>
        <strong>Risk:</strong> ${risk.risk_level || 'N/A'} @ ${risk.recommended_risk_pct ?? '-'}% | R:R ${risk.risk_reward_ratio ?? '-'} | Stop ~${risk.stop_loss ? risk.stop_loss.toFixed(2) : '-'}<br>
        <strong>Confirmations:</strong> ${conf.score ?? 0}/100 (${conf.ready_to_trade ? 'READY' : 'WAIT'})<br>
        <strong>Entry:</strong> ${data.entry_trigger || 'Waiting...'}<br>
        ${tradeSummary ? `<strong>Plan:</strong> ${tradeSummary}<br>` : ''}
        ${entryPlan ? `<strong>Entry Plan:</strong> ${entryPlan}<br>` : ''}
        ${stopPlan ? `<strong>Stop:</strong> ${stopPlan}<br>` : ''}
        ${targetPlan ? `<strong>Targets:</strong> ${targetPlan}<br>` : ''}
        ${bulletsHTML}
        ${invalidations.length ? `<div style=\"margin-top:6px;\"><strong>Invalidations:</strong><ul style=\"margin: 4px 0 0 16px; padding:0;\">${invalidations.map(i => `<li>${i}</li>`).join('')}</ul></div>` : ''}
        <strong style="color: #888; font-size: 11px;">Data: ${dataSource}</strong>
    `;

    const mentorTextEl = document.getElementById("mentorText");
    if (!mentorTextEl) return;

    // Shared container for drawers (keeps order stable: Narrative > Gann > Astro > Iceberg > News > Global)
    let drawerContainer = document.getElementById("drawerContainer");
    if (!drawerContainer) {
        drawerContainer = document.createElement("div");
        drawerContainer.id = "drawerContainer";
        drawerContainer.style.display = "flex";
        drawerContainer.style.flexDirection = "column";
        drawerContainer.style.gap = "8px";
        mentorTextEl.prepend(drawerContainer);
    }

    // Preserve drawers by updating a dedicated content container placed after drawers
    let mentorContent = document.getElementById("mentorContent");
    if (!mentorContent) {
        mentorContent = document.createElement("div");
        mentorContent.id = "mentorContent";
        mentorContent.style.marginTop = "8px";
        mentorTextEl.appendChild(mentorContent);
    }
    mentorContent.innerHTML = mentorHTML;
    console.log("✅ Mentor content updated");
    
    // Hide legacy mentor orderflow; use floating panel instead
    const orderflowFloating = document.getElementById("orderflowFloating");
    if (orderflowFloating && !orderflowVisible) orderflowFloating.style.display = "none";
    setupNarrativeDrawer(data);
    setupGannDrawer(data);
    setupAstroDrawer(data);
    setupIcebergDrawer(icebergZones, ohlcBars);
    setupNewsDrawer(data);
    setupGlobalMarketsDrawer(data);

    console.log("🔍 Iceberg condition check: detected =", data.iceberg_activity?.detected, ", zones.length =", icebergZones.length);

    document.getElementById("confidence").innerHTML = `
        <strong>Confidence:</strong> ${confidence}%<br>
        <div style="background: #1c2430; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 4px;">
            <div style="background: ${confidence > 70 ? '#2ea043' : '#f85149'}; width: ${confidence}%; height: 100%;"></div>
        </div>
    `;
    console.log("✅ Confidence updated:", confidence + "%");
}

function setupNarrativeDrawer(data) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;

    let drawer = document.getElementById("narrativeDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "narrativeDrawer";
        drawer.innerHTML = `
            <div id="narrativeDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#0f172a; border:1px solid #1f2937; border-radius:6px; cursor:pointer;">
                <div style="background:#111827; border:1px solid #1f2937; color:#93c5fd; padding:4px 8px; border-radius:4px; font-weight:700;">🧠 Mentor Verdict</div>
                <div id="narrativeVerdictChip" style="background:#1d4ed8; color:#e0f2fe; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700;">WAIT</div>
                <div id="narrativeDrawerStatus" style="color:#9ca3af; font-size:12px; margin-left:auto;">Tap to expand</div>
            </div>
            <div id="narrativeDrawerBody" style="display:none; padding:10px; background:#0b1220; border:1px solid #1f2937; border-radius:6px; margin-top:6px;"></div>
        `;
        container.prepend(drawer);

        const header = drawer.querySelector("#narrativeDrawerHeader");
        header.addEventListener("click", () => {
            const body = drawer.querySelector("#narrativeDrawerBody");
            const status = drawer.querySelector("#narrativeDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        });
    }

    const verdict = data.ai_verdict || 'WAIT';
    const confidence = data.confidence_percent ?? 0;
    const story = data.context_long_story || data.context_story || 'No narrative available.';
    const bullets = data.context_bullets || [];
    const sessionNarr = data.session_narrative || '';

    const chip = drawer.querySelector('#narrativeVerdictChip');
    if (chip) {
        chip.textContent = verdict;
        chip.style.background = verdict === 'BUY' ? '#166534' : verdict === 'SELL' ? '#7f1d1d' : '#1d4ed8';
        chip.style.color = '#e0f2fe';
    }

    const body = drawer.querySelector('#narrativeDrawerBody');
    if (!body) return;

    const bulletsHTML = bullets.length
        ? `<ul style="margin: 6px 0 0 16px; padding:0; color:#a7b3c6;">${bullets.map(b => `<li style="margin-bottom:2px;">${b}</li>`).join('')}</ul>`
        : '';

    body.innerHTML = `
        <div style="margin-bottom:8px; padding:8px; background:#0b1220; border-left:3px solid #3b82f6; border-radius:4px; line-height:1.4; color:#cbd5e1;">
            <div style="font-weight:700; color:#d1d5db; margin-bottom:6px;">Narrative</div>
            <div>${story}</div>
            ${sessionNarr ? `<div style="margin-top:6px; color:#94a3b8; font-size:12px;"><em>${sessionNarr}</em></div>` : ''}
            ${bulletsHTML}
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <div style="background:#111827; border:1px solid #1f2937; padding:8px 10px; border-radius:6px; color:#e5e7eb; font-size:12px;">
                <div style="font-weight:700; color:#93c5fd; margin-bottom:2px;">AI Verdict</div>
                <div style="font-weight:600;">${verdict}</div>
            </div>
            <div style="background:#111827; border:1px solid #1f2937; padding:8px 10px; border-radius:6px; color:#e5e7eb; font-size:12px;">
                <div style="font-weight:700; color:#93c5fd; margin-bottom:2px;">Confidence</div>
                <div style="font-weight:600;">${confidence}%</div>
            </div>
        </div>
    `;
}

function setupAstroDrawer(data) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;
    
    let drawer = document.getElementById("astroDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "astroDrawer";
        drawer.innerHTML = `
            <div id="astroDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#1a0a2e; border:1px solid #3d2963; border-radius:6px; cursor:pointer;">
                <div style="background:#0a0514; border:1px solid #3d2963; color:#c084fc; padding:4px 8px; border-radius:4px; font-weight:600;">🌙 Astrological Market Analysis</div>
                <div id="astroDrawerStatus" style="color:#9ca3af; font-size:12px;">Tap to expand</div>
                <button id="astroCyclesToggle" style="margin-left:auto; background:#1a1a2e; border:1px solid #3d2963; color:#6b7280; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:600; margin-right:4px;">⚪ Cycles: OFF</button>
                <button id="astroIndicatorsToggle" style="background:#1a1a2e; border:1px solid #3d2963; color:#7dd3fc; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:600;">🌙 Indicators: ON</button>
            </div>
            <div id="astroDrawerBody" style="display:none; padding:10px; background:#0a0514; border:1px solid #3d2963; border-radius:6px; margin-top:6px;"></div>
        `;
        container.appendChild(drawer);
        
        const header = drawer.querySelector("#astroDrawerHeader");
        const bodyClickHandler = (e) => {
            // Prevent toggle if clicking the cycles button
            if (e.target.id === "astroCyclesToggle") return;
            const body = drawer.querySelector("#astroDrawerBody");
            const status = drawer.querySelector("#astroDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        };
        header.addEventListener("click", bodyClickHandler);
        
        // Add astro cycles toggle button listener
        const cyclesToggle = drawer.querySelector("#astroCyclesToggle");
        cyclesToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            astroCyclesVisible = !astroCyclesVisible;
            cyclesToggle.textContent = astroCyclesVisible ? "🌙 Cycles: ON" : "⚪ Cycles: OFF";
            cyclesToggle.style.color = astroCyclesVisible ? "#c084fc" : "#6b7280";
            cyclesToggle.style.background = astroCyclesVisible ? "#2d1b4e" : "#1a1a2e";
            console.log("🌙 Astro cycles toggled:", astroCyclesVisible ? "ON" : "OFF");
            draw();  // Redraw chart immediately
        });
        
        // Add astro indicators toggle button listener
        const indicatorsToggle = drawer.querySelector("#astroIndicatorsToggle");
        indicatorsToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            astroIndicatorsVisible = !astroIndicatorsVisible;
            indicatorsToggle.textContent = astroIndicatorsVisible ? "🌙 Indicators: ON" : "⚫ Indicators: OFF";
            indicatorsToggle.style.color = astroIndicatorsVisible ? "#7dd3fc" : "#6b7280";
            indicatorsToggle.style.background = astroIndicatorsVisible ? "#1a3d3d" : "#1a1a2e";
            console.log("✨ Astro indicators toggled:", astroIndicatorsVisible ? "ON" : "OFF");
            draw();  // Redraw chart immediately
        });
    }
    
    const body = drawer.querySelector("#astroDrawerBody");
    if (!body) return;
    
    // Build Astro analysis HTML
    let html = '';
    
    // Trading Outlook
    if (data.astro_outlook) {
        const outlook = data.astro_outlook;
        const outlookColor = outlook.outlook === "BULLISH" ? "#10b981" : outlook.outlook === "BEARISH" ? "#ef4444" : "#6b7280";
        const volColor = outlook.volatility === "HIGH" ? "#ef4444" : outlook.volatility === "MODERATE" ? "#f59e0b" : "#10b981";
        
        html += `<div style="margin-bottom:12px; padding:10px; background:#1a1a2e; border-left:3px solid ${outlookColor}; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:${outlookColor}; margin-bottom:6px; font-size:14px;">🔮 Overall Trading Outlook: ${outlook.outlook}</div>`;
        html += `<div style="color:#cbd5e1; font-size:12px; margin-bottom:4px;">Confidence: <span style="color:#60a5fa;">${outlook.confidence}%</span> | Volatility: <span style="color:${volColor};">${outlook.volatility}</span></div>`;
        html += `<div style="display:flex; gap:12px; margin-top:6px;">`;
        html += `  <div style="color:#10b981;">Bullish Score: ${outlook.bullish_score}</div>`;
        html += `  <div style="color:#ef4444;">Bearish Score: ${outlook.bearish_score}</div>`;
        html += `</div>`;
        html += `</div>`;
    }
    
    // Moon Phase
    if (data.moon_phase) {
        const moon = data.moon_phase;
        const moonIcon = moon.phase.includes("Full") ? "🌕" : moon.phase.includes("New") ? "🌑" : moon.phase.includes("Waxing") ? "🌒" : "🌘";
        
        html += `<div style="margin-bottom:12px; padding:8px; background:#0f1419; border-left:3px solid #60a5fa; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#60a5fa; margin-bottom:4px;">${moonIcon} Moon Phase: ${moon.phase}</div>`;
        html += `<div style="color:#94a3b8; font-size:11px;">${moon.market_impact}</div>`;
        html += `<div style="margin-top:4px; background:#1c2532; height:6px; border-radius:3px; overflow:hidden;">`;
        html += `  <div style="background:#60a5fa; width:${moon.percentage}%; height:100%;"></div>`;
        html += `</div>`;
        html += `</div>`;
    }
    
    // Active Aspects
    if (data.astro_aspects && data.astro_aspects.length > 0) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#1e1430; border-left:3px solid #c084fc; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#c084fc; margin-bottom:6px;">✨ Active Planetary Aspects</div>`;
        
        data.astro_aspects.slice(0, 5).forEach(aspect => {
            const aspectColor = aspect.aspect === "square" || aspect.aspect === "opposition" ? "#f87171" :
                               aspect.aspect === "trine" || aspect.aspect === "sextile" ? "#34d399" : "#fbbf24";
            const aspectIcon = aspect.aspect === "square" ? "■" : aspect.aspect === "trine" ? "△" : 
                              aspect.aspect === "opposition" ? "○" : aspect.aspect === "sextile" ? "⬡" : "☆";
            
            // Format date and time helper function
            const formatDateTime = (isoString) => {
                if (!isoString) return "N/A";
                try {
                    const date = new Date(isoString);
                    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
                    return { date: dateStr, time: timeStr };
                } catch (e) {
                    return { date: "N/A", time: "N/A" };
                }
            };
            
            html += `<div style="margin-bottom:6px; padding:6px; background:#0a0514; border-radius:3px;">`;
            html += `  <div style="color:${aspectColor}; font-size:12px; margin-bottom:2px;">`;
            html += `    ${aspectIcon} ${aspect.planet1}-${aspect.planet2} <strong>${aspect.aspect.toUpperCase()}</strong> (${aspect.angle.toFixed(1)}°)`;
            html += `  </div>`;
            html += `  <div style="color:#94a3b8; font-size:10px;">${aspect.interpretation}</div>`;
            html += `  <div style="color:#6b7280; font-size:9px; margin-top:2px;">Influence: ${(aspect.market_influence * 100).toFixed(0)}% | Orb: ${aspect.orb.toFixed(2)}°</div>`;
            
            // Add timing information if available
            if (aspect.start_date && aspect.end_date) {
                const startDT = formatDateTime(aspect.start_date);
                const endDT = formatDateTime(aspect.end_date);
                const exactDT = aspect.exact_date ? formatDateTime(aspect.exact_date) : null;
                
                html += `  <div style="color:#8b5cf6; font-size:9px; margin-top:4px; padding:4px; background:#1a0f2e; border-radius:2px;">`;
                html += `    📅 <strong>Active Period:</strong> ${startDT.date}`;
                if (exactDT && aspect.is_exact) {
                    html += ` <span style="color:#fbbf24;">(⚡ Exact Now)</span>`;
                } else if (exactDT && aspect.is_applying) {
                    html += ` <span style="color:#60a5fa;">(→ Building)</span>`;
                }
                html += `    <br/>⏰ <strong>From:</strong> ${startDT.time} <strong>→ To:</strong> ${endDT.time}`;
                if (exactDT) {
                    html += ` | <strong>Peak:</strong> ${exactDT.time}`;
                }
                html += `  </div>`;
            }
            html += `</div>`;
        });
        html += `</div>`;
    }
    
    // Mercury Retrograde Warning
    if (data.mercury_retrograde) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#2d1b1b; border-left:3px solid #f59e0b; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#f59e0b; margin-bottom:4px;">⚠️ Mercury Retrograde Active</div>`;
        html += `<div style="color:#d1d5db; font-size:11px;">Expect: Communication delays, data errors, false signals, reversals</div>`;
        html += `<div style="color:#94a3b8; font-size:10px; margin-top:4px;"><em>Trade with caution - double-check all entries</em></div>`;
        html += `</div>`;
    }
    
    // Usage Guide
    html += `<div style="padding:8px; background:#0d1117; border:1px solid #30363d; border-radius:4px; font-size:11px; color:#8b949e;">`;
    html += `<div style="font-weight:600; color:#58a6ff; margin-bottom:4px;">💡 How to Use Astro Analysis:</div>`;
    html += `<ul style="margin:4px 0 0 16px; padding:0; line-height:1.5;">`;
    html += `<li><strong>Bullish Aspects:</strong> Trine (△) and Sextile (⬡) - support upward moves</li>`;
    html += `<li><strong>Bearish Aspects:</strong> Square (■) and Opposition (○) - create tension, volatility</li>`;
    html += `<li><strong>Full Moon:</strong> Peak volatility - expect major moves, reversals</li>`;
    html += `<li><strong>Mercury Retrograde:</strong> Review, delays - avoid new positions, use tight stops</li>`;
    html += `<li><strong>High Influence:</strong> 70%+ aspects have strongest market impact</li>`;
    html += `</ul>`;
    html += `</div>`;
    
    body.innerHTML = html;
}

function setupGannDrawer(data) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;
    
    let drawer = document.getElementById("gannDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "gannDrawer";
        drawer.innerHTML = `
            <div id="gannDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#1a0f2e; border:1px solid #2d1b4e; border-radius:6px; cursor:pointer;">
                <div style="background:#0f0920; border:1px solid #2d1b4e; color:#a78bfa; padding:4px 8px; border-radius:4px; font-weight:600;">📐 Gann Harmonic Analysis</div>
                <div id="gannDrawerStatus" style="color:#9ca3af; font-size:12px;">Tap to expand</div>
                <button id="gannCyclesToggle" style="margin-left:auto; background:#1a1a2e; border:1px solid #3d2963; color:#6b7280; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:600; margin-right:4px;">⚪ Cycles: OFF</button>
                <button id="gannLevelsToggle" style="background:#1a1a2e; border:1px solid #3d2963; color:#90ee90; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:600;">🟢 Levels: ON</button>
            </div>
            <div id="gannDrawerBody" style="display:none; padding:10px; background:#0f0920; border:1px solid #2d1b4e; border-radius:6px; margin-top:6px;"></div>
        `;
        container.appendChild(drawer);
        
        const header = drawer.querySelector("#gannDrawerHeader");
        const bodyClickHandler = (e) => {
            // Prevent toggle if clicking the cycles button
            if (e.target.id === "gannCyclesToggle") return;
            const body = drawer.querySelector("#gannDrawerBody");
            const status = drawer.querySelector("#gannDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        };
        header.addEventListener("click", bodyClickHandler);
        
        // Add cycles toggle button listener
        const cyclesToggle = drawer.querySelector("#gannCyclesToggle");
        cyclesToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            gannCyclesVisible = !gannCyclesVisible;
            cyclesToggle.textContent = gannCyclesVisible ? "🔵 Cycles: ON" : "⚪ Cycles: OFF";
            cyclesToggle.style.color = gannCyclesVisible ? "#c084fc" : "#6b7280";
            cyclesToggle.style.background = gannCyclesVisible ? "#2d1b4e" : "#1a1a2e";
            console.log("🔄 Gann cycles toggled:", gannCyclesVisible ? "ON" : "OFF");
            draw();  // Redraw chart immediately
        });
        
        // Add levels toggle button listener
        const levelsToggle = drawer.querySelector("#gannLevelsToggle");
        levelsToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            gannLevelsVisible = !gannLevelsVisible;
            levelsToggle.textContent = gannLevelsVisible ? "🟢 Levels: ON" : "⚫ Levels: OFF";
            levelsToggle.style.color = gannLevelsVisible ? "#90ee90" : "#6b7280";
            levelsToggle.style.background = gannLevelsVisible ? "#1a3d1a" : "#1a1a2e";
            console.log("📏 Gann levels toggled:", gannLevelsVisible ? "ON" : "OFF");
            draw();  // Redraw chart immediately
        });
    }
    
    const body = drawer.querySelector("#gannDrawerBody");
    if (!body) return;
    
    // Build Gann analysis HTML
    let html = '';
    
    // Cardinal Cross (Most Important Levels)
    if (data.gann_cardinal_cross && data.gann_cardinal_cross.length > 0) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#1a0f2e; border-left:3px solid #ef4444; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#ef4444; margin-bottom:6px;">🎯 Cardinal Cross (Critical Levels)</div>`;
        data.gann_cardinal_cross.forEach(level => {
            const color = level.strength === "CRITICAL" ? "#ef4444" : "#fbbf24";
            const icon = level.strength === "CRITICAL" ? "🔴" : "🟡";
            html += `<div style="color:${color}; font-size:12px; margin-bottom:3px;">${icon} ${level.angle}° → $${level.price.toFixed(2)} <span style="color:#94a3b8;">(${level.strength})</span></div>`;
        });
        html += `</div>`;
    }
    
    // Price Clusters (Confluence Zones)
    if (data.gann_clusters && data.gann_clusters.length > 0) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#0a2818; border-left:3px solid #10b981; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#10b981; margin-bottom:6px;">⚡ Price Clusters (Confluence)</div>`;
        data.gann_clusters.slice(0, 5).forEach(cluster => {
            const color = cluster.strength === "VERY STRONG" ? "#10b981" : "#3b82f6";
            html += `<div style="color:${color}; font-size:12px; margin-bottom:3px;">⚡ $${cluster.price.toFixed(2)} <span style="color:#94a3b8;">(${cluster.confluence} levels converge - ${cluster.strength})</span></div>`;
        });
        html += `</div>`;
    }
    
    // Square of 9
    if (data.gann_square_of_9) {
        const sq9 = data.gann_square_of_9;
        html += `<div style="margin-bottom:12px; padding:8px; background:#1e1b3e; border-left:3px solid #a78bfa; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#a78bfa; margin-bottom:6px;">🌀 Square of 9 Spiral</div>`;
        html += `<div style="color:#cbd5e1; font-size:11px; margin-bottom:4px;">Base: $${sq9.base?.toFixed(2) || 'N/A'}</div>`;
        if (sq9.resistances && sq9.resistances.length > 0) {
            html += `<div style="color:#f87171; font-size:11px;">↑ Resistances: ${sq9.resistances.slice(0, 4).map(r => '$' + r.toFixed(2)).join(', ')}</div>`;
        }
        if (sq9.supports && sq9.supports.length > 0) {
            html += `<div style="color:#34d399; font-size:11px;">↓ Supports: ${sq9.supports.slice(0, 4).map(s => '$' + s.toFixed(2)).join(', ')}</div>`;
        }
        html += `</div>`;
    }
    
    // Gann Angles
    if (data.gann_angles) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#1a1a2e; border-left:3px solid #60a5fa; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#60a5fa; margin-bottom:6px;">📊 Gann Angles (10 bars projection)</div>`;
        const angles = data.gann_angles;
        const key_angles = ["1x1", "2x1", "1x2"];
        key_angles.forEach(angle_name => {
            if (angles[angle_name]) {
                const angle = angles[angle_name];
                html += `<div style="color:#cbd5e1; font-size:11px; margin-bottom:2px;">${angle_name} (${angle.slope}x): ↑$${angle.uptrend?.toFixed(2)} / ↓$${angle.downtrend?.toFixed(2)}</div>`;
            }
        });
        html += `</div>`;
    }
    
    // Gann Cycle Timing (Before/After Inflections)
    if (window.gannData && window.gannData.gann_cycles && window.gannData.gann_cycles.length > 0) {
        html += `<div style="margin-bottom:12px; padding:8px; background:#1b0f1f; border-left:3px solid #c084fc; border-radius:4px;">`;
        html += `<div style="font-weight:600; color:#c084fc; margin-bottom:6px;">⏳ Cycle Inflection Points</div>`;
        
        window.gannData.gann_cycles.forEach(cycle => {
            let cycleColor = "#60a5fa";
            let cycleEmoji = "🔵";
            
            if (cycle.cycle_type.includes("90-bar")) {
                cycleColor = "#3b82f6";
                cycleEmoji = "🔵";
            } else if (cycle.cycle_type.includes("45-bar")) {
                cycleColor = "#10b981";
                cycleEmoji = "🟢";
            } else if (cycle.cycle_type.includes("180-bar")) {
                cycleColor = "#ef4444";
                cycleEmoji = "🔴";
            }
            
            const statusText = cycle.is_active 
                ? `<span style="color:#10b981;">✓ ACTIVE</span> - Cycle completed, watch for reversal signal`
                : `<span style="color:#fbbf24;">⏳ UPCOMING</span> - ${cycle.bars_until || '?'} bars until inflection`;
            
            const strength = cycle.strength === "CRITICAL" ? "CRITICAL ⚠️" : "MAJOR";
            
            html += `<div style="margin-bottom:8px; padding:6px; background:#0a0514; border-radius:3px; border-left:2px solid ${cycleColor};">`;
            html += `  <div style="color:${cycleColor}; font-weight:600; font-size:12px; margin-bottom:2px;">`;
            html += `    ${cycleEmoji} ${cycle.cycle_type} (${strength})`;
            html += `  </div>`;
            html += `  <div style="color:#94a3b8; font-size:11px;">`;
            html += `    ${statusText}`;
            html += `  </div>`;
            html += `</div>`;
        });
        
        html += `<div style="margin-top:6px; padding:6px; background:#0a0514; border:1px solid #3d2963; border-radius:3px; font-size:10px; color:#94a3b8;">`;
        html += `<strong style="color:#c084fc;">📌 Cycle Strategy:</strong> Before inflection: accumulate bias conviction. At inflection: expect volatility spike and potential reversal. After inflection: confirm new direction with price action.`;
        html += `</div>`;
        html += `</div>`;
    }
    
    // Usage Guide
    html += `<div style="padding:8px; background:#0d1117; border:1px solid #30363d; border-radius:4px; font-size:11px; color:#8b949e;">`;
    html += `<div style="font-weight:600; color:#58a6ff; margin-bottom:4px;">💡 How to Use Gann Levels:</div>`;
    html += `<ul style="margin:4px 0 0 16px; padding:0; line-height:1.5;">`;
    html += `<li><strong>Cardinal Cross (Red/Yellow):</strong> Major reversal points - watch for price reactions</li>`;
    html += `<li><strong>Price Clusters (Green/Blue):</strong> High probability zones where multiple levels converge</li>`;
    html += `<li><strong>Square of 9:</strong> Natural support/resistance from price spiral geometry</li>`;
    html += `<li><strong>1x1 Angle (45°):</strong> Most important - price above = bullish, below = bearish</li>`;
    html += `<li><strong>Cycle Inflections (🔵🟢🔴):</strong> Vertical dashed lines on chart mark 45/90/180-bar cycle completions</li>`;
    html += `</ul>`;
    html += `</div>`;
    
    body.innerHTML = html;
}

function setupIcebergDrawer(zones, bars) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;

    let drawer = document.getElementById("icebergDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "icebergDrawer";
        drawer.innerHTML = `
            <div id="icebergDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#0b1220; border:1px solid #1f2937; border-radius:6px; cursor:pointer;">
                <div style="background:#111827; border:1px solid #1f2937; color:#fbbf24; padding:4px 8px; border-radius:4px; font-weight:600;">🧊 Iceberg Orderflow</div>
                <div id="icebergDrawerStatus" style="color:#9ca3af; font-size:12px;">Tap to expand</div>
                <div style="margin-left:auto; color:#9ca3af; font-size:12px;">[toggle]</div>
            </div>
            <div id="icebergDrawerBody" style="display:none; padding:10px; background:#0b0f14; border:1px solid #1f2937; border-radius:6px; margin-top:6px;"></div>
        `;
        container.appendChild(drawer);

        const header = drawer.querySelector("#icebergDrawerHeader");
        header.addEventListener("click", () => {
            const body = drawer.querySelector("#icebergDrawerBody");
            const status = drawer.querySelector("#icebergDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        });
    }

    const body = drawer.querySelector("#icebergDrawerBody");
    if (!zones || zones.length === 0) {
        body.innerHTML = `<div style="color:#9ca3af; padding:10px; font-size:12px;">No iceberg activity detected. Institutional orders are not currently present at key price levels.</div>`;
        return;
    }

    // Build the table HTML with enhanced data including time and narrative
    const orderflowData = zones.map((zone, idx) => {
        const nearbyBars = bars.filter(b => b.low <= zone.price_bottom && b.high >= zone.price_top);
        const avgVol = nearbyBars.length > 0 
            ? Math.round(nearbyBars.reduce((sum, b) => sum + b.volume, 0) / nearbyBars.length)
            : Math.round(zone.volume);

        const buyVol = nearbyBars.filter(b => b.close > zone.price_bottom).reduce((sum, b) => sum + b.volume, 0);
        const sellVol = nearbyBars.filter(b => b.close < zone.price_bottom).reduce((sum, b) => sum + b.volume, 0);
        
        // Get time from first nearby bar
        const barTime = nearbyBars.length > 0
            ? (nearbyBars[0].timestamp || nearbyBars[0].time)
            : null;
        const timeStr = barTime
            ? new Date(barTime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
            : 'N/A';

        return {
            price: zone.price_bottom.toFixed(2),
            buy: Math.round(buyVol / (nearbyBars.length || 1)),
            sell: Math.round(sellVol / (nearbyBars.length || 1)),
            delta: Math.round(buyVol - sellVol),
            absorption: true,
            bias: buyVol > sellVol ? "BUY" : "SELL",
            time: timeStr,
            volume: Math.round(zone.volume),
            strength: zone.volume > 100000 ? "STRONG" : zone.volume > 50000 ? "MODERATE" : "WEAK"
        };
    });

    // Build narrative story
    let narrative = `<div style="margin-bottom:12px; padding:8px; background:#1a0f2e; border-left:3px solid #fbbf24; border-radius:4px;">`;
    narrative += `<div style="font-weight:600; color:#fbbf24; margin-bottom:6px; font-size:13px;">📖 Iceberg Story</div>`;
    
    const totalIcebergVol = orderflowData.reduce((sum, row) => sum + row.volume, 0);
    const strongZones = orderflowData.filter(r => r.strength === "STRONG").length;
    const buyZones = orderflowData.filter(r => r.bias === "BUY").length;
    const sellZones = orderflowData.filter(r => r.bias === "SELL").length;
    
    narrative += `<div style="color:#cbd5e1; font-size:12px; line-height:1.6; margin-bottom:6px;">`;
    narrative += `💡 <strong>${orderflowData.length} institutional orderflow zones detected</strong> with total volume of <span style="color:#fbbf24;">${(totalIcebergVol / 1000000).toFixed(1)}M</span>. `;
    narrative += `<strong style="color:#10b981;">${buyZones} buying pressure zones</strong> vs `;
    narrative += `<strong style="color:#ef4444;">${sellZones} selling pressure zones</strong>. `;
    narrative += `<strong>${strongZones} zones showing STRONG conviction</strong> (>100K volume).`;
    narrative += `</div>`;
    
    narrative += `<div style="color:#94a3b8; font-size:11px; margin-bottom:4px;">`;
    narrative += `🎯 <strong>Price Creation Zones:</strong> Icebergs are creating support/resistance at <span style="color:#fde047;">$${orderflowData.map(r => r.price).join(', $')}</span>. `;
    narrative += `Market will likely defend these levels or reverse sharply if they break.`;
    narrative += `</div>`;
    
    narrative += `<div style="color:#94a3b8; font-size:11px; margin-bottom:4px;">`;
    narrative += `⚡ <strong>Implied Intent:</strong> Institutions are currently ${buyZones > sellZones ? '<span style="color:#10b981;">ACCUMULATING</span>' : '<span style="color:#ef4444;">DISTRIBUTING</span>'}. `;
    narrative += `Watch for breakouts above strongest buy zones or breakdowns below strongest sell zones.`;
    narrative += `</div>`;
    
    const latestBarTime = bars && bars.length > 0
        ? (bars[bars.length - 1].timestamp || bars[bars.length - 1].time)
        : null;
    const detectionClock = latestBarTime
        ? new Date(latestBarTime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
        : new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    narrative += `<div style="color:#6b7280; font-size:10px; font-style:italic;">`;
    narrative += `📍 Detection Time: ${detectionClock}`;
    narrative += `</div>`;
    narrative += `</div>`;

    // Remove the mentor-embedded table; point users to the floating panel instead
    const cta = `
        <div style="margin-top:8px; padding:10px; background:#0b1220; border:1px dashed #fbbf24; border-radius:6px; color:#e5e7eb; font-size:12px;">
            <div style="font-weight:600; color:#fbbf24; margin-bottom:4px;">🧊 Orderflow Table Moved</div>
            <div>Use the toolbar button <strong>🧊 OF</strong> to open the floating orderflow panel. Drag it anywhere; close with ✕.</div>
        </div>
    `;

    body.innerHTML = narrative + cta;
    body.style.display = "block"; // Keep iceberg narrative visible
    drawer.querySelector("#icebergDrawerStatus").textContent = "Collapse";
}

function setupNewsDrawer(data) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;

    let drawer = document.getElementById("newsDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "newsDrawer";
        drawer.innerHTML = `
            <div id="newsDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#0f1319; border:1px solid #243040; border-radius:6px; cursor:pointer;">
                <div style="background:#0a1018; border:1px solid #243040; color:#38bdf8; padding:4px 8px; border-radius:4px; font-weight:600;">📰 News & Events</div>
                <div id="newsDrawerStatus" style="color:#9ca3af; font-size:12px;">Tap to expand</div>
                <div style="margin-left:auto; color:#9ca3af; font-size:12px;">[toggle]</div>
            </div>
            <div id="newsDrawerBody" style="display:none; padding:10px; background:#0b0f14; border:1px solid #243040; border-radius:6px; margin-top:6px;"></div>
        `;
        container.appendChild(drawer);

        const header = drawer.querySelector("#newsDrawerHeader");
        header.addEventListener("click", () => {
            const body = drawer.querySelector("#newsDrawerBody");
            const status = drawer.querySelector("#newsDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        });
    }

    const body = drawer.querySelector("#newsDrawerBody");
    const events = Array.isArray(data.news_events) ? data.news_events : [];
    const upcoming = data.upcoming_events_count || events.length || 0;
    const majorNews = Array.isArray(data.major_news) ? data.major_news : [];
    const newsMemory = data.news_memory || {};

    const formatDateTime = (ts, withSeconds = false) => {
        if (!ts) return "--";
        const d = new Date(ts);
        return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: withSeconds ? '2-digit' : undefined, hour12: true });
    };

    const calendarBlock = () => {
        if (!events.length) {
            return `<div style="color:#9ca3af; padding:8px; font-size:12px;">No high-impact events queued. Monitor calendar for fresh catalysts.</div>`;
        }
        const rows = events.slice(0, 5).map(ev => {
            const importanceColor = ev.importance === "HIGH" ? "#ef4444" : ev.importance === "MEDIUM" ? "#f59e0b" : "#94a3b8";
            const impact = ev.impact_xauusd || ev.sentiment || "";
            return `
                <div style="display:flex; gap:8px; align-items:center; padding:6px 0; border-bottom:1px solid #1f2937;">
                    <div style="width:68px; color:#9ca3af; font-size:11px;">${formatDateTime(ev.time_utc || ev.time)}</div>
                    <div style="flex:1; color:#e5e7eb; font-size:12px;">${ev.event_name || ev.title || 'Event'}</div>
                    <div style="color:${importanceColor}; font-size:11px; font-weight:600; min-width:70px; text-align:right;">${ev.importance || 'LOW'}</div>
                    <div style="color:#38bdf8; font-size:11px; min-width:48px; text-align:right;">${ev.country || ''}</div>
                    <div style="color:#fbbf24; font-size:11px; min-width:90px; text-align:right;">${impact}</div>
                </div>`;
        }).join("");
        return `<div style="color:#cbd5e1; font-size:12px; margin-bottom:6px;">${upcoming} upcoming catalyst${upcoming === 1 ? '' : 's'} tracked.</div><div>${rows}</div>`;
    };

    const newsSummaryBlock = () => {
        if (!majorNews.length) {
            return `<div style="color:#9ca3af; font-size:12px; padding:8px; border:1px solid #1f2937; border-radius:4px;">No headline-grade XAUUSD news yet. Stay nimble for surprise releases.</div>`;
        }
        return majorNews.slice(0, 3).map(n => {
            const bias = n.sentiment || n.bias || "NEUTRAL";
            const biasColor = bias.includes("BULL") ? "#10b981" : bias.includes("BEAR") ? "#ef4444" : "#cbd5e1";
            const summary = n.summary || n.impact || "";
            const when = formatDateTime(n.time_utc || n.time, true);
            return `
                <div style="padding:8px; border:1px solid #1f2937; border-radius:4px; margin-bottom:6px; background:#0f141a;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#e5e7eb; font-weight:600;">${n.headline || n.title || 'News'}</span>
                        <span style="color:#9ca3af; font-size:11px;">${when}</span>
                    </div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">${summary}</div>
                    <div style="color:${biasColor}; font-size:11px; margin-top:4px;">XAUUSD Bias: ${bias}</div>
                </div>`;
        }).join("");
    };

    const newsMemoryBlock = () => {
        const keys = Object.keys(newsMemory || {});
        if (!keys.length) {
            return `<div style="color:#9ca3af; font-size:11px; font-style:italic;">News memory not initialized yet.</div>`;
        }
        return keys.slice(0, 4).map(k => {
            const mem = newsMemory[k] || {};
            const adj = mem.confidence_adjustment || 0;
            const total = mem.total_events || 0;
            return `<div style="color:#cbd5e1; font-size:11px;">${k}: events ${total}, adj ${adj.toFixed ? adj.toFixed(2) : adj}</div>`;
        }).join("");
    };

    const formatTime = (val) => {
        if (!val) return "--";
        const ts = typeof val === "string" ? val : val?.time_utc || val?.time;
        if (!ts) return "--";
        return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    };

    const rows = events.slice(0, 4).map(ev => {
        const importanceColor = ev.importance === "HIGH" ? "#ef4444" : ev.importance === "MEDIUM" ? "#f59e0b" : "#94a3b8";
        return `
            <div style="display:flex; gap:8px; align-items:center; padding:6px 0; border-bottom:1px solid #1f2937;">
                <div style="width:68px; color:#9ca3af; font-size:11px;">${formatTime(ev.time_utc || ev.time)}</div>
                <div style="flex:1; color:#e5e7eb; font-size:12px;">${ev.event_name || ev.title || 'Event'}</div>
                <div style="color:${importanceColor}; font-size:11px; font-weight:600; min-width:70px; text-align:right;">${ev.importance || 'LOW'}</div>
                <div style="color:#38bdf8; font-size:11px; min-width:48px; text-align:right;">${ev.country || ''}</div>
            </div>`;
    }).join("");

    body.innerHTML = `
        ${calendarBlock()}
        <div style="margin-top:10px; color:#e5e7eb; font-weight:600;">Major XAUUSD News</div>
        ${newsSummaryBlock()}
        <div style="margin-top:8px; color:#9ca3af; font-size:11px;">News Memory</div>
        ${newsMemoryBlock()}
    `;
}

function setupGlobalMarketsDrawer(data) {
    const container = document.getElementById("drawerContainer");
    if (!container) return;

    let drawer = document.getElementById("globalDrawer");
    if (!drawer) {
        drawer = document.createElement("div");
        drawer.id = "globalDrawer";
        drawer.innerHTML = `
            <div id="globalDrawerHeader" style="display:flex; align-items:center; gap:8px; padding:8px; background:#0f172a; border:1px solid #243b53; border-radius:6px; cursor:pointer;">
                <div style="background:#0b1224; border:1px solid #243b53; color:#60a5fa; padding:4px 8px; border-radius:4px; font-weight:600;">🌐 Global Markets</div>
                <div id="globalDrawerStatus" style="color:#9ca3af; font-size:12px;">Tap to expand</div>
                <div style="margin-left:auto; color:#9ca3af; font-size:12px;">[toggle]</div>
            </div>
            <div id="globalDrawerBody" style="display:none; padding:10px; background:#0b1220; border:1px solid #243b53; border-radius:6px; margin-top:6px;"></div>
        `;
        container.appendChild(drawer);

        const header = drawer.querySelector("#globalDrawerHeader");
        header.addEventListener("click", () => {
            const body = drawer.querySelector("#globalDrawerBody");
            const status = drawer.querySelector("#globalDrawerStatus");
            const isOpen = body.style.display === "block";
            body.style.display = isOpen ? "none" : "block";
            status.textContent = isOpen ? "Tap to expand" : "Collapse";
        });
    }

    const body = drawer.querySelector("#globalDrawerBody");

    const session = data.session || "N/A";
    const volRatio = data.risk_assessment?.volume_ratio || data.volume_ratio || 1.0;
    const gm = data.global_markets || {};
    const globalContext = gm.context || gm.narrative || "";

    // Build comprehensive market narrative
    const buildNarrative = () => {
        if (globalContext) {
            return globalContext; // Use backend-provided narrative if available
        }

        // Generate contextual narrative based on available data
        const riskSentiment = volRatio > 1.5 
            ? "risk-off pressure dominating with elevated volatility driving defensive flows into gold" 
            : volRatio < 0.9 
            ? "risk-on sentiment prevailing as equities rally and investors rotate out of safe havens" 
            : "balanced market conditions with no clear directional bias from macro flows";

        const sessionContext = session === "LONDON" 
            ? "European morning trade saw mixed flows across asset classes"
            : session === "NY"
            ? "US session bringing fresh momentum from Wall Street participation"
            : session === "ASIA"
            ? "Asian markets set the tone with overnight positioning shifts"
            : "Current session showing typical interbank flows";

        const icebergImpact = data.iceberg_activity?.detected
            ? `Institutional accumulation detected around $${(data.iceberg_activity.price_from || 0).toFixed(2)}-$${(data.iceberg_activity.price_to || 0).toFixed(2)}, suggesting smart money positioning for upcoming moves.`
            : "No significant institutional absorption zones detected, indicating cleaner price discovery.";

        const xauusdImplication = volRatio > 1.5
            ? "XAUUSD benefits from safe-haven demand, likely defending support levels and targeting higher ranges if risk-off persists."
            : volRatio < 0.9
            ? "XAUUSD faces headwinds as capital flows to risk assets; watch for breaks below key support if USD strength compounds the pressure."
            : "XAUUSD trading within established ranges; waiting for catalyst from either DXY movement or geopolitical developments.";

        return `
            <div style="margin-bottom:8px; color:#cbd5e1; font-size:13px; line-height:1.6;">
                ${sessionContext}. Global macro backdrop shows ${riskSentiment}. 
                ${icebergImpact}
            </div>
            <div style="margin-bottom:8px; color:#94a3b8; font-size:12px; line-height:1.6;">
                <strong style="color:#60a5fa;">Equities Context:</strong> Major indices ${volRatio > 1.5 ? 'under pressure with broad-based selling' : volRatio < 0.9 ? 'pushing higher on optimism' : 'consolidating recent moves'}, 
                influencing cross-asset correlations. 
                <strong style="color:#38bdf8;">FX Dynamics:</strong> Dollar ${volRatio > 1.5 ? 'strengthening on safe-haven demand' : volRatio < 0.9 ? 'weakening as risk appetite returns' : 'ranging with no clear breakout'}, 
                creating ${volRatio > 1.5 ? 'upward' : volRatio < 0.9 ? 'downward' : 'neutral'} pressure on dollar-denominated commodities.
            </div>
            <div style="padding:8px; background:#1a0f2e; border-left:3px solid #fbbf24; border-radius:4px;">
                <div style="color:#fbbf24; font-weight:600; margin-bottom:4px; font-size:12px;">📊 XAUUSD Implication</div>
                <div style="color:#cbd5e1; font-size:12px; line-height:1.5;">${xauusdImplication}</div>
            </div>
        `;
    };

    body.innerHTML = buildNarrative();
}

function renderIcebergOrderflow(zones, bars) {
    const zoneCount = Array.isArray(zones) ? zones.length : 0;
    const barCount = Array.isArray(bars) ? bars.length : 0;
    console.log(`🧊 renderIcebergOrderflow CALLED - ${zoneCount} zones, ${barCount} bars, visible=${orderflowVisible}`);

    const panel = document.getElementById("orderflowFloating");
    const tableDiv = document.getElementById("orderflowTableFloating");
    const toggleBtn = document.getElementById("orderflowToggle");

    if (!panel || !tableDiv) {
        console.warn("⚠️ Orderflow floating panel nodes missing");
        return;
    }

    if (zoneCount === 0) {
        console.log("⚠️ No iceberg zones to display");
        tableDiv.innerHTML = `<div style="padding:12px; font-size:12px; color:#9ca3af;">No iceberg activity detected.</div>`;
        panel.style.display = orderflowVisible ? "block" : "none";
        if (toggleBtn) toggleBtn.classList.toggle("active", orderflowVisible);
        return;
    }
    
    const safeBars = Array.isArray(bars) ? bars : [];
    // Build orderflow data from zones
    const orderflowData = zones.map((zone, idx) => {
        const nearbyBars = safeBars.filter(b => b.low <= zone.price_bottom && b.high >= zone.price_top);
        const buyVol = nearbyBars.filter(b => b.close > zone.price_bottom).reduce((sum, b) => sum + b.volume, 0);
        const sellVol = nearbyBars.filter(b => b.close < zone.price_bottom).reduce((sum, b) => sum + b.volume, 0);
        
        // Get timestamp from most recent bar
        let timestamp = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            hour12: true 
        });
        let sortableTime = new Date();
        
        if (nearbyBars.length > 0) {
            const lastBar = nearbyBars[nearbyBars.length - 1];
            if (lastBar.timestamp) {
                const barTime = new Date(lastBar.timestamp);
                sortableTime = barTime;
                timestamp = barTime.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit',
                    hour12: true 
                });
            }
        }
        
        const row = {
            price: zone.price_bottom.toFixed(2),
            buy: Math.round(buyVol / (nearbyBars.length || 1)),
            sell: Math.round(sellVol / (nearbyBars.length || 1)),
            delta: Math.round(buyVol - sellVol),
            absorption: true,
            bias: buyVol > sellVol ? "BUY" : "SELL",
            time: timestamp,
            sortTime: sortableTime.getTime()  // Add sortable timestamp
        };
        console.log(`  Zone ${idx}: $${row.price} - Buy:${row.buy} Sell:${row.sell} Delta:${row.delta} Bias:${row.bias} Time:${row.time}`);
        return row;
    });
    
    // Sort by time DESCENDING (most recent first)
    orderflowData.sort((a, b) => b.sortTime - a.sortTime);
    
    console.log("📊 Built orderflow data (sorted by time DESC):", orderflowData);
    
    // Render table into floating panel
    const tableHTML = `
        <table>
            <tr>
                <th>Time</th>
                <th>Price</th>
                <th>Buy</th>
                <th>Sell</th>
                <th>Δ</th>
                <th>Status</th>
                <th>Bias</th>
            </tr>
            ${orderflowData.map(row => `
                <tr class="iceberg">
                    <td style="color:#60a5fa; font-size:11px;"><strong>${row.time}</strong></td>
                    <td><strong>$${row.price}</strong></td>
                    <td style="color:#3fb950">${row.buy.toLocaleString()}</td>
                    <td style="color:#f85149">${row.sell.toLocaleString()}</td>
                    <td style="color:${row.delta >= 0 ? '#3fb950' : '#f85149'}">${row.delta > 0 ? '+' : ''}${row.delta.toLocaleString()}</td>
                    <td>🧊 Zone</td>
                    <td><strong>${row.bias}</strong></td>
                </tr>
            `).join("")}
        </table>
    `;
    
    tableDiv.innerHTML = tableHTML;
    panel.style.display = orderflowVisible ? "block" : "none";
    if (toggleBtn) toggleBtn.classList.toggle("active", orderflowVisible);
    console.log("✅ Orderflow table rendered in floating panel");
}

function toggleOrderflowVisibility(forceState) {
    const nextState = typeof forceState === "boolean" ? forceState : !orderflowVisible;
    orderflowVisible = nextState;
    renderIcebergOrderflow(icebergZones, ohlcBars);
}

// ===== RAW ORDERS TABLE RENDERING (NEW) =====

function renderRawOrders(orders) {
    console.log("🔄 renderRawOrders called with", orders ? orders.length : 0, "orders");
    
    const panel = document.getElementById("rawOrdersFloating");
    const tableDiv = document.getElementById("rawOrdersTable");
    const toggleBtn = document.getElementById("rawOrdersBtn");
    
    if (!panel || !tableDiv) {
        console.warn("⚠️ Raw orders panel or tableDiv not found!");
        return;
    }
    
    // If no orders or visibility is off, just hide the panel but allow rendering when toggled back on
    if (!orders || orders.length === 0) {
        console.log("⚠️ No orders to display or visibility is off");
        panel.style.display = "none";
        if (toggleBtn) toggleBtn.classList.toggle("active", false);
        return;
    }
    
    console.log("✅ Rendering", orders.length, "raw orders");
    
    // Sort orders by timestamp (oldest first for proper cumulative balance)
    const sortedOrders = [...orders].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeA - timeB;  // Oldest first
    });
    
    // Calculate cumulative balance (running total of buy - sell)
    let runningBalance = 0;
    const ordersWithBalance = sortedOrders.map(order => {
        const size = parseInt(order.size);
        const side = order.side.toUpperCase();
        
        // Add to balance: BUY is positive, SELL is negative
        if (side === 'BUY') {
            runningBalance += size;
        } else if (side === 'SELL') {
            runningBalance -= size;
        }
        
        return {
            ...order,
            balance: runningBalance
        };
    });
    
    // Reverse for display (most recent first)
    const displayOrders = ordersWithBalance.reverse();
    
    // Ensure AI prediction container exists at top of table div (outside of innerHTML updates)
    let predictionContainer = document.getElementById("predictionPanelAI");
    if (!predictionContainer) {
        predictionContainer = document.createElement("div");
        predictionContainer.id = "predictionPanelAI";
        predictionContainer.style.cssText = `
            padding: 4px 8px;
            background: #1f2937;
            border-bottom: 1px solid #30363d;
            margin-bottom: 4px;
            border-radius: 3px;
            position: sticky;
            top: 0;
            z-index: 100;
        `;
        predictionContainer.innerHTML = '<div style="font-size:9px; color:#8b949e; text-align:center;">🔄 Fetching...</div>';
        // Insert at the very beginning of tableDiv
        tableDiv.insertBefore(predictionContainer, tableDiv.firstChild);
    }
    
    // Create table (without prediction - it's separate now)
    let tableHTML = `
        <table style="width:100%; font-size:10px; border-collapse:collapse;">
            <tr style="background:#1f2937; border-bottom:1px solid #374151; position:sticky; top:0;">
                <th style="padding:4px; text-align:left; color:#9ca3af;">Time</th>
                <th style="padding:4px; text-align:right; color:#9ca3af;">Price</th>
                <th style="padding:4px; text-align:right; color:#9ca3af;">Size</th>
                <th style="padding:4px; text-align:center; color:#9ca3af;">Side</th>
                <th style="padding:4px; text-align:right; color:#9ca3af;">Balance</th>
                <th style="padding:4px; text-align:right; color:#9ca3af;">$Volume</th>
            </tr>
    `;
    
    // Add order rows
    for (let i = 0; i < Math.min(displayOrders.length, 30); i++) {
        const order = displayOrders[i];
        
        // Parse timestamp and convert to Indian Standard Time (IST, UTC+5:30)
        let timeStr = "";
        try {
            const dt = new Date(order.timestamp);
            // Convert to IST (Asia/Kolkata timezone)
            timeStr = dt.toLocaleTimeString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit', 
                hour12: false 
            });
        } catch {
            timeStr = "N/A";
        }
        
        const price = parseFloat(order.price).toFixed(2);
        const size = parseInt(order.size);
        const side = order.side.toUpperCase();
        const volume = (parseFloat(order.price) * parseInt(order.size)).toFixed(0);
        const balance = order.balance;
        
        // Color by side
        const sideColor = side === 'BUY' ? '#3fb950' : '#f85149';
        const sideSymbol = side === 'BUY' ? '⬆️' : '⬇️';
        
        // Color balance based on value (green if positive, red if negative)
        const balanceColor = balance > 0 ? '#3fb950' : balance < 0 ? '#f85149' : '#9ca3af';
        const balanceSymbol = balance > 0 ? '+' : '';
        
        tableHTML += `
            <tr style="border-bottom:1px solid #374151; background:${i % 2 === 0 ? '#111827' : '#0f172a'};">
                <td style="padding:4px; color:#60a5fa; font-size:9px;"><strong>${timeStr}</strong></td>
                <td style="padding:4px; text-align:right; color:#fff;">$${price}</td>
                <td style="padding:4px; text-align:right; color:#d1d5db;">${size}</td>
                <td style="padding:4px; text-align:center; color:${sideColor}; font-weight:bold;">${sideSymbol} ${side}</td>
                <td style="padding:4px; text-align:right; color:${balanceColor}; font-weight:bold;">${balanceSymbol}${balance}</td>
                <td style="padding:4px; text-align:right; color:#fbbf24;">$${volume}</td>
            </tr>
        `;
    }
    
    tableHTML += `</table>`;
    
    // Find or create wrapper for just the table (not prediction)
    let tableWrapper = document.getElementById("rawOrdersTableWrapper");
    if (!tableWrapper) {
        tableWrapper = document.createElement("div");
        tableWrapper.id = "rawOrdersTableWrapper";
        tableDiv.appendChild(tableWrapper);
    }
    
    // Update only the table wrapper, not the entire tableDiv (preserves prediction container)
    tableWrapper.innerHTML = tableHTML;
    
    // Always display panel when there's data and rawOrdersVisible is true
    const shouldDisplay = rawOrdersVisible && orders.length > 0;
    panel.style.display = shouldDisplay ? "block" : "none";
    if (toggleBtn) toggleBtn.classList.toggle("active", shouldDisplay);
    console.log(`✅ Raw orders table rendered: ${orders.length} orders | Display: ${shouldDisplay ? 'VISIBLE' : 'HIDDEN'}`);
}

// ==================== 5-MINUTE CANDLE PREDICTION WITH AI & MEMORY ====================

let last5MinPrediction = null;

// Make panel draggable
function makeDraggable(element) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    element.onmousedown = dragMouseDown;
    
    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
        element.style.cursor = 'grabbing';
    }
    
    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        element.style.top = (element.offsetTop - pos2) + "px";
        element.style.left = (element.offsetLeft - pos1) + "px";
        element.style.right = 'auto'; // Remove right positioning when dragging
    }
    
    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
        element.style.cursor = 'move';
    }
}

async function fetch5MinCanclePrediction() {
    // Fetch AI-powered 5-minute candle prediction from backend
    try {
        console.log("🔄 Fetching 5-min prediction from:", `${API_BASE}/api/v1/candle/5min/predict`);
        
        const predictionRes = await fetch(`${API_BASE}/api/v1/candle/5min/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!predictionRes.ok) {
            console.warn("⚠️ Could not fetch 5-min prediction:", predictionRes.status, predictionRes.statusText);
            return null;
        }
        
        const predictionData = await predictionRes.json();
        console.log("✅ Prediction data received:", predictionData);
        
        last5MinPrediction = predictionData.prediction;
        
        console.log(`🎯 5-Min Prediction: ${predictionData.prediction.prediction} | Confidence: ${predictionData.prediction.confidence}%`);
        
        return predictionData.prediction;
    } catch (error) {
        console.error("❌ 5-min prediction error:", error);
        return null;
    }
}

function render5MinPredictionPanel(prediction) {
    // Render the 5-minute prediction panel with AI insights and memory patterns
    if (!prediction) {
        console.warn("⚠️ No prediction data to render");
        return;
    }
    
    console.log("🎨 Rendering prediction panel...");
    
    // Find the prediction container inside raw orders table
    let predictionContainer = document.getElementById("predictionPanelAI");
    
    // If container doesn't exist, create it (fallback for when raw orders panel is closed)
    if (!predictionContainer) {
        console.warn("⚠️ Prediction container not found - creating draggable panel");
        predictionContainer = document.createElement("div");
        predictionContainer.id = "predictionPanelAI";
        predictionContainer.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            width: auto;
            min-width: 400px;
            background: #0d1117;
            border: 2px solid #30363d;
            border-radius: 8px;
            padding: 8px;
            font-family: 'Monaco', monospace;
            font-size: 11px;
            color: #c9d1d9;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            z-index: 1001;
            cursor: move;
        `;
        
        // Make it draggable
        makeDraggable(predictionContainer);
        
        document.body.appendChild(predictionContainer);
    }
    
    console.log("✅ Prediction container found/created");
    
    // Extract with safety checks for undefined properties
    const { icon = '⚪', color = '#9ca3af', prediction: predDir = 'UNKNOWN', confidence = 0, order_flow = {}, volume_dynamics = {}, ai_analysis = {}, pattern_memory = {}, reasoning = '' } = prediction;
    
    // Ensure nested properties exist with defaults
    const safeOrderFlow = {
        total_orders: order_flow.total_orders || 0,
        buy_volume: order_flow.buy_volume || 0,
        sell_volume: order_flow.sell_volume || 0,
        buy_ratio: typeof order_flow.buy_ratio === 'number' ? order_flow.buy_ratio : 0,
        sell_ratio: typeof order_flow.sell_ratio === 'number' ? order_flow.sell_ratio : 0,
        balance: order_flow.balance || 0
    };
    
    const safeVolumeDynamics = {
        momentum: volume_dynamics.momentum || 'UNKNOWN',
        acceleration: typeof volume_dynamics.acceleration === 'number' ? volume_dynamics.acceleration : 0
    };
    
    const safeAiAnalysis = {
        decision: ai_analysis.decision || 'ANALYZING',
        regime: ai_analysis.regime || 'UNKNOWN'
    };
    
    const safePatternMemory = {
        similar_patterns: pattern_memory.similar_patterns || 0,
        historical_accuracy: pattern_memory.historical_accuracy || 'N/A'
    };
    
    // Calculate usage percentage and status
    const usagePercent = ((databentoUsage.dataConsumed / databentoUsage.planLimit) * 100).toFixed(1);
    const usageColor = usagePercent < 70 ? '#3fb950' : usagePercent < 90 ? '#d29922' : '#f85149';
    const daysUntilReset = Math.ceil((databentoUsage.resetDate - new Date()) / (1000 * 60 * 60 * 24));
    
    // Update the standalone Databento usage panel
    updateDatabentoUsagePanel();
    
    // Build COMPACT prediction panel HTML (single line to save space)
    const predictionHTML = `
        <div style="display: flex; align-items: center; gap: 6px; padding: 6px; background: #0d1117; border-radius: 4px; position: relative;">
            <div style="position: absolute; top: 2px; right: 4px; color: #6e7681; font-size: 10px; cursor: move;">⋮⋮</div>
            <span style="font-size: 16px;">${icon}</span>
            <div style="flex: 1; display: flex; align-items: center; gap: 10px; font-size: 9px;">
                <div style="font-weight: bold; color: ${color}; font-size: 10px;">
                    NEXT CANDLE: ${predDir}
                </div>
                <div style="color: #6e7681;">|</div>
                <div style="color: #6e7681;">
                    Confidence: <span style="color: ${color};">${confidence}%</span>
                </div>
                <div style="color: #6e7681;">|</div>
                <div>
                    <span style="color: #3fb950;">↑${safeOrderFlow.buy_volume}</span>
                    <span style="color: #6e7681;">/</span>
                    <span style="color: #f85149;">↓${safeOrderFlow.sell_volume}</span>
                </div>
                <div style="color: #6e7681;">|</div>
                <div style="color: ${safeOrderFlow.balance >= 0 ? '#3fb950' : '#f85149'};">
                    Bal: ${safeOrderFlow.balance > 0 ? '+' : ''}${safeOrderFlow.balance}
                </div>
                <div style="color: #6e7681;">|</div>
                <div style="color: #58a6ff;">
                    🤖 ${safeAiAnalysis.decision}
                </div>
                ${safePatternMemory.similar_patterns > 0 ? `
                <div style="color: #6e7681;">|</div>
                <div style="color: #a371f7;">
                    🧠 ${safePatternMemory.similar_patterns} patterns
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    predictionContainer.innerHTML = predictionHTML;
    predictionContainer.style.display = "block";
    console.log("✅ Prediction panel rendered:", predDir, confidence + "%");
}

// Update standalone Databento usage panel
function updateDatabentoUsagePanel() {
    const callCountEl = document.getElementById('databentoCallCount');
    const dataUsedEl = document.getElementById('databentoDataUsed');
    const dataLimitEl = document.getElementById('databentoDataLimit');
    const progressBarEl = document.getElementById('databentoProgressBar');
    const percentEl = document.getElementById('databentoUsagePercent');
    const resetDaysEl = document.getElementById('databentoResetDays');
    
    if (!callCountEl || !dataUsedEl || !progressBarEl || !percentEl) return;
    
    const usagePercent = ((databentoUsage.dataConsumed / databentoUsage.planLimit) * 100);
    const usageColor = usagePercent < 70 ? '#3fb950' : usagePercent < 90 ? '#d29922' : '#f85149';
    const daysUntilReset = Math.ceil((databentoUsage.resetDate - new Date()) / (1000 * 60 * 60 * 24));
    
    // Update values
    callCountEl.textContent = databentoUsage.apiCalls.toLocaleString();
    dataUsedEl.textContent = databentoUsage.dataConsumed.toFixed(2) + ' MB';
    dataUsedEl.style.color = usageColor;
    dataLimitEl.textContent = databentoUsage.planLimit + ' MB';
    
    // Update progress bar
    progressBarEl.style.width = Math.min(usagePercent, 100) + '%';
    progressBarEl.style.background = usageColor;
    
    // Update percentage
    percentEl.textContent = usagePercent.toFixed(1) + '%';
    percentEl.style.color = usageColor;
    
    // Update reset days
    if (resetDaysEl) {
        resetDaysEl.textContent = daysUntilReset;
    }
}

// Update Databento usage from API response headers
function updateDatabentoUsage(response) {
    try {
        // Check for usage headers from backend
        const apiCalls = response.headers?.get('X-Databento-Calls');
        const dataUsed = response.headers?.get('X-Databento-Data-MB');
        
        if (apiCalls) {
            databentoUsage.apiCalls = parseInt(apiCalls);
        }
        if (dataUsed) {
            databentoUsage.dataConsumed = parseFloat(dataUsed);
        }
        
        // Increment call counter locally (fallback if no headers)
        if (!apiCalls) {
            databentoUsage.apiCalls++;
        }
        
        // Estimate data size (fallback): ~0.001 MB per API call
        if (!dataUsed) {
            databentoUsage.dataConsumed += 0.001;
        }
        
        // Store in localStorage for persistence
        localStorage.setItem('databentoUsage', JSON.stringify(databentoUsage));
        
    } catch (e) {
        console.warn('Failed to update Databento usage:', e);
    }
}

// Load usage from localStorage on startup
function loadDatabentoUsage() {
    try {
        const stored = localStorage.getItem('databentoUsage');
        if (stored) {
            const parsed = JSON.parse(stored);
            // Check if reset date has passed
            const resetDate = new Date(parsed.resetDate);
            if (new Date() >= resetDate) {
                // Reset usage for new month
                databentoUsage.apiCalls = 0;
                databentoUsage.dataConsumed = 0;
                databentoUsage.resetDate = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1);
            } else {
                databentoUsage = parsed;
                databentoUsage.resetDate = resetDate; // Convert back to Date object
            }
        }
    } catch (e) {
        console.warn('Failed to load Databento usage:', e);
    }
}

// Initialize usage tracking
loadDatabentoUsage();
updateDatabentoUsagePanel(); // Update UI immediately

function toggleRawOrdersVisibility(forceState) {
    const nextState = typeof forceState === "boolean" ? forceState : !rawOrdersVisible;
    rawOrdersVisible = nextState;
    renderRawOrders(rawOrders);
}

function startOrderflowDrag(e) {
    const panel = document.getElementById("orderflowFloating");
    const layout = document.getElementById("layout");
    if (!panel || !layout) return;

    const panelRect = panel.getBoundingClientRect();
    const layoutRect = layout.getBoundingClientRect();
    isDraggingOrderflow = true;
    orderflowDragOffset = {
        x: e.clientX - panelRect.left,
        y: e.clientY - panelRect.top
    };
    panel.style.right = "auto";
    panel.style.left = `${panelRect.left - layoutRect.left}px`;
    panel.style.top = `${panelRect.top - layoutRect.top}px`;
    document.addEventListener("mousemove", handleOrderflowDrag);
    document.addEventListener("mouseup", stopOrderflowDrag);
}

function handleOrderflowDrag(e) {
    if (!isDraggingOrderflow) return;
    const panel = document.getElementById("orderflowFloating");
    const layout = document.getElementById("layout");
    if (!panel || !layout) return;

    const layoutRect = layout.getBoundingClientRect();
    let nextLeft = e.clientX - orderflowDragOffset.x - layoutRect.left;
    let nextTop = e.clientY - orderflowDragOffset.y - layoutRect.top;

    nextLeft = Math.max(0, Math.min(layoutRect.width - panel.offsetWidth, nextLeft));
    nextTop = Math.max(0, Math.min(layoutRect.height - panel.offsetHeight, nextTop));

    panel.style.left = `${nextLeft}px`;
    panel.style.top = `${nextTop}px`;
}

function stopOrderflowDrag() {
    isDraggingOrderflow = false;
    document.removeEventListener("mousemove", handleOrderflowDrag);
    document.removeEventListener("mouseup", stopOrderflowDrag);
}

let drawScheduled = false;
function requestDraw() {
    if (drawScheduled) return;
    drawScheduled = true;
    requestAnimationFrame(() => {
        drawScheduled = false;
        draw();
    });
}

// TradingView-style loading animation
let loaderAnimationFrame = 0;
let loaderPrice = 5312.50; // Starting price for animation
let loaderPriceDirection = 1;

function drawTradingViewLoader(ctx, width, height, theme) {
    loaderAnimationFrame++;
    
    // Animated shimmer effect time
    const shimmerPhase = (loaderAnimationFrame % 120) / 120;
    
    // Animate price ticker
    if (loaderAnimationFrame % 10 === 0) {
        loaderPrice += (Math.random() - 0.5) * 2 * loaderPriceDirection;
        if (Math.random() > 0.95) loaderPriceDirection *= -1; // Change direction occasionally
    }
    
    // Background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, theme.background);
    gradient.addColorStop(1, theme.gridBg);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Chart area dimensions
    const chartLeft = 30;
    const chartRight = width - 90;
    const chartTop = 60;
    const chartBottom = height - 170;
    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;
    
    // ===== ANIMATED PRICE TICKER (TOP LEFT) =====
    ctx.save();
    
    // Pulsing glow effect
    const pulseAlpha = 0.3 + Math.sin(shimmerPhase * Math.PI * 2) * 0.2;
    ctx.shadowBlur = 20;
    ctx.shadowColor = `rgba(96, 165, 250, ${pulseAlpha})`;
    
    // Ticker background
    ctx.fillStyle = 'rgba(13, 17, 23, 0.95)';
    ctx.fillRect(15, 15, 180, 50);
    ctx.strokeStyle = 'rgba(96, 165, 250, 0.5)';
    ctx.lineWidth = 2;
    ctx.strokeRect(15, 15, 180, 50);
    
    ctx.shadowBlur = 0;
    
    // Animated price
    ctx.fillStyle = '#60a5fa';
    ctx.font = "bold 20px 'Courier New', monospace";
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(`$${loaderPrice.toFixed(2)}`, 25, 22);
    
    // "LIVE" indicator with pulse
    const liveAlpha = 0.6 + Math.sin(shimmerPhase * Math.PI * 4) * 0.4;
    ctx.fillStyle = `rgba(34, 197, 94, ${liveAlpha})`;
    ctx.font = "bold 10px 'Segoe UI', Arial";
    ctx.fillText('● LOADING LIVE DATA', 25, 48);
    
    ctx.restore();
    
    // ===== SKELETON CHART WITH SHIMMER =====
    ctx.save();
    
    // Grid lines (static)
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = chartTop + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();
    }
    
    // Vertical grid
    for (let i = 0; i < 10; i++) {
        const x = chartLeft + (chartWidth / 10) * i;
        ctx.beginPath();
        ctx.moveTo(x, chartTop);
        ctx.lineTo(x, chartBottom);
        ctx.stroke();
    }
    
    // ===== ANIMATED SKELETON CANDLES WITH SHIMMER =====
    const candleCount = 40;
    const candleSpacing = chartWidth / candleCount;
    const candleWidth = candleSpacing * 0.6;
    
    for (let i = 0; i < candleCount; i++) {
        const x = chartLeft + candleSpacing * i + candleSpacing / 2;
        
        // Create shimmer wave effect
        const shimmerOffset = Math.sin((shimmerPhase * Math.PI * 2) + (i * 0.2)) * 0.5 + 0.5;
        const baseAlpha = 0.15 + shimmerOffset * 0.15;
        
        // Random candle heights for skeleton
        const candleHeight = 20 + Math.sin(i * 0.5 + loaderAnimationFrame * 0.05) * 40;
        const candleTop = chartTop + chartHeight / 2 - candleHeight / 2;
        
        // Draw skeleton candle body with shimmer
        ctx.fillStyle = `rgba(96, 165, 250, ${baseAlpha})`;
        ctx.fillRect(x - candleWidth / 2, candleTop, candleWidth, candleHeight);
        
        // Wick
        const wickHeight = candleHeight * 1.5;
        const wickTop = chartTop + chartHeight / 2 - wickHeight / 2;
        ctx.strokeStyle = `rgba(96, 165, 250, ${baseAlpha * 0.7})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, wickTop);
        ctx.lineTo(x, wickTop + wickHeight);
        ctx.stroke();
    }
    
    // ===== ANIMATED WAVE LINE (PRICE MOVEMENT) =====
    ctx.strokeStyle = 'rgba(96, 165, 250, 0.4)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    for (let i = 0; i <= candleCount; i++) {
        const x = chartLeft + (chartWidth / candleCount) * i;
        const waveY = chartTop + chartHeight / 2 + 
                     Math.sin((i * 0.3) + (shimmerPhase * Math.PI * 4)) * 30;
        
        if (i === 0) {
            ctx.moveTo(x, waveY);
        } else {
            ctx.lineTo(x, waveY);
        }
    }
    ctx.stroke();
    
    // ===== SHIMMER GRADIENT OVERLAY =====
    const shimmerX = chartLeft + (chartWidth * shimmerPhase) - 100;
    const shimmerGradient = ctx.createLinearGradient(shimmerX, 0, shimmerX + 200, 0);
    shimmerGradient.addColorStop(0, 'rgba(96, 165, 250, 0)');
    shimmerGradient.addColorStop(0.5, 'rgba(96, 165, 250, 0.15)');
    shimmerGradient.addColorStop(1, 'rgba(96, 165, 250, 0)');
    
    ctx.fillStyle = shimmerGradient;
    ctx.fillRect(chartLeft, chartTop, chartWidth, chartHeight);
    
    // ===== PRICE AXIS SKELETON =====
    ctx.fillStyle = 'rgba(96, 165, 250, 0.1)';
    ctx.fillRect(chartRight, chartTop, 90, chartHeight);
    
    // Price labels skeleton
    for (let i = 0; i <= 8; i++) {
        const y = chartTop + (chartHeight / 8) * i;
        const labelAlpha = 0.1 + Math.sin(shimmerPhase * Math.PI * 2 + i * 0.5) * 0.05;
        ctx.fillStyle = `rgba(96, 165, 250, ${labelAlpha})`;
        ctx.fillRect(chartRight + 5, y - 6, 70, 12);
    }
    
    // ===== TIME AXIS SKELETON =====
    ctx.fillStyle = 'rgba(96, 165, 250, 0.1)';
    ctx.fillRect(chartLeft, chartBottom + 10, chartWidth, 30);
    
    // Time labels skeleton
    for (let i = 0; i < 8; i++) {
        const x = chartLeft + (chartWidth / 8) * i;
        const labelAlpha = 0.1 + Math.sin(shimmerPhase * Math.PI * 2 + i * 0.7) * 0.05;
        ctx.fillStyle = `rgba(96, 165, 250, ${labelAlpha})`;
        ctx.fillRect(x - 20, chartBottom + 15, 50, 12);
    }
    
    // ===== LOADING TEXT WITH ANIMATED DOTS =====
    const dots = '.'.repeat((Math.floor(shimmerPhase * 3) % 3) + 1);
    ctx.fillStyle = 'rgba(96, 165, 250, 0.8)';
    ctx.font = "14px 'Segoe UI', Arial";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`Loading market data${dots}`, width / 2, height / 2);
    
    // ===== PROGRESS INDICATOR =====
    const progressWidth = 300;
    const progressHeight = 4;
    const progressX = (width - progressWidth) / 2;
    const progressY = height / 2 + 30;
    
    // Progress background
    ctx.fillStyle = 'rgba(96, 165, 250, 0.2)';
    ctx.fillRect(progressX, progressY, progressWidth, progressHeight);
    
    // Animated progress bar
    const progressFill = shimmerPhase * progressWidth;
    ctx.fillStyle = 'rgba(96, 165, 250, 0.8)';
    ctx.fillRect(progressX, progressY, progressFill, progressHeight);
    
    ctx.restore();
    
    // Continue animation
    requestAnimationFrame(() => {
        if (!ohlcBars || ohlcBars.length === 0) {
            draw(); // Keep animating until data loads
        }
    });
}

function draw() {
    try {
        console.log("🎨 Draw called - ohlcBars length:", ohlcBars?.length || 0);
        
        const theme = isDarkTheme ? THEMES.dark : THEMES.light;
        const dpr = window.devicePixelRatio || 1;
        const logicalWidth = canvas.width / dpr;
        const logicalHeight = canvas.height / dpr;
        
        ctx.clearRect(0, 0, logicalWidth, logicalHeight);
        ctx.fillStyle = theme.background;
        ctx.fillRect(0, 0, logicalWidth, logicalHeight);

        if (!ohlcBars || ohlcBars.length === 0) {
            console.warn("⚠️ No OHLC data to render");
            drawTradingViewLoader(ctx, logicalWidth, logicalHeight, theme);
            return;
        }
        
        // Show zoom level indicator if not at 100%
        if (zoomLevel !== 1.0) {
            ctx.save();
            ctx.fillStyle = 'rgba(96, 165, 250, 0.15)';
            ctx.fillRect(logicalWidth - 100, 10, 85, 24);
            ctx.strokeStyle = 'rgba(96, 165, 250, 0.4)';
            ctx.lineWidth = 1;
            ctx.strokeRect(logicalWidth - 100, 10, 85, 24);
            ctx.fillStyle = '#60a5fa';
            ctx.font = "11px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(`🔍 ${Math.round(zoomLevel * 100)}%`, logicalWidth - 95, 22);
            ctx.restore();
        }
        
        // Show timeframe indicator (top-left area after zoom)
        ctx.save();
        ctx.fillStyle = 'rgba(100, 150, 255, 0.15)';
        ctx.fillRect(logicalWidth - 200, 10, 95, 24);
        ctx.strokeStyle = 'rgba(100, 150, 255, 0.4)';
        ctx.lineWidth = 1;
        ctx.strokeRect(logicalWidth - 200, 10, 95, 24);
        ctx.fillStyle = '#64B6FF';
        ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`⏱️ ${currentTimeframe.toUpperCase()}`, logicalWidth - 152, 22);
        ctx.restore();
        
        // Show vertical pan indicator when dragging price scale
        if (isPanning && Math.abs(tempPricePan) > 0.1) {
            ctx.save();
            ctx.fillStyle = 'rgba(234, 179, 8, 0.2)';
            ctx.fillRect(logicalWidth - 95, 10, 85, 24);
            ctx.strokeStyle = 'rgba(234, 179, 8, 0.5)';
            ctx.lineWidth = 1;
            ctx.strokeRect(logicalWidth - 95, 10, 85, 24);
            ctx.fillStyle = '#eab308';
            ctx.font = "bold 10px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const panDirection = tempPricePan > 0 ? '⬆' : '⬇';
            ctx.fillText(`${panDirection} ${Math.abs(tempPricePan).toFixed(1)}`, logicalWidth - 52, 22);
            ctx.restore();
        }
        
        console.log("✅ Drawing", ohlcBars.length, "candles");

        // Chart dimensions (TradingView style with right price scale + volume below)
        const chartLeft = 30;
        const chartRight = logicalWidth - 90; // Space for right price scale
        const chartTop = 50;
        const chartBottom = logicalHeight - 170;  // Reserve space for volume area + time axis
        const chartWidth = chartRight - chartLeft;
        const chartHeight = chartBottom - chartTop;
        const volumeHeight = 60;

        // Calculate price range with forced padding for flat data
        const prices = ohlcBars.map(b => [b.high, b.low]).flat();
        const priceMax = Math.max(...prices);
        const priceMin = Math.min(...prices);
        let priceRange = priceMax - priceMin;
        
        // Force minimum padding even if price is flat
        if (priceRange < 1) {
            priceRange = priceMax > 0 ? priceMax * 0.1 : 10;
        }
        const pricePadding = priceRange * 0.15;

        // Apply pan offsets (vertical) and cache metrics for drag math
        const panBarOffset = barPan + tempBarPan;
        const clampedPanBar = Math.max(-ohlcBars.length, Math.min(ohlcBars.length, panBarOffset));
        const panPriceOffset = pricePan + tempPricePan;
        
        let adjustedMax, adjustedMin;
        
        // Use locked scale if enabled, otherwise auto-scale
        // IMPORTANT: Pan offset ALWAYS applies (moves both candles and scale together)
        if (priceScaleLocked && lockedPriceMin !== null && lockedPriceMax !== null) {
            // Locked mode: Use fixed range but allow vertical dragging
            adjustedMin = lockedPriceMin + panPriceOffset;
            adjustedMax = lockedPriceMax + panPriceOffset;
        } else {
            // Auto-scale mode: Fit data range + pan offset
            adjustedMax = priceMax + pricePadding + panPriceOffset;
            adjustedMin = priceMin - pricePadding + panPriceOffset;
            
            // Store current range when locking is activated (without pan offset)
            if (priceScaleLocked && (lockedPriceMin === null || lockedPriceMax === null)) {
                lockedPriceMin = priceMin - pricePadding;
                lockedPriceMax = priceMax + pricePadding;
            }
        }
        lastChartHeight = chartBottom - chartTop;
        lastPriceRange = adjustedMax - adjustedMin;

        // Price to Y conversion helper (shared across overlays)
        const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;

        lastChartState = {
            chartLeft,
            chartRight,
            chartTop,
            chartBottom,
            chartHeight,
            adjustedMin,
            adjustedMax,
            clampedPanBar
        };

    // ========== DRAW BACKGROUND GRID ==========
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 1;

    // Horizontal grid lines (using adjusted price range for alignment with labels)
    for (let i = 0; i <= 5; i++) {
        const price = adjustedMin + (adjustedMax - adjustedMin) * (i / 5);
        const y = chartBottom - (i / 5) * chartHeight;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();
    }

    // Calculate candleSpacing early for use throughout draw function
    const candleSpacingForGrid = chartWidth / Math.max(ohlcBars.length, 1);
    lastCandleSpacing = candleSpacingForGrid;
    const timeIntervalForGrid = Math.max(1, Math.floor(ohlcBars.length / 10)); // denser labels

    // Add vertical gridlines for time reference
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 0.5;
    for (let i = 0; i < ohlcBars.length; i += timeIntervalForGrid) {
        const x = chartLeft + (candleSpacingForGrid / 2) + ((i + clampedPanBar) * candleSpacingForGrid);
        if (x < chartLeft - 50 || x > chartRight + 50) continue; // skip offscreen gridlines
        ctx.beginPath();
        ctx.moveTo(x, chartTop);
        ctx.lineTo(x, chartBottom);
        ctx.stroke();
    }

    // ========== DRAW PRICE AXIS (RIGHT) TradingView Style ==========
    // Draw background strip for price axis
    ctx.fillStyle = theme.gridBg;
    ctx.fillRect(chartRight, chartTop, 90, chartHeight);
    
    // Draw price grid labels
    ctx.fillStyle = theme.text;
    ctx.font = "11px 'Segoe UI', Arial, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    
    // TradingView-style price step calculation - OPTIMIZED FOR INTRADAY TRADING
    // Shows continuous integer steps: 501, 502, 503, 504, 505...
    const axisRange = Math.abs(adjustedMax - adjustedMin);
    const targetLabelCount = Math.floor(chartHeight / 35); // More labels for intraday precision
    const rawStep = axisRange / Math.max(targetLabelCount, 8);
    
    let priceStep;
    
    // For intraday trading (typical price range < 1000), FORCE integer steps
    if (adjustedMin > 100) {
        // High-value assets (gold futures, indices): Use clean integer steps
        // Priority order: 1 > 2 > 5 > 10 > 20 > 50 > 100
        const integerSteps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
        
        priceStep = 1; // Default to smallest step for maximum detail
        
        for (let step of integerSteps) {
            const labelCount = axisRange / step;
            // Optimal range: 8-40 labels (dense for intraday, sparse for daily)
            if (labelCount >= 8 && labelCount <= 40) {
                priceStep = step;
                break;
            }
        }
        
        // If range is very small (< 10 points), always use step of 1
        if (axisRange < 10) {
            priceStep = 1;
        }
        
    } else {
        // Low-value assets (stocks < $100): Allow decimal steps
        const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
        const residual = rawStep / magnitude;
        
        if (residual <= 0.5) {
            priceStep = 0.5 * magnitude;
        } else if (residual <= 1.0) {
            priceStep = magnitude;
        } else if (residual <= 2) {
            priceStep = 2 * magnitude;
        } else if (residual <= 5) {
            priceStep = 5 * magnitude;
        } else {
            priceStep = 10 * magnitude;
        }
        
        // Minimum step
        if (priceStep < 0.01) priceStep = 0.01;
    }
    
    // Start from a nice round number (floor for continuous sequence)
    const firstPriceTick = Math.floor(adjustedMin / priceStep) * priceStep;
    
    // Track last drawn Y position to avoid overlapping labels
    let lastDrawnY = -999;
    const minLabelSpacing = 30; // Reduced spacing for more labels (intraday precision)
    
    for (let price = firstPriceTick; price <= adjustedMax; price += priceStep) {
        const y = chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
        
        // Only draw if within bounds and sufficient spacing from previous label
        if (y >= chartTop && y <= chartBottom && Math.abs(y - lastDrawnY) >= minLabelSpacing) {
            // Draw subtle grid line
            ctx.strokeStyle = theme.grid;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(chartRight - 5, y);
            ctx.lineTo(chartRight, y);
            ctx.stroke();
            
            // Draw price label with appropriate decimal places
            ctx.fillStyle = theme.text;
            let priceLabel;
            if (priceStep >= 1) {
                priceLabel = price.toFixed(0);
            } else if (priceStep >= 0.1) {
                priceLabel = price.toFixed(1);
            } else {
                priceLabel = price.toFixed(2);
            }
            ctx.fillText(`$${priceLabel}`, chartRight + 5, y);
            lastDrawnY = y;
        }
    }
    
    // ========== DRAW GANN LEVELS ON CHART ==========
    if (gannLevelsVisible && window.gannData && window.gannData.gann_cardinal_cross) {
        ctx.save();
        
        // Draw cardinal cross levels (most important)
        window.gannData.gann_cardinal_cross.forEach(level => {
            const price = level.price;
            const y = chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
            
            if (y >= chartTop && y <= chartBottom) {
                const isCritical = level.strength === "CRITICAL";
                
                // Draw glow effect
                ctx.shadowBlur = isCritical ? 12 : 8;
                ctx.shadowColor = isCritical ? 'rgba(239, 68, 68, 0.5)' : 'rgba(251, 191, 36, 0.4)';
                
                ctx.strokeStyle = isCritical ? 'rgba(248, 113, 113, 0.85)' : 'rgba(252, 211, 77, 0.7)';
                ctx.lineWidth = isCritical ? 2.5 : 2;
                ctx.setLineDash([10, 5]);
                
                ctx.beginPath();
                ctx.moveTo(chartLeft, y);
                ctx.lineTo(chartRight, y);
                ctx.stroke();
                
                ctx.shadowBlur = 0;
                
                // Label on left side with gradient background
                const labelX = chartLeft - 5;
                const labelW = 36;
                const labelH = 18;
                
                const gradient = ctx.createLinearGradient(labelX - labelW, y - labelH/2, labelX, y + labelH/2);
                if (isCritical) {
                    gradient.addColorStop(0, 'rgba(239, 68, 68, 0.25)');
                    gradient.addColorStop(1, 'rgba(220, 38, 38, 0.4)');
                } else {
                    gradient.addColorStop(0, 'rgba(251, 191, 36, 0.2)');
                    gradient.addColorStop(1, 'rgba(245, 158, 11, 0.35)');
                }
                
                ctx.fillStyle = gradient;
                ctx.fillRect(labelX - labelW, y - labelH/2, labelW, labelH);
                
                ctx.strokeStyle = isCritical ? 'rgba(239, 68, 68, 0.6)' : 'rgba(251, 191, 36, 0.5)';
                ctx.lineWidth = 1.2;
                ctx.strokeRect(labelX - labelW, y - labelH/2, labelW, labelH);
                
                ctx.fillStyle = isCritical ? '#fca5a5' : '#fde047';
                ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                ctx.fillText(`G${level.angle}°`, labelX - 4, y);
            }
        });
        
        // Draw price clusters (confluence zones)
        if (window.gannData.gann_clusters) {
            window.gannData.gann_clusters.slice(0, 5).forEach((cluster, idx) => {
                const price = cluster.price;
                const y = chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
                
                if (y >= chartTop && y <= chartBottom) {
                    const isVeryStrong = cluster.strength === "VERY STRONG";
                    
                    // Glow effect
                    ctx.shadowBlur = isVeryStrong ? 10 : 6;
                    ctx.shadowColor = isVeryStrong ? 'rgba(16, 185, 129, 0.5)' : 'rgba(59, 130, 246, 0.4)';
                    
                    ctx.strokeStyle = isVeryStrong ? 'rgba(34, 211, 238, 0.75)' : 'rgba(96, 165, 250, 0.6)';
                    ctx.lineWidth = isVeryStrong ? 2.2 : 1.8;
                    ctx.setLineDash([6, 3]);
                    
                    ctx.beginPath();
                    ctx.moveTo(chartLeft, y);
                    ctx.lineTo(chartRight, y);
                    ctx.stroke();
                    
                    ctx.shadowBlur = 0;
                    
                    // Draw confluence badge with gradient
                    const badgeX = chartLeft + 5;
                    const badgeY = y - 8;
                    const badgeW = 45;
                    const badgeH = 16;
                    
                    const badgeGrad = ctx.createLinearGradient(badgeX, badgeY, badgeX + badgeW, badgeY + badgeH);
                    if (isVeryStrong) {
                        badgeGrad.addColorStop(0, 'rgba(20, 184, 166, 0.3)');
                        badgeGrad.addColorStop(1, 'rgba(6, 182, 212, 0.4)');
                    } else {
                        badgeGrad.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
                        badgeGrad.addColorStop(1, 'rgba(37, 99, 235, 0.35)');
                    }
                    
                    ctx.fillStyle = badgeGrad;
                    ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
                    
                    ctx.strokeStyle = isVeryStrong ? 'rgba(20, 184, 166, 0.6)' : 'rgba(59, 130, 246, 0.5)';
                    ctx.lineWidth = 1;
                    ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
                    
                    ctx.fillStyle = isVeryStrong ? '#5eead4' : '#93c5fd';
                    ctx.font = "bold 10px 'Segoe UI', Arial, sans-serif";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText(`*${cluster.confluence}`, badgeX + 4, y);
                }
            });
        }
        
        ctx.restore();
        ctx.setLineDash([]);
    }
    
    // ========== ASTRO DATA STORED (No Header Display) ==========
    // Astro data still available for chart rendering if needed
    // Header display removed permanently

    // ========== DRAW VWAP LINE ==========
    if (vwapVisible && vwapValues.length === ohlcBars.length && ohlcBars.length > 1) {
        ctx.save();
        ctx.strokeStyle = '#f5c842';
        ctx.lineWidth = 1.6;
        ctx.setLineDash([6, 3]);

        ctx.beginPath();
        ohlcBars.forEach((bar, i) => {
            const x = chartLeft + (candleSpacingForGrid / 2) + ((i + clampedPanBar) * candleSpacingForGrid);
            const y = toY(vwapValues[i]);
            if (x < chartLeft - 10 || x > chartRight + 10) return; // skip offscreen to reduce draw cost
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
        ctx.setLineDash([]);

        // VWAP label on right
        const lastX = chartRight - 10;
        const lastVWAP = vwapValues[vwapValues.length - 1];
        const lastY = toY(lastVWAP);
        ctx.fillStyle = '#f5c842';
        ctx.font = "10px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(`VWAP ${lastVWAP.toFixed(2)}`, lastX, Math.min(Math.max(lastY, chartTop + 10), chartBottom - 10));
        ctx.restore();
    }

    // ========== DRAW GANN/ASTRO CALL-OUTS ==========
    // Gann price callouts (top-left stack)
    if (window.gannData) {
        let calloutY = chartTop + 72; // below Mercury Rx badge
        if (window.gannData.gann_clusters && window.gannData.gann_clusters.length > 0) {
            const cluster = window.gannData.gann_clusters[0];
            const y = toY(cluster.price);
            if (y >= chartTop && y <= chartBottom) {
                ctx.save();
                
                const boxX = chartLeft + 5;
                const boxY = calloutY - 13;
                const boxW = 160;
                const boxH = 26;
                
                // Gradient background
                const clusterGrad = ctx.createLinearGradient(boxX, boxY, boxX, boxY + boxH);
                clusterGrad.addColorStop(0, 'rgba(20, 184, 166, 0.22)');
                clusterGrad.addColorStop(1, 'rgba(6, 182, 212, 0.28)');
                
                ctx.shadowBlur = 10;
                ctx.shadowColor = 'rgba(20, 184, 166, 0.4)';
                
                ctx.fillStyle = clusterGrad;
                ctx.fillRect(boxX, boxY, boxW, boxH);
                
                ctx.strokeStyle = 'rgba(45, 212, 191, 0.6)';
                ctx.lineWidth = 1.3;
                ctx.strokeRect(boxX, boxY, boxW, boxH);
                
                ctx.shadowBlur = 0;
                
                ctx.fillStyle = '#5eead4';
                ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(`G* Cluster ${cluster.confluence} @ ${cluster.price.toFixed(2)}`, chartLeft + 10, calloutY);

                // Tie line to price level with glow
                ctx.shadowBlur = 6;
                ctx.shadowColor = 'rgba(20, 184, 166, 0.5)';
                ctx.strokeStyle = 'rgba(45, 212, 191, 0.7)';
                ctx.lineWidth = 1.8;
                ctx.setLineDash([5, 3]);
                ctx.beginPath();
                ctx.moveTo(chartLeft + boxW + 5, calloutY);
                ctx.lineTo(chartLeft + boxW + 40, y);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.shadowBlur = 0;
                ctx.restore();
                calloutY += 30;
            }
        }
        if (window.gannData.gann_cardinal_cross && window.gannData.gann_cardinal_cross.length > 0) {
            const critical = window.gannData.gann_cardinal_cross.find(l => l.strength === 'CRITICAL') || window.gannData.gann_cardinal_cross[0];
            const y = toY(critical.price);
            if (y >= chartTop && y <= chartBottom) {
                ctx.save();
                
                const boxX = chartLeft + 5;
                const boxY = calloutY - 13;
                const boxW = 160;
                const boxH = 26;
                
                // Gradient background
                const cardGrad = ctx.createLinearGradient(boxX, boxY, boxX, boxY + boxH);
                cardGrad.addColorStop(0, 'rgba(239, 68, 68, 0.22)');
                cardGrad.addColorStop(1, 'rgba(220, 38, 38, 0.28)');
                
                ctx.shadowBlur = 12;
                ctx.shadowColor = 'rgba(239, 68, 68, 0.5)';
                
                ctx.fillStyle = cardGrad;
                ctx.fillRect(boxX, boxY, boxW, boxH);
                
                ctx.strokeStyle = 'rgba(248, 113, 113, 0.65)';
                ctx.lineWidth = 1.3;
                ctx.strokeRect(boxX, boxY, boxW, boxH);
                
                ctx.shadowBlur = 0;
                
                ctx.fillStyle = '#fca5a5';
                ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(`G${critical.angle}° @ ${critical.price.toFixed(2)}`, chartLeft + 10, calloutY);

                // Tie line with glow
                ctx.shadowBlur = 7;
                ctx.shadowColor = 'rgba(239, 68, 68, 0.6)';
                ctx.strokeStyle = 'rgba(248, 113, 113, 0.75)';
                ctx.lineWidth = 1.8;
                ctx.setLineDash([5, 3]);
                ctx.beginPath();
                ctx.moveTo(chartLeft + boxW + 5, calloutY);
                ctx.lineTo(chartLeft + boxW + 40, y);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.shadowBlur = 0;
                ctx.restore();
            }
        }
    }

    // Astro aspect callout (top-center bar)
    if (astroCyclesVisible && window.astroData && window.astroData.astro_aspects && window.astroData.astro_aspects.length > 0) {
        const topAspect = window.astroData.astro_aspects[0];
        const barX = (chartLeft + chartRight) / 2;
        const barY = chartTop + 44;
        const barW = 280;
        const barH = 28;
        const isBearishAspect = ['square', 'opposition'].includes(topAspect.aspect);

        ctx.save();
        
        // Gradient background
        const aspectGrad = ctx.createLinearGradient(barX - barW/2, barY - barH/2, barX + barW/2, barY + barH/2);
        if (isBearishAspect) {
            aspectGrad.addColorStop(0, 'rgba(239, 68, 68, 0.18)');
            aspectGrad.addColorStop(0.5, 'rgba(220, 38, 38, 0.22)');
            aspectGrad.addColorStop(1, 'rgba(185, 28, 28, 0.18)');
        } else {
            aspectGrad.addColorStop(0, 'rgba(16, 185, 129, 0.18)');
            aspectGrad.addColorStop(0.5, 'rgba(5, 150, 105, 0.22)');
            aspectGrad.addColorStop(1, 'rgba(4, 120, 87, 0.18)');
        }
        
        ctx.shadowBlur = isBearishAspect ? 11 : 10;
        ctx.shadowColor = isBearishAspect ? 'rgba(239, 68, 68, 0.5)' : 'rgba(16, 185, 129, 0.4)';
        
        ctx.fillStyle = aspectGrad;
        ctx.fillRect(barX - barW / 2, barY - barH / 2, barW, barH);
        
        ctx.strokeStyle = isBearishAspect ? 'rgba(248, 113, 113, 0.6)' : 'rgba(45, 212, 191, 0.6)';
        ctx.lineWidth = 1.4;
        ctx.strokeRect(barX - barW / 2, barY - barH / 2, barW, barH);
        
        ctx.shadowBlur = 0;
        
        ctx.fillStyle = isBearishAspect ? '#fca5a5' : '#5eead4';
        ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${topAspect.planet1}-${topAspect.planet2} ${topAspect.aspect.toUpperCase()} (${topAspect.angle.toFixed(1)}°)`, barX, barY);
        ctx.restore();
    }

    // Draw current price label on right (TradingView style)
    if (ohlcBars.length > 0) {
        const lastCandle = ohlcBars[ohlcBars.length - 1];
        const currentPrice = lastCandle.close;
        const currentPriceY = chartBottom - ((currentPrice - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
        
        // Price line across chart
        ctx.strokeStyle = "rgba(33, 150, 243, 0.5)";
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(chartLeft, currentPriceY);
        ctx.lineTo(chartRight, currentPriceY);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Price badge on right
        const priceText = currentPrice.toFixed(2);
        ctx.font = "bold 13px 'Segoe UI', Arial";
        const textWidth = ctx.measureText(priceText).width;
        const badgeWidth = textWidth + 16;
        const badgeHeight = 24;
        const badgeX = chartRight;
        const badgeY = Math.min(Math.max(currentPriceY - badgeHeight / 2, chartTop), chartTop + chartHeight - badgeHeight);
        
        // Badge background
        ctx.fillStyle = lastCandle.close >= lastCandle.open ? "#2ea043" : "#f85149";
        ctx.fillRect(badgeX, badgeY, badgeWidth, badgeHeight);
        
        // Badge text
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.fillText(priceText, badgeX + badgeWidth / 2, currentPriceY);
    }

    // ========== HTF OVERLAY BADGE ==========
    if (htfVisible && htfOverlay) {
        ctx.save();
        const badgeX = chartLeft + 8;
        const badgeY = chartTop + 8;
        const badgeW = 140;
        const badgeH = 32;
        const isBull = (htfOverlay.bias || '').toUpperCase() === 'BULLISH';
        const badgeGrad = ctx.createLinearGradient(badgeX, badgeY, badgeX + badgeW, badgeY + badgeH);
        badgeGrad.addColorStop(0, isBull ? 'rgba(34,197,94,0.18)' : 'rgba(248,113,113,0.18)');
        badgeGrad.addColorStop(1, isBull ? 'rgba(16,185,129,0.22)' : 'rgba(220,38,38,0.22)');
        ctx.fillStyle = badgeGrad;
        ctx.strokeStyle = isBull ? 'rgba(34,197,94,0.4)' : 'rgba(248,113,113,0.4)';
        ctx.lineWidth = 1.2;
        ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
        ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
        ctx.fillStyle = '#e5e7eb';
        ctx.font = "bold 11px 'Segoe UI', Arial";
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`HTF ${htfOverlay.trend || 'N/A'}`, badgeX + 8, badgeY + 10);
        ctx.font = "10px 'Segoe UI', Arial";
        ctx.fillStyle = isBull ? '#86efac' : '#fca5a5';
        ctx.fillText((htfOverlay.bias || 'NEUTRAL').toUpperCase(), badgeX + 8, badgeY + 22);
        ctx.restore();
    }

    // ========== DRAW SESSION MARKERS (if enabled) ==========
    if (sessionMarkersVisible && ohlcBars.length > 0) {
        const candleSpacingValue = candleSpacingForGrid;
        
        // Group candles by session
        ohlcBars.forEach((candle, i) => {
            const timestamp = new Date(candle.timestamp);
            const utcHour = timestamp.getUTCHours();
            const sessionName = getSessionName(utcHour);
            const SESSION_COLORS = {
                'ASIA': { color: 'rgba(59, 130, 246, 0.08)', label: 'ASIA', rgb: 'rgb(59, 130, 246)' },      // blue
                'LONDON': { color: 'rgba(168, 85, 247, 0.08)', label: 'LONDON', rgb: 'rgb(168, 85, 247)' },   // purple
                'NEWYORK': { color: 'rgba(34, 197, 94, 0.08)', label: 'NEWYORK', rgb: 'rgb(34, 197, 94)' }     // green
            };
            
            if (sessionName && SESSION_COLORS[sessionName]) {
                const x = chartLeft + candleSpacingValue / 2 + ((i + clampedPanBar) * candleSpacingValue);
                const barWidth = candleSpacingValue * 0.9;
                
                // Draw session background rectangle
                ctx.fillStyle = SESSION_COLORS[sessionName].color;
                ctx.fillRect(x - barWidth/2, chartTop, barWidth, chartHeight);
            }
        });
        
        // Draw session labels at bottom
        const SESSION_LABELS = {
            'ASIA': { color: 'rgb(59, 130, 246)', utcRange: '0-8' },
            'LONDON': { color: 'rgb(168, 85, 247)', utcRange: '8-17' },
            'NEWYORK': { color: 'rgb(34, 197, 94)', utcRange: '13-21' }
        };
        
        ctx.font = "9px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        let labelX = chartLeft + 50;
        Object.entries(SESSION_LABELS).forEach(([session, style]) => {
            ctx.fillStyle = style.color;
            ctx.fillText(session, labelX, chartBottom + 50);
            ctx.font = "8px 'Segoe UI', Arial, sans-serif";
            ctx.fillStyle = 'rgba(200, 200, 200, 0.6)';
            ctx.fillText(`(UTC ${style.utcRange})`, labelX, chartBottom + 62);
            labelX += 120;
            ctx.font = "9px 'Segoe UI', Arial, sans-serif";
        });
    }

    // ========== DRAW CANDLESTICKS (TradingView style) ==========
    // Use pre-calculated candleSpacing for consistency
    const candleSpacingValue = candleSpacingForGrid;
    // INTRADAY OPTIMIZED: Wider candles (80% instead of 70%) for better visibility
    const candleWidth = Math.max(3, candleSpacingValue * 0.8);
    
    // Draw price line connecting candles (TradingView style)
    ctx.strokeStyle = "rgba(100, 150, 200, 0.3)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    let firstPoint = true;
    ohlcBars.forEach((candle, i) => {
        const x = chartLeft + candleSpacingValue / 2 + ((i + clampedPanBar) * candleSpacingValue);
        const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
        const closeY = toY(candle.close);
        if (firstPoint) {
            ctx.moveTo(x, closeY);
            firstPoint = false;
        } else {
            ctx.lineTo(x, closeY);
        }
    });
    ctx.stroke();

    // ========== DRAW ICEBERG ZONES (background bands with labels) ==========
    if (icebergVisible) {
        icebergZones.forEach((zone, idx) => {
            const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;
            const yTop = toY(zone.price_top);
            const yBot = toY(zone.price_bottom);
            const top = Math.min(yTop, yBot);
            const height = Math.abs(yBot - yTop);
            
            // Draw zone band
            ctx.fillStyle = zone.color || "rgba(255,159,28,0.18)";
            ctx.fillRect(chartLeft, top, chartWidth, height);
            
            // Draw zone border
            ctx.strokeStyle = "rgba(255,159,28,0.4)";
            ctx.lineWidth = 1;
            ctx.strokeRect(chartLeft, top, chartWidth, height);
            
            // Label: show volume spike ratio at zone center
            const zoneMidY = top + height / 2;
            const zoneLabel = `ICEBERG: ${zone.volume.toFixed(0)} vol`;
            ctx.fillStyle = "#ff9f1c";
            ctx.font = "bold 11px Arial";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillText(zoneLabel, chartLeft + 5, zoneMidY);
        });
    }

    // ========== DRAW FVG ZONES ==========
    if (fvgVisible) {
        ctx.save();
        let fvgCount = 0;
        ohlcBars.forEach((bar, i) => {
            if (i < 2) return;
            const prev2 = ohlcBars[i - 2];
            const isBullGap = bar.low > prev2.high;
            const isBearGap = bar.high < prev2.low;
            if (!isBullGap && !isBearGap) return;

            const xStart = chartLeft + candleSpacingForGrid / 2 + ((i - 2 + clampedPanBar) * candleSpacingForGrid);
            const xEnd = chartLeft + candleSpacingForGrid / 2 + ((i + clampedPanBar) * candleSpacingForGrid);
            if (xEnd < chartLeft || xStart > chartRight) return;

            const gapTop = isBullGap ? bar.low : prev2.low;
            const gapBot = isBullGap ? prev2.high : bar.high;
            const yTop = toY(gapTop);
            const yBot = toY(gapBot);
            const top = Math.min(yTop, yBot);
            const height = Math.abs(yBot - yTop);

            const grad = ctx.createLinearGradient(xStart, top, xStart, top + height);
            if (isBullGap) {
                grad.addColorStop(0, 'rgba(16,185,129,0.18)');
                grad.addColorStop(1, 'rgba(16,185,129,0.08)');
                ctx.strokeStyle = 'rgba(16,185,129,0.35)';
            } else {
                grad.addColorStop(0, 'rgba(248,113,113,0.18)');
                grad.addColorStop(1, 'rgba(248,113,113,0.08)');
                ctx.strokeStyle = 'rgba(248,113,113,0.35)';
            }
            ctx.fillStyle = grad;
            ctx.fillRect(Math.max(chartLeft, xStart), top, Math.min(chartRight, xEnd) - Math.max(chartLeft, xStart), height || 2);
            ctx.lineWidth = 1;
            ctx.strokeRect(Math.max(chartLeft, xStart), top, Math.min(chartRight, xEnd) - Math.max(chartLeft, xStart), height || 2);
            
            // Draw text label on FVG zone
            if (height > 20) {
                ctx.fillStyle = isBullGap ? 'rgba(16,185,129,0.7)' : 'rgba(248,113,113,0.7)';
                ctx.font = 'bold 10px Segoe UI';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                const labelText = isBullGap ? '📈 FVG-B' : '📉 FVG-B';
                ctx.fillText(labelText, (Math.max(chartLeft, xStart) + Math.min(chartRight, xEnd)) / 2, top + height / 2);
            }
            fvgCount++;
        });
        ctx.restore();
    }

    // ========== DRAW GANN CYCLE LINES (Vertical inflection points) ==========
    if (gannCyclesVisible && window.gannData && window.gannData.gann_cycles && window.gannData.gann_cycles.length > 0) {
        window.gannData.gann_cycles.forEach(cycle => {
            try {
                // Color-code by cycle type
                let cycleColor = "#60a5fa";  // Default blue
                let cycleLabel = cycle.cycle_type;
                
                if (cycle.cycle_type.includes("90-bar")) {
                    cycleColor = "#3b82f6";  // Blue for 90-bar
                } else if (cycle.cycle_type.includes("45-bar")) {
                    cycleColor = "#10b981";  // Green for 45-bar
                } else if (cycle.cycle_type.includes("180-bar")) {
                    cycleColor = "#ef4444";  // Red for 180-bar
                }
                
                // Calculate X position from bar_index
                const barIdx = cycle.bar_index;
                if (barIdx < 0 || barIdx >= ohlcBars.length) return;
                
                const x = chartLeft + candleSpacingValue / 2 + ((barIdx + clampedPanBar) * candleSpacingValue);
                
                // Only draw if x is within chart bounds
                if (x < chartLeft || x > chartRight) return;
                
                // Draw vertical line
                ctx.strokeStyle = cycleColor;
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.6;
                ctx.setLineDash([4, 4]);  // Dashed line
                ctx.beginPath();
                ctx.moveTo(x, chartTop);
                ctx.lineTo(x, chartBottom);
                ctx.stroke();
                ctx.setLineDash([]);  // Reset dash
                ctx.globalAlpha = 1.0;
                
                // Draw cycle label at top
                const labelText = cycle.is_active ? `${cycleLabel} ✓` : `${cycleLabel} (${cycle.bars_until || '?'} bars)`;
                ctx.fillStyle = cycleColor;
                ctx.font = "bold 10px Arial";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                
                // Background for label
                const textMetrics = ctx.measureText(labelText);
                const labelWidth = textMetrics.width + 6;
                const labelHeight = 16;
                const labelX = Math.max(chartLeft, Math.min(x, chartRight - labelWidth / 2));
                const labelY = chartTop + 5;
                
                ctx.fillStyle = "rgba(20, 20, 40, 0.9)";
                ctx.fillRect(labelX - labelWidth / 2, labelY, labelWidth, labelHeight);
                
                // Label text
                ctx.fillStyle = cycleColor;
                ctx.fillText(labelText, labelX, labelY + 2);
                
                // ========== ADD DATE & TIME INFO BELOW CYCLE LABEL ==========
                if (cycle.timestamp || cycle.cycle_start || cycle.cycle_end) {
                    ctx.font = "9px Arial";
                    let timeY = labelY + 20;
                    
                    // Format date and time from ISO string
                    const formatDateTime = (isoString) => {
                        if (!isoString || isoString === "Upcoming") return "Upcoming";
                        try {
                            const date = new Date(isoString);
                            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                            const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
                            return `${dateStr} ${timeStr}`;
                        } catch (e) {
                            return isoString.split('T')[0] || "N/A";
                        }
                    };
                    
                    // Date label
                    if (cycle.timestamp) {
                        const dateTime = formatDateTime(cycle.timestamp);
                        const dateLabel = dateTime.split(' ').slice(0, 3).join(' '); // "Jan 23, 2026"
                        const dateMetrics = ctx.measureText(dateLabel);
                        const dateLabelWidth = dateMetrics.width + 6;
                        
                        ctx.fillStyle = "rgba(20, 20, 40, 0.85)";
                        ctx.fillRect(labelX - dateLabelWidth / 2, timeY, dateLabelWidth, 14);
                        ctx.fillStyle = cycleColor;
                        ctx.fillText(dateLabel, labelX, timeY + 2);
                        timeY += 16;
                    }
                    
                    // From/To Time labels
                    if (cycle.cycle_start && cycle.is_active) {
                        const startTime = formatDateTime(cycle.cycle_start);
                        const endTime = cycle.cycle_end ? formatDateTime(cycle.cycle_end) : formatDateTime(cycle.timestamp);
                        
                        // Extract time only (HH:MM)
                        const startTimeOnly = startTime.split(' ').slice(-1)[0] || startTime;
                        const endTimeOnly = endTime.split(' ').slice(-1)[0] || endTime;
                        
                        const timeRangeLabel = `${startTimeOnly} → ${endTimeOnly}`;
                        const timeMetrics = ctx.measureText(timeRangeLabel);
                        const timeLabelWidth = timeMetrics.width + 6;
                        
                        ctx.fillStyle = "rgba(20, 20, 40, 0.85)";
                        ctx.fillRect(labelX - timeLabelWidth / 2, timeY, timeLabelWidth, 14);
                        ctx.fillStyle = cycleColor;
                        ctx.fillText(timeRangeLabel, labelX, timeY + 2);
                    } else if (cycle.cycle_start && !cycle.is_active) {
                        // For upcoming cycles, show "From" time
                        const startTime = formatDateTime(cycle.cycle_start);
                        const startTimeOnly = startTime.split(' ').slice(-1)[0] || startTime;
                        const timeLabel = `From: ${startTimeOnly}`;
                        const timeMetrics = ctx.measureText(timeLabel);
                        const timeLabelWidth = timeMetrics.width + 6;
                        
                        ctx.fillStyle = "rgba(20, 20, 40, 0.85)";
                        ctx.fillRect(labelX - timeLabelWidth / 2, timeY, timeLabelWidth, 14);
                        ctx.fillStyle = cycleColor;
                        ctx.fillText(timeLabel, labelX, timeY + 2);
                    }
                }
                
                console.log(`🔄 Cycle rendered: ${labelText} at x=${x.toFixed(0)}`);
            } catch (e) {
                console.error("Error rendering cycle:", e);
            }
        });
    }

    // ========== DRAW ASTRO CYCLE LINES (Lunar & Solar cycles) ==========
    if (astroCyclesVisible && window.astroData && window.astroData.astro_cycles && window.astroData.astro_cycles.length > 0) {
        window.astroData.astro_cycles.forEach(cycle => {
            try {
                // Color-code by cycle type
                let cycleColor = "#c084fc";  // Default purple
                let cycleLabel = cycle.cycle_type;
                
                if (cycle.cycle_type.includes("Lunar")) {
                    cycleColor = "#7dd3fc";  // Light blue for Lunar
                } else if (cycle.cycle_type.includes("New Moon")) {
                    cycleColor = "#c084fc";  // Purple for New Moon
                } else if (cycle.cycle_type.includes("Solar")) {
                    cycleColor = "#fbbf24";  // Amber for Solar
                }
                
                // Calculate X position from bar_index
                const barIdx = cycle.bar_index;
                if (barIdx < 0 || barIdx >= ohlcBars.length) return;
                
                const x = chartLeft + candleSpacingValue / 2 + ((barIdx + clampedPanBar) * candleSpacingValue);
                
                // Only draw if x is within chart bounds
                if (x < chartLeft || x > chartRight) return;
                
                // Draw vertical line
                ctx.strokeStyle = cycleColor;
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.5;
                ctx.setLineDash([3, 3]);  // Dotted line (different from Gann dashed)
                ctx.beginPath();
                ctx.moveTo(x, chartTop);
                ctx.lineTo(x, chartBottom);
                ctx.stroke();
                ctx.setLineDash([]);  // Reset dash
                ctx.globalAlpha = 1.0;
                
                // Draw cycle label at bottom (different position from Gann cycles)
                const labelText = cycle.is_active ? `${cycleLabel} ✓` : `${cycleLabel} (${cycle.bars_until || '?'} bars)`;
                ctx.fillStyle = cycleColor;
                ctx.font = "bold 10px Arial";
                ctx.textAlign = "center";
                ctx.textBaseline = "bottom";
                
                // Background for label
                const textMetrics = ctx.measureText(labelText);
                const labelWidth = textMetrics.width + 6;
                const labelHeight = 16;
                const labelX = Math.max(chartLeft, Math.min(x, chartRight - labelWidth / 2));
                const labelY = chartBottom - 5;  // Position at bottom instead of top
                
                ctx.fillStyle = "rgba(30, 10, 50, 0.9)";
                ctx.fillRect(labelX - labelWidth / 2, labelY - labelHeight, labelWidth, labelHeight);
                
                // Label text
                ctx.fillStyle = cycleColor;
                ctx.fillText(labelText, labelX, labelY - 4);
                
                console.log(`🌙 Astro cycle rendered: ${labelText} at x=${x.toFixed(0)}`);
            } catch (e) {
                console.error("Error rendering astro cycle:", e);
            }
        });
    }

    // ========== ASTRO DISPLAYS MOVED TO HEADER BAR ==========
    // Moon Phase, Mercury Retrograde, and Aspects now display only in header bar
    // (removed from chart canvas to declutter visualization)

    ohlcBars.forEach((candle, i) => {
        const x = chartLeft + candleSpacingValue / 2 + ((i + clampedPanBar) * candleSpacingValue);

        // Price to Y coordinate conversion (with padding)
        const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;

        const openY = toY(candle.open);
        const closeY = toY(candle.close);
        const highY = toY(candle.high);
        const lowY = toY(candle.low);
        // Clamp Y coordinates to chart bounds to prevent wicks from extending beyond chart
        const clampedHighY = Math.max(highY, chartTop);
        const clampedLowY = Math.min(lowY, chartBottom);

        // Determine if bullish (green) or bearish (red)
        const isBullish = candle.close >= candle.open;
        const bodyColor = isBullish ? theme.up : theme.down;
        const wickColor = isBullish ? theme.up : theme.down;

        // Check if this is the newest candle (for flash animation)
        const isNewestCandle = (i === ohlcBars.length - 1) && newCandleAdded;
        const flashElapsed = Date.now() - newCandleFlashTime;
        const shouldFlash = isNewestCandle && flashElapsed < 2000; // Flash for 2 seconds

        // --- LIVE CANDLE EFFECT ---
        const isLiveCandle = (i === ohlcBars.length - 1);
        if (isLiveCandle) {
            // --- TradingView-style live candle: crisp dashed outline, semi-transparent fill, normal wick/body ---
            ctx.save();
            // Draw wick (high-low line) as normal
            ctx.strokeStyle = wickColor;
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(x, clampedHighY);
            ctx.lineTo(x, clampedLowY);
            ctx.stroke();

            // Draw body (open-close rectangle) with semi-transparent fill
            const bodyTop = Math.min(openY, closeY);
            let bodyHeight = Math.abs(closeY - openY);
            if (bodyHeight < 3) bodyHeight = 3;
            ctx.fillStyle = isBullish ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)';
            ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

            // Draw dashed outline
            ctx.lineWidth = 2.2;
            ctx.setLineDash([4, 3]);
            ctx.strokeStyle = isBullish ? 'rgba(34,197,94,0.85)' : 'rgba(239,68,68,0.85)';
            ctx.strokeRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
            ctx.setLineDash([]);
            ctx.restore();
        }

        // Draw glow effect for new candle
        if (shouldFlash) {
            const flashOpacity = Math.max(0, 1 - (flashElapsed / 2000)); // Fade out over 2 seconds
            ctx.save();
            ctx.shadowBlur = 20 * flashOpacity;
            ctx.shadowColor = isBullish ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)';
            ctx.strokeStyle = isBullish ? `rgba(34, 197, 94, ${flashOpacity})` : `rgba(239, 68, 68, ${flashOpacity})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(x, clampedHighY);
            ctx.lineTo(x, clampedLowY);
            ctx.stroke();
            ctx.restore();
        }

        // Draw wick (high-low line)
        ctx.strokeStyle = wickColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, clampedHighY);
        ctx.lineTo(x, clampedLowY);
        ctx.stroke();

        // Draw body (open-close rectangle) with minimum height, except for live candle (handled above)
        if (!isLiveCandle) {
            ctx.fillStyle = bodyColor;
            const bodyTop = Math.min(openY, closeY);
            let bodyHeight = Math.abs(closeY - openY);
            if (bodyHeight < 3) bodyHeight = 3; // Minimum 3px for flat candles
            ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
        }

        // Draw "NEW" badge on newest candle
        if (shouldFlash && flashElapsed < 1500) {
            ctx.save();
            ctx.fillStyle = isBullish ? '#22c55e' : '#ef4444';
            ctx.font = "bold 10px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.globalAlpha = Math.max(0, 1 - (flashElapsed / 1500));
            ctx.fillText('NEW', x, clampedHighY - 8);
            ctx.restore();
        }

        // Iceberg markers removed per user request
    });
    
    // Clear new candle flag after animation completes
    if (newCandleAdded && (Date.now() - newCandleFlashTime) > 2000) {
        newCandleAdded = false;
    }

    // ========== DRAW SWEEPS (wick raids) ==========
    if (sweepsVisible && ohlcBars.length > 5) {
        ctx.save();
        const lookback = 20;
        let lastSellIdx = -99;
        let lastBuyIdx = -99;
        let lastSellPrice = null;
        let lastBuyPrice = null;
        const tolerancePct = 0.001; // 0.1% price proximity filter to avoid duplicates

        ohlcBars.forEach((bar, i) => {
            if (i === 0) return;
            const start = Math.max(0, i - lookback);
            const prevSlice = ohlcBars.slice(start, i);
            const prevHigh = Math.max(...prevSlice.map(b => b.high));
            const prevLow = Math.min(...prevSlice.map(b => b.low));

            // Basic swing break
            const brokeHigh = bar.high >= prevHigh;
            const brokeLow = bar.low <= prevLow;

            // Displacement + volume filters
            const range = bar.high - bar.low;
            const avgRange = prevSlice.reduce((s, b) => s + (b.high - b.low), 0) / Math.max(prevSlice.length, 1);
            const avgVol = prevSlice.reduce((s, b) => s + b.volume, 0) / Math.max(prevSlice.length, 1);
            const hasDisplacement = range >= avgRange * 1.05; // >5% bigger than recent average range
            const hasVolume = bar.volume >= avgVol * 1.1;      // >10% more volume than recent average

            const isSellSweep = brokeHigh && bar.close < bar.open && hasDisplacement && hasVolume;
            const isBuySweep = brokeLow && bar.close > bar.open && hasDisplacement && hasVolume;
            if (!isSellSweep && !isBuySweep) return;

            // De-duplicate clusters near the same level
            if (isSellSweep) {
                if (i - lastSellIdx < 3) return;
                if (lastSellPrice && Math.abs(bar.high - lastSellPrice) / lastSellPrice < tolerancePct) return;
                lastSellIdx = i;
                lastSellPrice = bar.high;
            }
            if (isBuySweep) {
                if (i - lastBuyIdx < 3) return;
                if (lastBuyPrice && Math.abs(bar.low - lastBuyPrice) / lastBuyPrice < tolerancePct) return;
                lastBuyIdx = i;
                lastBuyPrice = bar.low;
            }

            const x = chartLeft + candleSpacingValue / 2 + ((i + clampedPanBar) * candleSpacingValue);
            if (x < chartLeft - 20 || x > chartRight + 20) return;
            const y = isSellSweep ? toY(bar.high) - 6 : toY(bar.low) + 6;
            ctx.beginPath();
            ctx.fillStyle = isSellSweep ? '#f87171' : '#34d399';
            ctx.moveTo(x, y + (isSellSweep ? -6 : 6));
            ctx.lineTo(x - 5, y + (isSellSweep ? 6 : -6));
            ctx.lineTo(x + 5, y + (isSellSweep ? 6 : -6));
            ctx.closePath();
            ctx.fill();
            
            // Draw text label for sweep
            ctx.fillStyle = isSellSweep ? 'rgba(248,113,113,0.9)' : 'rgba(52,211,153,0.9)';
            ctx.font = 'bold 11px Segoe UI';
            ctx.textAlign = 'center';
            ctx.textBaseline = isSellSweep ? 'bottom' : 'top';
            const sweepLabel = isSellSweep ? '🔴 SWEEP' : '🟢 SWEEP';
            ctx.fillText(sweepLabel, x, isSellSweep ? y - 10 : y + 10);
        });
        ctx.restore();
    }

    // ========== DRAW LIQUIDITY POOLS (swing highs/lows) ==========
    if (liquidityVisible && ohlcBars.length > 5) {
        ctx.save();
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 1;
        let liquidityLabels = [];
        for (let i = 2; i < ohlcBars.length - 2; i++) {
            const ph = ohlcBars[i - 1].high > ohlcBars[i - 2].high && ohlcBars[i - 1].high > ohlcBars[i].high;
            const pl = ohlcBars[i - 1].low < ohlcBars[i - 2].low && ohlcBars[i - 1].low < ohlcBars[i].low;
            if (!ph && !pl) continue;
            const pivotPrice = ph ? ohlcBars[i - 1].high : ohlcBars[i - 1].low;
            const y = toY(pivotPrice);
            if (y < chartTop || y > chartBottom) continue;
            ctx.strokeStyle = ph ? 'rgba(248,113,113,0.5)' : 'rgba(52,211,153,0.5)';
            ctx.beginPath();
            ctx.moveTo(chartLeft, y);
            ctx.lineTo(chartRight, y);
            ctx.stroke();
            
            // Draw text label for liquidity level
            const label = ph ? '🔴 HIGH' : '🟢 LOW';
            ctx.fillStyle = ph ? 'rgba(248,113,113,0.8)' : 'rgba(52,211,153,0.8)';
            ctx.font = 'bold 10px Segoe UI';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(label + ` ${pivotPrice.toFixed(2)}`, chartLeft + 5, y);
        }
        ctx.setLineDash([]);
        ctx.restore();
    }

    // ========== DRAW VOLUME BARS (Below chart) ==========
    if (volumeVisible) {
        const maxVolume = Math.max(...ohlcBars.map(b => b.volume), 1000);
        const volumeAreaHeight = 60;
        const volumeAreaTop = chartBottom + 2;
        const volumeAreaBottom = volumeAreaTop + volumeAreaHeight;
        const candleSpacing = candleSpacingForGrid;
        
        // Draw volume area background
        ctx.fillStyle = theme.background;
        ctx.fillRect(chartLeft, volumeAreaTop, chartWidth, volumeAreaHeight);
        
        // Draw grid line separator
        ctx.strokeStyle = theme.grid;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(chartLeft, volumeAreaTop);
        ctx.lineTo(chartRight, volumeAreaTop);
        ctx.stroke();
        
        // Draw volume bars
        ohlcBars.forEach((candle, i) => {
            const x = chartLeft + (candleSpacing / 2) + ((i + clampedPanBar) * candleSpacing);
            
            // Skip if offscreen
            if (x < chartLeft - 20 || x > chartRight + 20) return;
            
            const volColor = candle.close >= candle.open ? theme.volume : theme.volumeDown;
            const barWidth = Math.max(2, candleSpacing * 0.6);
            
            // Scale volume to fit in area (max height ~45px to leave room for label)
            const volHeightPx = Math.min((candle.volume / maxVolume) * (volumeAreaHeight - 15), volumeAreaHeight - 15);
            const barX = x - barWidth / 2;
            const barTop = volumeAreaBottom - volHeightPx;
            
            // Draw volume bar
            ctx.fillStyle = volColor;
            ctx.fillRect(barX, barTop, barWidth, volHeightPx);
            
            // Draw bar border
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 0.5;
            ctx.strokeRect(barX, barTop, barWidth, volHeightPx);
            
            // Draw volume quantity on bar (show only for hovered bar or every 5th bar to avoid clutter)
            if (i % 5 === 0 || i === hoveredBarIndex) {
                const volumeLabel = candle.volume > 999999 
                    ? (candle.volume / 1000000).toFixed(1) + 'M'
                    : candle.volume > 999
                    ? (candle.volume / 1000).toFixed(0) + 'K'
                    : candle.volume.toString();
                
                ctx.fillStyle = theme.text;
                ctx.font = "9px 'Segoe UI', Arial, sans-serif";
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.fillText(volumeLabel, x, barTop - 2);
            }
        });
        
        // Draw volume axis label
        ctx.fillStyle = theme.text;
        ctx.font = "10px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText('VOL', chartLeft + 5, volumeAreaTop + 8);
        
        // Draw volume scale reference
        const refVolume = maxVolume / 2;
        const refLabel = refVolume > 999999 
            ? (refVolume / 1000000).toFixed(1) + 'M'
            : refVolume > 999
            ? (refVolume / 1000).toFixed(0) + 'K'
            : refVolume.toString();
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = "8px 'Segoe UI', Arial, sans-serif";
        ctx.fillText(refLabel, chartRight - 35, volumeAreaTop + 8);
    }

    // ========== DRAW VOLUME PROFILE (Left side histogram) ==========
    if (volumeProfileVisible && volumeProfileData) {
        const profile = volumeProfileData;
        const histogramWidth = 150; // pixels from left edge
        const histogramRight = chartLeft + histogramWidth;
        
        // Find max volume for scaling
        const maxVol = Math.max(...profile.histogram.map(b => b.volume), 1);
        
        // Draw semi-transparent background for histogram area
        ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
        ctx.fillRect(chartLeft, chartTop, histogramWidth, chartBottom - chartTop);
        
        // Draw histogram bars (horizontal, from left) - Buy and Sell separated
        profile.histogram.forEach(bar => {
            const y = toY(bar.price);
            if (y < chartTop || y > chartBottom) return;
            
            const buyVol = bar.buy_volume || 0;
            const sellVol = bar.sell_volume || 0;
            const totalVol = bar.volume;
            
            if (totalVol === 0) return;
            
            const maxBarWidth = histogramWidth * 0.85;
            const totalBarWidth = (totalVol / maxVol) * maxBarWidth;
            const barHeight = 2.5; // slightly thicker bars
            
            // Calculate buy and sell widths proportionally
            const buyWidth = (buyVol / totalVol) * totalBarWidth;
            const sellWidth = (sellVol / totalVol) * totalBarWidth;
            
            const startX = chartLeft + 10;
            
            // Draw sell bar (red) first
            if (sellVol > 0) {
                ctx.fillStyle = bar.in_value_area 
                    ? 'rgba(239, 68, 68, 0.5)'  // red
                    : 'rgba(239, 68, 68, 0.3)'; // lighter red
                ctx.fillRect(startX, y - barHeight/2, sellWidth, barHeight);
            }
            
            // Draw buy bar (green) on top
            if (buyVol > 0) {
                ctx.fillStyle = bar.in_value_area 
                    ? 'rgba(34, 197, 94, 0.5)'  // green
                    : 'rgba(34, 197, 94, 0.3)'; // lighter green
                ctx.fillRect(startX + sellWidth, y - barHeight/2, buyWidth, barHeight);
            }
            
            // Draw volume text for significant levels
            const showLabel = bar.is_poc || bar.volume > maxVol * 0.3;
            if (showLabel && totalBarWidth > 30) {
                const buyLabel = buyVol > 999 ? (buyVol / 1000).toFixed(1) + 'K' : buyVol.toFixed(0);
                const sellLabel = sellVol > 999 ? (sellVol / 1000).toFixed(1) + 'K' : sellVol.toFixed(0);
                
                ctx.font = "bold 9px 'Segoe UI', Arial, sans-serif";
                ctx.textBaseline = 'middle';
                
                // Buy volume label (green)
                if (buyVol > 0) {
                    ctx.fillStyle = 'rgba(34, 197, 94, 1)';
                    ctx.textAlign = 'left';
                    ctx.fillText(buyLabel, startX + sellWidth + buyWidth + 3, y);
                }
                
                // Sell volume label (red)
                if (sellVol > 0) {
                    ctx.fillStyle = 'rgba(239, 68, 68, 1)';
                    ctx.textAlign = 'right';
                    ctx.fillText(sellLabel, startX + sellWidth - 3, y);
                }
            }
        });
        
        // Draw volume header at top with buy/sell breakdown
        ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        
        const totalVolLabel = profile.total_volume > 999999 
            ? (profile.total_volume / 1000000).toFixed(2) + 'M'
            : profile.total_volume > 999
            ? (profile.total_volume / 1000).toFixed(1) + 'K'
            : profile.total_volume.toString();
        
        ctx.fillStyle = theme.text;
        ctx.fillText(`VOL: ${totalVolLabel}`, chartLeft + 8, chartTop + 5);
        
        // Buy volume (green)
        ctx.font = "10px 'Segoe UI', Arial, sans-serif";
        const buyVolLabel = profile.total_buy_volume > 999999 
            ? (profile.total_buy_volume / 1000000).toFixed(2) + 'M'
            : profile.total_buy_volume > 999
            ? (profile.total_buy_volume / 1000).toFixed(1) + 'K'
            : profile.total_buy_volume.toString();
        ctx.fillStyle = 'rgba(34, 197, 94, 1)';
        ctx.fillText(`▲ ${buyVolLabel}`, chartLeft + 8, chartTop + 20);
        
        // Sell volume (red)
        const sellVolLabel = profile.total_sell_volume > 999999 
            ? (profile.total_sell_volume / 1000000).toFixed(2) + 'M'
            : profile.total_sell_volume > 999
            ? (profile.total_sell_volume / 1000).toFixed(1) + 'K'
            : profile.total_sell_volume.toString();
        ctx.fillStyle = 'rgba(239, 68, 68, 1)';
        ctx.fillText(`▼ ${sellVolLabel}`, chartLeft + 8, chartTop + 35);
        
        // Bar count
        ctx.fillStyle = theme.text;
        ctx.font = "9px 'Segoe UI', Arial, sans-serif";
        ctx.fillText(`${profile.bars_analyzed} bars`, chartLeft + 8, chartTop + 50);
        
        // Draw POC line (yellow, thick)
        ctx.strokeStyle = 'rgb(234, 179, 8)'; // yellow
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        const pocY = toY(profile.poc);
        if (pocY >= chartTop && pocY <= chartBottom) {
            // Draw animated glow if POC just moved
            if (previousPOC !== null) {
                const prevPocY = toY(previousPOC);
                // Glow effect
                ctx.save();
                ctx.strokeStyle = 'rgba(234, 179, 8, 0.3)';
                ctx.lineWidth = 8;
                ctx.beginPath();
                ctx.moveTo(chartLeft, pocY);
                ctx.lineTo(chartRight, pocY);
                ctx.stroke();
                
                // Draw arrow showing movement direction
                const arrow = previousPOC < profile.poc ? '▲' : '▼';
                ctx.fillStyle = 'rgba(234, 179, 8, 0.8)';
                ctx.font = "16px 'Segoe UI', Arial, sans-serif";
                ctx.textAlign = 'right';
                ctx.fillText(arrow, chartRight - 10, pocY);
                ctx.restore();
            }
            
            ctx.beginPath();
            ctx.moveTo(chartLeft, pocY);
            ctx.lineTo(chartRight, pocY);
            ctx.stroke();
            
            // POC label (on left side)
            ctx.fillStyle = 'rgb(234, 179, 8)';
            ctx.font = "bold 11px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            ctx.fillText(`POC ${profile.poc.toFixed(2)}`, chartLeft + 8, pocY - 3);
        }
        
        // Draw VAH line (dashed gray)
        ctx.strokeStyle = 'rgba(156, 163, 175, 0.8)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 3]);
        const vahY = toY(profile.vah);
        if (vahY >= chartTop && vahY <= chartBottom) {
            ctx.beginPath();
            ctx.moveTo(chartLeft, vahY);
            ctx.lineTo(chartRight, vahY);
            ctx.stroke();
            
            // VAH label (on left side)
            ctx.fillStyle = 'rgba(156, 163, 175, 0.9)';
            ctx.font = "10px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            ctx.fillText(`VAH ${profile.vah.toFixed(2)}`, chartLeft + 8, vahY - 2);
        }
        
        // Draw VAL line (dashed gray)
        const valY = toY(profile.val);
        if (valY >= chartTop && valY <= chartBottom) {
            ctx.beginPath();
            ctx.moveTo(chartLeft, valY);
            ctx.lineTo(chartRight, valY);
            ctx.stroke();
            
            // VAL label (on left side)
            ctx.fillStyle = 'rgba(156, 163, 175, 0.9)';
            ctx.font = "10px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(`VAL ${profile.val.toFixed(2)}`, chartLeft + 8, valY + 2);
        }
        
        // Draw VWAP line (blue)
        ctx.strokeStyle = 'rgb(59, 130, 246)'; // blue
        ctx.lineWidth = 1.5;
        ctx.setLineDash([]);
        const vwapY = toY(profile.vwap);
        if (vwapY >= chartTop && vwapY <= chartBottom) {
            ctx.beginPath();
            ctx.moveTo(chartLeft, vwapY);
            ctx.lineTo(chartRight, vwapY);
            ctx.stroke();
            
            // VWAP label (on left side)
            ctx.fillStyle = 'rgb(59, 130, 246)';
            ctx.font = "10px 'Segoe UI', Arial, sans-serif";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'bottom';
            ctx.fillText(`VWAP ${profile.vwap.toFixed(2)}`, chartLeft + 8, vwapY - 2);
        }
        
        // Draw volume profile legend panel
        if (volumeProfileLegendVisible) {
            drawVolumeProfileLegend(ctx, profile, chartRight, chartTop);
        }
        
        // Reset line dash
        ctx.setLineDash([]);
    }
    
    // ========== DRAW ALL DRAWINGS (TRENDLINES, HORIZONTAL, FUBONACCI) ==========
    drawAllDrawings();
    
    // ========== DRAW ORDERFLOW VISUALIZATION ==========
    drawOrderflowOnChart();
    
    const timeStripY = chartBottom + 65;  // Position below volume area (60px + 5ms margin)
    const timeStripHeight = 28;
    
    // Draw time axis background strip
    ctx.fillStyle = theme.gridBg;
    ctx.fillRect(chartLeft, timeStripY, chartWidth, timeStripHeight);
    
    // Add border line at top of time strip
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartLeft, timeStripY);
    ctx.lineTo(chartRight, timeStripY);
    ctx.stroke();
    
    // Configure text style
    ctx.fillStyle = theme.text;
    ctx.font = "10px 'Segoe UI', Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    // Draw time labels with proper spacing
    const labelCount = Math.min(10, ohlcBars.length);
    const labelInterval = Math.max(1, Math.floor(ohlcBars.length / labelCount));
    
    for (let i = 0; i < ohlcBars.length; i += labelInterval) {
        const x = chartLeft + candleSpacingForGrid / 2 + ((i + clampedPanBar) * candleSpacingForGrid);
        
        // Only draw labels within visible bounds
        if (x >= chartLeft && x <= chartRight) {
            const candle = ohlcBars[i];
            let timeLabel = "--:--";
            
            if (candle && candle.timestamp) {
                try {
                    // Parse timestamp - handle both ISO strings and epoch timestamps
                    let date;
                    if (typeof candle.timestamp === 'number') {
                        date = new Date(candle.timestamp * 1000); // Convert epoch to ms
                    } else {
                        date = new Date(candle.timestamp);
                    }
                    
                    // Format based on timeframe using local time
                    if (currentTimeframe === '1d') {
                        const month = date.toLocaleDateString('en-US', { month: 'short' });
                        const day = date.getDate();
                        timeLabel = `${month} ${day}`;
                    } else if (currentTimeframe === '4h' || currentTimeframe === '1h') {
                        const hour = String(date.getHours()).padStart(2, '0');
                        timeLabel = `${hour}:00`;
                    } else {
                        const hour = String(date.getHours()).padStart(2, '0');
                        const min = String(date.getMinutes()).padStart(2, '0');
                        timeLabel = `${hour}:${min}`;
                    }
                } catch (e) {
                    console.error("Error parsing timestamp:", candle.timestamp, e);
                    timeLabel = "--:--";
                }
            }
            
            // Draw time label
            ctx.fillStyle = theme.text;
            ctx.fillText(timeLabel, x, timeStripY + timeStripHeight / 2);
        }
    }

    // ========== CROSSHAIR & TOOLTIP ==========
    if (mouseX >= chartLeft && mouseX <= chartRight && mouseY >= chartTop && mouseY <= chartBottom) {
        // Draw crosshair lines
        ctx.strokeStyle = theme.crosshair;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        
        // Vertical line
        ctx.beginPath();
        ctx.moveTo(mouseX, chartTop);
        ctx.lineTo(mouseX, chartBottom);
        ctx.stroke();
        
        // Horizontal line
        ctx.beginPath();
        ctx.moveTo(chartLeft, mouseY);
        ctx.lineTo(chartRight, mouseY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw price label at cursor on right axis
        const priceAtCursor = adjustedMax - ((mouseY - chartTop) / chartHeight) * (adjustedMax - adjustedMin);
        const labelText = `$${priceAtCursor.toFixed(2)}`;
        const labelWidth = 72;
        const labelHeight = 16;
        const labelX = chartRight + 6;
        const labelY = Math.max(chartTop, Math.min(chartBottom - labelHeight, mouseY - labelHeight / 2));
        ctx.fillStyle = theme.tooltip;
        ctx.fillRect(labelX, labelY, labelWidth, labelHeight);
        ctx.strokeStyle = theme.border;
        ctx.lineWidth = 1;
        ctx.strokeRect(labelX, labelY, labelWidth, labelHeight);
        ctx.fillStyle = theme.text;
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(labelText, labelX + labelWidth / 2, labelY + labelHeight / 2);
        ctx.textAlign = "left";
        ctx.textBaseline = "alphabetic";
        
        // Find closest bar
        const mouseBarOffset = Math.round((chartRight - mouseX) / candleSpacingForGrid);
        const barIndex = mouseBarOffset - clampedPanBar;
        
        // Draw OHLC tooltip only if cursorOHLCVisible is enabled
        if (cursorOHLCVisible && barIndex >= 0 && barIndex < ohlcBars.length) {
            const bar = ohlcBars[barIndex];
            hoveredBarIndex = barIndex;
            
            // Draw tooltip
            const tooltipWidth = 180;
            const tooltipHeight = 110;
            let tooltipX = mouseX + 15;
            let tooltipY = mouseY - tooltipHeight - 10;
            
            // Keep tooltip on screen
            if (tooltipX + tooltipWidth > logicalWidth) tooltipX = mouseX - tooltipWidth - 15;
            if (tooltipY < 0) tooltipY = mouseY + 15;
            
            // Tooltip background
            ctx.fillStyle = theme.tooltip;
            ctx.fillRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
            ctx.strokeStyle = theme.border;
            ctx.lineWidth = 1;
            ctx.strokeRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
            
            // Tooltip text
            ctx.fillStyle = theme.text;
            ctx.font = "11px monospace";
            ctx.textAlign = "left";
            
            // Parse timestamp properly - handle both ISO and epoch
            let dt;
            if (typeof bar.timestamp === 'number') {
                dt = new Date(bar.timestamp * 1000); // Convert epoch to ms
            } else {
                dt = new Date(bar.timestamp);
            }
            const timeStr = `${dt.getHours().toString().padStart(2,'0')}:${dt.getMinutes().toString().padStart(2,'0')}`;
            const dateStr = `${dt.getDate()}/${dt.getMonth()+1}/${dt.getFullYear()}`;
            
            let yOffset = tooltipY + 16;
            ctx.fillText(`${dateStr} ${timeStr}`, tooltipX + 8, yOffset);
            yOffset += 16;
            ctx.fillStyle = theme.up;
            ctx.fillText(`O: $${bar.open.toFixed(2)}`, tooltipX + 8, yOffset);
            yOffset += 14;
            ctx.fillText(`H: $${bar.high.toFixed(2)}`, tooltipX + 8, yOffset);
            yOffset += 14;
            ctx.fillStyle = theme.down;
            ctx.fillText(`L: $${bar.low.toFixed(2)}`, tooltipX + 8, yOffset);
            yOffset += 14;
            ctx.fillStyle = bar.close >= bar.open ? theme.up : theme.down;
            ctx.fillText(`C: $${bar.close.toFixed(2)}`, tooltipX + 8, yOffset);
            yOffset += 14;
            ctx.fillStyle = theme.text;
            ctx.fillText(`V: ${bar.volume.toLocaleString()}`, tooltipX + 8, yOffset);
        }
    }

    // ========== DRAW TITLE & PRICE ==========
    if (ohlcBars.length > 0) {
        const lastCandle = ohlcBars[ohlcBars.length - 1];
        // Price display removed from chart canvas
        
        // ========== DRAW ASTRO INDICATORS ON CANVAS ==========
        if (astroIndicatorsVisible && window.astroData) {
            let astroX = 20;
            let astroY = 60;
            
            // Moon Phase
            if (window.astroData.moon_phase) {
                const moon = window.astroData.moon_phase;
                const moonIcon = moon.phase.includes("Full") ? "🌕" : 
                                moon.phase.includes("New") ? "🌑" : 
                                moon.phase.includes("Waxing") ? "🌒" : "🌘";
                const phaseShort = moon.phase.split(' ')[0];
                const illum = moon.percentage.toFixed(0);
                
                ctx.font = "16px Arial";
                ctx.fillStyle = "#7dd3fc";
                ctx.fillText(moonIcon, astroX, astroY);
                
                ctx.font = "11px Arial";
                ctx.fillStyle = "#94a3b8";
                ctx.fillText(`Moon ${phaseShort} (${illum}%)`, astroX + 22, astroY + 4);
                astroX += 160;
            }
            
            // Warning (HIGH volatility)
            if (window.astroData.astro_outlook && window.astroData.astro_outlook.volatility === 'HIGH') {
                ctx.font = "16px Arial";
                ctx.fillStyle = "#f59e0b";
                ctx.fillText("⚠️", astroX, astroY);
                
                ctx.font = "11px Arial";
                ctx.fillStyle = "#f59e0b";
                ctx.fillText("HIGH Volatility", astroX + 22, astroY + 4);
                astroX += 130;
            }
            
            // Mercury Retrograde
            if (window.astroData.mercury_retrograde) {
                ctx.font = "16px Arial";
                ctx.fillStyle = "#f59e0b";
                ctx.fillText("☿", astroX, astroY);
                
                ctx.font = "11px Arial";
                ctx.fillStyle = "#f59e0b";
                ctx.fillText("Mercury Rx - Caution", astroX + 22, astroY + 4);
            }
        }
    } else {
        console.warn("⚠️ No candles to display price");
    }

    // ========== DRAW LEGEND (Bottom-Right) ==========
    const legendX = chartRight - 150;
    const legendY = chartBottom + 65;
    
    ctx.fillStyle = "#1c2430";
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 1;
    ctx.fillRect(legendX - 5, legendY - 5, 140, 45);
    ctx.strokeRect(legendX - 5, legendY - 5, 140, 45);
    
    ctx.fillStyle = "#888";
    ctx.font = "10px Arial";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("Legend:", legendX, legendY);
    
    // Iceberg marker
    ctx.fillStyle = "#ff9f1c";
    ctx.beginPath();
    ctx.arc(legendX + 10, legendY + 18, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#888";
    ctx.fillText("Iceberg zone", legendX + 16, legendY + 15);
    
    // Green candle
    ctx.fillStyle = "#2ea043";
    ctx.fillRect(legendX + 10, legendY + 32, 3, 6);
    ctx.fillStyle = "#888";
    ctx.fillText("Bull", legendX + 16, legendY + 30);
    
    // Red candle
    ctx.fillStyle = "#f85149";
    ctx.fillRect(legendX + 45, legendY + 32, 3, 6);
    ctx.fillStyle = "#888";
    ctx.fillText("Bear", legendX + 55, legendY + 30);
    
    } catch (error) {
        console.error("Draw error:", error);
        ctx.fillStyle = "#ff6b6b";
        ctx.font = "12px Arial";
        ctx.fillText("Chart rendering error", 20, 30);
    }
}

// ========== INITIALIZATION ==========
console.log("🚀 Chart initialization starting...");
console.log("📍 API Base:", API_BASE);
console.log("🖼️ Canvas size:", canvas.clientWidth, "x", canvas.clientHeight);

// ========== TIMEFRAME SELECTOR ==========
document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        btn.classList.add('active');
        // Update current timeframe
        currentTimeframe = btn.dataset.tf;
        console.log(`⏱️ Timeframe changed to: ${currentTimeframe}`);
        // Fetch new data
        fetchData();
    });
});

// ========== CHART TOOLS ==========
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        console.log(`🔧 Tool activated: ${tool}`);
        
        if (tool === 'orderflow') {
            const willBeActive = !btn.classList.contains('active');
            toggleOrderflowVisibility(willBeActive);
            btn.classList.toggle('active', orderflowVisible);
            return;
        }

        // Toggle active state
        btn.classList.toggle('active');
        
        // Handle specific tools
        switch(tool) {
            case 'fullscreen':
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
                break;
            case 'zoom':
                // Future: Implement zoom functionality
                console.log('🔍 Zoom tool - Coming soon!');
                break;
            case 'line':
                console.log('📈 Trendline tool - Coming soon!');
                break;
            case 'fib':
                console.log('🔢 Fibonacci tool - Coming soon!');
                break;
            case 'hline':
                console.log('➖ Horizontal line tool - Coming soon!');
                break;
        }
    });
});

// ========== INDICATORS ==========
document.querySelectorAll('.indicator-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const indicator = btn.dataset.indicator;
        console.log(`📊 Indicator toggled: ${indicator}`);
        btn.classList.toggle('active');
        if (indicator === 'volume') {
            volumeVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'vwap') {
            vwapVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'volumeprofile') {
            volumeProfileVisible = btn.classList.contains('active');
            if (volumeProfileVisible && !volumeProfileData) {
                fetchVolumeProfile();
            } else {
                draw();
            }
            return;
        }
        if (indicator === 'vp-legend') {
            volumeProfileLegendVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'sessions') {
            sessionMarkersVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'iceberg') {
            icebergVisible = btn.classList.contains('active');
            draw();
            return;
        }

        if (indicator === 'sweeps') {
            sweepsVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'fvg') {
            fvgVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'liquidity') {
            liquidityVisible = btn.classList.contains('active');
            draw();
            return;
        }
        if (indicator === 'htf') {
            htfVisible = btn.classList.contains('active');
            draw();
            return;
        }

        // Not implemented yet: keep button off and inform user
        btn.classList.remove('active');
        alert('This indicator is not available yet. Currently supported: Volume, VWAP, Iceberg.');
    });
});

// Sync button states with defaults
const volumeBtn = document.querySelector('.indicator-btn[data-indicator="volume"]');
if (volumeBtn) volumeBtn.classList.toggle('active', volumeVisible);
const vwapBtn = document.querySelector('.indicator-btn[data-indicator="vwap"]');
if (vwapBtn) vwapBtn.classList.toggle('active', vwapVisible);
const volumeProfileBtn = document.querySelector('.indicator-btn[data-indicator="volumeprofile"]');
if (volumeProfileBtn) volumeProfileBtn.classList.toggle('active', volumeProfileVisible);
const vpLegendBtn = document.querySelector('.indicator-btn[data-indicator="vp-legend"]');
if (vpLegendBtn) vpLegendBtn.classList.toggle('active', volumeProfileLegendVisible);
const sessionsBtn = document.querySelector('.indicator-btn[data-indicator="sessions"]');
if (sessionsBtn) sessionsBtn.classList.toggle('active', sessionMarkersVisible);
const icebergBtn = document.querySelector('.indicator-btn[data-indicator="iceberg"]');
if (icebergBtn) icebergBtn.classList.toggle('active', icebergVisible);
const sweepsBtn = document.querySelector('.indicator-btn[data-indicator="sweeps"]');
if (sweepsBtn) sweepsBtn.classList.toggle('active', sweepsVisible);
const fvgBtn = document.querySelector('.indicator-btn[data-indicator="fvg"]');
if (fvgBtn) fvgBtn.classList.toggle('active', fvgVisible);
const liquidityBtn = document.querySelector('.indicator-btn[data-indicator="liquidity"]');
if (liquidityBtn) liquidityBtn.classList.toggle('active', liquidityVisible);
const htfBtn = document.querySelector('.indicator-btn[data-indicator="htf"]');
if (htfBtn) htfBtn.classList.toggle('active', htfVisible);

const orderflowCloseBtn = document.getElementById('orderflowClose');
if (orderflowCloseBtn) {
    orderflowCloseBtn.addEventListener('click', () => {
        toggleOrderflowVisibility(false);
        const toggle = document.getElementById('orderflowToggle');
        if (toggle) toggle.classList.remove('active');
    });
}

// Raw Orders Close Button (NEW)
const rawOrdersCloseBtn = document.getElementById('rawOrdersClose');
if (rawOrdersCloseBtn) {
    rawOrdersCloseBtn.addEventListener('click', () => {
        toggleRawOrdersVisibility(false);
        const toggle = document.getElementById('rawOrdersBtn');
        if (toggle) toggle.classList.remove('active');
    });
}

// Orderflow Export Handlers
const exportBtn = document.getElementById('orderflowExportBtn');
const exportPanel = document.getElementById('exportPanel');
const exportAllBtn = document.getElementById('exportAllBtn');
const exportRangeBtn = document.getElementById('exportRangeBtn');
const exportCancelBtn = document.getElementById('exportCancelBtn');

if (exportBtn) {
    exportBtn.addEventListener('click', () => {
        exportPanel.style.display = exportPanel.style.display === 'none' ? 'block' : 'none';
        
        // Set default dates (last 7 days)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7);
        
        const startInput = document.getElementById('exportStartDate');
        const endInput = document.getElementById('exportEndDate');
        
        if (startInput) startInput.value = startDate.toISOString().slice(0, 16);
        if (endInput) endInput.value = endDate.toISOString().slice(0, 16);
    });
}

if (exportAllBtn) {
    exportAllBtn.addEventListener('click', async () => {
        try {
            showToast('📥 Downloading all iceberg data...', 2000);
            
            const response = await fetch(`http://localhost:8000/api/v1/iceberg/export`);
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `iceberg_orderflow_all_${new Date().toISOString().slice(0, 10)}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('✅ Export completed!', 2000);
            exportPanel.style.display = 'none';
        } catch (error) {
            console.error('Export error:', error);
            showToast('❌ Export failed', 2000);
        }
    });
}

if (exportRangeBtn) {
    exportRangeBtn.addEventListener('click', async () => {
        try {
            const startDate = document.getElementById('exportStartDate').value;
            const endDate = document.getElementById('exportEndDate').value;
            
            if (!startDate || !endDate) {
                showToast('⚠️ Please select date range', 2000);
                return;
            }
            
            showToast('📥 Downloading iceberg data...', 2000);
            
            const startISO = new Date(startDate).toISOString();
            const endISO = new Date(endDate).toISOString();
            
            const response = await fetch(
                `http://localhost:8000/api/v1/iceberg/export?start_date=${encodeURIComponent(startISO)}&end_date=${encodeURIComponent(endISO)}`
            );
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `iceberg_orderflow_${startDate}_to_${endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('✅ Export completed!', 2000);
            exportPanel.style.display = 'none';
        } catch (error) {
            console.error('Export error:', error);
            showToast('❌ Export failed', 2000);
        }
    });
}

if (exportCancelBtn) {
    exportCancelBtn.addEventListener('click', () => {
        exportPanel.style.display = 'none';
    });
}

const orderflowDragHandle = document.getElementById('orderflowDragHandle');
if (orderflowDragHandle) {
    orderflowDragHandle.addEventListener('mousedown', startOrderflowDrag);
}

// ========== THEME TOGGLE ==========
document.getElementById('themeToggle').addEventListener('click', () => {
    isDarkTheme = !isDarkTheme;
    console.log(`🌓 Theme switched to: ${isDarkTheme ? 'Dark' : 'Light'}`);
    document.body.style.background = isDarkTheme ? '#0e0e0e' : '#ffffff';
    document.getElementById('mentor').style.background = isDarkTheme ? '#0f172a' : '#f5f5f5';
    document.getElementById('mentor').style.color = isDarkTheme ? '#e0e0e0' : '#333';
    draw();
});

// ========== AUTO-SCROLL TOGGLE ==========
const autoScrollBtn = document.getElementById('autoScrollToggle');
if (autoScrollBtn) {
    autoScrollBtn.addEventListener('click', () => {
        autoScrollEnabled = !autoScrollEnabled;
        autoScrollBtn.classList.toggle('active', autoScrollEnabled);
        console.log(`📜 Auto-scroll: ${autoScrollEnabled ? 'ON' : 'OFF'}`);
        showToast(autoScrollEnabled ? '📜 Auto-scroll enabled' : '📜 Auto-scroll disabled');
    });
    autoScrollBtn.classList.toggle('active', autoScrollEnabled);
}

// ========== TOAST NOTIFICATION SYSTEM ==========
function showToast(message, duration = 2000) {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ========== LIVE DATA INTEGRATION ==========
let lastUpdateTime = null;
let connectionStatus = 'connected'; // 'connected', 'disconnected', 'error'
let failedRequests = 0;
const MAX_FAILED_REQUESTS = 3;

// Update connection status indicator
function updateConnectionStatus(status) {
    connectionStatus = status;
    const statusDot = document.getElementById('connectionStatus');
    if (statusDot) {
        statusDot.className = `status-dot status-${status}`;
        statusDot.title = status === 'connected' ? 'Live data streaming' : 
                         status === 'disconnected' ? 'Connection lost' :
                         'Connection error';
    }
}

// Enhanced fetchData with error handling and live updates
const originalFetchData = fetchData;
fetchData = async function() {
    try {
        await originalFetchData();
        
        // Fetch live status for header updates
        const statusResponse = await fetch(`${API_BASE}/api/v1/status`);
        if (statusResponse.ok) {
            const status = await statusResponse.json();
            
            // Update live price display
            const livePriceEl = document.getElementById('livePrice');
            if (livePriceEl && status.price) {
                const previousPrice = parseFloat(livePriceEl.textContent.replace('$', '').replace(',', ''));
                livePriceEl.textContent = `$${status.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                
                // Add price change animation
                if (!isNaN(previousPrice) && previousPrice !== status.price) {
                    livePriceEl.classList.remove('price-up', 'price-down');
                    void livePriceEl.offsetWidth; // Trigger reflow
                    livePriceEl.classList.add(status.price > previousPrice ? 'price-up' : 'price-down');
                    setTimeout(() => livePriceEl.classList.remove('price-up', 'price-down'), 500);
                }
            }
            
            // Update session indicator
            const sessionEl = document.querySelector('.symbol-name');
            if (sessionEl && status.session) {
                const sessionIcon = status.session === 'ASIA' ? '🌏' :
                                   status.session === 'LONDON' ? '🇬🇧' :
                                   status.session === 'NEWYORK' ? '🇺🇸' : '🌙';
                sessionEl.textContent = `GC=F ${sessionIcon} ${status.session}`;
            }
            
            // Update orderflow (buys/sells)
            if (status.orderflow) {
                const priceChangeEl = document.getElementById('priceChange');
                if (priceChangeEl) {
                    const delta = status.orderflow.buys - status.orderflow.sells;
                    const deltaSymbol = delta > 0 ? '▲' : delta < 0 ? '▼' : '●';
                    priceChangeEl.textContent = `${deltaSymbol} B:${status.orderflow.buys} S:${status.orderflow.sells}`;
                    priceChangeEl.className = delta > 0 ? 'price-change price-up' : 
                                             delta < 0 ? 'price-change price-down' : 'price-change';
                }
            }
            
            lastUpdateTime = new Date();
            failedRequests = 0;
            updateConnectionStatus('connected');
        }
    } catch (error) {
        console.error('❌ Live data fetch error:', error);
        failedRequests++;
        if (failedRequests >= MAX_FAILED_REQUESTS) {
            updateConnectionStatus('disconnected');
        } else {
            updateConnectionStatus('error');
        }
    }

};

fetchData(); // Initial load
console.log("⏰ Setting refresh interval to 3 seconds for real-time iceberg updates...");
setInterval(fetchData, 3000); // Refresh every 3 seconds for faster iceberg detection

// 5-Minute Candle Prediction with AI & Memory (every 5 seconds)
console.log("🎯 Setting 5-Minute Candle Prediction refresh to 5 seconds...");

// Fetch immediately on load
(async () => {
    console.log("⏰ Initial prediction fetch...");
    const prediction = await fetch5MinCanclePrediction();
    if (prediction) {
        console.log("✅ Got prediction, rendering...");
        render5MinPredictionPanel(prediction);
    } else {
        console.warn("⚠️ No prediction returned");
    }
})();

// Then fetch every 5 seconds
setInterval(async () => {
    console.log("⏰ 5-min prediction interval triggered");
    const prediction = await fetch5MinCanclePrediction();
    if (prediction) {
        console.log("✅ Got prediction, rendering...");
        render5MinPredictionPanel(prediction);
    } else {
        console.warn("⚠️ No prediction returned");
    }
}, 5000);

// Volume Profile auto-refresh every 15 seconds
console.log("📊 Setting Volume Profile auto-refresh to 15 seconds...");
setInterval(() => {
    if (volumeProfileVisible) {
        console.log("🔄 Auto-refreshing Volume Profile...");
        fetchVolumeProfile();
    }
}, 15000); // Refresh every 15 seconds

// Display last update time
setInterval(() => {
    if (lastUpdateTime) {
        const elapsed = Math.floor((new Date() - lastUpdateTime) / 1000);
        const statusText = document.getElementById('lastUpdate');
        if (statusText) {
            statusText.textContent = elapsed < 60 ? `${elapsed}s ago` : `${Math.floor(elapsed/60)}m ago`;
        }
    }
    // Redraw to update legend timestamp
    if (volumeProfileVisible && volumeProfileData && !isVolumeProfileUpdating) {
        draw();
    }
}, 1000);

window.addEventListener("resize", () => {
    console.log("📐 Window resized, updating canvas...");
    resizeCanvases();
    requestDraw();
});

// ========== CHART PANNING (TradingView style) ==========
canvas.addEventListener('mousedown', (e) => {
    isPanning = true;
    panStartX = e.clientX;
    panStartY = e.clientY;
    canvas.style.cursor = 'grabbing';
});

canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
    
    if (!isPanning) {
        canvas.style.cursor = 'crosshair';
        requestDraw(); // Throttled redraw for crosshair and tooltip
        return;
    }
    
    const dx = e.clientX - panStartX;
    const dy = e.clientY - panStartY;
    
    // Translate drag into bar/time and price offsets
    tempBarPan = Math.round(-dx / Math.max(1, lastCandleSpacing));
    tempPricePan = (dy / Math.max(1, lastChartHeight)) * lastPriceRange;
    
    // Redraw live while dragging
    requestDraw();
});

canvas.addEventListener('mouseup', () => {
    isPanning = false;
    canvas.style.cursor = 'crosshair';
    barPan += tempBarPan;
    pricePan += tempPricePan;
    tempBarPan = 0;
    tempPricePan = 0;
    draw();
});

canvas.addEventListener('mouseleave', () => {
    isPanning = false;
    canvas.style.cursor = 'default';
    tempBarPan = 0;
    tempPricePan = 0;
    mouseX = -1;
    mouseY = -1;
    hoveredBarIndex = -1;
    draw();
});

// ========== MOUSE WHEEL ZOOM ==========
canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1; // Zoom in/out by 10%
    const newZoomLevel = Math.max(0.3, Math.min(3.0, zoomLevel * zoomDelta));
    
    if (newZoomLevel !== zoomLevel) {
        zoomLevel = newZoomLevel;
        
        // Adjust visible candles based on zoom
        visibleCandles = Math.floor(100 / zoomLevel);
        visibleCandles = Math.max(20, Math.min(500, visibleCandles));
        
        console.log(`🔍 Zoom: ${zoomLevel.toFixed(2)}x | Visible: ${visibleCandles} candles`);
        
        // Show zoom level toast
        const zoomPercent = Math.round(zoomLevel * 100);
        showToast(`🔍 Zoom: ${zoomPercent}%`, 1000);
        
        draw();
    }
}, { passive: false });

// ========== DRAWING TOOLS ==========
function updateDrawingStatus() {
    const status = document.getElementById('drawingStatus');
    if (!status) return;
    
    if (!drawingMode) {
        status.textContent = '';
        status.classList.remove('active');
        return;
    }
    
    const points = currentDrawing.points.length;
    const modeText = drawingMode.charAt(0).toUpperCase() + drawingMode.slice(1);
    
    if (drawingMode === 'trendline') {
        status.textContent = `📐 Trendline: ${points}/2 points`;
        status.classList.toggle('active', points > 0);
    } else if (drawingMode === 'horizontal') {
        status.textContent = `─ Line: Click level`;
        status.classList.toggle('active', true);
    } else if (drawingMode === 'fibonacci') {
        status.textContent = `🔢 Fib: ${points}/2 points`;
        status.classList.toggle('active', points > 0);
    }
}

function startDrawingTrendline() {
    if (drawingMode === 'trendline') {
        drawingMode = null;
        currentDrawing.points = [];
    } else {
        drawingMode = 'trendline';
        currentDrawing.points = [];
    }
    updateDrawingButtons();
    updateDrawingStatus();
    showToast('📐 Click 2 points to draw trendline', 1500);
}

function startDrawingHorizontal() {
    if (drawingMode === 'horizontal') {
        drawingMode = null;
        currentDrawing.points = [];
    } else {
        drawingMode = 'horizontal';
        currentDrawing.points = [];
    }
    updateDrawingButtons();
    updateDrawingStatus();
    showToast('─ Click price level to draw horizontal line', 1500);
}

function startDrawingFibonacci() {
    if (drawingMode === 'fibonacci') {
        drawingMode = null;
        currentDrawing.points = [];
    } else {
        drawingMode = 'fibonacci';
        currentDrawing.points = [];
    }
    updateDrawingButtons();
    updateDrawingStatus();
    showToast('🔢 Click high point, then low point', 1500);
}

function clearAllDrawings() {
    drawings = [];
    drawingMode = null;
    currentDrawing.points = [];
    updateDrawingButtons();
    updateDrawingStatus();
    showToast('🗑️ All drawings cleared', 1200);
    draw();
}

function updateDrawingButtons() {
    const trendBtn = document.getElementById('trendlineTool');
    const horizBtn = document.getElementById('horizontalTool');
    const fibBtn = document.getElementById('fibonacciTool');
    
    if (trendBtn) trendBtn.classList.toggle('active', drawingMode === 'trendline');
    if (horizBtn) horizBtn.classList.toggle('active', drawingMode === 'horizontal');
    if (fibBtn) fibBtn.classList.toggle('active', drawingMode === 'fibonacci');
}

function handleChartClick(e) {
    if (!drawingMode) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / dpiScale;
    const y = (e.clientY - rect.top) / dpiScale;
    
    // Convert screen coordinates to data coordinates
    const candle = Math.round((x - chartMarginLeft) / lastCandleSpacing) + startIndex;
    const price = lastMinPrice + (lastChartHeight - (y - chartMarginTop)) / lastChartHeight * lastPriceRange;
    
    currentDrawing.points.push({candle, price, x, y});
    updateDrawingStatus();
    
    // Check if drawing is complete
    let isComplete = false;
    if (drawingMode === 'trendline' && currentDrawing.points.length === 2) {
        isComplete = true;
        drawings.push({
            type: 'trendline',
            points: [...currentDrawing.points],
            color: '#FFD700',
            label: `TL ${drawings.filter(d => d.type === 'trendline').length + 1}`
        });
        showToast('✅ Trendline added!', 1000);
    } else if (drawingMode === 'horizontal' && currentDrawing.points.length === 1) {
        isComplete = true;
        drawings.push({
            type: 'horizontal',
            points: [...currentDrawing.points],
            color: '#64B6FF',
            label: `H ${drawings.filter(d => d.type === 'horizontal').length + 1}`
        });
        showToast('✅ Horizontal line added!', 1000);
    } else if (drawingMode === 'fibonacci' && currentDrawing.points.length === 2) {
        isComplete = true;
        drawings.push({
            type: 'fibonacci',
            points: [...currentDrawing.points],
            color: '#90EE90',
            label: `Fib ${drawings.filter(d => d.type === 'fibonacci').length + 1}`
        });
        showToast('✅ Fibonacci retracement added!', 1000);
    }
    
    if (isComplete) {
        currentDrawing.points = [];
        drawingMode = null;
        updateDrawingButtons();
        updateDrawingStatus();
    }
    
    draw();
}

function drawAllDrawings() {
    // Draw completed drawings
    drawings.forEach(drawing => {
        if (drawing.type === 'trendline') {
            drawTrendline(drawing.points, drawing.color, drawing.label);
        } else if (drawing.type === 'horizontal') {
            drawHorizontalLine(drawing.points, drawing.color, drawing.label);
        } else if (drawing.type === 'fibonacci') {
            drawFibonacciLevels(drawing.points, drawing.color, drawing.label);
        }
    });
    
    // Draw active positions (STEP 7)
    drawPositions();
    
    // Draw in-progress drawing
    if (currentDrawing.points.length > 0) {
        if (drawingMode === 'trendline' && currentDrawing.points.length === 1) {
            // Show preview line from first point to mouse
            ctx.strokeStyle = 'rgba(255, 215, 0, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(currentDrawing.points[0].x, currentDrawing.points[0].y);
            ctx.lineTo(mouseX, mouseY);
            ctx.stroke();
        } else if (drawingMode === 'horizontal') {
            // Show preview line at mouse height
            ctx.strokeStyle = 'rgba(100, 182, 255, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(chartMarginLeft, mouseY);
            ctx.lineTo(logicalWidth - chartMarginRight, mouseY);
            ctx.stroke();
        } else if (drawingMode === 'fibonacci' && currentDrawing.points.length === 1) {
            // Show preview fib from high to mouse
            ctx.strokeStyle = 'rgba(144, 238, 144, 0.3)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(currentDrawing.points[0].x, currentDrawing.points[0].y);
            ctx.lineTo(mouseX, mouseY);
            ctx.stroke();
        }
    }
}

function drawTrendline(points, color, label) {
    if (points.length < 2) return;
    
    const p1 = points[0];
    const p2 = points[1];
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw points
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p1.x, p1.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(p2.x, p2.y, 4, 0, Math.PI * 2);
    ctx.fill();
}

function drawHorizontalLine(points, color, label) {
    if (points.length < 1) return;
    
    const p = points[0];
    const price = p.price.toFixed(2);
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(chartMarginLeft, p.y);
    ctx.lineTo(logicalWidth - chartMarginRight, p.y);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw price label
    ctx.fillStyle = color;
    ctx.font = 'bold 12px Segoe UI';
    ctx.textAlign = 'right';
    ctx.fillText(`${price}`, logicalWidth - chartMarginRight - 5, p.y - 5);
}

function drawFibonacciLevels(points, color, label) {
    if (points.length < 2) return;
    
    const p1 = points[0];  // High
    const p2 = points[1];  // Low
    
    const highPrice = p1.price;
    const lowPrice = p2.price;
    const range = Math.abs(highPrice - lowPrice);
    
    const levels = [
        {ratio: 0.0, label: '0%', color: 'rgba(144, 238, 144, 0.4)'},
        {ratio: 0.236, label: '23.6%', color: 'rgba(144, 238, 144, 0.3)'},
        {ratio: 0.382, label: '38.2%', color: 'rgba(144, 238, 144, 0.3)'},
        {ratio: 0.5, label: '50%', color: 'rgba(144, 238, 144, 0.2)'},
        {ratio: 0.618, label: '61.8%', color: 'rgba(144, 238, 144, 0.3)'},
        {ratio: 1.0, label: '100%', color: 'rgba(144, 238, 144, 0.4)'}
    ];
    
    levels.forEach(level => {
        const price = lowPrice + range * level.ratio;
        const yPos = chartMarginTop + (lastMaxPrice - price) / lastPriceRange * lastChartHeight;
        
        ctx.strokeStyle = level.color;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(chartMarginLeft, yPos);
        ctx.lineTo(logicalWidth - chartMarginRight, yPos);
        ctx.stroke();
        
        // Draw label
        ctx.fillStyle = color;
        ctx.font = '10px Segoe UI';
        ctx.textAlign = 'right';
        ctx.fillText(level.label, logicalWidth - chartMarginRight - 5, yPos - 2);
    });
    
    ctx.setLineDash([]);
}

// ========== STEP 7: POSITION MANAGEMENT FUNCTIONS ==========

function drawPositions() {
    if (!positionsVisible || activePositions.length === 0) return;
    
    const candleSpacing = lastCandleSpacing;
    const chartHeight = lastChartHeight;
    const priceRange = lastPriceRange;
    const minPrice = lastMinPrice;
    const currentPrice = ohlcBars.length > 0 ? ohlcBars[ohlcBars.length - 1].close : 0;
    
    activePositions.forEach(position => {
        const entryIndex = position.entryIndex;
        const entryX = chartMarginLeft + (entryIndex + barPan + tempBarPan) * candleSpacing;
        const entryY = chartMarginTop + chartHeight - ((position.entryPrice - minPrice) / priceRange) * chartHeight;
        
        // Skip if offscreen
        if (entryX < chartMarginLeft - 100 || entryX > logicalWidth) return;
        
        const isBuy = position.type === 'BUY';
        const entryColor = isBuy ? 'rgba(52, 211, 153, 1)' : 'rgba(248, 113, 113, 1)';
        const lineColor = isBuy ? 'rgba(52, 211, 153, 0.6)' : 'rgba(248, 113, 113, 0.6)';
        
        // Calculate P&L
        const pnl = isBuy 
            ? (currentPrice - position.entryPrice) * position.size
            : (position.entryPrice - currentPrice) * position.size;
        position.pnl = pnl;
        
        const isProfitable = pnl > 0;
        const pnlColor = isProfitable ? '#34d399' : '#f87171';
        
        // Draw entry marker (arrow)
        ctx.save();
        ctx.fillStyle = entryColor;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        if (isBuy) {
            // Buy arrow (pointing up)
            ctx.moveTo(entryX, entryY - 15);
            ctx.lineTo(entryX - 8, entryY);
            ctx.lineTo(entryX + 8, entryY);
        } else {
            // Sell arrow (pointing down)
            ctx.moveTo(entryX, entryY + 15);
            ctx.lineTo(entryX - 8, entryY);
            ctx.lineTo(entryX + 8, entryY);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // Draw entry price label
        ctx.font = 'bold 10px Segoe UI';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = isBuy ? 'bottom' : 'top';
        ctx.fillText(position.entryPrice.toFixed(2), entryX, isBuy ? entryY - 18 : entryY + 18);
        
        // Draw position line to current price
        const currentX = logicalWidth - chartMarginRight;
        const currentY = chartMarginTop + chartHeight - ((currentPrice - minPrice) / priceRange) * chartHeight;
        
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(entryX, entryY);
        ctx.lineTo(currentX, currentY);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Draw P&L label at current price
        const pnlText = `${isProfitable ? '+' : ''}$${pnl.toFixed(2)}`;
        const pnlBgWidth = ctx.measureText(pnlText).width + 12;
        const pnlBgHeight = 20;
        const pnlBgX = currentX + 10;
        const pnlBgY = currentY - pnlBgHeight / 2;
        
        ctx.fillStyle = isProfitable ? 'rgba(52, 211, 153, 0.9)' : 'rgba(248, 113, 113, 0.9)';
        ctx.fillRect(pnlBgX, pnlBgY, pnlBgWidth, pnlBgHeight);
        
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.strokeRect(pnlBgX, pnlBgY, pnlBgWidth, pnlBgHeight);
        
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Segoe UI';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(pnlText, pnlBgX + 6, currentY);
        
        // Draw Stop Loss line (red dashed)
        if (position.stopLoss) {
            const slY = chartMarginTop + chartHeight - ((position.stopLoss - minPrice) / priceRange) * chartHeight;
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(chartMarginLeft, slY);
            ctx.lineTo(logicalWidth - chartMarginRight, slY);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // SL label
            ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
            ctx.font = 'bold 9px Segoe UI';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            ctx.fillText(`SL ${position.stopLoss.toFixed(2)}`, logicalWidth - chartMarginRight - 5, slY);
        }
        
        // Draw Take Profit line (green dashed)
        if (position.takeProfit) {
            const tpY = chartMarginTop + chartHeight - ((position.takeProfit - minPrice) / priceRange) * chartHeight;
            ctx.strokeStyle = 'rgba(34, 197, 94, 0.7)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(chartMarginLeft, tpY);
            ctx.lineTo(logicalWidth - chartMarginRight, tpY);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // TP label
            ctx.fillStyle = 'rgba(34, 197, 94, 0.9)';
            ctx.font = 'bold 9px Segoe UI';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            ctx.fillText(`TP ${position.takeProfit.toFixed(2)}`, logicalWidth - chartMarginRight - 5, tpY);
        }
        
        ctx.restore();
    });
}

function addPosition(type, entryPrice, stopLoss, takeProfit, size) {
    const currentIndex = ohlcBars.length - 1;
    const position = {
        id: positionIdCounter++,
        type: type,  // 'BUY' or 'SELL'
        entryPrice: parseFloat(entryPrice),
        entryTime: new Date().toISOString(),
        entryIndex: currentIndex,
        stopLoss: stopLoss ? parseFloat(stopLoss) : null,
        takeProfit: takeProfit ? parseFloat(takeProfit) : null,
        size: parseFloat(size) || 1,
        pnl: 0
    };
    
    activePositions.push(position);
    showToast(`✅ ${type} position added at ${entryPrice}`, 2000);
    draw();
    updatePositionPanel();
}

function closePosition(positionId) {
    const position = activePositions.find(p => p.id === positionId);
    if (!position) return;
    
    // Move to closed trades
    closedTrades.push({
        ...position,
        exitPrice: ohlcBars[ohlcBars.length - 1].close,
        exitTime: new Date().toISOString(),
        finalPnl: position.pnl
    });
    
    // Remove from active
    activePositions = activePositions.filter(p => p.id !== positionId);
    
    showToast(`✅ Position closed: ${position.pnl > 0 ? '+' : ''}$${position.pnl.toFixed(2)}`, 2000);
    draw();
    updatePositionPanel();
}

function closeAllPositions() {
    if (activePositions.length === 0) return;
    
    const totalPnl = activePositions.reduce((sum, p) => sum + p.pnl, 0);
    
    activePositions.forEach(position => {
        closedTrades.push({
            ...position,
            exitPrice: ohlcBars[ohlcBars.length - 1].close,
            exitTime: new Date().toISOString(),
            finalPnl: position.pnl
        });
    });
    
    activePositions = [];
    showToast(`✅ All positions closed: ${totalPnl > 0 ? '+' : ''}$${totalPnl.toFixed(2)}`, 2000);
    draw();
    updatePositionPanel();
}

function updatePositionPanel() {
    const panel = document.getElementById('positionPanel');
    if (!panel || !positionPanelVisible) return;
    
    const totalPnl = activePositions.reduce((sum, p) => sum + p.pnl, 0);
    
    let html = `
        <div style="background: rgba(0,0,0,0.9); color: white; padding: 15px; border-radius: 8px; max-width: 350px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; font-size: 14px; color: #fbbf24;">📊 POSITIONS</h3>
                <button onclick="togglePositionPanel()" style="background: none; border: none; color: white; cursor: pointer; font-size: 18px;">✖</button>
            </div>
            <div style="margin-bottom: 10px; font-size: 12px;">
                <strong>Total P&L:</strong> <span style="color: ${totalPnl >= 0 ? '#34d399' : '#f87171'}; font-weight: bold;">
                    ${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}
                </span>
            </div>
    `;
    
    if (activePositions.length === 0) {
        html += `<p style="font-size: 11px; color: #9ca3af; margin: 10px 0;">No active positions</p>`;
    } else {
        html += `<div style="max-height: 200px; overflow-y: auto;">`;
        activePositions.forEach(pos => {
            const pnlColor = pos.pnl >= 0 ? '#34d399' : '#f87171';
            html += `
                <div style="background: rgba(255,255,255,0.05); padding: 8px; margin-bottom: 5px; border-radius: 4px; font-size: 11px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: ${pos.type === 'BUY' ? '#34d399' : '#f87171'}; font-weight: bold;">${pos.type}</span>
                        <button onclick="closePosition(${pos.id})" style="background: #ef4444; color: white; border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px;">Close</button>
                    </div>
                    <div>Entry: ${pos.entryPrice.toFixed(2)} | Size: ${pos.size}</div>
                    ${pos.stopLoss ? `<div>SL: ${pos.stopLoss.toFixed(2)}</div>` : ''}
                    ${pos.takeProfit ? `<div>TP: ${pos.takeProfit.toFixed(2)}</div>` : ''}
                    <div style="color: ${pnlColor}; font-weight: bold;">P&L: ${pos.pnl >= 0 ? '+' : ''}$${pos.pnl.toFixed(2)}</div>
                </div>
            `;
        });
        html += `</div>`;
    }
    
    html += `
            <div style="margin-top: 10px;">
                <button onclick="showAddPositionForm()" style="background: #3b82f6; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; width: 100%; margin-bottom: 5px;">➕ Add Position</button>
                ${activePositions.length > 0 ? `<button onclick="closeAllPositions()" style="background: #ef4444; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; width: 100%;">Close All</button>` : ''}
            </div>
        </div>
    `;
    
    panel.innerHTML = html;
}

// ========== END STEP 7 FUNCTIONS ==========

// ========== DRAWING TOOLS EVENT HANDLERS ==========
canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouseX = (e.clientX - rect.left) / dpiScale;
    mouseY = (e.clientY - rect.top) / dpiScale;
    
    if (drawingMode && currentDrawing.points.length > 0) {
        draw();  // Redraw to show preview
    }
});

canvas.addEventListener('click', handleChartClick);

document.getElementById('trendlineTool')?.addEventListener('click', startDrawingTrendline);
document.getElementById('horizontalTool')?.addEventListener('click', startDrawingHorizontal);
document.getElementById('fibonacciTool')?.addEventListener('click', startDrawingFibonacci);
document.getElementById('clearDrawings')?.addEventListener('click', clearAllDrawings);

// Price scale lock button
document.getElementById('priceScaleLockBtn')?.addEventListener('click', () => {
    priceScaleLocked = !priceScaleLocked;
    
    if (priceScaleLocked) {
        // Lock to current visible range
        if (ohlcBars.length > 0) {
            const prices = ohlcBars.map(b => [b.high, b.low]).flat();
            const priceMax = Math.max(...prices);
            const priceMin = Math.min(...prices);
            let priceRange = priceMax - priceMin;
            if (priceRange < 1) priceRange = priceMax > 0 ? priceMax * 0.1 : 10;
            const pricePadding = priceRange * 0.15;
            lockedPriceMin = priceMin - pricePadding;
            lockedPriceMax = priceMax + pricePadding;
        }
        showToast('🔒 Price Scale Locked', 1500);
    } else {
        lockedPriceMin = null;
        lockedPriceMax = null;
        showToast('🔓 Price Scale Unlocked', 1500);
    }
    
    const lockBtn = document.getElementById('priceScaleLockBtn');
    if (lockBtn) {
        lockBtn.classList.toggle('active', priceScaleLocked);
        lockBtn.textContent = priceScaleLocked ? '🔒' : '🔓';
    }
    
    draw();
});

// ========== KEYBOARD SHORTCUTS ==========
document.addEventListener('keydown', (e) => {
    // Prevent shortcuts when typing in input fields
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    switch(e.key.toLowerCase()) {
        // Reset view
        case 'r':
            barPan = 0;
            tempBarPan = 0;
            pricePan = 0;
            tempPricePan = 0;
            zoomLevel = 1.0;
            visibleCandles = 100;
            showToast('🔄 View Reset', 1000);
            draw();
            break;
            
        // Toggle auto-scroll
        case 'a':
            autoScrollEnabled = !autoScrollEnabled;
            const autoScrollBtn = document.getElementById('autoScrollToggle');
            if (autoScrollBtn) autoScrollBtn.classList.toggle('active', autoScrollEnabled);
            showToast(autoScrollEnabled ? '📜 Auto-scroll ON' : '📜 Auto-scroll OFF', 1000);
            break;
            
        // Toggle volume profile
        case 'v':
            volumeProfileVisible = !volumeProfileVisible;
            if (volumeProfileVisible && !volumeProfileData) fetchVolumeProfile();
            const vpBtn = document.querySelector('.indicator-btn[data-indicator="volumeprofile"]');
            if (vpBtn) vpBtn.classList.toggle('active', volumeProfileVisible);
            showToast(volumeProfileVisible ? '📊 Volume Profile ON' : '📊 Volume Profile OFF', 1000);
            draw();
            break;
            
        // Toggle price scale lock
        case 'l':
            document.getElementById('priceScaleLockBtn')?.click();
            break;
            
        // Toggle legend panel
        case 'l':
            volumeProfileLegendVisible = !volumeProfileLegendVisible;
            const legendBtn = document.querySelector('.indicator-btn[data-indicator="vp-legend"]');
            if (legendBtn) legendBtn.classList.toggle('active', volumeProfileLegendVisible);
            showToast(volumeProfileLegendVisible ? '📋 Legend ON' : '📋 Legend OFF', 1000);
            draw();
            break;
            
        // Toggle session markers
        case 's':
            sessionMarkersVisible = !sessionMarkersVisible;
            const sessionBtn = document.querySelector('.indicator-btn[data-indicator="sessions"]');
            if (sessionBtn) sessionBtn.classList.toggle('active', sessionMarkersVisible);
            showToast(sessionMarkersVisible ? '🕐 Sessions ON' : '🕐 Sessions OFF', 1000);
            draw();
            break;
            
        // Toggle theme
        case 't':
            document.getElementById('themeToggle').click();
            break;
            
        // Zoom in (+ or =)
        case '=':
        case '+':
            e.preventDefault();
            zoomLevel = Math.min(3.0, zoomLevel * 1.2);
            visibleCandles = Math.floor(100 / zoomLevel);
            showToast(`🔍 Zoom: ${Math.round(zoomLevel * 100)}%`, 1000);
            draw();
            break;
            
        // Zoom out (-)
        case '-':
        case '_':
            e.preventDefault();
            zoomLevel = Math.max(0.3, zoomLevel * 0.8);
            visibleCandles = Math.floor(100 / zoomLevel);
            showToast(`🔍 Zoom: ${Math.round(zoomLevel * 100)}%`, 1000);
            draw();
            break;
            
        // Pan left (arrow left)
        case 'arrowleft':
            e.preventDefault();
            barPan -= 5;
            showToast('⬅️ Pan Left', 800);
            draw();
            break;
            
        // Pan right (arrow right)
        case 'arrowright':
            e.preventDefault();
            barPan += 5;
            showToast('➡️ Pan Right', 800);
            draw();
            break;
            
        // Pan up (arrow up)
        case 'arrowup':
            e.preventDefault();
            pricePan += lastPriceRange * 0.05;
            showToast('⬆️ Pan Up', 800);
            draw();
            break;
            
        // Pan down (arrow down)
        case 'arrowdown':
            e.preventDefault();
            pricePan -= lastPriceRange * 0.05;
            showToast('⬇️ Pan Down', 800);
            draw();
            break;
            
        // Show help
        case '?':
        case 'h':
            if (e.shiftKey || e.key === '?') {
                showKeyboardShortcutsHelp();
            }
            break;
    }
});

// ========== KEYBOARD SHORTCUTS HELP ==========
function showKeyboardShortcutsHelp() {
    const helpText = `
⌨️ KEYBOARD SHORTCUTS
━━━━━━━━━━━━━━━━━━━━━━━━━
R - Reset view
A - Toggle auto-scroll
V - Toggle volume profile
L - Lock/Unlock price scale
S - Toggle session markers
T - Toggle theme
+ = Zoom in
- _ Zoom out
← → Pan left/right
↑ ↓ Pan up/down
? H Show this help

MOUSE:
🖱️ Wheel - Zoom
🖱️ Drag - Pan chart
🖱️ Hover - Crosshair + tooltip
    `;
    
    alert(helpText);
}

// ========== MULTI-TIMEFRAME SUPPORT ==========
function saveTimeframeState() {
    timeframeZoomState[currentTimeframe] = {
        zoomLevel: zoomLevel,
        barPan: barPan,
        pricePan: pricePan,
        visibleCandles: visibleCandles
    };
}

function restoreTimeframeState() {
    if (timeframeZoomState[currentTimeframe]) {
        const state = timeframeZoomState[currentTimeframe];
        zoomLevel = state.zoomLevel || 1.0;
        barPan = state.barPan || 0;
        pricePan = state.pricePan || 0;
        visibleCandles = state.visibleCandles || 100;
    } else {
        // First time seeing this timeframe
        zoomLevel = 1.0;
        barPan = 0;
        pricePan = 0;
        visibleCandles = 100;
    }
}

async function switchTimeframe(newTimeframe) {
    if (newTimeframe === currentTimeframe) return;
    
    // Save current state
    saveTimeframeState();
    
    // Switch timeframe
    currentTimeframe = newTimeframe;
    
    // Update dropdown to show selected timeframe
    const select = document.getElementById('timeframeSelect');
    if (select) {
        select.value = newTimeframe;
    }
    
    showToast(`⏱️ Loading ${newTimeframe}...`, 1500);
    
    // Check if we have data cached
    if (timeframeCache[newTimeframe].length === 0) {
        // Fetch new timeframe data from backend
        await fetchTimeframeData(newTimeframe);
    } else {
        // Use cached data
        ohlcBars = timeframeCache[newTimeframe];
    }
    
    // Restore zoom/pan state for this timeframe
    restoreTimeframeState();
    
    // Redraw chart
    draw();
    
    showToast(`✅ Switched to ${newTimeframe}`, 1000);
}

async function fetchTimeframeData(timeframe) {
    try {
        const response = await fetch(`http://localhost:8000/api/ohlc/${timeframe}`);
        if (response.ok) {
            const data = await response.json();
            timeframeCache[timeframe] = data || [];
            ohlcBars = timeframeCache[timeframe];
            timeframeLastUpdate[timeframe] = Date.now();
        } else {
            console.warn(`Failed to fetch ${timeframe} data:`, response.status);
            // Use placeholder data if API fails
            generatePlaceholderCandles(timeframe);
        }
    } catch (error) {
        console.warn(`Error fetching ${timeframe} data:`, error.message);
        // Use placeholder data if network fails
        generatePlaceholderCandles(timeframe);
    }
}

function generatePlaceholderCandles(timeframe) {
    // Generate realistic candles for this timeframe if API unavailable
    const baseCandles = ohlcBars.length > 0 ? ohlcBars : [];
    const multiplier = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '1H': 60,
        '4H': 240,
        '1D': 1440
    }[timeframe] || 5;
    
    const generatedCount = Math.max(50, Math.floor(100 / multiplier));
    const generated = [];
    
    if (baseCandles.length > 0) {
        const lastCandle = baseCandles[baseCandles.length - 1];
        let currentPrice = lastCandle.close;
        let currentTime = lastCandle.time;
        
        for (let i = 0; i < generatedCount; i++) {
            const volatility = currentPrice * 0.001;
            const change = (Math.random() - 0.5) * volatility * 2;
            const open = currentPrice;
            const close = currentPrice + change;
            const high = Math.max(open, close) + Math.random() * volatility;
            const low = Math.min(open, close) - Math.random() * volatility;
            const volume = Math.floor(Math.random() * 10000000);
            
            generated.push({
                time: currentTime,
                open: parseFloat(open.toFixed(2)),
                high: parseFloat(high.toFixed(2)),
                low: parseFloat(low.toFixed(2)),
                close: parseFloat(close.toFixed(2)),
                volume: volume
            });
            
            currentPrice = close;
            currentTime += multiplier * 60 * 1000;
        }
    }
    
    timeframeCache[timeframe] = generated;
    ohlcBars = generated;
}

// ========== ORDERFLOW VISUALIZATION ==========
function generateOrderflowData() {
    // Generate realistic DOM ladder and institutional order flow data
    orderflowData = {};
    institutionalAlerts = [];
    
    if (ohlcBars.length === 0) return;
    
    const lastCandle = ohlcBars[ohlcBars.length - 1];
    const currentPrice = lastCandle.close;
    const priceRange = Math.max(lastCandle.high - lastCandle.low, currentPrice * 0.002);
    
    // Generate DOM ladder around current price
    domLadderData = [];
    const levels = 10;  // 5 bid, 5 ask
    
    for (let i = -levels; i <= levels; i++) {
        const price = currentPrice + (i * priceRange / levels);
        const volumeMultiplier = Math.exp(-(Math.abs(i) / 3));  // Concentration at mid
        const volume = Math.floor(Math.random() * 5000000 * volumeMultiplier);
        
        domLadderData.push({
            price: parseFloat(price.toFixed(2)),
            volume: volume,
            isBid: i < 0,
            isAsk: i > 0,
            atMarket: i === 0
        });
    }
    
    // Detect institutional order flow patterns
    detectInstitutionalPatterns();
}

function detectInstitutionalPatterns() {
    institutionalAlerts = [];
    
    if (ohlcBars.length < 2) return;
    
    const current = ohlcBars[ohlcBars.length - 1];
    const previous = ohlcBars[ohlcBars.length - 2];
    
    // Detect sweeps: break previous high/low on high volume
    const volumeRatio = current.volume / (previous.volume || 1);
    if (volumeRatio > 2.5) {
        if (current.low < previous.low) {
            institutionalAlerts.push({
                type: 'sweep',
                label: '🔴 SWEEP DOWN',
                detail: `Vol spike: ${(volumeRatio * 100).toFixed(0)}% ↓`,
                price: current.low
            });
        } else if (current.high > previous.high) {
            institutionalAlerts.push({
                type: 'sweep',
                label: '🟢 SWEEP UP',
                detail: `Vol spike: ${(volumeRatio * 100).toFixed(0)}% ↑`,
                price: current.high
            });
        }
    }
    
    // Detect absorptions: high volume with small range
    const range = current.high - current.low;
    const avgRange = (current.close + previous.close) / 2 * 0.002;
    if (range < avgRange && current.volume > 5000000) {
        institutionalAlerts.push({
            type: 'absorption',
            label: '💛 ABSORPTION',
            detail: `Volume absorbed at ${current.close.toFixed(2)}`,
            price: current.close
        });
    }
    
    // Detect large orders: volume 3x+ normal
    const avgVolume = ohlcBars.slice(-20).reduce((sum, c) => sum + c.volume, 0) / Math.min(20, ohlcBars.length);
    if (current.volume > avgVolume * 3) {
        institutionalAlerts.push({
            type: 'large-order',
            label: '💜 LARGE ORDER',
            detail: `${(current.volume / 1000000).toFixed(1)}M contracts`,
            price: current.close
        });
    }
}

function updateDOMPanel() {
    const panel = document.getElementById('domLadderContent');
    if (!panel) return;
    
    let html = '';
    
    // Sort by price descending (asks first)
    const sorted = [...domLadderData].sort((a, b) => b.price - a.price);
    
    sorted.forEach(level => {
        const volK = (level.volume / 1000).toFixed(0);
        const priceStr = level.price.toFixed(2);
        
        if (level.isAsk) {
            html += `<div class="dom-ladder-row ask">
                <div class="dom-ask-vol">${volK}</div>
                <div class="dom-price">${priceStr}</div>
                <div style="color: rgba(255,107,107,0.4);">∆</div>
            </div>`;
        } else if (level.isBid) {
            html += `<div class="dom-ladder-row bid">
                <div style="color: rgba(81,207,102,0.4);">∆</div>
                <div class="dom-price">${priceStr}</div>
                <div class="dom-bid-vol">${volK}</div>
            </div>`;
        } else {
            // Market price level
            html += `<div class="dom-ladder-row" style="background: rgba(255,255,255,0.05); font-weight: 700; color: #FFD700;">
                <div class="dom-ask-vol">${volK}</div>
                <div class="dom-price">⚡${priceStr}</div>
                <div class="dom-bid-vol">${volK}</div>
            </div>`;
        }
    });
    
    panel.innerHTML = html;
    
    // Update institutional alerts
    const alertsDiv = document.getElementById('institutionalAlerts');
    if (alertsDiv) {
        let alertsHtml = '';
        institutionalAlerts.forEach(alert => {
            alertsHtml += `<div class="institutional-alert ${alert.type}">
                <strong>${alert.label}</strong>
                <div style="font-size: 9px; margin-top: 2px;">${alert.detail}</div>
            </div>`;
        });
        alertsDiv.innerHTML = alertsHtml || '<div style="color: rgba(255,255,255,0.3); font-size: 10px;">No alerts</div>';
    }
}

function drawOrderflowOnChart() {
    if (!ictVisible || ohlcBars.length === 0 || !lastChartState) return;
    renderICTOverlay(lastChartState);
}

function getRecentOrderflowStats(windowMs = 5 * 60 * 1000) {
    const now = Date.now();
    let buy = 0;
    let sell = 0;
    let total = 0;
    let recentCount = 0;
    rawOrders.forEach(order => {
        const ts = order.timestamp ? new Date(order.timestamp).getTime() : now;
        if (now - ts <= windowMs) {
            const size = parseFloat(order.size) || 0;
            total += size;
            recentCount += 1;
            if (String(order.side).toUpperCase() === 'BUY') buy += size;
            if (String(order.side).toUpperCase() === 'SELL') sell += size;
        }
    });
    if (total === 0) {
        // Fallback to all orders if timestamps not available
        rawOrders.forEach(order => {
            const size = parseFloat(order.size) || 0;
            total += size;
            if (String(order.side).toUpperCase() === 'BUY') buy += size;
            if (String(order.side).toUpperCase() === 'SELL') sell += size;
        });
    }
    const balance = buy - sell;
    const accuracy = total > 0 ? Math.max(50, Math.min(99, Math.round(50 + (balance / total) * 50))) : 50;
    const bias = balance >= 0 ? 'BUY' : 'SELL';
    return { buy, sell, total, balance, accuracy, bias, recentCount };
}

function updateIctMemory(signalType) {
    const entry = { type: signalType, ts: new Date().toISOString() };
    ictMemory.push(entry);
    ictMemory = ictMemory.slice(-100);
    try {
        localStorage.setItem('ictMemory', JSON.stringify(ictMemory));
    } catch {}
}

function renderICTOverlay({ chartLeft, chartRight, chartTop, chartBottom, chartHeight, adjustedMin, adjustedMax, clampedPanBar }) {
    if (!ictVisible || ohlcBars.length < 3) return;

    const lastIndex = ohlcBars.length - 1;
    const recentWindow = ohlcBars.slice(Math.max(0, lastIndex - 12), lastIndex);
    const swingHigh = Math.max(...recentWindow.map(b => b.high));
    const swingLow = Math.min(...recentWindow.map(b => b.low));
    const lastBar = ohlcBars[lastIndex];
    const orderflow = getRecentOrderflowStats();

    const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;

    const labels = [];
    if (lastBar.high > swingHigh && lastBar.close < swingHigh) {
        labels.push({ type: 'Liquidity Sweep (Buy-side)', price: swingHigh, color: '#f59e0b' });
    }
    if (lastBar.low < swingLow && lastBar.close > swingLow) {
        labels.push({ type: 'Liquidity Sweep (Sell-side)', price: swingLow, color: '#f59e0b' });
    }
    if (lastBar.close > swingHigh) {
        labels.push({ type: 'BOS ↑', price: lastBar.close, color: '#22c55e' });
    }
    if (lastBar.close < swingLow) {
        labels.push({ type: 'BOS ↓', price: lastBar.close, color: '#ef4444' });
    }

    // FVG detection (simple 3-candle gap)
    const a = ohlcBars[lastIndex - 2];
    const b = ohlcBars[lastIndex - 1];
    const c = ohlcBars[lastIndex];
    if (a && b && c) {
        if (a.high < c.low) {
            // Bullish FVG
            const y1 = toY(c.low);
            const y2 = toY(a.high);
            ctx.fillStyle = 'rgba(34, 197, 94, 0.15)';
            ctx.fillRect(chartLeft + 6, Math.min(y1, y2), chartRight - chartLeft - 12, Math.abs(y2 - y1));
            labels.push({ type: 'Bullish FVG', price: (a.high + c.low) / 2, color: '#22c55e' });
        } else if (a.low > c.high) {
            // Bearish FVG
            const y1 = toY(a.low);
            const y2 = toY(c.high);
            ctx.fillStyle = 'rgba(239, 68, 68, 0.15)';
            ctx.fillRect(chartLeft + 6, Math.min(y1, y2), chartRight - chartLeft - 12, Math.abs(y2 - y1));
            labels.push({ type: 'Bearish FVG', price: (a.low + c.high) / 2, color: '#ef4444' });
        }
    }

    labels.forEach((label, idx) => {
        const y = toY(label.price);
        const x = chartLeft + 8;
        ctx.fillStyle = label.color;
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(label.type, x, y - (idx * 14));
    });

    // Accuracy & summary banner
    const bannerText = `ICT ${orderflow.bias} | Accuracy ${orderflow.accuracy}% | OF: ${orderflow.buy.toFixed(0)}/${orderflow.sell.toFixed(0)}`;
    ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
    ctx.fillRect(chartLeft + 6, chartTop + 6, 320, 20);
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
    ctx.strokeRect(chartLeft + 6, chartTop + 6, 320, 20);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '11px Arial';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(bannerText, chartLeft + 12, chartTop + 16);

    // Memory update
    const signalKey = labels.map(l => l.type).join('|') || 'NONE';
    if (signalKey !== lastIctSignalKey && labels.length > 0) {
        lastIctSignalKey = signalKey;
        updateIctMemory(signalKey);
    }
    const memoryMatches = ictMemory.filter(m => m.type === signalKey).length;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Arial';
    ctx.fillText(`Memory matches: ${memoryMatches}`, chartLeft + 12, chartTop + 34);
}

// ========== TIMEFRAME DROPDOWN HANDLER ==========
const timeframeSelect = document.getElementById('timeframeSelect');
if (timeframeSelect) {
    timeframeSelect.addEventListener('change', (e) => {
        const timeframe = e.target.value;
        switchTimeframe(timeframe);
    });
}

// Initialize 5m as active
switchTimeframe('1m');

// ========== ORDERFLOW BUTTON HANDLERS ==========
document.getElementById('orderflowVisBtn')?.addEventListener('click', () => {
    ictVisible = !ictVisible;
    document.getElementById('orderflowVisBtn').classList.toggle('active', ictVisible);
    showToast(ictVisible ? '📈 ICT Indicator ON' : '📈 ICT Indicator OFF', 1000);
    draw();
});

document.getElementById('domLadderBtn')?.addEventListener('click', () => {
    domLadderVisible = !domLadderVisible;
    const panel = document.getElementById('domLadderPanel');
    if (panel) {
        panel.classList.toggle('show', domLadderVisible);
        document.getElementById('domLadderBtn').classList.toggle('active', domLadderVisible);
    }
    showToast(domLadderVisible ? '🪜 DOM Ladder ON' : '🪜 DOM Ladder OFF', 1000);
    if (domLadderVisible) generateOrderflowData();
    updateDOMPanel();
});

// Cursor OHLC Display Button
document.getElementById('cursorOHLCBtn')?.addEventListener('click', () => {
    cursorOHLCVisible = !cursorOHLCVisible;
    document.getElementById('cursorOHLCBtn').classList.toggle('active', cursorOHLCVisible);
    showToast(cursorOHLCVisible ? '📋 Cursor OHLC ON' : '📋 Cursor OHLC OFF', 1000);
    draw();  // Redraw immediately to show/hide tooltip
});

// Sync cursor OHLC button state on load
const cursorOHLCBtn = document.getElementById('cursorOHLCBtn');
if (cursorOHLCBtn) cursorOHLCBtn.classList.toggle('active', cursorOHLCVisible);

// Raw Orders Display Button (NEW)
document.getElementById('rawOrdersBtn')?.addEventListener('click', () => {
    toggleRawOrdersVisibility();
    showToast(rawOrdersVisible ? '📊 Raw Orders ON' : '📊 Raw Orders OFF', 1000);
    renderRawOrders(rawOrders);
});

// ========== RAW ORDERS DRAG & RESIZE FUNCTIONALITY ==========
const rawOrdersFloatingPanel = document.getElementById('rawOrdersFloating');
const rawOrdersDragHandle = document.getElementById('rawOrdersDragHandle');
const rawOrdersResizeHandle = rawOrdersFloatingPanel?.querySelector('.resize-handle');

// Drag functionality
if (rawOrdersDragHandle && rawOrdersFloatingPanel) {
    let isDraggingRawOrders = false;
    let rawOrdersDragStartX = 0;
    let rawOrdersDragStartY = 0;
    let rawOrdersPanelStartX = 0;
    let rawOrdersPanelStartY = 0;

    rawOrdersDragHandle.addEventListener('mousedown', (e) => {
        // Don't drag if clicking the close button
        if (e.target.id === 'rawOrdersClose' || e.target.closest('#rawOrdersClose')) return;
        
        isDraggingRawOrders = true;
        rawOrdersDragStartX = e.clientX;
        rawOrdersDragStartY = e.clientY;
        
        // Get current position
        const rect = rawOrdersFloatingPanel.getBoundingClientRect();
        rawOrdersPanelStartX = rect.left;
        rawOrdersPanelStartY = rect.top;
        
        // Switch from right/top to left/top for absolute positioning
        rawOrdersFloatingPanel.style.left = rawOrdersPanelStartX + 'px';
        rawOrdersFloatingPanel.style.top = rawOrdersPanelStartY + 'px';
        rawOrdersFloatingPanel.style.right = 'auto';
        rawOrdersFloatingPanel.style.bottom = 'auto';
        
        rawOrdersDragHandle.style.cursor = 'grabbing';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDraggingRawOrders) return;
        
        const deltaX = e.clientX - rawOrdersDragStartX;
        const deltaY = e.clientY - rawOrdersDragStartY;
        
        const newX = rawOrdersPanelStartX + deltaX;
        const newY = rawOrdersPanelStartY + deltaY;
        
        // Keep panel within viewport bounds
        const maxX = window.innerWidth - rawOrdersFloatingPanel.offsetWidth;
        const maxY = window.innerHeight - rawOrdersFloatingPanel.offsetHeight;
        
        rawOrdersFloatingPanel.style.left = Math.max(0, Math.min(newX, maxX)) + 'px';
        rawOrdersFloatingPanel.style.top = Math.max(0, Math.min(newY, maxY)) + 'px';
    });

    document.addEventListener('mouseup', () => {
        if (isDraggingRawOrders) {
            isDraggingRawOrders = false;
            rawOrdersDragHandle.style.cursor = 'move';
        }
    });
}

// Resize functionality
if (rawOrdersResizeHandle && rawOrdersFloatingPanel) {
    let isResizingRawOrders = false;
    let resizeStartX = 0;
    let resizeStartY = 0;
    let startWidth = 0;
    let startHeight = 0;

    rawOrdersResizeHandle.addEventListener('mousedown', (e) => {
        isResizingRawOrders = true;
        resizeStartX = e.clientX;
        resizeStartY = e.clientY;
        startWidth = rawOrdersFloatingPanel.offsetWidth;
        startHeight = rawOrdersFloatingPanel.offsetHeight;
        e.preventDefault();
        e.stopPropagation();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizingRawOrders) return;
        
        const deltaX = e.clientX - resizeStartX;
        const deltaY = e.clientY - resizeStartY;
        
        const newWidth = Math.max(300, startWidth + deltaX);  // Min width 300px
        const newHeight = Math.max(400, startHeight + deltaY);  // Min height 400px
        
        rawOrdersFloatingPanel.style.width = newWidth + 'px';
        rawOrdersFloatingPanel.style.height = newHeight + 'px';
    });

    document.addEventListener('mouseup', () => {
        if (isResizingRawOrders) {
            isResizingRawOrders = false;
        }
    });
}

// AI Mentor Toggle Button
document.getElementById('mentorToggleBtn')?.addEventListener('click', () => {
    const mentorPanel = document.getElementById('mentor');
    const mentorToggleBtn = document.getElementById('mentorToggleBtn');
    const layoutDiv = document.getElementById('layout');
    
    if (mentorPanel && layoutDiv) {
        mentorPanel.classList.toggle('collapsed');
        layoutDiv.classList.toggle('mentor-collapsed');
        mentorToggleBtn.classList.toggle('active');
        
        const isOpen = !mentorPanel.classList.contains('collapsed');
        showToast(isOpen ? '🤖 AI Mentor OPEN' : '🤖 AI Mentor CLOSED', 1000);
        
        // Trigger canvas resize after transition
        setTimeout(() => {
            resizeCanvas();
            draw();
        }, 300);
    }
});

// STEP 7: Position Panel Button
document.getElementById('positionPanelBtn')?.addEventListener('click', () => {
    positionPanelVisible = !positionPanelVisible;
    const panel = document.getElementById('positionPanel');
    if (panel) {
        panel.style.display = positionPanelVisible ? 'block' : 'none';
        document.getElementById('positionPanelBtn').classList.toggle('active', positionPanelVisible);
    }
    showToast(positionPanelVisible ? '📍 Positions ON' : '📍 Positions OFF', 1000);
    if (positionPanelVisible) updatePositionPanel();
});

// STEP 7: Position Panel Functions (Global)
window.togglePositionPanel = function() {
    positionPanelVisible = !positionPanelVisible;
    const panel = document.getElementById('positionPanel');
    if (panel) {
        panel.style.display = positionPanelVisible ? 'block' : 'none';
        document.getElementById('positionPanelBtn')?.classList.toggle('active', positionPanelVisible);
    }
};

window.showAddPositionForm = function() {
    const form = document.getElementById('addPositionForm');
    if (form) {
        form.style.display = 'block';
        // Pre-fill with current price
        if (ohlcBars.length > 0) {
            document.getElementById('positionEntry').value = ohlcBars[ohlcBars.length - 1].close.toFixed(2);
        }
    }
};

window.cancelAddPosition = function() {
    const form = document.getElementById('addPositionForm');
    if (form) form.style.display = 'none';
};

window.submitPosition = function() {
    const type = document.getElementById('positionType').value;
    const entry = document.getElementById('positionEntry').value;
    const size = document.getElementById('positionSize').value || 1;
    const stopLoss = document.getElementById('positionStopLoss').value || null;
    const takeProfit = document.getElementById('positionTakeProfit').value || null;
    
    if (!entry || parseFloat(entry) <= 0) {
        showToast('❌ Invalid entry price', 2000);
        return;
    }
    
    addPosition(type, entry, stopLoss, takeProfit, size);
    cancelAddPosition();
    
    // Clear form
    document.getElementById('positionEntry').value = '';
    document.getElementById('positionStopLoss').value = '';
    document.getElementById('positionTakeProfit').value = '';
    document.getElementById('positionSize').value = '1';
};

// Update orderflow data every 2 seconds
setInterval(() => {
    if (domLadderVisible) {
        generateOrderflowData();
        updateDOMPanel();
        draw();
    }
}, 2000);

console.log("✅ Chart initialized successfully");

