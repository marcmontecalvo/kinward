/**
 * kinward-assistant-card - Epic 3 Story 10.5.
 *
 * Renders one assistant's visual identity generically from whatever Story 3.7
 * catalog pack it uses - the card never hardcodes a shape (orb/robot/animal/
 * humanoid all render through the same markup, driven entirely by the icon
 * and accent the backend already resolved for the assistant's current stage).
 *
 * Data source: sensor.kinward_assistants' `assistants` attribute (see sensor.py's
 * KinwardAssistantsSensor) - public identity fields only (id, name, visual pack,
 * current stage + icon, accent). Never reads `personality` - that never enters
 * HA entity state at all (cross-cutting architecture rule 6), so there is
 * nothing private for this card to accidentally expose.
 *
 * No build step, no framework dependency, no external network request - a
 * single self-contained custom element, consistent with this integration's
 * "core HA cards by default, additive HACS enhancements only" approach
 * (cross-cutting rule 11).
 */

const DEFAULT_SENSOR_ENTITY = "sensor.kinward_assistants";

class KinwardAssistantCard extends HTMLElement {
  setConfig(config) {
    if (!config || (!config.assistant_id && !config.assistant_name)) {
      throw new Error(
        "kinward-assistant-card: set either 'assistant_id' or 'assistant_name' in the card config."
      );
    }
    this._config = config;
    this._lastRenderKey = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 3;
  }

  static getStubConfig() {
    return { assistant_name: "" };
  }

  _findAssistant() {
    const entityId = this._config.entity || DEFAULT_SENSOR_ENTITY;
    const state = this._hass.states[entityId];
    const assistants = (state && state.attributes && state.attributes.assistants) || [];
    if (this._config.assistant_id) {
      return assistants.find((assistant) => assistant.id === this._config.assistant_id);
    }
    return assistants.find((assistant) => assistant.name === this._config.assistant_name);
  }

  _reducedMotion() {
    return (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  _renderEmpty(message) {
    this.innerHTML = `
      <ha-card>
        <div class="kinward-assistant-card__body kinward-assistant-card__body--empty">
          ${message}
        </div>
      </ha-card>
      ${this._styles()}
    `;
  }

  _styles() {
    return `
      <style>
        ha-card { overflow: hidden; }
        .kinward-assistant-card__body {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 20px 16px;
        }
        .kinward-assistant-card__body--empty {
          color: var(--secondary-text-color);
          font-style: italic;
        }
        .kinward-assistant-card__visual {
          width: 72px;
          height: 72px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          --mdc-icon-size: 40px;
        }
        .kinward-assistant-card__visual--transition {
          transition: background-color 0.6s ease, opacity 0.6s ease;
        }
        .kinward-assistant-card__visual img {
          width: 100%;
          height: 100%;
          border-radius: 50%;
          object-fit: cover;
        }
        .kinward-assistant-card__name {
          font-size: 1.1em;
          font-weight: 500;
        }
        .kinward-assistant-card__stage {
          font-size: 0.85em;
          color: var(--secondary-text-color);
          text-transform: capitalize;
        }
      </style>
    `;
  }

  _render() {
    if (!this._hass || !this._config) {
      return;
    }
    const assistant = this._findAssistant();
    if (!assistant) {
      this._renderEmpty("Kinward assistant not found - check the card's configuration.");
      return;
    }

    const renderKey = `${assistant.id}:${assistant.visual_stage}:${assistant.accent}`;
    const isFirstRender = this._lastRenderKey === null;
    this._lastRenderKey = renderKey;
    const transitionClass =
      !isFirstRender && !this._reducedMotion() ? " kinward-assistant-card__visual--transition" : "";

    const visualMarkup = assistant.visual_stage_preview_image
      ? `<img src="${assistant.visual_stage_preview_image}" alt="" />`
      : `<ha-icon icon="${assistant.visual_stage_icon}"></ha-icon>`;

    this.innerHTML = `
      <ha-card>
        <div class="kinward-assistant-card__body">
          <div
            class="kinward-assistant-card__visual${transitionClass}"
            style="background-color: ${assistant.accent}22; color: ${assistant.accent};"
          >
            ${visualMarkup}
          </div>
          <div class="kinward-assistant-card__name">${assistant.name}</div>
          <div class="kinward-assistant-card__stage">${assistant.visual_stage}</div>
        </div>
      </ha-card>
      ${this._styles()}
    `;
  }
}

customElements.define("kinward-assistant-card", KinwardAssistantCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kinward-assistant-card",
  name: "Kinward Assistant",
  description: "Shows one Kinward assistant's visual identity (Epic 3 Story 10.5).",
});
