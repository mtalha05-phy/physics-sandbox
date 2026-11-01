/**
 * Mission 3: The Uncertainty Challenge - Visualization Engine
 * Displays side-by-side Position Distribution rho(x) and Momentum Distribution phi(p).
 */

class UncertaintyVisualizer {
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
    this.animTime += dt * 3.0;
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.resultData || !this.resultData.x_grid_nm) return;

    const midX = w / 2;
    const chartWidth = midX - 40;
    const chartHeight = h * 0.65;
    const baselineY = h * 0.8;

    // 1. Position Space Box (Left)
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.strokeRect(20, 20, chartWidth, h - 40);

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('POSITION SPACE |ψ(x)|²', 30, 42);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.fillText(`Δx = ${this.resultData.delta_x_nm} nm`, 30, 58);

    // Plot rho(x)
    const xGrid = this.resultData.x_grid_nm;
    const rhoX = this.resultData.psi_prob_density_x;
    const psiReal = this.resultData.psi_real_x;

    const xMin = xGrid[0];
    const xMax = xGrid[xGrid.length - 1];
    const toScreenXPos = (x) => 20 + ((x - xMin) / (xMax - xMin)) * chartWidth;

    // Wave real part oscillation
    ctx.strokeStyle = '#c084fc';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < xGrid.length; i++) {
      const sx = toScreenXPos(xGrid[i]);
      const sy = baselineY - (chartHeight * 0.45) - psiReal[i] * (chartHeight * 0.35) * Math.cos(this.animTime);
      if (i === 0) ctx.moveTo(sx, sy);
      else ctx.lineTo(sx, sy);
    }
    ctx.stroke();

    // Probability density fill
    ctx.beginPath();
    ctx.moveTo(toScreenXPos(xGrid[0]), baselineY);
    for (let i = 0; i < xGrid.length; i++) {
      const sx = toScreenXPos(xGrid[i]);
      const sy = baselineY - rhoX[i] * chartHeight * 0.85;
      ctx.lineTo(sx, sy);
    }
    ctx.lineTo(toScreenXPos(xGrid[xGrid.length - 1]), baselineY);
    ctx.closePath();

    const gradX = ctx.createLinearGradient(0, baselineY - chartHeight, 0, baselineY);
    gradX.addColorStop(0, 'rgba(56, 189, 248, 0.4)');
    gradX.addColorStop(1, 'rgba(56, 189, 248, 0.05)');
    ctx.fillStyle = gradX;
    ctx.fill();

    // 2. Momentum Space Box (Right)
    const rightBoxLeft = midX + 20;
    ctx.strokeStyle = '#1e293b';
    ctx.strokeRect(rightBoxLeft, 20, chartWidth, h - 40);

    ctx.fillStyle = '#a855f7';
    ctx.font = 'bold 12px monospace';
    ctx.fillText('MOMENTUM SPACE |φ(p)|²', rightBoxLeft + 10, 42);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.fillText(`Δp = ${this.resultData.delta_p_si} kg·m/s`, rightBoxLeft + 10, 58);

    // Plot rho(p)
    const pGrid = this.resultData.p_grid_scaled;
    const rhoP = this.resultData.phi_prob_density_p;
    const pMin = pGrid[0];
    const pMax = pGrid[pGrid.length - 1];
    const toScreenXMom = (p) => rightBoxLeft + ((p - pMin) / (pMax - pMin)) * chartWidth;

    ctx.beginPath();
    ctx.moveTo(toScreenXMom(pGrid[0]), baselineY);
    for (let i = 0; i < pGrid.length; i++) {
      const sx = toScreenXMom(pGrid[i]);
      const sy = baselineY - rhoP[i] * chartHeight * 0.85;
      ctx.lineTo(sx, sy);
    }
    ctx.lineTo(toScreenXMom(pGrid[pGrid.length - 1]), baselineY);
    ctx.closePath();

    const gradP = ctx.createLinearGradient(0, baselineY - chartHeight, 0, baselineY);
    gradP.addColorStop(0, 'rgba(168, 85, 247, 0.4)');
    gradP.addColorStop(1, 'rgba(168, 85, 247, 0.05)');
    ctx.fillStyle = gradP;
    ctx.fill();

    // Bottom Center Banner showing Delta x * Delta p >= hbar / 2
    ctx.fillStyle = '#f59e0b';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    const prodStr = `Δx · Δp = ${(this.resultData.ratio_to_minimum).toFixed(2)} × (ℏ / 2)  [Heisenberg Limit Saturated: ${this.resultData.is_minimum_uncertainty ? 'YES' : 'NO'}]`;
    ctx.fillText(prodStr, w / 2, h - 8);
  }
}

window.UncertaintyVisualizer = UncertaintyVisualizer;
