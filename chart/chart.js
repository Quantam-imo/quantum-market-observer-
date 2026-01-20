class Chart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
  }

  draw_candlestick(x, open, high, low, close, width) {
    const color = close >= open ? '#00ff00' : '#ff0000';
    
    // Wick
    this.ctx.strokeStyle = color;
    this.ctx.beginPath();
    this.ctx.moveTo(x, high);
    this.ctx.lineTo(x, low);
    this.ctx.stroke();

    // Body
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x - width / 2, Math.min(open, close), width, Math.abs(close - open));
  }

  draw_support_resistance(level, label) {
    this.ctx.strokeStyle = '#ffff00';
    this.ctx.setLineDash([5, 5]);
    this.ctx.beginPath();
    this.ctx.moveTo(0, level);
    this.ctx.lineTo(this.canvas.width, level);
    this.ctx.stroke();
    this.ctx.setLineDash([]);
  }
}
