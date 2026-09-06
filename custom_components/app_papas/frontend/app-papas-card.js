class AppPapasCard extends HTMLElement {
  set hass(hass) { this._hass = hass; this.render(); }
  setConfig(config) { this.config = {...config}; }
  getCardSize() { return 4; }
  render() {
    if (!this._hass) return;
    const states = this._hass.states || {};
    const find = (domainKey, friendly) => {
      if (this.config?.[domainKey] && states[this.config[domainKey]]) return states[this.config[domainKey]].state;
      const candidate = Object.values(states).find(s => s.entity_id?.startsWith("sensor.") && s.attributes?.friendly_name === friendly);
      return candidate ? candidate.state : "–";
    };
    const score = find("score_entity", "Puntuación de hoy");
    const pending = find("shopping_entity", "Compra pendiente");
    const streak = find("streak_entity", "Racha actual");
    this.innerHTML = `<ha-card><div style="padding:18px"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><div><div style="font-size:11px;letter-spacing:.12em;font-weight:900;opacity:.7">APP PAPÁS</div><h2 style="margin:4px 0">Hoy</h2></div><button id="open" style="border:0;border-radius:10px;padding:9px 12px;cursor:pointer">Abrir</button></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px"><div style="padding:11px;border:1px solid var(--divider-color);border-radius:12px"><div>✅</div><small>Checklist</small><strong style="display:block;font-size:22px">${score}/8</strong></div><div style="padding:11px;border:1px solid var(--divider-color);border-radius:12px"><div>🛒</div><small>Compra</small><strong style="display:block;font-size:22px">${pending}</strong></div><div style="padding:11px;border:1px solid var(--divider-color);border-radius:12px"><div>🔥</div><small>Racha</small><strong style="display:block;font-size:22px">${streak}</strong></div></div></div></ha-card>`;
    this.querySelector("#open")?.addEventListener("click",()=>{window.history.pushState({},"","/app_papas");window.dispatchEvent(new Event("location-changed"));});
  }
}
customElements.define("app-papas-card", AppPapasCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(x=>x.type==="app-papas-card"))window.customCards.push({type:"app-papas-card",name:"App Papás",description:"Resumen de Alimentación para Papás",preview:true,documentationURL:"https://github.com/Alfmat01/app-papas",getStubConfig:()=>({})});
