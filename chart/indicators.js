class Indicators {
  static gann_fans(high, low, factor=1) {
    return {
      "50%": (high + low) / 2,
      "100%": abs(high - low) * factor,
      "200%": abs(high - low) * 2 * factor
    };
  }

  static moving_average(prices, period) {
    let ma = [];
    for (let i = period - 1; i < prices.length; i++) {
      let sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      ma.push(sum / period);
    }
    return ma;
  }

  static atr(highs, lows, closes, period=14) {
    let trs = [];
    for (let i = 1; i < highs.length; i++) {
      let tr = Math.max(
        highs[i] - lows[i],
        Math.abs(highs[i] - closes[i-1]),
        Math.abs(lows[i] - closes[i-1])
      );
      trs.push(tr);
    }
    return Indicators.moving_average(trs, period);
  }
}
