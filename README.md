# 🌌 ScienceQuest Live
> **Two Worlds. Different Rules. One Curious Universe.**

[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![WebSockets](https://img.shields.io/badge/WebSockets-Enabled-purple.svg)](https://websockets.readthedocs.io)
[![Physics Tests](https://img.shields.io/badge/Physics%20Validation-36%20Passed%20(100%25)-brightgreen.svg)]()
[![Twitch IRC](https://img.shields.io/badge/Twitch-IRC%20%26%20Mock%20Mode-9146FF.svg)](https://dev.twitch.tv)

**ScienceQuest Live** is a multiplayer, livestream-native science adventure game built for the Twitch community and the OpenAI Codex hackathon. Instead of merely *telling* audiences how classical mechanics and quantum mechanics differ, ScienceQuest Live lets streamers and real viewers investigate those differences together through interactive, mathematically rigorous physics experiments in real time.

---

## 🧭 Table of Contents
1. [Core Features & Brand Identity](#-core-features--brand-identity)
2. [The Four Scientific Worlds](#-the-four-scientific-worlds)
3. [The Five Core Science Missions](#-the-five-core-science-missions)
4. [Scientific Validation & Physical Models](#-scientific-validation--physical-models)
5. [Architecture & Technology Stack](#-architecture--technology-stack)
6. [Quark: The AI Science Companion](#-quark-the-ai-science-companion)
7. [Twitch Community Integration](#-twitch-community-integration)
8. [OBS Studio Stream Overlay](#-obs-studio-stream-overlay)
9. [Installation & Quickstart](#-installation--quickstart)
10. [Automated Testing Suite](#-automated-testing-suite)
11. [Configuration & Environment Variables](#-configuration--environment-variables)
12. [Hackathon Demo & Submission Checklist](#-hackathon-demo--submission-checklist)

---

## 🌟 Core Features & Brand Identity

- **Product Name:** ScienceQuest Live
- **Tagline:** *Two Worlds. Different Rules. One Curious Universe.*
- **AI Science Companion:** **Quark** — an animated, expressive cyber-robot mascot who introduces missions, explains results across three comprehension tiers, and answers live viewer questions.
- **Deep-Space Futuristic Lab Aesthetics:**
  - Dark navy foundations (`#070b14`) with high legibility.
  - Classical Blue accents (`#3b82f6`) for deterministic Newtonian phenomena.
  - Quantum Purple accents (`#8b5cf6`) for probabilistic wave mechanics.
  - Cyan interactive highlights (`#06b6d4`) and Gold alerts (`#f59e0b`).
- **60 FPS Hardware-Accelerated Visualizations:** Pure Canvas 2D engines rendering stationary wavefunctions $\text{Re}[\psi(x,t)]$, probability density $|\psi(x)|^2$ fills, barrier potentials $V(x)$, classical particle tracks, double-slit interference fringes, wave superposition, and packet dispersion.
- **Audience Prediction Challenges:** Real-time Twitch prediction voting (`!vote A/B/C/D`), timer countdowns, community consensus resolution, point rewards, streaks, and achievement badges.
- **OBS Studio Broadcast Source:** Dedicated `/overlay` route with transparent/dark high-contrast layout, live poll bars, and Quark commentary for livestreamers.

---

## 🌍 The Four Scientific Worlds

| World | Purpose & Pedagogical Focus | Key Principles |
| :--- | :--- | :--- |
| **1. Classical World** | Introduce familiar macroscopic physical laws and deterministic Newtonian mechanics. | Particle trajectories, forces, conservation of energy, classical waves, and impenetrable potential barriers. |
| **2. Quantum World** | Introduce microscopic phenomena through visual experiments and probability amplitudes. | Wavefunctions, quantum tunneling, wave-particle duality, uncertainty principle, and which-path decoherence. |
| **3. Reality Battle** | Direct side-by-side comparison of classical and quantum predictions for identical physical situations. | Identifies when classical mechanics is an outstanding approximation and where quantum effects diverge. |
| **4. Challenge Lab** | Cooperative audience prediction arena where viewers pool knowledge to discover physical laws. | Timed community votes, parameter adjustments, scientific mysteries, and badges. |

---

## 🔬 The Five Core Science Missions

### 1. The Impossible Wall (Classical Mechanics vs Quantum Tunneling)
- **Scientific Topic:** 1D Rectangular Potential Barrier ($V_0$, $a$, $E$, $m$).
- **Classical Model:** If $E < V_0$, kinetic energy inside the barrier $K = E - V_0 < 0$ is strictly forbidden, so classical transmission $T = 0\%$. The particle elastically bounces off at $x = 0$. If $E > V_0$, the particle crosses with reduced velocity.
- **Quantum Model:** The wavefunction obeys the 1D Schrödinger equation. For $E < V_0$, the solution inside the barrier is evanescent ($\psi \sim e^{-\kappa x}$), producing a non-zero transmission probability:
  $$T = \frac{1}{1 + \frac{V_0^2 \sinh^2(\kappa a)}{4E(V_0 - E)}}, \quad \kappa = \frac{\sqrt{2m(V_0 - E)}}{\hbar}$$
- **Badge Earned:** ⚡ *Quantum Explorer*

### 2. Wave or Particle? (Double-Slit Interference & Decoherence)
- **Scientific Topic:** Wave-particle duality, probability amplitudes, and measurement interactions.
- **Classical Model:** Continuous wave interference with diffraction envelope $\text{sinc}^2(\beta)$ and two-slit fringes $\cos^2(\alpha)$.
- **Quantum Model:** Coherent probability amplitude addition $P(y) = |\psi_1 + \psi_2|^2$. When a which-path detector is switched on, environmental decoherence eliminates the cross-term: $P(y) = |\psi_1|^2 + |\psi_2|^2$, causing interference fringes to vanish into an incoherent sum.
- **Badge Earned:** 🌊 *Wave Detective*

### 3. The Uncertainty Challenge (Heisenberg's Uncertainty Principle)
- **Scientific Topic:** Conjugate variables and wavepacket Fourier transforms: $\Delta x \cdot \Delta p \ge \hbar / 2$.
- **Model:** Normalized Gaussian wavepacket. Narrowing the spatial width $\sigma_x$ directly broadens the momentum distribution $\sigma_p = \hbar / (2\sigma_x)$.
- **Badge Earned:** 🧠 *Quantum Thinker*

### 4. The Wave Laboratory (Superposition & Interference)
- **Scientific Topic:** Superposition of two coherent waves with variable phase difference $\Delta \phi$, frequency, and amplitude.
- **Model:** Demonstrates constructive ($\Delta \phi = 0^\circ$) and destructive ($\Delta \phi = 180^\circ$) interference, comparing classical wave energy with quantum probability amplitude interference.
- **Badge Earned:** ✨ *Wave Master*

### 5. The Classical–Quantum Boundary (Correspondence Principle)
- **Scientific Topic:** Emergence of classical Newtonian behavior in macroscopic systems.
- **Model:** Free wavepacket dispersion timescale $\tau = \frac{2 m \sigma_0^2}{\hbar}$. For an electron, $\tau \sim 10^{-16}\text{ s}$ (rapid spreading). For a baseball ($m = 0.145\text{ kg}$), $\tau \sim 10^{23}\text{ s}$ (dispersion is unobservable on cosmological timescales), validating Ehrenfest's theorem.
- **Badge Earned:** 🌌 *Reality Explorer*

---

## 📐 Scientific Validation & Physical Models

All physical computations are executed in Python (`app/physics/`) using SI units internally with CODATA fundamental constants:
- $\hbar = 1.054571817 \times 10^{-34}\text{ J}\cdot\text{s}$
- $m_e = 9.1093837 \times 10^{-31}\text{ kg}$
- $1\text{ eV} = 1.602176634 \times 10^{-19}\text{ J}$

### Numerical Stability Guarantees:
- In `app/physics/tunneling.py`, when $\kappa a > 50$, $\sinh^2(\kappa a)$ can trigger float overflow. The engine dynamically activates asymptotic logarithmic expansions ($T \approx \frac{16 E (V_0 - E)}{V_0^2} e^{-2\kappa a}$) and clamps gracefully to 0 when $2\kappa a > 700$.
- The exact boundary $E = V_0$ is evaluated via the continuous analytical limit:
  $$\lim_{E \to V_0} T = \frac{1}{1 + \frac{m a^2 V_0}{2\hbar^2}}$$
- 100% of physical equations, boundary conditions, and limiting cases are covered by automated unit tests in `tests/test_tunneling.py`, `tests/test_double_slit.py`, and `tests/test_uncertainty.py`.

---

## 🏗️ Architecture & Technology Stack

```
ScienceQuest
├── api/index.py                    # Vercel entrypoint (exposes app.web:app)
├── public/                         # Static frontend, served from Vercel's CDN
│   ├── index.html, overlay.html, favicon.svg
│   └── static/ (css/, js/app.js, js/backend.js, js/overlay.js, js/visualizations/*.js)
├── app/
│   ├── web.py                      # Stateless HTTP API for the website (Vercel)
│   ├── solo.py                     # Pure, framework-free game logic used by web.py
│   ├── main.py                     # Self-hosted LIVE server: REST, WebSocket hub, Twitch, OBS
│   ├── config.py, ratelimit.py
│   ├── physics/                    # Physics engine (numpy): tunneling, double slit, uncertainty,
│   │                               #   wave lab, correspondence
│   ├── game/
│   │   ├── missions.py             # Missions, controls, quiz questions (single source of truth)
│   │   ├── validation.py           # Strict parameter and username validation
│   │   ├── state.py                # Live-mode state and voting
│   │   └── scoring.py              # Points, streaks, badges (live mode)
│   ├── twitch/ (client.py, parser.py)
│   └── ai/ (quark.py, fallback_knowledge.py)
├── tests/                          # pytest suite (physics reference checks, validation, API)
├── vercel.json                     # Routing + security headers
├── requirements.txt                # Runtime deps for Vercel (fastapi, numpy, httpx)
├── requirements-live.txt           # + uvicorn, websockets, python-dotenv for run.py
├── requirements-dev.txt            # + pytest
├── run.py                          # Start the self-hosted live server
└── AUDIT.md                        # Quality, security and scientific review
```

---

## 🤖 Quark: The AI Science Companion

Quark is an integrated educational assistant who is always contextually aware of the active mission, current physical parameter values, and exact numerical results.

### Explanation Tiers:
- **EXPLORER:** Plain language, playful analogies, no complex math. Suitable for children and beginners.
- **SCIENTIST:** Formal physical terminology, parameter effects, graph interpretation, and equations in words.
- **RESEARCHER:** Exact wave equations, boundary conditions, Hamiltonian operators, and formal semiclassical limits.

### Zero-Downtime Fallback:
If an OpenAI API key is not provided or if the network is offline, Quark automatically falls back to curated scientific responses from `app/ai/fallback_knowledge.py`, ensuring the game never crashes or freezes.

---

## 🎮 Twitch Community Integration

ScienceQuest Live connects to Twitch chat via real-time WebSocket IRC (`wss://irc-ws.chat.twitch.tv:443`).

### Supported Chat Commands:
- `!vote <A|B|C|D>`: Casts prediction vote for active round.
- `!energy <value>`: Sets particle energy in eV (e.g., `!energy 4.5`).
- `!barrier <value>`: Sets barrier height in eV (e.g., `!barrier 6.0`).
- `!width <value>`: Sets barrier width in nm (e.g., `!width 0.35`).
- `!ask <question>`: Asks Quark a question about the active experiment.
- `!score`: Displays current player points, streak, and badges.
- `!mission <1-5>`: Requests a mission change.
- `!help`: Lists available commands.

### Dual Operating Modes:
1. **Live Twitch Mode (`SIMULATION_MODE=false`):** Connects to your live Twitch channel with your bot nickname and OAuth token.
2. **Simulation Mode (`SIMULATION_MODE=true`):** Simulates realistic audience participation (votes, questions, and parameter adjustments from simulated viewers like `QuantumAlice`, `NeutrinoNed`, and `CosmicBob`) clearly labeled with `[SIM]` tags for effortless local testing.

---

## 📺 OBS Studio Stream Overlay

ScienceQuest Live includes a broadcast overlay for OBS Studio:
1. Open OBS Studio.
2. Add a new **Browser Source**.
3. Set URL to: `http://localhost:8000/overlay`
4. Set Width to `1920` and Height to `1080` (or `1280` x `720`).
5. Check **Shutdown source when not visible** and **Refresh browser when scene becomes active**.
6. The overlay provides a transparent, broadcast-ready graphic showing the active question, live audience voting bars, and Quark's spoken commentary.

---

## ☁️ Deploying the website to Vercel

The public website is a **static frontend (`public/`) plus a small stateless Python API (`api/index.py`)**.
Each visitor plays their own session: progress is stored in their browser and the server only computes
validated physics. (Serverless instances do not share memory, so the shared-room Twitch mode cannot run
on Vercel; see "Two editions" below.)

```bash
pip install -r requirements-dev.txt
pytest                                   # run this first: it also exercises the HTTP layer
npm i -g vercel
vercel                                   # preview deployment
vercel --prod                            # production
```

Or push the repository to GitHub and import it at vercel.com/new. No build command or output directory is
needed (leave "Framework Preset" as *Other*).

Optional environment variables (Project Settings -> Environment Variables):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Lets Quark answer free-form questions with an LLM. **Leave unset to use the curated offline answers.** If you set it, also add the rate-limit rule below, otherwise anyone can run up your bill. |
| `OPENAI_MODEL` | Model name (default `gpt-4o-mini`). |

### Hardening on Vercel
* Add a **Vercel Firewall rate-limit rule** for `/api/solo/quark` (for example 10 requests/minute per IP). The
  in-app limiter is per function instance, so it is only a first line of defence.
* Security headers (CSP, HSTS, frame denial ...) are set in `vercel.json`.
* Never commit `.env`; set secrets in the Vercel dashboard.

### Two editions
| | Website (Vercel) | Live mode (`python run.py`) |
|---|---|---|
| State | In the visitor's browser | Shared server memory |
| Twitch chat / OBS overlay | not available | yes |
| Needs a long-running process | no | yes (your PC, Railway, Fly.io, Render, a VPS) |
| Leaderboard | personal progress (localStorage) | shared, server-side |

Live mode needs `ADMIN_TOKEN` when reachable from the internet (see `.env.example`).

---

## 🚀 Installation & Quickstart

### 1. Prerequisites
- Python 3.12+ installed.
- Git installed.

### 2. Clone and Setup Environment
```powershell
cd c:\Users\HP\Music\Downloads\Codex
python -m pip install -r requirements-live.txt
```

### 3. Configure Credentials (Optional)
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
To run with live Twitch chat:
```env
SIMULATION_MODE=false
TWITCH_CHANNEL=your_channel_name
TWITCH_BOT_NICKNAME=your_bot_name
TWITCH_OAUTH_TOKEN=oauth:your_token_here
OPENAI_API_KEY=sk-your_openai_api_key_here
```
*(If you leave `.env` empty or omit it, the game runs automatically in Simulation Mode with local offline AI fallback!)*

### 4. Launch the Game Server
```powershell
python run.py
```
Open your browser to:
- **Main Game UI:** `http://localhost:8000`
- **OBS Stream Overlay:** `http://localhost:8000/overlay`

---

## 🧪 Automated Testing Suite

Execute the complete pytest test suite covering physics equations, boundary conditions, Twitch command parsing, rate limiting, game state transitions, and API endpoints:
```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

**Results:**
- `tests/test_tunneling.py`: 12 passed
- `tests/test_double_slit.py`: 3 passed
- `tests/test_uncertainty.py`: 3 passed
- `tests/test_twitch_parser.py`: 6 passed
- `tests/test_game_state.py`: 5 passed
- `tests/test_api.py`: 7 passed
- **Total: 36 passed with 100% success in ~1.2s**

---

## 🏆 Hackathon Demo & Submission Checklist

- [x] **Core Idea:** Interactive science education comparing classical and quantum mechanics.
- [x] **Brand & Mascot:** ScienceQuest Live with animated Quark AI science companion.
- [x] **The Four Worlds:** Classical World, Quantum World, Reality Battle, and Challenge Lab.
- [x] **Flagship Mission 1 (The Impossible Wall):** Mathematically rigorous rectangular barrier tunneling vs classical ball bounce, with numerical stability and continuous boundary limits.
- [x] **Missions 2-5:** Double-slit with which-path decoherence, Heisenberg uncertainty principle, wave superposition laboratory, and the classical correspondence limit.
- [x] **Twitch Integration:** Real IRC connection (`wss://irc-ws.chat.twitch.tv:443`) + built-in simulation mode.
- [x] **OBS Studio Overlay:** Dedicated `/overlay` route for broadcast livestreams.
- [x] **Testing & Verification:** 36 automated tests passing.
- [x] **Security:** All credentials isolated in `.env` (gitignored), zero private keys committed.
- [x] **Codex Session ID:** Recorded from the hackathon development thread.

---

*ScienceQuest Live — Two Worlds. Different Rules. One Curious Universe.*
