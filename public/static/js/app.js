/**
 * ScienceQuest - master frontend controller.
 *
 * Security note: nothing that comes from the network or from other players (chat text, usernames,
 * Quark answers, option texts) is ever inserted with innerHTML. Everything is built with DOM APIs
 * (textContent / createElement), so markup in user input is displayed, never executed. This also
 * lets the site run under a strict Content-Security-Policy with `script-src 'self'`.
 */

const VIZ_BY_MISSION = {
  mission_1: () => TunnelingVisualizer,
  mission_2: () => DoubleSlitVisualizer,
  mission_3: () => UncertaintyVisualizer,
  mission_4: () => WaveLabVisualizer,
  mission_5: () => BoundaryVisualizer,
};

const TOGGLE_FLAGS = ['showWavefunction', 'showProbDensity', 'showClassicalParticle', 'showQuantumDetector'];

/* ---------------------------------------------------------------- helpers */
function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null) continue;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'style' && typeof value === 'object') Object.assign(node.style, value);
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    if (child === undefined || child === null) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function fmt(x, digits = 3) {
  const n = Number(x);
  if (!Number.isFinite(n)) return '–';
  if (n !== 0 && (Math.abs(n) >= 1e5 || Math.abs(n) < 1e-3)) return n.toExponential(2);
  return Number(n.toPrecision(digits)).toString();
}

function rankFor(points) {
  if (points >= 500) return 'Principal Quantum Investigator';
  if (points >= 200) return 'Senior Research Fellow';
  if (points >= 100) return 'Staff Physicist';
  return 'Junior Investigator';
}

/** Per-mission telemetry rows: [label, value] x3 */
const HUD_ROWS = {
  mission_1: p => [
    ['Incident Energy E:', `${fmt(p.energy_ev)} eV`],
    ['Barrier Height V₀:', `${fmt(p.barrier_height_ev)} eV`],
    ['Transmission T (quantum):', `${(p.quantum_transmission * 100).toFixed(2)}%`],
  ],
  mission_2: p => [
    ['Wavelength λ:', `${fmt(p.wavelength_nm)} nm`],
    ['Slit separation d:', `${fmt(p.slit_separation_um)} µm`],
    ['Fringe visibility V:', p.num_slits === 1 ? 'single slit' : `${Math.round(p.visibility * 100)}%`],
  ],
  mission_3: p => [
    ['Position spread Δx:', `${fmt(p.delta_x_nm)} nm`],
    ['Momentum spread Δp:', `${fmt(p.delta_p_si)} kg·m/s`],
    ['Δx·Δp / (ℏ/2):', `${Number(p.ratio_to_minimum).toFixed(2)}×`],
  ],
  mission_4: p => [
    ['Resultant amplitude:', fmt(p.resultant_amplitude)],
    ['Phase difference:', `${fmt(p.phase_diff_deg, 4)}°`],
    ['Interference:', p.interference_type],
  ],
  mission_5: p => [
    ['Object:', p.mass_description],
    ['Spreading time τ:', `${fmt(p.dispersion_timescale_s)} s`],
    ['Packet width at t:', `×${fmt(p.spreading_factor)}`],
  ],
};

