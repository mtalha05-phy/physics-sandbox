/**
 * Mission 5: The Classical–Quantum Boundary - Visualization Engine
 * Renders wave packet dispersion vs classical deterministic trajectory.
 */

class BoundaryVisualizer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resultData = null;
    this.simTimeProgress = 0;
  }

  setData(data) {
    this.resultData = data;
    this.simTimeProgress = 0;
  }

  update(dt) {
    this.simTimeProgress = (this.simTimeProgress + dt * 0.4) % 1.0;
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.resultData || !this.resultData.time_points_s) return;

    const tArr = this.resultData.time_points_s;
    const xCl = this.resultData.classical_center_m;
    const wQ = this.resultData.quantum_width_m;

    const centerY = h / 2;
    const trackStartX = 50;
    const trackEndX = w - 50;
    const trackWidth = trackEndX - trackStartX;

    // Center motion track
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(trackStartX, centerY);
    ctx.lineTo(trackEndX, centerY);
    ctx.stroke();

    // Current step in simulated progress
    const idx = Math.floor(this.simTimeProgress * (tArr.length - 1));
    const currX = trackStartX + (idx / (tArr.length - 1)) * trackWidth;
    const currWidthPx = Math.min(180, (wQ[idx] / wQ[0]) * 16);

    // 1. Quantum Wavepacket Dispersion Cloud (Purple Gradient)
    const cloudGrad = ctx.createRadialGradient(currX, centerY, 2, currX, centerY, currWidthPx + 10);
    cloudGrad.addColorStop(0, 'rgba(168, 85, 247, 0.7)');
    cloudGrad.addColorStop(0.5, 'rgba(168, 85, 247, 0.25)');
    cloudGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = cloudGrad;
    ctx.beginPath();
    ctx.arc(currX, centerY, currWidthPx + 10, 0, Math.PI * 2);
    ctx.fill();

    // 2. Classical Point Particle (Blue Solid Core)
    ctx.fillStyle = '#38bdf8';
    ctx.shadowColor = '#38bdf8';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(currX, centerY, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Header Meta
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`Target: ${this.resultData.mass_description}`, 20, 30);

    ctx.fillStyle = this.resultData.is_classical_approximation_valid ? '#10b981' : '#f59e0b';
    ctx.font = '11px monospace';
    ctx.fillText(`Spreading Factor: ${this.resultData.spreading_factor}x  |  Classical Regime Valid: ${this.resultData.is_classical_approximation_valid ? 'YES' : 'NO (Quantum Dispersion Dominates)'}`, 20, 50);

    // Scientific explanation footer
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(this.resultData.domain_explanation, w / 2, h - 20);
  }
}

window.BoundaryVisualizer = BoundaryVisualizer;
