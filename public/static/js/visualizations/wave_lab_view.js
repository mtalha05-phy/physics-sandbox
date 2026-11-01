/**
 * Mission 4: The Wave Laboratory - Visualization Engine
 * Renders wave 1, wave 2 with relative phase shift, and their superposition resultant.
 */

class WaveLabVisualizer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resultData = null;
    this.animTime = 0;
  }

  setData(data) {
    this.resultData = data;
  }

  update(dt) {
    this.animTime += dt * 4.0;
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.resultData || !this.resultData.x_grid) return;

    const xGrid = this.resultData.x_grid;
    const w1 = this.resultData.wave1_values;
    const w2 = this.resultData.wave2_values;
    const wNet = this.resultData.superposed_values;

    const lane1Y = h * 0.22;
    const lane2Y = h * 0.50;
    const laneNetY = h * 0.80;

    const toX = (i) => (i / (xGrid.length - 1)) * w;
    const ampScale = 22;

    // Draw Lane 1: Wave 1 (Classical Blue)
    ctx.fillStyle = '#3b82f6';
    ctx.font = 'bold 10px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`Wave 1 (A₁ = ${this.resultData.amplitude_1})`, 16, lane1Y - 18);

    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < xGrid.length; i++) {
      const y = lane1Y - w1[i] * ampScale * Math.cos(this.animTime);
      if (i === 0) ctx.moveTo(toX(i), y);
      else ctx.lineTo(toX(i), y);
    }
    ctx.stroke();

    // Draw Lane 2: Wave 2 (Cyan) with Phase Shift
    ctx.fillStyle = '#06b6d4';
    ctx.fillText(`Wave 2 (A₂ = ${this.resultData.amplitude_2}, Phase Δφ = ${this.resultData.phase_diff_deg}°)`, 16, lane2Y - 18);

    ctx.strokeStyle = '#06b6d4';
    ctx.beginPath();
    for (let i = 0; i < xGrid.length; i++) {
      const y = lane2Y - w2[i] * ampScale * Math.cos(this.animTime);
      if (i === 0) ctx.moveTo(toX(i), y);
      else ctx.lineTo(toX(i), y);
    }
    ctx.stroke();

    // Draw Lane 3: Superposition Net Wave (Quantum Purple Glow)
    ctx.fillStyle = '#c084fc';
    ctx.fillText(`Resultant Superposition [${this.resultData.interference_type}] - Net Amp: ${this.resultData.resultant_amplitude}`, 16, laneNetY - 18);

    ctx.strokeStyle = '#a855f7';
    ctx.lineWidth = 3;
    ctx.shadowColor = 'rgba(168, 85, 247, 0.7)';
    ctx.shadowBlur = 10;
    ctx.beginPath();
    for (let i = 0; i < xGrid.length; i++) {
      const y = laneNetY - wNet[i] * ampScale * Math.cos(this.animTime);
      if (i === 0) ctx.moveTo(toX(i), y);
      else ctx.lineTo(toX(i), y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }
}

window.WaveLabVisualizer = WaveLabVisualizer;
