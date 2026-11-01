# ScienceQuest: Quality, Security and Scientific Audit

Scope: the code in `Codex - Copy.zip` (FastAPI backend, physics engine, vanilla-JS frontend, Twitch integration).
Method: code reading, independent re-derivation of the physics (brute-force solvers, FFT moments, flux
conservation, closed-form limits), hostile-input probing of the game logic, and a dependency/deployment review.

## 0. Why the original could not simply be "deployed on Vercel"

| Original design | Why it fails on Vercel | What changed |
|---|---|---|
| One global `GameStateManager` in process memory | Serverless instances do not share memory: two requests can see two different games | The website is stateless. The browser owns the session; the server only computes validated physics (`app/solo.py`) |
| WebSocket broadcast to all viewers | Vercel WebSockets exist (GA for Python), but each connection is pinned to one instance and closed at the function's max duration. Broadcasts do not cross instances | Not used on the website |
| Twitch IRC loop in `lifespan` | Needs a process that stays alive | Kept as a self-hosted *live mode* (`python run.py`) |
| Every visitor shares one lab | On a public site, one visitor moving a slider changed everyone's experiment | Per-visitor sessions |
| `builds` + `routes` legacy config, `pytest`/`uvicorn`/`httpx` in runtime requirements | Larger bundle, deprecated config | `rewrites` + `headers`, split requirements files |

The earlier commit's polling fallback (`/api/state/poll`) had the same root problem and was correctly reverted.

## 1. Scientific findings

| # | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| S1 | **High** | Uncertainty: chirped packet had its momentum spread understated. Plotted phase used `b = C/(2σ²)` but `Δp` used `√(1+C²)`; the true factor for that phase is `√(1+4C²)`. At C = 3 the app showed Δx·Δp = 3.16 × ħ/2, the true value is 6.08 × | FFT moments of the same wavefunction | Fixed (phase now `C/(4σ²)`, consistent with `√(1+C²)`); regression test against FFT |
| S2 | **High** | Tunneling plot for E > V₀ violated flux conservation. A floor `max(1e-18, E−V₀)` is 6.24 eV, so for any excess energy below that the wavevector was wrong; the plot showed ≈ 100 % transmission while the reported T was 0.64 | `|ψ|²` right of the barrier = 0.9999 vs T = 0.635 | Fixed; flux test over/under barrier |
| S3 | Medium | Exact E = V₀ made the matching matrix singular (k₂ = 0). The bug in S2 had been masking it | `LinAlgError` after S2 fix | Fixed with the analytic linear-interior solution `t = 2/(2 − i k₁ a)`, verified against the closed-form limit |
| S4 | Medium | Tunneling `κ` readout was always **0**: the field was never exported by `to_dict()` | UI reads `kappa_or_k2_inv_nm` | Fixed |
| S5 | Medium | Mission 5 text claimed a baseball's spreading time is "millions of years". It is ≈ 3×10²⁷ s ≈ 10²⁰ years, about 10¹⁰ times the age of the universe | τ = 2mσ₀²/ħ | Fixed everywhere |
| S6 | Medium | Unsupported specific claims: decoherence "in picoseconds" and "under 10⁻²⁰ s"; electron packet "disperses instantaneously"; "ontological, not epistemological" stated as fact | Text review | Removed or reworded; test forbids those phrases |
| S7 | Medium | Double slit: visibility was hard-coded 1.0/0.0, fringe count came from a 300-point peak search that aliases for fine fringes, and the which-path pattern used a ±d/2 *screen* shift that had no physical meaning | Code review | Rewritten: analytic V = √(1−D²) (Englert–Greenberger), analytic fringe count/spacing, partial which-path information supported |
| S8 | Medium | The "classical" curve in the double slit equalled the quantum curve, so the comparison was empty | `np.allclose` | Added `classical_particle_pattern` (what classical particles would do); wave-vs-particle difference is now real |
| S9 | Low | Correspondence output rounded metre-scale values to 4 decimals, so the electron's envelope bounds were all 0.0 in the API | Output inspection | Fixed (scientific notation) |
| S10 | Low | Dust grain labelled "1 picogram" but 1e-12 kg is 1 nanogram | Unit check | Label fixed |
| S11 | Low | Quiz question for Mission 1 stated concrete E, V₀ but the sliders could contradict it (E = 8 eV > V₀ = 5 eV) | Probe | Question now states the regime (E < V₀) explicitly and stays true for every slider value |

Verified correct (no change needed): the closed-form tunneling transmission matches an independent 4×4 solver to
~1e-15 relative error across 100+ parameter combinations, including both regimes; `Δx·Δp ≥ ħ/2` holds across the full slider range; the
Fraunhofer approximation is valid over the whole allowed range (worst case `w²/λ` = 22.5 mm ≪ L ≥ 0.5 m).

## 2. Functional / quality findings

