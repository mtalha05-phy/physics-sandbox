/**
 * Mission 2: Wave or Particle? - Double-Slit Visualization Engine
 * Renders source, slits, photon/electron hits, and diffraction intensity patterns.
 */

class DoubleSlitVisualizer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resultData = null;
    this.particles = [];
    this.hits = [];
    this.maxHits = 400;
    this.animTime = 0;
  }

  setData(data) {
    this.resultData = data;
    this.hits = []; // reset screen hits on configuration change
    this.particles = [];
  }

  update(dt) {
    if (!this.resultData) return;
    this.animTime += dt * 3.0;

    // Spawn quantum particles from electron source
    if (Math.random() < 0.4 && this.particles.length < 35) {
      this.particles.push({
        x: 30,
        y: this.canvas.height / 2 + (Math.random() - 0.5) * 40,
        vx: 140 + Math.random() * 40,
        vy: (Math.random() - 0.5) * 20,
        passedSlits: false,
      });
    }

    const slitX = this.canvas.width * 0.35;
    const screenX = this.canvas.width * 0.85;

    // Move particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx * dt;
      p.y += p.vy * dt;

      // Pass slits
      if (!p.passedSlits && p.x >= slitX) {
        p.passedSlits = true;
        // Sample screen arrival y based on quantum probability distribution!
        if (this.resultData.quantum_probability) {
          const probs = this.resultData.quantum_probability;
          const pos = this.resultData.screen_positions_mm;
          // Random sample from CDF
          let rand = Math.random();
          let cum = 0;
          let sum = probs.reduce((a, b) => a + b, 0);
          let targetY = this.canvas.height / 2;
          for (let j = 0; j < probs.length; j++) {
            cum += probs[j] / sum;
            if (rand <= cum) {
              const mmY = pos[j];
              targetY = (this.canvas.height / 2) + mmY * 26;
              break;
            }
          }
          // Redirect particle trajectory toward target point on screen
          const remainingDist = screenX - slitX;
          const flightTime = remainingDist / p.vx;
          p.vy = (targetY - p.y) / flightTime;
        }
      }

      // Hit screen
      if (p.x >= screenX) {
        this.hits.push({ y: p.y, alpha: 1.0 });
        if (this.hits.length > this.maxHits) this.hits.shift();
        this.particles.splice(i, 1);
      }
    }
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.resultData) return;

    const slitX = w * 0.35;
    const screenX = w * 0.85;

    // 1. Particle Source (Left)
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(35, h / 2, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#06b6d4';
    ctx.font = 'bold 10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Source', 35, h / 2 + 26);

    // 2. Barrier with Slits (Center)
    ctx.fillStyle = '#334155';
    const slitSepPx = this.resultData.slit_separation_um * 14;
    const slitGap = 16;
    const numSlits = this.resultData.num_slits;

    if (numSlits === 1) {
      // 1 Central Slit
      ctx.fillRect(slitX, 0, 8, h / 2 - slitGap / 2);
      ctx.fillRect(slitX, h / 2 + slitGap / 2, 8, h);
    } else {
      // 2 Slits
      const y1 = h / 2 - slitSepPx / 2;
      const y2 = h / 2 + slitSepPx / 2;

      ctx.fillRect(slitX, 0, 8, y1 - slitGap / 2);
      ctx.fillRect(slitX, y1 + slitGap / 2, 8, (y2 - slitGap / 2) - (y1 + slitGap / 2));
      ctx.fillRect(slitX, y2 + slitGap / 2, 8, h);

      // Detector indicators if enabled
      if (this.resultData.which_path_enabled) {
        ctx.fillStyle = '#ef4444';
        ctx.shadowColor = '#ef4444';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(slitX + 4, y1, 5, 0, Math.PI * 2);
        ctx.arc(slitX + 4, y2, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#fca5a5';
        ctx.font = 'bold 9px monospace';
        ctx.fillText('DETECTOR ON', slitX + 4, y1 - 12);
      }
    }

    // 3. Screen (Right)
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(screenX, 20);
    ctx.lineTo(screenX, h - 20);
    ctx.stroke();

    // 4. Draw Individual Quantum Particle Hits on Screen
    for (const hit of this.hits) {
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(screenX, hit.y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // 5. Draw Flying Quantum Particles / Wavelets
    for (const p of this.particles) {
      ctx.fillStyle = '#c084fc';
      ctx.shadowColor = '#c084fc';
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // 6. Intensity / Probability Curve Projection on Far Right
    if (this.resultData.quantum_probability) {
      const qP = this.resultData.quantum_probability;
      const pos = this.resultData.screen_positions_mm;
      const maxCurveWidth = w * 0.12;

      ctx.strokeStyle = this.resultData.which_path_enabled ? '#f59e0b' : '#a855f7';
      ctx.lineWidth = 2;
      ctx.beginPath();

      for (let i = 0; i < qP.length; i++) {
        const py = h / 2 + pos[i] * 26;
        const px = screenX + qP[i] * maxCurveWidth;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      ctx.fillStyle = this.resultData.which_path_enabled ? '#f59e0b' : '#c084fc';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'left';
      const label = this.resultData.which_path_enabled ? 'Incoherent Sum' : 'Interference Fringes';
      ctx.fillText(label, screenX + 10, 30);
    }
  }
}

window.DoubleSlitVisualizer = DoubleSlitVisualizer;