/** Per-mission classical vs quantum comparison boxes. */
const COMPARISON = {
  mission_1: p => ({
    classicalVal: `${(p.classical_transmission * 100).toFixed(0)}%`,
    classicalColor: p.classical_crosses ? '#10b981' : '#ef4444',
    classicalNote: p.classical_note,
    quantumVal: `${(p.quantum_transmission * 100).toFixed(2)}%`,
    quantumNote: (p.energy_ev < p.barrier_height_ev
      ? `Decay constant κ = ${fmt(p.kappa_or_k2_inv_nm)} nm⁻¹ inside the barrier. `
      : `Wavevector k₂ = ${fmt(p.kappa_or_k2_inv_nm)} nm⁻¹ over the barrier (partial reflection is still possible). `) +
      `de Broglie wavelength λ = ${fmt(p.de_broglie_wavelength_nm)} nm.`,
  }),
  mission_2: p => ({
    classicalVal: 'No fringes',
    classicalColor: '#3b82f6',
    classicalNote: 'Classical particles would simply add two single-slit patterns: no cross term, no fringes.',
    quantumVal: p.num_slits === 1 ? 'Diffraction only' : `${Math.round(p.visibility * 100)}% visibility`,
    quantumNote: p.num_slits === 1
      ? 'One open slit gives a single-slit diffraction pattern.'
      : `Fringe spacing λL/d = ${fmt(p.fringe_spacing_mm)} mm, ${p.fringes_peak_count} bright fringes on the screen.` +
        (p.which_path_enabled ? ` Detector strength D = ${fmt(p.which_path_strength)} gives V = √(1 − D²).` : ''),
  }),
  mission_3: p => ({
    classicalVal: 'No limit',
    classicalColor: '#3b82f6',
    classicalNote: 'Classical mechanics lets position and momentum both be specified exactly at once.',
    quantumVal: `${Number(p.ratio_to_minimum).toFixed(2)} × ℏ/2`,
    quantumNote: `Δx·Δp = ${fmt(p.uncertainty_product)} J·s, never below ℏ/2 = ${fmt(p.hbar_over_two)} J·s.`,
  }),
  mission_4: p => ({
    classicalVal: `I = ${fmt(p.classical_intensity)}`,
    classicalColor: '#3b82f6',
    classicalNote: `Classical intensity is the squared resultant amplitude (${fmt(p.resultant_amplitude)}).`,
    quantumVal: `P = ${fmt(p.quantum_prob_interference)}`,
    quantumNote: `Adding amplitudes gives the same arithmetic: P₁ + P₂ + cross term (${fmt(p.quantum_cross_term)}). ` +
      'The difference is in meaning: a probability for single detection events, not an energy flux.',
  }),
  mission_5: p => ({
    classicalVal: 'Point path',
    classicalColor: '#3b82f6',
    classicalNote: 'Classical mechanics: the centre moves at constant speed and the object stays sharply localised.',
    quantumVal: `×${fmt(p.spreading_factor)} width`,
    quantumNote: p.domain_explanation,
  }),
};

/* ---------------------------------------------------------------- app */
class ScienceQuestApp {
  constructor() {
    this.backend = null;
    this.state = null;
    this.currentView = 'home';
    this.activeVisualizer = null;
    this.renderedMission = null;
    this.controlEls = {};
    this.lastFrameTime = performance.now();
    this._paramTimers = {};

    this.initElements();
    this.initEventListeners();
    this.quarkMascot = new QuarkRenderer('quark-mascot-canvas');
    if (this.dom.canvas) {
      this.resizeCanvas();
      this.activeVisualizer = new TunnelingVisualizer(this.dom.canvas);
    }
    this.startMainRenderLoop();
    this.init();
  }

  async init() {
    this.backend = await createBackend((e) => this.handleEvent(e), (m) => this.notify(m));
    document.body.dataset.mode = this.backend.mode;
    this.applyModeText();
    this.updateProfileUI();
    try {
      await this.backend.start();
    } catch (err) {
      this.notify('Could not reach the server. Please reload the page.');
    }
  }

  applyModeText() {
    const solo = this.backend.mode === 'solo';
    this.dom.openLeaderboard.textContent = solo ? '🏆 My Progress' : '🏆 Scores';
    this.dom.leaderboardTitle.textContent = solo ? '🏆 Your Progress & Badges' : '🏆 Community Scoreboard & Badges';
  }

  initElements() {
    const $ = (id) => document.getElementById(id);
    this.dom = {
      navTabs: document.querySelectorAll('.nav-tab-btn'),
      viewSections: document.querySelectorAll('.view-section'),
      canvas: $('science-canvas'),
      hudMissionTitle: $('hud-mission-title'),
      hudMissionTopic: $('hud-mission-topic'),
      slidersContainer: $('sliders-container'),
      votingQuestion: $('voting-question'),
      votingOptions: $('voting-options'),
      votingTimer: $('voting-timer'),
      roundResult: $('round-result'),
      compClassicalVal: $('comp-classical-val'),
      compClassicalNote: $('comp-classical-note'),
      compQuantumVal: $('comp-quantum-val'),
      compQuantumNote: $('comp-quantum-note'),
      quarkBubble: $('quark-bubble-text'),
      quarkInput: $('quark-input'),
      quarkSendBtn: $('quark-send-btn'),
      tierBtns: document.querySelectorAll('.tier-btn'),
      chatMessagesBox: $('chat-messages-box'),
      chatInput: $('chat-input'),
      chatSendBtn: $('chat-send-btn'),
      leaderboardModal: $('leaderboard-modal'),
      leaderboardList: $('leaderboard-list'),
      leaderboardTitle: $('leaderboard-title'),
      openLeaderboard: $('btn-open-leaderboard'),
      toast: $('toast'),
      hudLabels: [$('hud-label-1'), $('hud-label-2'), $('hud-label-3')],
      hudVals: [$('hud-val-1'), $('hud-val-2'), $('hud-val-3')],
    };
  }

