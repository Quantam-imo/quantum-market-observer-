export function drawIcebergZones(chart, zones) {
  zones.forEach(zone => {
    chart.addPriceLine({
      price: zone.price_high,
      color: zone.side === "SELL" ? '#ff5252' : '#2ecc71',
      lineWidth: 2,
      title: `${zone.session} ICEBERG`
    });
  });
}
