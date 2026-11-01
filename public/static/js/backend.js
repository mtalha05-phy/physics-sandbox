/**
 * ScienceQuest backends.
 *
 * Both classes expose the same small interface to app.js and report changes through
 * `onEvent(event)`, using the same event names the live WebSocket hub has always used
 * (init_state, state_update, vote_update, quark_speech, round_resolved, chat_message).
 *
 *   SoloBackend  - the public website (Vercel). Stateless server: this browser owns the player's
 *                  mission, parameters and progress (localStorage) and asks the server only for
 *                  validated physics, answer checking and explanations.
 *   LiveBackend  - self-hosted Twitch/OBS mode: shared server state over REST + WebSocket.
 */

const SQ_LEVELS = ['EXPLORER', 'SCIENTIST', 'RESEARCHER'];

async function sqJson(path, options = {}) {
  const res = await fetch(path, {
    method: options.method || 'GET',
    headers: options.body ? { 'Content-Type': 'application/json', ...(options.headers || {}) } : (options.headers || {}),
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON error body */ }
  if (!res.ok) {
    const detail = data && data.detail;
    const error = new Error(typeof detail === 'string' ? detail : `Request failed (${res.status})`);
    error.status = res.status;
    throw error;
  }
  return data;
}

/* ------------------------------------------------------------------ solo profile (localStorage) */
class SoloProfile {
  static KEY = 'sq_solo_profile_v1';

  static defaults() {
    return {
      name: `Player_${Math.floor(1000 + Math.random() * 9000)}`,
      points: 0, made: 0, correct: 0, streak: 0, best: 0, badges: [], done: {},
    };
  }

  /** localStorage is user-editable, so every field is type-checked and clamped. */
  static load() {
    const profile = SoloProfile.defaults();
    try {
      const raw = JSON.parse(localStorage.getItem(SoloProfile.KEY) || 'null');
      if (!raw || typeof raw !== 'object') return profile;
      if (typeof raw.name === 'string' && raw.name.trim()) profile.name = raw.name.trim().slice(0, 24);
      for (const key of ['points', 'made', 'correct', 'streak', 'best']) {
        const v = Number(raw[key]);
        profile[key] = Number.isFinite(v) ? Math.max(0, Math.min(1e7, Math.floor(v))) : 0;
      }
      if (Array.isArray(raw.badges)) {
        profile.badges = raw.badges.filter(b => typeof b === 'string' && /^badge_[a-z_]{1,40}$/.test(b)).slice(0, 20);
      }
      if (raw.done && typeof raw.done === 'object') {
        for (const id of Object.keys(raw.done)) {
          if (/^mission_[0-9]{1,2}$/.test(id) && raw.done[id] === true) profile.done[id] = true;
        }
      }
    } catch (_) { /* corrupted or unavailable storage: start fresh */ }
    return profile;
  }

  static save(profile) {
    try { localStorage.setItem(SoloProfile.KEY, JSON.stringify(profile)); } catch (_) { /* private mode */ }
  }

  static asPlayer(profile) {
    return {
      username: profile.name,
      points: profile.points,
      predictions_made: profile.made,
      predictions_correct: profile.correct,
      accuracy_pct: profile.made ? Math.round((profile.correct / profile.made) * 1000) / 10 : 0,
      current_streak: profile.streak,
      best_streak: profile.best,
      badges: profile.badges,
    };
  }
}

/* ------------------------------------------------------------------ solo backend */
class SoloBackend {
  constructor(onEvent, onNotice) {
    this.mode = 'solo';
    this.onEvent = onEvent;
    this.onNotice = onNotice || (() => {});
    this.profile = SoloProfile.load();
    this.level = 'SCIENTIST';
    this.catalog = {};
    this.badges = {};
    this.missionId = null;
    this.params = {};
    this.state = null;
    this.round = null;
    this._computeSeq = 0;
  }

  async start() {
    const data = await sqJson('/api/solo/missions');
    for (const m of data.missions) this.catalog[m.id] = m;
    this.badges = data.badges || {};
    await this.selectMission('mission_1', false);
  }

  _newRound() {
    const ids = Object.keys(this.state.question.options);
    for (let i = ids.length - 1; i > 0; i--) {          // shuffle so position never gives the answer away
      const j = Math.floor(Math.random() * (i + 1));
      [ids[i], ids[j]] = [ids[j], ids[i]];
    }
    this.round = { order: ids, selected: null, resolved: false, correctDisplay: null, official: false };
  }

  _votingStatus() {
    const letters = ['A', 'B', 'C', 'D'];
    const options = {};
    const optionIds = {};
    this.round.order.forEach((id, i) => {
      options[letters[i]] = this.state.question.options[id];
      optionIds[letters[i]] = id;
    });
    return {
      mode: 'solo',
      question: this.state.question.text,
      options, optionIds,
      selected: this.round.selected,
      resolved: this.round.resolved,
      correct_display: this.round.correctDisplay,
      voting_open: !this.round.resolved,
      time_remaining_seconds: 0,
      tallies: {}, percentages: {}, total_votes: 0,
    };
  }

  _emitState(eventName = 'state_update') {
    this.onEvent({ event: eventName, state: { ...this.state, voting_status: this._votingStatus() } });
  }

  async _compute() {
    const seq = ++this._computeSeq;
    const state = await sqJson('/api/solo/compute', { method: 'POST', body: { mission_id: this.missionId, params: this.params } });
    if (seq !== this._computeSeq) return false;        // a newer request superseded this one
    this.state = state;
    this.params = { ...state.current_params };
    return true;
  }

  async selectMission(id, announce = true) {
    const mission = this.catalog[id];
    if (!mission) return;
    const previous = { id: this.missionId, params: this.params };
    this.missionId = id;
    this.params = { ...mission.default_params };
    try {
      await this._compute();
    } catch (err) {
      this.missionId = previous.id;
      this.params = previous.params;
      this.onNotice(err.message);
      return;
    }
    this._newRound();
    this._emitState('init_state');
    if (announce) this._announce();
  }

  async _announce() {
    try {
      const reply = await this._quark(null);
      this.onEvent({ event: 'quark_speech', username: 'Quark', question: this.state.mission_title, answer: reply, level: this.level });
    } catch (_) { /* the explanation is a nicety; the lab works without it */ }
  }

  async setParam(key, value) {
    const before = { ...this.params };
    this.params[key] = value;
    try {
      if (await this._compute()) this._emitState();
    } catch (err) {
      this.params = before;
      this.onNotice(err.message);
      this._emitState();                                // snap the controls back to a valid state
    }
  }

  startVoting() { /* solo mode has no timed rounds: the question is always open */ }

  vote(letter) {
    if (!this.round || this.round.resolved || !(letter in this._votingStatus().options)) return;
    this.round.selected = letter;
    this.onEvent({ event: 'vote_update', voting_status: this._votingStatus() });
  }

  async resolve() {
    if (!this.round) return;
    if (this.round.resolved) { this.onNotice('Already answered. Pick another mission or press "New attempt".'); return; }
    if (!this.round.selected) { this.onNotice('Pick an answer first.'); return; }
    const status = this._votingStatus();
    let verdict;
    try {
      verdict = await sqJson('/api/solo/answer', {
        method: 'POST', body: { mission_id: this.missionId, option: status.optionIds[this.round.selected] },
      });
    } catch (err) { this.onNotice(err.message); return; }

    this.round.resolved = true;
    this.round.correctDisplay = Object.keys(status.optionIds).find(k => status.optionIds[k] === verdict.correct_option);
    const first = !this.profile.done[this.missionId];
    this.round.official = first;
    let awarded = 0;
    if (first) {                                        // only the first attempt per mission is scored
      const p = this.profile;
      p.done[this.missionId] = true;
      p.made += 1;
      if (verdict.correct) {
        p.correct += 1; p.streak += 1; p.best = Math.max(p.best, p.streak);
        awarded = 120 + (p.streak - 1) * 15;
        if (verdict.badge_id && !p.badges.includes(verdict.badge_id)) p.badges.push(verdict.badge_id);
      } else {
        p.streak = 0; awarded = 20;
      }
      p.points += awarded;
      SoloProfile.save(p);
    }
    let explanation = verdict.rationale;
    try { explanation = await this._quark(null); } catch (_) { /* keep the rationale */ }
    this.onEvent({
      event: 'round_resolved',
      round_result: { ...verdict, points_awarded: awarded, official: first, rationale: verdict.rationale },
      quark_explanation: explanation,
    });
    this._emitState();
  }

  newAttempt() {
    if (!this.state) return;
    this._newRound();
    this._emitState();
  }

  async _quark(question) {
    const data = await sqJson('/api/solo/quark', {
      method: 'POST',
      body: { mission_id: this.missionId, params: this.params, question, level: this.level },
    });
    return data.answer;
  }

  async askQuark(question) {
    try {
      const answer = await this._quark(question);
      this.onEvent({ event: 'quark_speech', username: this.profile.name, question, answer, level: this.level });
    } catch (err) {
      this.onNotice(err.status === 429 ? 'Quark needs a moment to cool down. Try again shortly.' : err.message);
    }
  }

  setLevel(level) { if (SQ_LEVELS.includes(level)) this.level = level; }
  sendChat() { /* chat belongs to live mode */ }

  async getProfile() {
    return { me: SoloProfile.asPlayer(this.profile), leaders: [SoloProfile.asPlayer(this.profile)], badges: this.badges };
  }

  setName(name) {
    this.profile.name = name.trim().slice(0, 24) || this.profile.name;
    SoloProfile.save(this.profile);
  }

  get playerName() { return this.profile.name; }

  resetProgress() {
    this.profile = { ...SoloProfile.defaults(), name: this.profile.name };
    SoloProfile.save(this.profile);
    if (this.state) { this._newRound(); this._emitState(); }
  }
}

/* ------------------------------------------------------------------ live backend */
class LiveBackend {
  constructor(onEvent, onNotice) {
    this.mode = 'live';
    this.onEvent = onEvent;
    this.onNotice = onNotice || (() => {});
    this.level = 'SCIENTIST';
    this.ws = null;
    this._name = localStorage.getItem('sq_username') || `Viewer_${Math.floor(1000 + Math.random() * 9000)}`;
    localStorage.setItem('sq_username', this._name);
  }

  get playerName() { return this._name; }

  /** Audience name for Twitch-style endpoints: letters, digits and underscore, 1-25 characters. */
  _viewerName() { return (this._name.replace(/[^A-Za-z0-9_]/g, '_').slice(0, 25)) || 'Viewer'; }

  async start() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const connect = () => {
      this.ws = new WebSocket(`${protocol}//${location.host}/ws`);
      this.ws.onmessage = (e) => { try { this.onEvent(JSON.parse(e.data)); } catch (_) { /* ignore malformed frame */ } };
      this.ws.onclose = () => setTimeout(connect, 3000);
    };
    connect();
  }

  async _admin(path, body) {
    const call = () => sqJson(path, {
      method: 'POST', body,
      headers: { 'X-Admin-Token': sessionStorage.getItem('sq_admin_token') || '' },
    });
    try { return await call(); } catch (err) {
      if (err.status !== 401) throw err;
      const token = window.prompt('Admin token required for this control (ADMIN_TOKEN on the server):');
      if (!token) throw err;
      sessionStorage.setItem('sq_admin_token', token);
      return call();
    }
  }

  async _try(fn) { try { return await fn(); } catch (err) { this.onNotice(err.message); } }

  selectMission(id) { return this._try(() => this._admin(`/api/mission/${encodeURIComponent(id)}`)); }
  setParam(key, value) { return this._try(() => this._admin('/api/parameter', { param: key, value })); }
  startVoting() { return this._try(() => this._admin('/api/voting/start', { duration_seconds: 45 })); }
  resolve() { return this._try(() => this._admin('/api/voting/resolve')); }
  newAttempt() { /* live rounds are controlled by the streamer */ }
  vote(letter) {
    return this._try(() => sqJson('/api/voting/vote', { method: 'POST', body: { username: this._viewerName(), option: letter } }));
  }
  askQuark(question) {
    return this._try(() => sqJson('/api/quark/ask', {
      method: 'POST', body: { question, username: this._viewerName(), level: this.level },
    }));
  }
  setLevel(level) { if (SQ_LEVELS.includes(level)) this.level = level; }
  sendChat(text) {
    return this._try(() => sqJson('/api/chat/send', { method: 'POST', body: { username: this._viewerName(), text } }));
  }

  async getProfile() {
    const data = await sqJson('/api/leaderboard');
    const leaders = data.leaderboard || [];
    const key = this._viewerName().toLowerCase();
    const me = leaders.find(p => p.username.toLowerCase() === key) ||
      { username: this._name, points: 0, current_streak: 0, best_streak: 0, accuracy_pct: 0, badges: [] };
    return { me, leaders, badges: data.badges || {} };
  }

  setName(name) {
    this._name = name.trim().slice(0, 24) || this._name;
    localStorage.setItem('sq_username', this._name);
  }
  resetProgress() { /* server-side scores are not resettable by players */ }
}

async function createBackend(onEvent, onNotice) {
  let mode = 'solo';
  try { mode = (await sqJson('/api/mode')).mode; } catch (_) { /* default to the stateless edition */ }
  return mode === 'live' ? new LiveBackend(onEvent, onNotice) : new SoloBackend(onEvent, onNotice);
}