  initEventListeners() {
    this.dom.navTabs.forEach(btn => btn.addEventListener('click', () => this.switchView(btn.dataset.view)));
    this.dom.tierBtns.forEach(btn => btn.addEventListener('click', () => this.setQuarkTier(btn.dataset.tier)));
    this.dom.quarkSendBtn.addEventListener('click', () => this.sendQuarkQuestion());
    this.dom.quarkInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') this.sendQuarkQuestion(); });
    this.dom.chatSendBtn.addEventListener('click', () => this.sendChatMessage());
    this.dom.chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') this.sendChatMessage(); });
    this.dom.openLeaderboard.addEventListener('click', () => this.openLeaderboard());
    document.getElementById('btn-close-modal').addEventListener('click', () => this.dom.leaderboardModal.classList.remove('open'));
    window.addEventListener('resize', () => this.dom.canvas && this.resizeCanvas());

    // One delegated listener replaces every inline onclick="" (inline handlers would need
    // 'unsafe-inline' in the Content-Security-Policy).
    document.addEventListener('click', (event) => {
      const el = event.target.closest('[data-action]');
      if (!el) return;
      const handler = this.actions[el.dataset.action];
      if (handler) handler(el.dataset.arg, el);
    });
    this.actions = {
      view: (arg) => this.switchView(arg),
      mission: (arg) => this.startMission(arg, false),
      'mission-quest': (arg) => this.startMission(arg, true),
      'vote-start': () => this.backend && this.backend.startVoting(),
      resolve: () => this.backend && this.backend.resolve(),
      'new-attempt': () => this.backend && this.backend.newAttempt(),
      fire: () => { const v = this.activeVisualizer; if (v && typeof v.fireSingleParticle === 'function') v.fireSingleParticle(); },
      'toggle-viz': (arg, el) => {
        const v = this.activeVisualizer;
        if (!TOGGLE_FLAGS.includes(arg) || !v || !(arg in v)) return;
        el.classList.toggle('active');
        v[arg] = !v[arg];
      },
      'profile-open': () => this.openProfileModal(),
      'profile-close': () => document.getElementById('profile-modal').classList.remove('open'),
      'profile-save': () => this.saveProfileName(),
      'profile-reset': () => this.resetProgress(),
    };
  }

