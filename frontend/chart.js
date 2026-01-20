const canvas = document.getElementById("chart");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth * 0.75;
canvas.height = window.innerHeight * 0.9;

let bars = [];

async function fetchData() {
    const res = await fetch("http://127.0.0.1:8000/status");
    const data = await res.json();

    if (!data.price) return;

    bars.push({
        price: data.price,
        buys: data.orderflow.buys,
        sells: data.orderflow.sells,
        iceberg: data.iceberg,
        decision: data.decision,
        narrative: data.narrative
    });

    if (bars.length > 60) bars.shift();

    updateMentor(data);
    draw();
}

function updateMentor(data) {
    document.getElementById("mentorText").innerText =
        data.narrative || "Monitoring market...";

    document.getElementById("confidence").innerText =
        data.decision
            ? `Decision: ${data.decision.decision} (${data.decision.confidence}%)`
            : "";
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const maxQty = Math.max(...bars.map(b => Math.max(b.buys, b.sells)), 1);
    const priceMin = Math.min(...bars.map(b => b.price));
    const priceMax = Math.max(...bars.map(b => b.price));

    const barWidth = canvas.width / bars.length;

    bars.forEach((b, i) => {
        const x = i * barWidth + barWidth / 2;

        // PRICE SCALE
        const y =
            canvas.height -
            ((b.price - priceMin) / (priceMax - priceMin + 0.01)) *
                (canvas.height * 0.6) -
            50;

        // BUY QTY BAR
        const buyH = (b.buys / maxQty) * 80;
        ctx.fillStyle = "#2ea043";
        ctx.fillRect(x - 6, canvas.height - buyH, 5, buyH);

        // SELL QTY BAR
        const sellH = (b.sells / maxQty) * 80;
        ctx.fillStyle = "#f85149";
        ctx.fillRect(x + 1, canvas.height - sellH, 5, sellH);

        // PRICE DOT
        ctx.fillStyle = "#e6e6e6";
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();

        // ICEBERG MARKER
        if (b.iceberg) {
            ctx.fillStyle = "#ff9f1c";
            ctx.fillRect(x - 4, y - 14, 8, 8);
        }
    });
}

// REFRESH SPEED (IMPORTANT)
setInterval(fetchData, 1000); // 🔥 1s = institutional speed
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