| # | Severity | Finding | Status |
|---|---|---|---|
| Q1 | **High** | Missions 2 and 5 could not be completed: the which-path detector, slit count and object selector (electron/baseball) existed only in the raw API, never in the UI | Added toggle/select/slider controls |
| Q2 | **High** | Home-page mission cards sent `GET` to a `POST`-only route (405), so selecting Missions 2–5 from the cards silently did nothing | Calls now go through the backend layer |
| Q3 | High | Correct answer was "A" for all 5 missions (and the longest option in most), so a player could score 100 % by position or length | Letters redistributed, distractors balanced, options shuffled per attempt; tests enforce it |
| Q4 | Medium | HUD labels, comparison boxes, legend and math drawer were hard-wired to Mission 1, so Missions 2–5 showed mislabeled numbers | Per-mission HUD/comparison; Mission-1-only widgets hidden elsewhere |
| Q5 | Medium | Sliders were rebuilt on every state update, interrupting drags | Built once per mission, then synced |
| Q6 | Medium | Quark prompt embedded the whole physics result including plot arrays (thousands of tokens per call) | Scalars only (measured: 6.5–27k characters down to 0.2–0.6k per call) |
| Q7 | Medium | Tests wrote fake players ("testviewer", 1155 pts) into the real leaderboard; nothing tested flux or FFT moments | Tests use temp files; added independent reference tests |
| Q8 | Low | `1`-second rounds closed instantly (integer truncation); rounds only expired when polled | `ceil`, deadline enforced on every vote |

## 3. Security findings

| # | Severity | Finding | Fix |
|---|---|---|---|
| X1 | **Critical** | Stored XSS: chat text, usernames and Quark answers were inserted with `innerHTML` in the main app and in the **OBS overlay**; `/api/chat/send` was unauthenticated and broadcast to every client (so `<img onerror=…>` ran in the streamer's OBS) | All rendering uses DOM APIs/`textContent`; no `innerHTML` remains; strict CSP (`script-src 'self'`) and inline `onclick` handlers removed |
| X2 | **Critical** | No authentication at all: anyone could change missions/parameters, open/resolve votes, and `/api/chat/send` hard-coded `is_mod_or_streamer=True`, so any visitor could run privileged chat commands | Admin token (or loopback-only) on control endpoints; privileged commands honoured only from the channel owner; web chat is never moderator input |
| X3 | High | `NaN`/strings/huge numbers bypassed validation (`nan < min` is false) and permanently poisoned the shared state: every later request returned HTTP 500 | One strict validator shared by REST, WebSocket, Twitch chat and the stateless API; failed updates roll back |
| X4 | High | Vote stuffing: `Alice`, `alice`, `ALICE`, `" alice"` counted separately in voting yet merged in scoring, so one person scored 945 points in a round instead of 120 | Usernames normalised and validated (Twitch charset) |
| X5 | High | OAuth callback had no `state` (login CSRF: anyone could swap the server's Twitch token); login open to all; `whispers:read` scope unused | One-time `state`, admin-only login, least-privilege scope |
| X6 | Medium | Votes accepted after the deadline until something polled the status; `/api/voting/resolve` re-awarded points on every call | Deadline checked per vote; resolution idempotent |
| X7 | Medium | Answer leaked: `GET /api/state` returned `correct_option` whenever voting was not open (including before any round) | Revealed only after resolution |
| X8 | Medium | Unbounded memory: vote table, rate-limit table, player table, chat DOM | Caps and purging |
| X9 | Medium | `/api/quark/ask` unauthenticated and unrate-limited (LLM cost abuse); viewer text placed inside the instruction prompt | Rate limits, length/control-char limits, delimited untrusted text |
| X10 | Low | `/api/status` disclosed OAuth redirect URI and client-id presence; WebSocket accepted any `Origin`, any message size; OpenAI error bodies were logged | Admin-only details, origin check, size/rate limits, status code only |
| X11 | Low | `.gitignore`d `data/` is correct; **no secrets were found in the git history** | n/a |

## 4. Not fixed / residual risks (be aware)

* **I could not run the FastAPI layer in my sandbox** (no network, FastAPI not installable). All logic lives in
  framework-free modules that *are* tested (96 tests pass, plus an end-to-end run of the real frontend
  `SoloBackend`). The thin HTTP adapters (`app/web.py`, `app/main.py`) are covered by `tests/test_web_api.py` and
  `tests/test_api.py`, which skip here. **Run `pytest` before deploying.** I also did not render the UI in a browser.
* One question per mission: the answer is discoverable by repeated attempts (solo mode has no leaderboard to
  cheat, and only the first attempt scores). In live mode, the previous round's answer is public. A larger question
  bank is the real fix.
* The website's progress lives in `localStorage`, so it is not tamper-proof. A trustworthy global leaderboard needs a
  database (Vercel Marketplace Redis/Postgres) plus server-side answer verification.
* In-app rate limiting is per serverless instance. Add a Vercel Firewall rate-limit rule (see README).
* Setting `OPENAI_API_KEY` on the public site exposes cost and prompt-injection surface (affects only the asking
  user, as nothing is broadcast). The offline curated answers are the safer default.
* Fonts load from Google Fonts (third-party request). Self-host them for full privacy/CSP tightening.
* Physics scope: idealised 1-D models. Which-path decoherence is parametrised by D, not simulated dynamically; the
  baseball τ depends on the chosen σ₀ (1 mm).