  notify(message) {
    const t = this.dom.toast;
    if (!t) return;
    t.textContent = message;
    t.classList.add('show');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => t.classList.remove('show'), 4000);
  }

  /* ------------------------------------------------------------ navigation */
  resizeCanvas() {
    const rect = this.dom.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.dom.canvas.width = rect.width * dpr;
    this.dom.canvas.height = rect.height * dpr;
    this.dom.canvas.getContext('2d').scale(dpr, dpr);
  }

  switchView(viewName) {
    this.currentView = viewName;
    this.dom.navTabs.forEach(t => t.classList.toggle('active', t.dataset.view === viewName));
    this.dom.viewSections.forEach(s => s.classList.toggle('active-view', s.id === `view-${viewName}`));
    if (viewName === 'lab' || viewName === 'reality-battle') setTimeout(() => this.resizeCanvas(), 50);
  }

  async startMission(missionId, startVote) {
    if (!this.backend) return;
    this.switchView('lab');
    await this.backend.selectMission(missionId);
    if (startVote && this.backend.mode === 'live') await this.backend.startVoting();
  }

  /* ------------------------------------------------------------ events from the backend */
  handleEvent(data) {
    switch (data.event) {
      case 'init_state':
      case 'state_update':
        this.state = data.state;
        this.renderFullState();
        break;
      case 'vote_update':
      case 'voting_started':
        if (this.state) this.state.voting_status = data.voting_status;
        this.renderVotingStatus(data.voting_status);
        break;
      case 'quark_speech':
        this.displayQuarkSpeech(data.answer);
        break;
      case 'chat_message':
        this.appendChatMessage(data.username, data.text, data.is_simulated);
        break;
      case 'round_resolved':
        this.handleRoundResolved(data.round_result, data.quark_explanation);
        break;
      default:
        break;
    }
  }

  /* ------------------------------------------------------------ rendering */
  renderFullState() {
    const s = this.state;
    if (!s) return;
    const mid = s.active_mission_id;
    const missionChanged = mid !== this.renderedMission;

    if (missionChanged) {
      const VizClass = VIZ_BY_MISSION[mid] && VIZ_BY_MISSION[mid]();
      if (VizClass && !(this.activeVisualizer instanceof VizClass)) this.activeVisualizer = new VizClass(this.dom.canvas);
      this.renderedMission = mid;
      this.renderControls();
      this.dom.roundResult.hidden = true;
      this.applyMissionScope(mid);
      document.querySelectorAll('.mission-card[data-mission]').forEach(
        c => c.classList.toggle('active-mission', c.dataset.mission === mid));
    }
    if (this.dom.hudMissionTitle) this.dom.hudMissionTitle.textContent = s.mission_title;
    if (this.dom.hudMissionTopic) this.dom.hudMissionTopic.textContent = s.mission_topic;
    if (this.activeVisualizer && s.physics_result) this.activeVisualizer.setData(s.physics_result);

    this.renderHUD();
    this.syncControls();
    this.renderComparison();
    this.renderVotingStatus(s.voting_status);
  }

  /** Hide controls that only make sense for some missions (tunneling legend, toolbar, math drawer). */
  applyMissionScope(mid) {
    document.querySelectorAll('[data-only-mission]').forEach(el => {
      el.hidden = !el.dataset.onlyMission.split(' ').includes(mid);
    });
  }

  renderHUD() {
    const rows = HUD_ROWS[this.state.active_mission_id];
    if (!rows || !this.state.physics_result) return;
    rows(this.state.physics_result).forEach(([label, value], i) => {
      if (this.dom.hudLabels[i]) this.dom.hudLabels[i].textContent = label;
      if (this.dom.hudVals[i]) this.dom.hudVals[i].textContent = value;
    });
  }

  renderComparison() {
    const build = COMPARISON[this.state.active_mission_id];
    if (!build || !this.state.physics_result) return;
    const c = build(this.state.physics_result);
    this.dom.compClassicalVal.textContent = c.classicalVal;
    this.dom.compClassicalVal.style.color = c.classicalColor;
    this.dom.compClassicalNote.textContent = c.classicalNote;
    this.dom.compQuantumVal.textContent = c.quantumVal;
    this.dom.compQuantumVal.style.color = '#c084fc';
    this.dom.compQuantumNote.textContent = c.quantumNote;
  }

  /** Build sliders, toggles and selects once per mission, so dragging a slider is never interrupted. */
  renderControls() {
    const container = this.dom.slidersContainer;
    container.replaceChildren();
    this.controlEls = {};
    const controls = this.state.controls ||
      Object.entries(this.state.allowed_ranges || {}).map(([key, r]) => ({ key, kind: 'slider', label: key.replace(/_/g, ' '), ...r }));

    for (const c of controls) {
      const unitBox = h('div', { class: 'slider-unit' });
      if (c.kind === 'slider') {
        const valueEl = h('span', { class: 'slider-value' });
        const input = h('input', { type: 'range', min: c.min, max: c.max, step: c.step, 'aria-label': c.label });
        input.addEventListener('input', () => {
          const v = parseFloat(input.value);
          valueEl.textContent = `${v} ${c.unit || ''}`;
          this.updateParamDebounced(c.key, v);
        });
        unitBox.append(h('div', { class: 'slider-label-row' }, h('span', { class: 'slider-name', text: c.label }), valueEl), input);
        this.controlEls[c.key] = { kind: 'slider', input, valueEl, unit: c.unit };
      } else if (c.kind === 'toggle') {
        const input = h('input', { type: 'checkbox', 'aria-label': c.label });
        input.addEventListener('change', () => this.backend.setParam(c.key, input.checked));
        unitBox.append(h('label', { class: 'slider-label-row toggle-row' }, h('span', { class: 'slider-name', text: c.label }), input));
        this.controlEls[c.key] = { kind: 'toggle', input };
      } else if (c.kind === 'select') {
        const select = h('select', { class: 'control-select', 'aria-label': c.label });
        c.options.forEach((o, i) => select.append(h('option', { value: String(i), text: o.label })));
        select.addEventListener('change', () => this.backend.setParam(c.key, c.options[Number(select.value)].value));
        unitBox.append(h('div', { class: 'slider-label-row' }, h('span', { class: 'slider-name', text: c.label })), select);
        this.controlEls[c.key] = { kind: 'select', input: select, options: c.options };
      }
      container.append(unitBox);
    }
  }

  syncControls() {
    const params = this.state.current_params || {};
    for (const [key, ctl] of Object.entries(this.controlEls)) {
      const value = params[key];
      if (value === undefined || document.activeElement === ctl.input) continue;
      if (ctl.kind === 'slider') { ctl.input.value = value; ctl.valueEl.textContent = `${value} ${ctl.unit || ''}`; }
      else if (ctl.kind === 'toggle') ctl.input.checked = !!value;
      else if (ctl.kind === 'select') ctl.input.value = String(Math.max(0, ctl.options.findIndex(o => o.value === value)));
    }
  }

  updateParamDebounced(key, value) {
    clearTimeout(this._paramTimers[key]);
    this._paramTimers[key] = setTimeout(() => this.backend.setParam(key, value), 120);
  }

  renderVotingStatus(v) {
    if (!v) return;
    this.dom.votingQuestion.textContent = v.question;
    const solo = v.mode === 'solo';
    const timer = this.dom.votingTimer;
    if (solo) {
      timer.textContent = v.resolved ? 'ANSWERED' : (v.selected ? 'READY TO CHECK' : 'PICK AN ANSWER');
    } else {
      timer.textContent = v.voting_open ? `${v.time_remaining_seconds}s REMAINING` : 'ROUND CLOSED';
    }
    timer.style.background = (solo ? !v.resolved : v.voting_open) ? 'rgba(239, 68, 68, 0.15)' : 'rgba(100, 116, 139, 0.2)';

    const box = this.dom.votingOptions;
    box.replaceChildren();
    for (const [letter, text] of Object.entries(v.options || {})) {
      const pct = (v.percentages || {})[letter] || 0;
      const count = (v.tallies || {})[letter] || 0;
      const classes = ['vote-opt-btn'];
      if (solo && v.selected === letter) classes.push('selected');
      if (solo && v.resolved && v.correct_display === letter) classes.push('correct');
      if (solo && v.resolved && v.selected === letter && v.correct_display !== letter) classes.push('wrong');

      const content = h('div', { class: 'vote-content' },
        h('div', {}, h('span', { class: 'vote-opt-letter', text: `[${letter}]` }), ` ${text}`));
      if (!solo) content.append(h('span', { class: 'vote-percent', text: `${pct}% (${count})` }));
      const btn = h('button', { class: classes.join(' '), type: 'button' });
      if (!solo) btn.append(h('div', { class: 'vote-bar-fill', style: { width: `${Math.max(0, Math.min(100, pct))}%` } }));
      btn.append(content);
      btn.addEventListener('click', () => { this.backend.vote(letter); if (this.quarkMascot) this.quarkMascot.setMood('happy'); });
      box.append(btn);
    }
  }

  /* ------------------------------------------------------------ Quark */
  setQuarkTier(tier) {
    this.dom.tierBtns.forEach(b => b.classList.toggle('active', b.dataset.tier === tier));
    if (this.backend) this.backend.setLevel(tier);
  }

  displayQuarkSpeech(text) {
    if (this.dom.quarkBubble) this.dom.quarkBubble.textContent = text;
    if (this.quarkMascot) {
      this.quarkMascot.setMood('calculating');
      setTimeout(() => this.quarkMascot.setMood('curious'), 1800);
    }
  }

  sendQuarkQuestion() {
    const q = this.dom.quarkInput.value.trim();
    if (!q || !this.backend) return;
    this.dom.quarkInput.value = '';
    this.displayQuarkSpeech('Processing question with the physics engine...');
    this.backend.askQuark(q.slice(0, 200));
  }

  /* ------------------------------------------------------------ chat (live mode) */
  sendChatMessage() {
    const text = this.dom.chatInput.value.trim();
    if (!text || !this.backend) return;
    this.dom.chatInput.value = '';
    this.backend.sendChat(text.slice(0, 500));
  }

  appendChatMessage(user, text, isSimulated) {
    const box = this.dom.chatMessagesBox;
    if (!box) return;
    const msg = h('div', { class: 'chat-msg' },
      h('span', { class: `chat-tag ${isSimulated ? 'sim' : 'live'}`, text: isSimulated ? '[SIM]' : '[TWITCH]' }),
      h('span', { class: 'chat-user', text: `${String(user).slice(0, 25)}:` }),
      ` ${String(text).slice(0, 500)}`);
    box.append(msg);
    while (box.childElementCount > 200) box.firstElementChild.remove();   // bound DOM growth
    box.scrollTop = box.scrollHeight;
  }

  /* ------------------------------------------------------------ round result */
  handleRoundResolved(result, explanation) {
    if (this.quarkMascot) this.quarkMascot.setMood('happy');
    this.displayQuarkSpeech(explanation);
    const box = this.dom.roundResult;
    box.replaceChildren();
    if (this.backend.mode === 'solo') {
      box.append(h('strong', { text: result.correct ? '✅ Correct!' : '❌ Not quite.' }),
        ` ${result.rationale} `,
        h('em', { text: result.official ? `+${result.points_awarded} points (first attempt on this mission).` : 'Practice attempt: no points. Progress counts the first attempt only.' }));
    } else {
      box.append(h('strong', { text: `Correct answer: ${result.correct_option}.` }), ` ${result.rationale}`);
    }
    box.hidden = false;
    this.updateProfileUI();
  }

  /* ------------------------------------------------------------ profile / scores */
  async openLeaderboard() {
    const data = await this.backend.getProfile().catch(() => null);
    if (!data) return;
    const list = this.dom.leaderboardList;
    list.replaceChildren();
    data.leaders.forEach((p, idx) => list.append(
      h('div', { class: 'hud-row', style: { padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.06)' } },
        h('span', {}, `#${idx + 1} `, h('strong', { text: p.username })),
        h('span', { style: { color: '#06b6d4', fontWeight: '700' }, text: `${p.points} pts` }))));
    this.dom.leaderboardModal.classList.add('open');
  }

  async openProfileModal() {
    const modal = document.getElementById('profile-modal');
    const data = await this.backend.getProfile().catch(() => null);
    if (!modal || !data) return;
    document.getElementById('profile-username-input').value = this.backend.playerName;
    const me = data.me;
    document.getElementById('modal-points').textContent = `${me.points} pts`;
    document.getElementById('modal-streak').textContent = `${me.best_streak ?? me.current_streak}🔥`;
    document.getElementById('modal-accuracy').textContent = `${me.accuracy_pct}%`;
    document.getElementById('modal-rank').textContent = rankFor(me.points);
    const badges = document.getElementById('modal-badges-list');
    badges.replaceChildren();
    if (!me.badges.length) {
      badges.append(h('span', { class: 'dim-note', text: 'No badges earned yet. Complete experiments to unlock badges!' }));
    } else {
      me.badges.forEach(id => {
        const info = data.badges[id] || { name: id, icon: '⚡' };
        badges.append(h('div', { class: 'badge-chip', text: `${info.icon} ${info.name}` }));
      });
    }
    modal.classList.add('open');
  }

  saveProfileName() {
    const input = document.getElementById('profile-username-input');
    const clean = input.value.trim();
    if (!clean) return;
    this.backend.setName(clean);
    this.updateProfileUI();
    document.getElementById('profile-modal').classList.remove('open');
  }

  resetProgress() {
    if (!window.confirm('Reset all progress stored in this browser?')) return;
    this.backend.resetProgress();
    this.updateProfileUI();
    document.getElementById('profile-modal').classList.remove('open');
  }

  async updateProfileUI() {
    if (!this.backend) return;
    const data = await this.backend.getProfile().catch(() => null);
    if (!data) return;
    const me = data.me;
    const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
    set('nav-player-name', this.backend.playerName);
    set('home-player-name', this.backend.playerName);
    set('nav-player-points', `${me.points} pts`);
    set('home-player-pts', `${me.points}`);
    set('home-player-streak', `${me.current_streak}🔥`);
    set('home-player-acc', `${me.accuracy_pct}%`);
    set('home-player-rank', rankFor(me.points));
    set('home-player-badges', me.badges.length ? me.badges.map(() => '🏅').join(' ') : '⚡ 🔒 🔒 🔒 🔒');

    const leaders = document.getElementById('home-scoreboard-leaders');
    if (leaders) {
      leaders.replaceChildren();
      data.leaders.slice(0, 5).forEach((p, i) => leaders.append(
        h('div', { class: 'leader-row' },
          h('span', {}, `#${i + 1} `, h('strong', { text: p.username })),
          h('span', { class: 'leader-score', text: `${p.points} pts (${p.current_streak}🔥)` }))));
    }
  }

  /* ------------------------------------------------------------ render loop */
  startMainRenderLoop() {
    const loop = (now) => {
      const dt = Math.min(0.1, (now - this.lastFrameTime) / 1000);
      this.lastFrameTime = now;
      if (this.activeVisualizer && (this.currentView === 'lab' || this.currentView === 'reality-battle')) {
        this.activeVisualizer.update(dt);
        this.activeVisualizer.render();
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

window.addEventListener('DOMContentLoaded', () => { window.app = new ScienceQuestApp(); });
