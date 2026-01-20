import { createChart } from "https://unpkg.com/lightweight-charts/dist/lightweight-charts.esm.production.js";

/* ============================
   CHART INITIALIZATION
   ============================ */

const chart = createChart(document.getElementById("chart"), {
    layout: {
        background: { color: "#0B0F14" },
        textColor: "#D9DEE7",
        fontFamily: "Inter, sans-serif"
    },
    grid: {
        vertLines: { color: "#1F2A38" },
        horzLines: { color: "#1F2A38" }
    },
    rightPriceScale: {
        borderColor: "#1F2A38"
    },
    timeScale: {
        borderColor: "#1F2A38",
        timeVisible: true,
        secondsVisible: false
    },
    crosshair: {
        mode: 1
    }
});

/* ============================
   PRICE SERIES
   ============================ */

const candleSeries = chart.addCandlestickSeries({
    upColor: "#26A69A",
    downColor: "#EF5350",
    borderUpColor: "#26A69A",
    borderDownColor: "#EF5350",
    wickUpColor: "#26A69A",
    wickDownColor: "#EF5350"
});

/* ============================
   LOAD PRICE DATA
   (Replace with live CME feed)
   ============================ */

fetch("/api/price")
    .then(res => res.json())
    .then(data => {
        candleSeries.setData(data);
    });

/* ============================
   GANN LEVELS
   ============================ */

function drawGannLevel(price, label) {
    const line = chart.addLineSeries({
        color: "#FFD54F",
        lineWidth: 1,
        lineStyle: 2
    });
    line.setData([
        { time: 0, value: price },
        { time: 9999999999, value: price }
    ]);
}

/* Example */
drawGannLevel(3369, "200% Range");
drawGannLevel(3326, "Equilibrium");

/* ============================
   ICEBERG / ABSORPTION ZONES
   ============================ */

function drawIcebergZone(fromPrice, toPrice, fromTime, toTime) {
    chart.addPriceLine({
        price: fromPrice,
        color: "rgba(255, 82, 82, 0.35)",
        lineWidth: 0,
        axisLabelVisible: false
    });
    chart.addPriceLine({
        price: toPrice,
        color: "rgba(255, 82, 82, 0.35)",
        lineWidth: 0,
        axisLabelVisible: false
    });
}

/* Example Iceberg Zone */
drawIcebergZone(3358, 3369);

/* ============================
   SESSION BOXES
   ============================ */

function drawSession(start, end, color) {
    const box = chart.addHistogramSeries({
        color,
        priceFormat: { type: "volume" },
        priceScaleId: ""
    });
    box.setData([
        { time: start, value: 1 },
        { time: end, value: 1 }
    ]);
}

/* Example Sessions */
drawSession(1700000000, 1700007200, "rgba(0, 120, 255, 0.08)"); // Asia
drawSession(1700010000, 1700017200, "rgba(0, 200, 150, 0.08)"); // London
drawSession(1700020000, 1700027200, "rgba(255, 140, 0, 0.08)"); // NY

/* ============================
   RESIZE HANDLING
   ============================ */

window.addEventListener("resize", () => {
    chart.resize(
        document.getElementById("chart").clientWidth,
        document.getElementById("chart").clientHeight
    );
});
