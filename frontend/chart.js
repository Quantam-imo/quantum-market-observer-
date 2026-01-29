const canvas = document.getElementById("chart");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth * 0.75;
canvas.height = window.innerHeight * 0.9;

let ohlcBars = []; // Store OHLC data like TradingView

// Build API base compatible with Codespaces (port encoded in hostname)
const proto = window.location.protocol;
const host = window.location.hostname; // e.g., <name>-8080.app.github.dev or localhost
let apiHost = host;

// If running on app.github.dev, swap the port segment in hostname
const m = host.match(/^(.*)-(\d+)\.app\.github\.dev$/);
if (m) {
    apiHost = `${m[1]}-8000.app.github.dev`;
}
// Local development: if served from localhost, target port 8000
if (host === "localhost" || host === "127.0.0.1") {
    apiHost = `${host}:8000`;
}

const API_BASE = `${proto}//${apiHost}`;

async function fetchData() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/mentor`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: 'XAUUSD', refresh: true })
        });
        const data = await res.json();

        if (!data.current_price) return;

        // Add to OHLC bars
        if (ohlcBars.length === 0 || ohlcBars[ohlcBars.length - 1].close !== data.current_price) {
            ohlcBars.push({
                open: data.current_price,
                high: data.current_price,
                low: data.current_price,
                close: data.current_price,
                volume: data.iceberg_activity?.volume_spike_ratio * 10 || 50,
                icebergDetected: data.iceberg_activity?.detected || false,
                decision: data.ai_verdict,
                timestamp: new Date().getTime()
            });
        } else {
            // Update the last candle
            const last = ohlcBars[ohlcBars.length - 1];
            last.high = Math.max(last.high, data.current_price);
            last.low = Math.min(last.low, data.current_price);
            last.close = data.current_price;
            last.volume = data.iceberg_activity?.volume_spike_ratio * 10 || 50;
        }

        if (ohlcBars.length > 100) ohlcBars.shift();

        updateMentor(data);
        draw();
    } catch (error) {
        console.error("Failed to fetch data:", error);
        document.getElementById("mentorText").innerText = "Connection error. Retrying...";
    }
}

function updateMentor(data) {
    const htfTrend = data.htf_structure?.trend || 'N/A';
    const bias = data.htf_structure?.bias || 'NEUTRAL';
    const confidence = data.confidence_percent || 0;
    const verdict = data.ai_verdict || 'WAIT';
    
    document.getElementById("mentorText").innerHTML = `
        <strong>AI Verdict:</strong> ${verdict}<br>
        <strong>HTF Trend:</strong> ${htfTrend} (${bias})<br>
        <strong>Session:</strong> ${data.session || 'N/A'}<br>
        <strong>Price:</strong> $${data.current_price?.toFixed(2) || '0.00'}<br>
        <strong>Iceberg:</strong> ${data.iceberg_activity?.detected ? '🧊 Active' : 'None'}<br>
        <strong>Entry:</strong> ${data.entry_trigger || 'Waiting...'}<br>
    `;

    document.getElementById("confidence").innerHTML = `
        <strong>Confidence:</strong> ${confidence}%<br>
        <div style="background: #1c2430; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 4px;">
            <div style="background: ${confidence > 70 ? '#2ea043' : '#f85149'}; width: ${confidence}%; height: 100%;"></div>
        </div>
    `;
}

function draw() {
    try {
        ctx.fillStyle = "#0b0f14";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (!ohlcBars || ohlcBars.length === 0) {
            ctx.fillStyle = "#e6e6e6";
            ctx.font = "14px Arial";
            ctx.textAlign = "left";
            ctx.fillText("Loading data...", 20, 30);
            return;
        }

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
        const adjustedMax = priceMax + pricePadding;
        const adjustedMin = priceMin - pricePadding;

    // Chart dimensions (TradingView style)
    const chartLeft = 70;
    const chartRight = canvas.width - 30;
    const chartTop = 50;
    const chartBottom = canvas.height - 120;
    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;
    const volumeHeight = 50;

    // ========== DRAW BACKGROUND GRID ==========
    ctx.strokeStyle = "#1c2430";
    ctx.lineWidth = 1;

    // Horizontal grid lines (using adjusted price range for alignment with labels)
    ctx.strokeStyle = '#1e1e1e';
    ctx.lineWidth = 1;
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
    const timeIntervalForGrid = Math.max(1, Math.floor(ohlcBars.length / 8));

    // Add vertical gridlines for time reference
    ctx.strokeStyle = '#1e1e1e';
    ctx.lineWidth = 0.5;
    for (let i = 0; i < ohlcBars.length; i += timeIntervalForGrid) {
        const x = chartLeft + (candleSpacingForGrid / 2) + (i * candleSpacingForGrid);
        ctx.beginPath();
        ctx.moveTo(x, chartTop);
        ctx.lineTo(x, chartBottom);
        ctx.stroke();
    }

    // ========== DRAW PRICE AXIS (LEFT) ==========
    ctx.fillStyle = "#888";
    ctx.font = "13px Arial";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let i = 0; i <= 5; i++) {
        const price = adjustedMin + (adjustedMax - adjustedMin) * (i / 5);
        const y = chartBottom - (i / 5) * chartHeight;
        ctx.fillText(price.toFixed(2), chartLeft - 15, y);
    }

    // ========== DRAW CANDLESTICKS (TradingView style) ==========
    // Use pre-calculated candleSpacing for consistency
    const candleSpacingValue = candleSpacingForGrid;
    const candleWidth = Math.max(2, candleSpacingValue * 0.6); // 60% of spacing, min 2px

    ohlcBars.forEach((candle, i) => {
        const x = chartLeft + candleSpacingValue / 2 + (i * candleSpacingValue);

        // Price to Y coordinate conversion (with padding)
        const toY = (price) => chartBottom - ((price - adjustedMin) / (adjustedMax - adjustedMin)) * chartHeight;

        const highY = toY(candle.high);
        const lowY = toY(candle.low);
        // Clamp Y coordinates to chart bounds to prevent wicks from extending beyond chart
        const clampedHighY = Math.max(highY, chartTop);
        const clampedLowY = Math.min(lowY, chartBottom);

        // Determine if bullish (green) or bearish (red)
        const isBullish = candle.close >= candle.open;
        const bodyColor = isBullish ? "#2ea043" : "#f85149";
        const wickColor = isBullish ? "#4da05f" : "#ff8b8b";

        // Draw wick (high-low line)
        ctx.strokeStyle = wickColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, clampedHighY);
        ctx.lineTo(x, clampedLowY);
        ctx.stroke();

        // Draw body (open-close rectangle) with minimum height
        ctx.fillStyle = bodyColor;
        const bodyTop = Math.min(openY, closeY);
        let bodyHeight = Math.abs(closeY - openY);
        if (bodyHeight < 3) bodyHeight = 3; // Minimum 3px for flat candles
        ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

        // Draw iceberg marker if icebergDetected
        if (candle.icebergDetected) {
            ctx.fillStyle = "#ff9f1c";
            ctx.beginPath();
            // Position marker inside chart area, just below the high
            const markerY = Math.max(clampedHighY + 5, chartTop + 5);
            ctx.arc(x, markerY, 3, 0, Math.PI * 2);
            ctx.fill();
        }
    });

    // ========== DRAW VOLUME BARS ==========
    const maxVolume = Math.max(...ohlcBars.map(b => b.volume), 100);
    const volumeChartTop = chartBottom + 10;

    ohlcBars.forEach((candle, i) => {
        const x = chartLeft + candleSpacingValue / 2 + (i * candleSpacingValue);
        const rawVolHeight = (candle.volume / maxVolume) * volumeHeight;
        // Clamp volume height to prevent overflow beyond chart boundary
        const volHeight = Math.min(rawVolHeight, volumeHeight);
        const volColor = candle.close >= candle.open ? "#2ea04388" : "#f8514488";

        ctx.fillStyle = volColor;
        ctx.fillRect(x - candleWidth / 2, volumeChartTop + volumeHeight - volHeight, candleWidth, volHeight);
    });

    // Volume axis label
    ctx.fillStyle = "#888";
    ctx.font = "10px Arial";
    ctx.textAlign = "right";
    ctx.fillText("VOL", chartLeft - 10, volumeChartTop + volumeHeight / 2);

    // ========== DRAW TIME AXIS (BOTTOM) ==========
    ctx.fillStyle = "#888";
    ctx.font = "11px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    for (let i = 0; i < ohlcBars.length; i += timeIntervalForGrid) {
        const x = chartLeft + candleSpacingForGrid / 2 + (i * candleSpacingForGrid);
        const hour = (9 + Math.floor(i / 4)) % 24;
        const min = (i % 4) * 15;
        ctx.fillText(`${hour}:${String(min).padStart(2, '0')}`, x, chartBottom + 30);
    }

    // ========== DRAW TITLE & PRICE ==========
    if (ohlcBars.length > 0) {
        const lastCandle = ohlcBars[ohlcBars.length - 1];
        ctx.fillStyle = "#e6e6e6";
        ctx.font = "bold 18px Arial";
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText(`XAUUSD: $${lastCandle.close.toFixed(2)}`, 20, 15);

        // Price change info
        const priceChange = lastCandle.close - lastCandle.open;
        const changePercent = ((priceChange / lastCandle.open) * 100).toFixed(2);
        const changeColor = priceChange >= 0 ? "#2ea043" : "#f85149";
        ctx.fillStyle = changeColor;
        ctx.font = "14px Arial";
        ctx.fillText(`${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)} (${changePercent}%)`, 20, 38);
        }
    } catch (error) {
        console.error("Draw error:", error);
        ctx.fillStyle = "#ff6b6b";
        ctx.font = "12px Arial";
        ctx.fillText("Chart rendering error", 20, 30);
    }
}

// ========== INITIALIZATION ==========
fetchData(); // Initial load
setInterval(fetchData, 15000); // Refresh every 15 seconds
window.addEventListener("resize", () => {
    canvas.width = window.innerWidth * 0.75;
    canvas.height = window.innerHeight * 0.9;
    draw();
});
