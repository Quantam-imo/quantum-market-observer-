import { createChart } from 'lightweight-charts';

const histogramChart = createChart(
  document.getElementById('orderflow'),
  {
    height: 180,
    layout: {
      background: { color: '#0b0f14' },
      textColor: '#cfd8dc',
    },
    grid: {
      vertLines: { color: '#1e222d' },
      horzLines: { color: '#1e222d' },
    }
  }
);

const buySeries = histogramChart.addHistogramSeries({
  color: '#2ecc71',
  priceFormat: { type: 'volume' }
});

const sellSeries = histogramChart.addHistogramSeries({
  color: '#e74c3c',
  priceFormat: { type: 'volume' }
});

export function updateOrderFlow(data) {
  const buy = [];
  const sell = [];

  data.forEach(([time, bar]) => {
    buy.push({
      time: time,
      value: bar.buy
    });
    sell.push({
      time: time,
      value: -bar.sell
    });
  });

  buySeries.setData(buy);
  sellSeries.setData(sell);
}
