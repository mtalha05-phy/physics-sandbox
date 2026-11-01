/**
 * Quark AI Robot Mascot Visual Engine
 * Renders an expressive, animated, high-tech robot companion on HTML5 Canvas.
 */

class QuarkRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.mood = 'curious'; // 'curious', 'calculating', 'happy', 'thinking'
    this.blinkTimer = 0;
    this.isBlinking = false;
    this.animTime = 0;
    this.antennaPulse = 0;

    // Handle high DPI
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    this.width = rect.width || this.canvas.width;
    this.height = rect.height || this.canvas.height;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);

    this.startLoop();
  }

  setMood(mood) {
    if (['curious', 'calculating', 'happy', 'thinking'].includes(mood)) {
      this.mood = mood;
    }
  }

  startLoop() {
    const loop = (timestamp) => {
      this.update(timestamp);
      this.draw();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  update(timestamp) {
    this.animTime = timestamp * 0.003;
    this.antennaPulse = Math.sin(timestamp * 0.006) * 0.5 + 0.5;

    // Random blinking
    this.blinkTimer++;
    if (this.blinkTimer > 180 && Math.random() < 0.04) {
      this.isBlinking = true;
      this.blinkTimer = 0;
      setTimeout(() => { this.isBlinking = false; }, 150);
    }
  }

  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    ctx.clearRect(0, 0, w, h);

    const centerX = w / 2;
    const hoverY = (h / 2) + Math.sin(this.animTime * 1.5) * 4;

    // 1. Antenna
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(centerX, hoverY - 35);
    ctx.lineTo(centerX, hoverY - 50);
    ctx.stroke();

    // Antenna glowing orb
    const orbRadius = 5 + (this.antennaPulse * 2);
    const gradOrb = ctx.createRadialGradient(centerX, hoverY - 52, 1, centerX, hoverY - 52, orbRadius + 6);
    gradOrb.addColorStop(0, '#38bdf8');
    gradOrb.addColorStop(0.5, '#06b6d4');
    gradOrb.addColorStop(1, 'transparent');
    ctx.fillStyle = gradOrb;
    ctx.beginPath();
    ctx.arc(centerX, hoverY - 52, orbRadius + 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#e0f2fe';
    ctx.beginPath();
    ctx.arc(centerX, hoverY - 52, 4, 0, Math.PI * 2);
    ctx.fill();

    // 2. Ears / Headphone Node Accents
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    // Left ear
    ctx.beginPath();
    ctx.roundRect(centerX - 46, hoverY - 14, 8, 28, 4);
    ctx.fill();
    ctx.stroke();
    // Right ear
    ctx.beginPath();
    ctx.roundRect(centerX + 38, hoverY - 14, 8, 28, 4);
    ctx.fill();
    ctx.stroke();

    // 3. Robot Head Shell
    const headGrad = ctx.createLinearGradient(centerX - 35, hoverY - 35, centerX + 35, hoverY + 35);
    headGrad.addColorStop(0, '#1e293b');
    headGrad.addColorStop(1, '#0f172a');

    ctx.fillStyle = headGrad;
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(6, 182, 212, 0.35)';
    ctx.shadowBlur = 12;

    ctx.beginPath();
    ctx.roundRect(centerX - 38, hoverY - 35, 76, 70, 18);
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0; // reset shadow

    // 4. Digital Visor Screen
    ctx.fillStyle = '#030712';
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(centerX - 30, hoverY - 24, 60, 48, 12);
    ctx.fill();
    ctx.stroke();

    // 5. Expressive Cyan Eyes
    ctx.fillStyle = '#06b6d4';
    ctx.shadowColor = '#06b6d4';
    ctx.shadowBlur = 8;

    const eyeY = hoverY - 4;
    const eyeSpacing = 14;

    if (this.isBlinking) {
      // Blink horizontal slit
      ctx.fillRect(centerX - eyeSpacing - 8, eyeY, 14, 2);
      ctx.fillRect(centerX + eyeSpacing - 6, eyeY, 14, 2);
    } else if (this.mood === 'happy') {
      // Curved happy arches
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(centerX - eyeSpacing, eyeY, 6, Math.PI, 0);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(centerX + eyeSpacing, eyeY, 6, Math.PI, 0);
      ctx.stroke();
    } else if (this.mood === 'calculating') {
      // Spinning scan rings
      ctx.save();
      ctx.translate(centerX - eyeSpacing, eyeY);
      ctx.rotate(this.animTime * 4);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.strokeRect(-6, -6, 12, 12);
      ctx.restore();

      ctx.save();
      ctx.translate(centerX + eyeSpacing, eyeY);
      ctx.rotate(-this.animTime * 4);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.strokeRect(-6, -6, 12, 12);
      ctx.restore();
    } else {
      // Standard curious rounded eyes
      ctx.beginPath();
      ctx.roundRect(centerX - eyeSpacing - 7, eyeY - 7, 13, 14, 4);
      ctx.fill();

      ctx.beginPath();
      ctx.roundRect(centerX + eyeSpacing - 6, eyeY - 7, 13, 14, 4);
      ctx.fill();

      // Eye reflections
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(centerX - eyeSpacing - 3, eyeY - 3, 2, 0, Math.PI * 2);
      ctx.arc(centerX + eyeSpacing - 2, eyeY - 3, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

window.QuarkRenderer = QuarkRenderer;
