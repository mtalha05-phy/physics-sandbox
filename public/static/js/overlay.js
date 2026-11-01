/**
 * ScienceQuest Live - OBS Studio Stream Overlay Client
 * Real-time WebSocket consumer rendering clean on-stream graphics.
 */

class StreamOverlayClient {
  constructor() {
    this.ws = null;
    this.initElements();
    this.connectWebSocket();
  }

  initElements() {
    this.el = {
      missionTitle: document.getElementById('overlay-mission-title'),
      missionTopic: document.getElementById('overlay-mission-topic'),
      worldBadge: document.getElementById('overlay-world-badge'),
      pollQuestion: document.getElementById('overlay-poll-question'),
      pollTimer: document.getElementById('overlay-poll-timer'),
      pollOptions: document.getElementById('overlay-poll-options'),
      quarkSpeech: document.getElementById('overlay-quark-speech'),
    };
  }

  connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleEvent(data);
      } catch (e) {
        console.error('Overlay WS error:', e);
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.connectWebSocket(), 3000);
    };
  }

  handleEvent(data) {
    if (data.event === 'init_state' || data.event === 'state_update') {
      const s = data.state;
      if (this.el.missionTitle) this.el.missionTitle.innerText = s.mission_title;
      if (this.el.missionTopic) this.el.missionTopic.innerText = s.mission_topic;
      if (this.el.worldBadge) this.el.worldBadge.innerText = s.active_world.toUpperCase();
      this.renderPoll(s.voting_status);
    } else if (data.event === 'vote_update' || data.event === 'voting_started') {
      this.renderPoll(data.voting_status);
    } else if (data.event === 'quark_speech') {
      if (this.el.quarkSpeech) {
        this.setQuarkText('Quark:', data.answer);
      }
    } else if (data.event === 'round_resolved') {
      if (this.el.quarkSpeech) {
        this.setQuarkText('Quark (Resolution):', data.quark_explanation);
      }
    }
  }

  /** Text is untrusted (viewer questions are echoed back), so it is never parsed as HTML. */
  setQuarkText(label, text) {
    const strong = document.createElement('strong');
    strong.textContent = label;
    this.el.quarkSpeech.replaceChildren(strong, document.createTextNode(` "${String(text)}"`));
  }

  renderPoll(status) {
    if (!status) return;

    if (this.el.pollQuestion) this.el.pollQuestion.innerText = status.question;
    if (this.el.pollTimer) {
      this.el.pollTimer.innerText = status.voting_open ? `${status.time_remaining_seconds}s` : 'CLOSED';
    }

    const container = this.el.pollOptions;
    if (!container) return;
    container.replaceChildren();

    const opts = status.options || {};
    const pcts = status.percentages || {};

    for (const [letter, text] of Object.entries(opts)) {
      const pct = pcts[letter] || 0;
      const safePct = Math.max(0, Math.min(100, Number(pct) || 0));
      const row = document.createElement('div');
      row.className = 'poll-opt';
      const bar = document.createElement('div');
      bar.className = 'poll-opt-bar';
      bar.style.width = `${safePct}%`;
      const content = document.createElement('div');
      content.className = 'poll-opt-content';
      const label = document.createElement('span');
      label.textContent = `[${letter}] ${text}`;
      const pctEl = document.createElement('span');
      pctEl.className = 'poll-opt-pct';
      pctEl.textContent = `${safePct}%`;
      content.append(label, pctEl);
      row.append(bar, content);
      container.appendChild(row);
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  new StreamOverlayClient();
});
