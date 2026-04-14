/**
 * Snoo Premium Card - Custom Lovelace card mimicking the Snoo iOS app.
 *
 * Displays a circular level indicator with color-coded states,
 * play/stop button, level controls, lock toggle, and premium settings.
 */

const LEVEL_COLORS = {
  stop: "#8E8E93",
  baseline: "#007AFF",
  weaning_baseline: "#5856D6",
  level1: "#AF52DE",
  level2: "#34C759",
  level3: "#FF9500",
  level4: "#FF3B30",
  pretimeout: "#FF3B30",
  timeout: "#FF3B30",
};

const LEVEL_LABELS = {
  stop: "Off",
  baseline: "Baseline",
  weaning_baseline: "Weaning",
  level1: "Level 1",
  level2: "Level 2",
  level3: "Level 3",
  level4: "Level 4",
  pretimeout: "Pre-Timeout",
  timeout: "Timeout",
};

const LEVEL_ORDER = [
  "stop",
  "baseline",
  "weaning_baseline",
  "level1",
  "level2",
  "level3",
  "level4",
];

class SnooCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._buildCard();
      this._initialized = true;
    }
    this._updateCard();
  }

  setConfig(config) {
    this._config = config;
    this._entityPrefix = config.entity_prefix || "snoo_premium";
  }

  _getEntity(suffix) {
    // Try various entity ID patterns
    const candidates = [
      `${suffix}.${this._entityPrefix}_${suffix.split(".").pop()}`,
    ];
    // Build from config prefix
    const domain = suffix.split("_")[0];
    for (const [key, state] of Object.entries(this._hass.states)) {
      if (key.includes("snoo") && key.endsWith(suffix.replace(/^[^.]*\./, ""))) {
        return state;
      }
    }
    return null;
  }

  _findEntity(domain, key) {
    for (const [entityId, state] of Object.entries(this._hass.states)) {
      if (
        entityId.startsWith(`${domain}.`) &&
        entityId.includes("snoo") &&
        entityId.includes(key)
      ) {
        return { entityId, state };
      }
    }
    return { entityId: null, state: null };
  }

  _buildCard() {
    const shadow = this.attachShadow({ mode: "open" });
    shadow.innerHTML = `
      <style>
        :host {
          --card-bg: #1C1C1E;
          --text-primary: #FFFFFF;
          --text-secondary: #8E8E93;
          --surface: #2C2C2E;
          --surface-hover: #3A3A3C;
          --accent: #007AFF;
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }

        .snoo-card {
          background: var(--card-bg);
          border-radius: 20px;
          padding: 24px 20px;
          color: var(--text-primary);
          max-width: 420px;
          margin: 0 auto;
        }

        /* Header */
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .header h2 {
          font-size: 20px;
          font-weight: 600;
          letter-spacing: -0.3px;
        }
        .status-badges {
          display: flex;
          gap: 6px;
        }
        .badge {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 700;
          background: var(--surface);
          color: var(--text-secondary);
          transition: all 0.2s;
        }
        .badge.active {
          background: var(--accent);
          color: white;
        }

        /* Safety clips */
        .clips {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        .clip {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--text-secondary);
        }
        .clip-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #FF3B30;
        }
        .clip-dot.connected {
          background: #34C759;
        }

        /* Main circle */
        .circle-container {
          display: flex;
          justify-content: center;
          align-items: center;
          margin: 20px 0;
        }
        .level-ring {
          width: 220px;
          height: 220px;
          border-radius: 50%;
          border: 6px solid var(--level-color, var(--accent));
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          position: relative;
          transition: border-color 0.4s ease, box-shadow 0.4s ease;
          box-shadow: 0 0 30px rgba(0, 122, 255, 0.15);
        }
        .level-ring.active {
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 30px rgba(0, 122, 255, 0.15); }
          50% { box-shadow: 0 0 50px rgba(0, 122, 255, 0.35); }
        }
        .level-label {
          font-size: 28px;
          font-weight: 700;
          letter-spacing: -0.5px;
        }
        .session-time {
          font-size: 16px;
          color: var(--text-secondary);
          margin-top: 4px;
          font-variant-numeric: tabular-nums;
        }

        /* Level dots */
        .level-dots {
          display: flex;
          justify-content: center;
          gap: 10px;
          margin: 16px 0;
        }
        .level-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--surface);
          transition: background 0.3s, transform 0.2s;
          cursor: pointer;
        }
        .level-dot:active {
          transform: scale(1.3);
        }
        .level-dot.filled {
          background: var(--level-color, var(--accent));
        }

        /* Controls row */
        .controls {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 20px;
          margin: 20px 0;
        }
        .ctrl-btn {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          border: none;
          background: var(--surface);
          color: var(--text-primary);
          font-size: 24px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.15s, transform 0.1s;
          -webkit-tap-highlight-color: transparent;
        }
        .ctrl-btn:active {
          transform: scale(0.92);
          background: var(--surface-hover);
        }
        .play-btn {
          width: 72px;
          height: 72px;
          background: var(--accent);
          font-size: 30px;
        }
        .play-btn:active {
          background: #0062CC;
        }
        .ctrl-btn.active-toggle {
          background: var(--accent);
        }

        /* Divider */
        .divider {
          height: 1px;
          background: var(--surface);
          margin: 20px 0;
        }

        /* Premium settings section */
        .settings-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.8px;
          margin-bottom: 12px;
        }
        .setting-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          background: var(--surface);
          border-radius: 12px;
          margin-bottom: 8px;
          transition: background 0.15s;
          cursor: pointer;
          -webkit-tap-highlight-color: transparent;
        }
        .setting-row:active {
          background: var(--surface-hover);
        }
        .setting-label {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 15px;
          font-weight: 500;
        }
        .setting-icon {
          font-size: 18px;
          width: 24px;
          text-align: center;
        }

        /* Toggle switch */
        .toggle {
          width: 50px;
          height: 30px;
          border-radius: 15px;
          background: #48484A;
          position: relative;
          transition: background 0.25s;
          flex-shrink: 0;
        }
        .toggle.on {
          background: #34C759;
        }
        .toggle::after {
          content: "";
          position: absolute;
          width: 26px;
          height: 26px;
          border-radius: 50%;
          background: white;
          top: 2px;
          left: 2px;
          transition: transform 0.25s;
          box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        .toggle.on::after {
          transform: translateX(20px);
        }

        /* Select dropdown */
        .setting-select {
          background: var(--surface-hover);
          color: var(--text-primary);
          border: none;
          border-radius: 8px;
          padding: 6px 12px;
          font-size: 14px;
          font-family: inherit;
          cursor: pointer;
          -webkit-appearance: none;
          appearance: none;
        }
      </style>

      <div class="snoo-card">
        <div class="header">
          <h2>Snoo</h2>
          <div class="status-badges">
            <div class="badge" id="badge-m" title="Motion Limiter">M</div>
            <div class="badge" id="badge-w" title="Weaning Mode">W</div>
            <div class="badge" id="badge-c" title="Car Ride Mode">C</div>
          </div>
        </div>

        <div class="clips">
          <div class="clip">
            <div class="clip-dot" id="clip-left"></div>
            <span>Left clip</span>
          </div>
          <div class="clip">
            <div class="clip-dot" id="clip-right"></div>
            <span>Right clip</span>
          </div>
        </div>

        <div class="circle-container">
          <div class="level-ring" id="level-ring">
            <div class="level-label" id="level-label">Off</div>
            <div class="session-time" id="session-time">--:--:--</div>
          </div>
        </div>

        <div class="level-dots" id="level-dots"></div>

        <div class="controls">
          <button class="ctrl-btn" id="btn-down" title="Level Down">&#x25BC;</button>
          <button class="ctrl-btn play-btn" id="btn-play" title="Start/Stop">&#x25B6;</button>
          <button class="ctrl-btn" id="btn-up" title="Level Up">&#x25B2;</button>
          <button class="ctrl-btn" id="btn-lock" title="Level Lock">&#x1F512;</button>
        </div>

        <div class="divider"></div>

        <div class="settings-title">Premium Settings</div>

        <div class="setting-row" id="row-motion-limiter">
          <div class="setting-label">
            <span class="setting-icon">&#x1F3CE;</span>
            <span>Motion Limiter</span>
          </div>
          <div class="toggle" id="toggle-motion-limiter"></div>
        </div>

        <div class="setting-row" id="row-weaning">
          <div class="setting-label">
            <span class="setting-icon">&#x1F6CF;</span>
            <span>Weaning Mode</span>
          </div>
          <div class="toggle" id="toggle-weaning"></div>
        </div>

        <div class="setting-row" id="row-car-ride">
          <div class="setting-label">
            <span class="setting-icon">&#x1F697;</span>
            <span>Car Ride Mode</span>
          </div>
          <div class="toggle" id="toggle-car-ride"></div>
        </div>

        <div class="setting-row" id="row-sleepytime">
          <div class="setting-label">
            <span class="setting-icon">&#x1F3B5;</span>
            <span>Sleepytime Sounds</span>
          </div>
          <div class="toggle" id="toggle-sleepytime"></div>
        </div>

        <div class="divider"></div>

        <div class="settings-title">Response Settings</div>

        <div class="setting-row">
          <div class="setting-label">
            <span class="setting-icon">&#x1F442;</span>
            <span>Responsiveness</span>
          </div>
          <select class="setting-select" id="select-responsiveness">
            <option value="Normal">Normal</option>
            <option value="Increased">Increased</option>
          </select>
        </div>

        <div class="setting-row">
          <div class="setting-label">
            <span class="setting-icon">&#x1F4C8;</span>
            <span>Start Level</span>
          </div>
          <select class="setting-select" id="select-start-level">
            <option value="Baseline">Baseline</option>
            <option value="Level 1">Level 1</option>
            <option value="Level 2">Level 2</option>
          </select>
        </div>
      </div>
    `;

    // Build level dots
    const dotsContainer = shadow.getElementById("level-dots");
    const levels = ["baseline", "level1", "level2", "level3", "level4"];
    levels.forEach((lvl, i) => {
      const dot = document.createElement("div");
      dot.className = "level-dot";
      dot.dataset.level = lvl;
      dot.addEventListener("click", () => this._setLevel(lvl));
      dotsContainer.appendChild(dot);
    });

    // Bind controls
    shadow.getElementById("btn-play").addEventListener("click", () => this._togglePlay());
    shadow.getElementById("btn-up").addEventListener("click", () => this._levelUp());
    shadow.getElementById("btn-down").addEventListener("click", () => this._levelDown());
    shadow.getElementById("btn-lock").addEventListener("click", () => this._toggleLock());

    // Bind toggles
    shadow.getElementById("row-motion-limiter").addEventListener("click", () =>
      this._toggleSwitch("motion_limiter")
    );
    shadow.getElementById("row-weaning").addEventListener("click", () =>
      this._toggleSwitch("weaning")
    );
    shadow.getElementById("row-car-ride").addEventListener("click", () =>
      this._toggleSwitch("car_ride_mode")
    );
    shadow.getElementById("row-sleepytime").addEventListener("click", () =>
      this._toggleSwitch("sticky_white_noise")
    );

    // Bind selects
    shadow.getElementById("select-responsiveness").addEventListener("change", (e) =>
      this._setSelect("responsiveness", e.target.value)
    );
    shadow.getElementById("select-start-level").addEventListener("change", (e) =>
      this._setSelect("motion_start_level", e.target.value)
    );
  }

  _updateCard() {
    if (!this._hass || !this.shadowRoot) return;
    const s = this.shadowRoot;

    const stateEntity = this._findEntity("sensor", "state_premium");
    const intensityEntity = this._findEntity("select", "intensity");
    const holdEntity = this._findEntity("switch", "level_lock");
    const stickyEntity = this._findEntity("switch", "sleepytime");
    const motionEntity = this._findEntity("switch", "motion_limiter");
    const weaningEntity = this._findEntity("switch", "weaning");
    const carRideEntity = this._findEntity("switch", "car_ride_mode");
    const sessionEntity = this._findEntity("sensor", "session_duration");
    const leftClip = this._findEntity("binary_sensor", "left_clip");
    const rightClip = this._findEntity("binary_sensor", "right_clip");
    const responsiveness = this._findEntity("select", "responsiveness");
    const startLevel = this._findEntity("select", "motion_start_level");

    // Current state/level
    const currentState = stateEntity.state?.state || "stop";
    const color = LEVEL_COLORS[currentState] || LEVEL_COLORS.stop;
    const label = LEVEL_LABELS[currentState] || currentState;
    const isActive = currentState !== "stop" && currentState !== "timeout";

    // Update ring
    const ring = s.getElementById("level-ring");
    ring.style.setProperty("--level-color", color);
    ring.style.borderColor = color;
    ring.style.boxShadow = `0 0 30px ${color}33`;
    ring.classList.toggle("active", isActive);

    // Label
    s.getElementById("level-label").textContent = label;
    s.getElementById("level-label").style.color = color;

    // Session time
    const sessionTime = sessionEntity.state?.state;
    s.getElementById("session-time").textContent =
      sessionTime && sessionTime !== "unknown" && sessionTime !== "unavailable"
        ? sessionTime
        : isActive
        ? "0:00:00"
        : "--:--:--";

    // Level dots
    const dots = s.querySelectorAll(".level-dot");
    const activeLevels = ["baseline", "level1", "level2", "level3", "level4"];
    const currentIdx = activeLevels.indexOf(
      currentState === "weaning_baseline" ? "baseline" : currentState
    );
    dots.forEach((dot, i) => {
      dot.classList.toggle("filled", i <= currentIdx && isActive);
      dot.style.setProperty("--level-color", color);
    });

    // Play button
    const playBtn = s.getElementById("btn-play");
    playBtn.innerHTML = isActive ? "&#x25A0;" : "&#x25B6;";
    playBtn.style.background = isActive ? "#FF3B30" : "#007AFF";

    // Lock button
    const isLocked = holdEntity.state?.state === "on";
    const lockBtn = s.getElementById("btn-lock");
    lockBtn.classList.toggle("active-toggle", isLocked);

    // Safety clips
    const leftClipEl = s.getElementById("clip-left");
    const rightClipEl = s.getElementById("clip-right");
    leftClipEl.classList.toggle("connected", leftClip.state?.state === "on");
    rightClipEl.classList.toggle("connected", rightClip.state?.state === "on");

    // Status badges
    s.getElementById("badge-m").classList.toggle(
      "active",
      motionEntity.state?.state === "on"
    );
    s.getElementById("badge-w").classList.toggle(
      "active",
      weaningEntity.state?.state === "on"
    );
    s.getElementById("badge-c").classList.toggle(
      "active",
      carRideEntity.state?.state === "on"
    );

    // Toggles
    this._updateToggle(s, "toggle-motion-limiter", motionEntity.state?.state === "on");
    this._updateToggle(s, "toggle-weaning", weaningEntity.state?.state === "on");
    this._updateToggle(s, "toggle-car-ride", carRideEntity.state?.state === "on");
    this._updateToggle(s, "toggle-sleepytime", stickyEntity.state?.state === "on");

    // Selects
    const respSelect = s.getElementById("select-responsiveness");
    if (responsiveness.state) {
      respSelect.value = responsiveness.state.state;
    }
    const startSelect = s.getElementById("select-start-level");
    if (startLevel.state) {
      startSelect.value = startLevel.state.state;
    }

    // Store entity IDs for actions
    this._entities = {
      intensity: intensityEntity.entityId,
      hold: holdEntity.entityId,
      stickyWhiteNoise: stickyEntity.entityId,
      motionLimiter: motionEntity.entityId,
      weaning: weaningEntity.entityId,
      carRide: carRideEntity.entityId,
      responsiveness: responsiveness.entityId,
      startLevel: startLevel.entityId,
      start: this._findEntity("button", "start_premium").entityId,
      state: stateEntity.entityId,
    };
    this._currentState = currentState;
  }

  _updateToggle(shadow, id, isOn) {
    const el = shadow.getElementById(id);
    if (el) el.classList.toggle("on", !!isOn);
  }

  _togglePlay() {
    const isActive =
      this._currentState !== "stop" && this._currentState !== "timeout";
    if (isActive) {
      // Stop: set intensity to stop
      this._hass.callService("select", "select_option", {
        entity_id: this._entities.intensity,
        option: "stop",
      });
    } else {
      // Start
      this._hass.callService("button", "press", {
        entity_id: this._entities.start,
      });
    }
  }

  _levelUp() {
    const idx = LEVEL_ORDER.indexOf(this._currentState);
    if (idx < LEVEL_ORDER.length - 1 && idx >= 0) {
      this._setLevel(LEVEL_ORDER[idx + 1]);
    }
  }

  _levelDown() {
    const idx = LEVEL_ORDER.indexOf(this._currentState);
    if (idx > 1) {
      // Don't go below baseline (index 1), stop is index 0
      this._setLevel(LEVEL_ORDER[idx - 1]);
    }
  }

  _setLevel(level) {
    this._hass.callService("select", "select_option", {
      entity_id: this._entities.intensity,
      option: level,
    });
  }

  _toggleLock() {
    const entity = this._hass.states[this._entities.hold];
    const service = entity?.state === "on" ? "turn_off" : "turn_on";
    this._hass.callService("switch", service, {
      entity_id: this._entities.hold,
    });
  }

  _toggleSwitch(key) {
    const map = {
      motion_limiter: this._entities.motionLimiter,
      weaning: this._entities.weaning,
      car_ride_mode: this._entities.carRide,
      sticky_white_noise: this._entities.stickyWhiteNoise,
    };
    const entityId = map[key];
    if (!entityId) return;
    const entity = this._hass.states[entityId];
    const service = entity?.state === "on" ? "turn_off" : "turn_on";
    this._hass.callService("switch", service, { entity_id: entityId });
  }

  _setSelect(key, value) {
    const map = {
      responsiveness: this._entities.responsiveness,
      motion_start_level: this._entities.startLevel,
    };
    const entityId = map[key];
    if (!entityId) return;
    this._hass.callService("select", "select_option", {
      entity_id: entityId,
      option: value,
    });
  }

  getCardSize() {
    return 8;
  }

  static getStubConfig() {
    return {};
  }
}

customElements.define("snoo-card", SnooCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "snoo-card",
  name: "Snoo Premium Card",
  description: "Full Snoo bassinet control card mimicking the iOS app",
});
