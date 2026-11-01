/**
 * Mission 1: The Impossible Wall - Visualization Engine
 * Renders rectangular potential barrier, quantum wavefunction oscillation,
 * probability density, classical particle trajectory, AND a probabilistic
 * single-particle quantum detector simulation distinguishing theoretical T
 * from individual measurement detection events.
 */

class TunnelingVisualizer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.resultData = null;
    this.animPhase = 0;
    this.animSpeed = 1.0;
    this.showWavefunction = true;
    this.showProbDensity = true;
    this.showClassicalParticle = true;
    this.showQuantumDetector = true;

    // Classical test particle trajectory state
    this.particleX = -1.5; // in nm coordinates
    this.particleDirection = 1; // 1 = right, -1 = left

    // Probabilistic Quantum Particle Measurement
    this.quantumPulses = [];
    this.detectedTransmitted = 0;
    this.detectedReflected = 0;
    this.lastFireTime = 0;
    this.autoFire = true;
  }

  setData(data) {
    this.resultData = data;
    if (this.particleX > (data.barrier_width_nm || 0.5) + 1.0) {
      this.particleX = -1.5;
      this.particleDirection = 1;
    }
    // Reset detection counts when barrier parameters change significantly
    this.detectedTransmitted = 0;
    this.detectedReflected = 0;
    this.quantumPulses = [];
  }

  fireSingleParticle() {
    this.quantumPulses.push({
      x: -2.0,
      state: 'approaching', // 'approaching', 'tunneled', 'reflected'
      speed: 1.6,
      opacity: 1.0,
      radius: 6,
    });
  }

  update(dt) {
    if (!this.resultData) return;
    this.animPhase += dt * 3.5 * this.animSpeed;

    const v0 = this.resultData.barrier_height_ev;
    const e = this.resultData.energy_ev;
    const a = this.resultData.barrier_width_nm;
    const T = this.resultData.quantum_transmission;

    // 1. Classical particle position update
    const baseSpeed = Math.sqrt(Math.max(0.1, e)) * 0.8 * this.animSpeed * dt;
    if (e < v0) {
      this.particleX += this.particleDirection * baseSpeed;
      if (this.particleX >= 0.0 && this.particleDirection === 1) {
        this.particleX = 0.0;
        this.particleDirection = -1; // Classical elastic bounce
      } else if (this.particleX < -2.0) {
        this.particleX = -2.0;
        this.particleDirection = 1;
      }
    } else {
      let currentSpeed = baseSpeed;
      if (this.particleX >= 0.0 && this.particleX <= a) {
        currentSpeed = Math.sqrt(Math.max(0.01, e - v0)) * 0.8 * this.animSpeed * dt;
      }
      this.particleX += currentSpeed;
      if (this.particleX > a + 2.0) {
        this.particleX = -2.0;
      }
    }

    // 2. Probabilistic Quantum Particles Update
    if (this.autoFire && this.showQuantumDetector) {
      this.lastFireTime += dt;
      if (this.lastFireTime > 1.2 && this.quantumPulses.length < 8) {
        this.fireSingleParticle();
        this.lastFireTime = 0;
      }
    }

    for (let i = this.quantumPulses.length - 1; i >= 0; i--) {
      const p = this.quantumPulses[i];

      if (p.state === 'approaching') {
        p.x += p.speed * dt * this.animSpeed;
        if (p.x >= 0.0) {
          // Quantum Measurement Collapse at the Barrier!
          // Does this individual quantum event tunnel or reflect?
          const willTunnel = Math.random() < T;
          if (willTunnel) {
            p.state = 'tunneled';
            p.x = a + 0.02; // Appears on transmitted side
            this.detectedTransmitted++;
          } else {
            p.state = 'reflected';
            p.speed = -p.speed; // Reflects back
            this.detectedReflected++;
          }
        }
      } else if (p.state === 'tunneled') {
        p.x += p.speed * dt * this.animSpeed;
        if (p.x > a + 2.0) {
          this.quantumPulses.splice(i, 1);
        }
      } else if (p.state === 'reflected') {
        p.x += p.speed * dt * this.animSpeed;
        if (p.x < -2.2) {
          this.quantumPulses.splice(i, 1);
        }
      }
    }
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.resultData || !this.resultData.spatial_grid_nm) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Awaiting quantum simulation parameters...', w / 2, h / 2);
      return;
    }

    const grid = this.resultData.spatial_grid_nm;
    const xMin = grid[0];
    const xMax = grid[grid.length - 1];
    const xRange = xMax - xMin;

    const v0 = this.resultData.barrier_height_ev;
    const e = this.resultData.energy_ev;
    const a = this.resultData.barrier_width_nm;
    const T = this.resultData.quantum_transmission;

    // Coordinate mapping functions
    const toScreenX = (x) => ((x - xMin) / xRange) * w;
    const baselineY = h * 0.65;
    const maxV = Math.max(10.0, v0 * 1.35, e * 1.35);
    const toScreenY = (v) => baselineY - (v / maxV) * (h * 0.48);

    // 1. Draw Background Reference Line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, baselineY);
    ctx.lineTo(w, baselineY);
    ctx.stroke();

    // 2. Draw Rectangular Potential Barrier V(x)
    const bLeft = toScreenX(0.0);
    const bRight = toScreenX(a);
    const bTop = toScreenY(v0);
    const bWidth = bRight - bLeft;
    const bHeight = baselineY - bTop;

    const barrierGrad = ctx.createLinearGradient(0, bTop, 0, baselineY);
    barrierGrad.addColorStop(0, 'rgba(245, 158, 11, 0.45)');
    barrierGrad.addColorStop(1, 'rgba(245, 158, 11, 0.08)');
    ctx.fillStyle = barrierGrad;
    ctx.fillRect(bLeft, bTop, bWidth, bHeight);

    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(245, 158, 11, 0.5)';
    ctx.shadowBlur = 10;
    ctx.strokeRect(bLeft, bTop, bWidth, bHeight);
    ctx.shadowBlur = 0;

    // Barrier Dimension Labels
    ctx.fillStyle = '#fbbf24';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`V₀ = ${v0.toFixed(1)} eV`, bLeft + bWidth / 2, bTop - 10);
    ctx.fillText(`Width a = ${a.toFixed(2)} nm`, bLeft + bWidth / 2, baselineY + 16);

    // 3. Draw Particle Total Energy Level E
    const energyY = toScreenY(e);
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(0, energyY);
    ctx.lineTo(w, energyY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#06b6d4';
    ctx.textAlign = 'left';
    ctx.fillText(`E = ${e.toFixed(2)} eV`, 14, energyY - 6);

    // 4. Quantum Probability Density |psi(x)|^2 Area Fill
    if (this.showProbDensity && this.resultData.prob_density) {
      const pDens = this.resultData.prob_density;
      const ampScale = h * 0.16;

      ctx.beginPath();
      ctx.moveTo(toScreenX(grid[0]), baselineY);

      for (let i = 0; i < grid.length; i++) {
        const sx = toScreenX(grid[i]);
        const sy = baselineY - pDens[i] * ampScale;
        ctx.lineTo(sx, sy);
      }
      ctx.lineTo(toScreenX(grid[grid.length - 1]), baselineY);
      ctx.closePath();

      const probGrad = ctx.createLinearGradient(0, baselineY - ampScale, 0, baselineY);
      probGrad.addColorStop(0, 'rgba(139, 92, 246, 0.45)');
      probGrad.addColorStop(1, 'rgba(139, 92, 246, 0.03)');
      ctx.fillStyle = probGrad;
      ctx.fill();
    }

    // 5. Dynamic Quantum Wavefunction Psi(x, t)
    if (this.showWavefunction && this.resultData.psi_real) {
      const psiR = this.resultData.psi_real;
      const psiI = this.resultData.psi_imag;
      const waveScale = h * 0.13;

      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 2.5;
      ctx.shadowColor = 'rgba(192, 132, 252, 0.6)';
      ctx.shadowBlur = 8;
      ctx.beginPath();

      const cosPhase = Math.cos(this.animPhase);
      const sinPhase = Math.sin(this.animPhase);

      for (let i = 0; i < grid.length; i++) {
        const sx = toScreenX(grid[i]);
        const dynamicPsi = psiR[i] * cosPhase + psiI[i] * sinPhase;
        const sy = energyY - dynamicPsi * waveScale;
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // 6. Classical Particle Comparison Track
    if (this.showClassicalParticle) {
      const classicalY = baselineY + 36;
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.25)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, classicalY);
      ctx.lineTo(w, classicalY);
      ctx.stroke();

      ctx.fillStyle = 'rgba(245, 158, 11, 0.2)';
      ctx.fillRect(bLeft, classicalY - 12, bWidth, 24);
      ctx.strokeStyle = '#f59e0b';
      ctx.strokeRect(bLeft, classicalY - 12, bWidth, 24);

      const ballScreenX = toScreenX(this.particleX);
      ctx.fillStyle = '#3b82f6';
      ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(ballScreenX, classicalY, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#93c5fd';
      ctx.font = '9px monospace';
      ctx.textAlign = 'center';
      const labelText = this.particleDirection === 1 ? 'Classical Ball →' : '← Classical Bounce';
      ctx.fillText(labelText, ballScreenX, classicalY - 10);
    }

    // 7. Probabilistic Quantum Measurement Track (Lower Lane)
    if (this.showQuantumDetector) {
      const detectorY = baselineY + 80;

      // Track line
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, detectorY);
      ctx.lineTo(w, detectorY);
      ctx.stroke();

      // Detector Screens on Left (Reflection) and Right (Transmission)
      const leftDetX = 25;
      const rightDetX = w - 25;

      // Left Detector (Reflection Counter)
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(leftDetX - 4, detectorY - 15, 8, 30);
      // Right Detector (Transmission Counter)
      ctx.fillStyle = '#10b981';
      ctx.fillRect(rightDetX - 4, detectorY - 15, 8, 30);

      // Render flying quantum wave packet pulses
      for (const p of this.quantumPulses) {
        const sx = toScreenX(p.x);
        let color = '#a855f7';
        if (p.state === 'tunneled') color = '#10b981';
        if (p.state === 'reflected') color = '#ef4444';

        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(sx, detectorY, p.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // Live Empirical Detection Telemetry vs Theoretical Model
      const totalClicks = this.detectedTransmitted + this.detectedReflected;
      const empiricalPct = totalClicks > 0 ? ((this.detectedTransmitted / totalClicks) * 100).toFixed(1) : '0.0';
      const theoreticalPct = (T * 100).toFixed(2);

      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(
        `🔬 Individual Quantum Hits: ${this.detectedTransmitted} Transmitted (Green) | ${this.detectedReflected} Reflected (Red) ` +
        `→ Empirical: ${empiricalPct}% | Calculated Probability T: ${theoreticalPct}%`,
        w / 2,
        detectorY + 28
      );
    }
  }
}

window.TunnelingVisualizer = TunnelingVisualizer;
