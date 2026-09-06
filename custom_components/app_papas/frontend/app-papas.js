const DOMAIN = "app_papas";
const API = `/api/${DOMAIN}`;

const PLAN = [
  ["Día 1: Encuentra tu Punto Débil", "d1_problema", "Mi mayor problema es", "Ej: Me derrumbo por la noche..."],
  ["Día 1: Encuentra tu Punto Débil", "d1_cuando", "¿Cuándo suelo desmoronarme?", "Ej: 10:30 pm, en la oficina..."],
  ["Día 2: La Regla de la Palma", "d2_proteinas", "Mis 3 proteínas rápidas favoritas", "Ej: Huevos, Atún, Yogur Griego"],
  ["Día 3: El Interruptor de Líquidos", "d3_bebida", "¿Qué bebida azucarada voy a sustituir esta semana?", "Ej: Refresco de cola por agua con limón"],
  ["Día 4: Cocina Fantasma", "d4_rapida1", "Mi Comida Rápida 1 (Papá / Niñas)", "Ej: Revuelto de 3 huevos + arroz / Revuelto con jamón y queso", true],
  ["Día 4: Cocina Fantasma", "d4_rapida2", "Mi Comida Rápida 2 (Papá / Niñas)", "Ej: Atún con frijoles y aguacate / Atún con maíz en sándwich", true],
  ["Día 4: Cocina Fantasma", "d4_rapida3", "Mi Comida Rápida 3 (Papá / Niñas)", "Ej: Huevos duros + yogurt / Tostada con aguacate", true],
  ["Día 5: Antirrestaurante", "d5_pedido", "Mi pedido saludable de comida rápida favorito", "Ej: Dos tacos de carne y agua, sin refresco"],
  ["Día 6: Protocolo de Reinicio", "d6_reinicio", "¿Qué haré si me salgo del camino?", "Ej: Beber agua, respirar hondo y decidir mi próxima comida sana"],
  ["Día 7: Tablero de Operaciones", "d7_problema", "Mi problema principal detectado", "Ej: Comer en la cama a medianoche"],
  ["Día 7: Tablero de Operaciones", "d7_bebida", "Mi bebida de emergencia (para no beber calorías)", "Ej: Agua con limón"],
];

const DAYS = [
  ["lunes", "Lunes"], ["martes", "Martes"], ["miercoles", "Miércoles"], ["jueves", "Jueves"],
  ["viernes", "Viernes"], ["sabado", "Sábado"], ["domingo", "Domingo"]
];
const MEALS = [["desayuno", "Desayuno"], ["almuerzo", "Almuerzo"], ["cena", "Cena"]];
const SHOPPING = [
  ["proteina", "Proteína"], ["carbohidratos", "Carbohidratos"],
  ["verduras_frutas", "Verduras / Frutas"], ["extras", "Extras"]
];
const CHECKLIST = [
  ["proteina", "¿Construí mis comidas principales alrededor de una proteína?"],
  ["agua", "¿Bebí suficiente agua hoy?"],
  ["calorias_liquidas", "¿Limité las calorías líquidas innecesarias?"],
  ["fruta_verdura", "¿Comí alguna fruta o verdura hoy?"],
  ["respaldo", "¿Tenía una comida de respaldo fácil disponible?"],
  ["comer_fuera", "¿Tomé al menos una mejor decisión al comer fuera?"],
  ["satisfecho", "¿Dejé de comer cuando estaba satisfecho en lugar de repleto?"],
  ["reinicio", "Si me salí del camino, ¿volví a él con mi siguiente comida?"]
];

function localDate() {
  const d = new Date();
  const off = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - off).toISOString().slice(0, 10);
}

class AppPapasPanel extends HTMLElement {
  set hass(value) {
    this._hass = value;
  }

  connectedCallback() {
    this.attachShadow({mode: "open"});
    this.state = this.initialState();
    this.day = localDate();
    this.tab = "hoy";
    this.busy = true;
    this.render();
    this.load();
  }

  initialState() {
    return {
      settings: {active_tab: "hoy"},
      days: {},
      plan: Object.fromEntries(PLAN.map(([, id]) => [id, ""])),
      menu: Object.fromEntries(DAYS.map(([d]) => [d, Object.fromEntries(MEALS.map(([m]) => [m, {papa: "", ninas: ""}]))])),
      shopping: Object.fromEntries(SHOPPING.map(([cat]) => [cat, []]))
    };
  }

  async load() {
    try {
      const res = await fetch(`${API}/data`, {credentials: "same-origin"});
      this.state = this.mergeState(this.initialState(), await res.json());
      this.tab = this.state.settings?.active_tab || "hoy";
      this.busy = false;
      this.render();
    } catch (err) {
      this.busy = false;
      this.error = err.message;
      this.render();
    }
  }

  mergeState(base, incoming) {
    const src = incoming || {};
    const result = {...base, ...src};
    result.settings = {...base.settings, ...(src.settings || {})};
    result.days = {...base.days, ...(src.days || {})};
    result.plan = {...base.plan, ...(src.plan || {})};
    result.menu = {...base.menu};
    for (const [day, meals] of Object.entries(src.menu || {})) {
      result.menu[day] = {...(base.menu[day] || {}), ...(meals || {})};
      for (const [meal, value] of Object.entries(meals || {})) {
        result.menu[day][meal] = {papa: "", ninas: "", ...(base.menu[day]?.[meal] || {}), ...(value || {})};
      }
    }
    result.shopping = {...base.shopping, ...(src.shopping || {})};
    for (const [cat] of Object.entries(base.shopping)) {
      result.shopping[cat] = Array.isArray(src.shopping?.[cat]) ? src.shopping[cat] : [];
    }
    return result;
  }

  async save() {
    this.busy = true;
    this.render();
    const res = await fetch(`${API}/data`, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(this.state),
    });
    this.state = this.mergeState(this.initialState(), await res.json());
    this.busy = false;
    this.render();
  }

  async saveDay() {
    this.state ||= this.initialState();
    this.state.days = this.state.days || {};
    this.busy = true;
    const res = await fetch(`${API}/day/${this.day}`, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(this.state.days[this.day] || {}),
    });
    this.state.days[this.day] = await res.json();
    this.busy = false;
    this.render();
  }

  setTab(tab) { this.tab = tab; this.state.settings.active_tab = tab; this.save(); }

  dayData() {
    this.state.days = this.state.days || {};
    this.state.days[this.day] ||= {desayuno:"", almuerzo:"", cena:"", notas:"", checklist:{}};
    this.state.days[this.day].checklist ||= {};
    return this.state.days[this.day];
  }

  setDayField(field, value) { this.dayData()[field] = value; this.saveDay(); }
  setPlan(id, value) { this.state.plan[id] = value; this.save(); }
  setMenu(day, meal, person, value) { this.state.menu[day][meal][person] = value; this.save(); }
  toggleShop(cat, id) {
    const item = this.state.shopping[cat].find(x => x.id === id);
    if (item) item.checked = !item.checked;
    this.save();
  }

  addProduct() {
    const input = this.shadowRoot.querySelector("#new-product");
    const name = input.value.trim();
    if (!name) return;
    this.state.shopping.extras.push({id:`custom_${Date.now()}`, name, checked:false, source:"custom"});
    input.value = "";
    this.save();
  }

  toggleCheck(key) { const d = this.dayData(); d.checklist[key] = !d.checklist[key]; this.saveDay(); }

  resetToday() {
    const d = this.dayData();
    d.desayuno = d.almuerzo = d.cena = d.notas = ""; d.checklist = {};
    this.saveDay();
  }

  async generateShopping() {
    if (!this._hass || !this._hass.callService) return;
    try { await this._hass.callService(DOMAIN, "generate_shopping"); await this.load(); } catch (_) {}
  }

  score() { if (!this.state) return 0; return CHECKLIST.reduce((n,[k]) => n + (this.dayData().checklist[k] ? 1 : 0), 0); }

  render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>${this.css()}</style>
      <div class="app">
        <header>
          <div><div class="eyebrow">APP DE ALIMENTACIÓN</div><h1>Para papás ocupados</h1><p>Cocina una vez, come bien tú y que tus hijas aprendan de ti.</p></div>
          <div class="score">Hoy <b>${this.score()}/8</b></div>
        </header>
        <nav>${this.nav()}</nav>
        <main>${this.busy ? `<div class="loading">Guardando…</div>` : (this.error ? `<div class="error">${this.error}</div>` : this.content())}</main>
        <footer>“Cocinad y comed juntos, sé el mejor ejemplo que tus hijas pueden ver” — Alfonso</footer>
      </div>`;
    this.bind();
  }

  nav() {
    return [["hoy","📅 Hoy"],["inicio","🏠 Inicio"],["plan","📅 Plan 7 Días"],["menu","🍽️ Menú"],["compra","🛒 Compra"],["checklist","📋 Checklist"]]
      .map(([k,l]) => `<button class="tab ${this.tab===k?"active":""}" data-tab="${k}">${l}</button>`).join("");
  }

  content() {
    switch(this.tab) {
      case "inicio": return this.home();
      case "plan": return this.planPage();
      case "menu": return this.menuPage();
      case "compra": return this.shoppingPage();
      case "checklist": return this.checklistPage();
      default: return this.todayPage();
    }
  }

  todayPage() {
    const d = this.dayData();
    return `<section><h2>¿Qué comemos hoy?</h2><div class="card featured">
      <div class="date-row"><label>Fecha</label><input id="date" type="date" value="${this.day}"></div>
      ${this.area("Desayuno","desayuno",d.desayuno,"Ej: Café, huevos y tostadas")}
      ${this.area("Almuerzo","almuerzo",d.almuerzo,"Ej: Pollo asado y ensalada")}
      ${this.area("Cena","cena",d.cena,"Ej: Sopa de verduras y pan")}
      ${this.area("Notas","notas",d.notas,"Opcional")}
      <div class="actions"><button class="primary" id="reset">Reiniciar este día</button></div>
    </div></section>`;
  }

  area(label, field, value, placeholder) { return `<label>${label}<textarea data-day-field="${field}" placeholder="${placeholder}">${this.escape(value)}</textarea></label>`; }
  escape(v="") { return String(v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

  home() { return `<section><h2>El Método de la Base Única</h2>
    <div class="card featured"><p>Cocinar dos comidas distintas cada día es la forma más rápida de agotarte. <b>Cocinas una sola vez</b>, ahorras tiempo y dinero, y tus hijas ven a papá comer verduras.</p><p><b>Pros:</b> Ahorro de tiempo, mejor ejemplo y menos estrés.<br><b>Contras:</b> Hay que controlar las porciones y adaptar especias o salsas.</p></div>
    <div class="callout"><b>¿Cómo controlar tus porciones?</b><br><b>Papá:</b> mitad verduras, cuarto proteína y cuarto carbohidratos.<br><b>Niñas:</b> mitad carbohidratos, cuarto proteína y cuarto verduras.</div>
    <div class="card"><h3>Las 3 Reglas de Oro</h3><ol><li><b>Separa antes de sazonar:</b> saca la porción de las niñas antes de añadir chile, curry o mucha sal.</li><li><b>“No, pero sí”:</b> no prepares otra comida; pueden comer las partes aceptadas y la verdura permanece en el plato.</li><li><b>“Bocado de adulto”:</b> probar un bocado antes de decidir que no gusta.</li></ol></div>
  </section>`; }

  planPage() { let last=""; let html=`<section><h2>Plan de los 7 Días</h2><p class="muted">Responde poco a poco. Los cambios se guardan automáticamente.</p>`;
    PLAN.forEach(([title,id,label,ph,multi])=>{ if(title!==last){ if(last) html+="</div>"; html+=`<div class="card"><h3>${title}</h3>`; last=title;} html+=`<label>${label}${multi?`<textarea data-plan="${id}" placeholder="${ph}">${this.escape(this.state.plan[id])}</textarea>`:`<input data-plan="${id}" value="${this.escape(this.state.plan[id])}" placeholder="${ph}">`}</label>`; });
    return html+"</div></section>";
  }

  menuPage() { let html=`<section><h2>🍽️ Planificación Semanal</h2><p class="muted">Edita cualquier campo. Papá y Niñas comparten la base, con porciones/adaptaciones diferentes.</p><div class="table-wrap"><table><thead><tr><th>Día</th>${MEALS.map(m=>`<th>${m[1]}</th>`).join("")}</tr></thead><tbody>`;
    DAYS.forEach(([day,label])=>{ html+=`<tr><th>${label}</th>`; MEALS.forEach(([meal])=>{ const v=this.state.menu[day][meal]; html+=`<td><div class="person papa">PAPÁ</div><textarea data-menu="${day}|${meal}|papa">${this.escape(v.papa)}</textarea><div class="person ninas">NIÑAS</div><textarea data-menu="${day}|${meal}|ninas">${this.escape(v.ninas)}</textarea></td>`; }); html+="</tr>"; });
    return html+`</tbody></table></div></section>`;
  }

  shoppingPage() { let html=`<section><div class="head-row"><div><h2>🛒 Lista de la Compra</h2><p class="muted">Marca lo que ya tienes o compras. También puedes añadir productos.</p></div><button class="secondary" id="gen-shop">Generar desde menú</button></div>`;
    SHOPPING.forEach(([cat,label])=>{ html+=`<div class="card"><h3>${label}</h3><ul class="checklist">${(this.state.shopping[cat]||[]).map(item=>`<li><label><input type="checkbox" data-shop="${cat}|${item.id}" ${item.checked?"checked":""}>${this.escape(item.name)}</label></li>`).join("")}</ul></div>`; });
    return html+`<div class="card"><h3>Añadir producto</h3><div class="add-row"><input id="new-product" placeholder="Ej: Leche entera"><button class="primary" id="add-product">Añadir</button></div></div></section>`;
  }

  checklistPage() { const d=this.dayData(); return `<section><div class="head-row"><div><h2>📋 Checklist Diario</h2><p class="muted">El objetivo es que cada día haya más casillas marcadas que el anterior.</p></div><div class="big-score">${this.score()}<span>/8</span></div></div><div class="card featured"><ul class="checklist large">${CHECKLIST.map(([k,t])=>`<li><label><input type="checkbox" data-check="${k}" ${d.checklist[k]?"checked":""}><span>${t}</span></label></li>`).join("")}</ul><div class="actions"><button class="primary" id="reset">Desmarcar y reiniciar hoy</button></div></div></section>`; }

  bind() {
    this.shadowRoot.querySelectorAll("[data-tab]").forEach(el=>el.onclick=()=>{this.tab=el.dataset.tab; this.state.settings.active_tab=this.tab; this.render(); this.save();});
    const date=this.shadowRoot.querySelector("#date"); if(date) date.onchange=()=>{this.day=date.value; this.render();};
    this.shadowRoot.querySelectorAll("[data-day-field]").forEach(el=>el.oninput=()=>{ this.dayData()[el.dataset.dayField]=el.value; clearTimeout(this.t); this.t=setTimeout(()=>this.saveDay(),350); });
    this.shadowRoot.querySelectorAll("[data-plan]").forEach(el=>el.oninput=()=>{this.state.plan[el.dataset.plan]=el.value; clearTimeout(this.t); this.t=setTimeout(()=>this.save(),350);});
    this.shadowRoot.querySelectorAll("[data-menu]").forEach(el=>el.oninput=()=>{const [d,m,p]=el.dataset.menu.split("|");this.state.menu[d][m][p]=el.value;clearTimeout(this.t);this.t=setTimeout(()=>this.save(),350);});
    this.shadowRoot.querySelectorAll("[data-shop]").forEach(el=>el.onchange=()=>{const [cat,id]=el.dataset.shop.split("|");this.toggleShop(cat,id);});
    this.shadowRoot.querySelectorAll("[data-check]").forEach(el=>el.onchange=()=>this.toggleCheck(el.dataset.check));
    const add=this.shadowRoot.querySelector("#add-product"); if(add) add.onclick=()=>this.addProduct();
    const gen=this.shadowRoot.querySelector("#gen-shop"); if(gen) gen.onclick=()=>this.generateShopping();
    const reset=this.shadowRoot.querySelector("#reset"); if(reset) reset.onclick=()=>this.resetToday();
  }

  css(){return `
    :host{display:block;min-height:100vh;background:var(--primary-background-color,#f4f4f4);color:var(--primary-text-color,#333);font-family:var(--paper-font-body1_-_font-family,system-ui,sans-serif)}
    *{box-sizing:border-box} .app{max-width:1200px;margin:0 auto;padding:20px} header{background:var(--card-background-color,#fff);border-radius:20px;padding:28px 30px;display:flex;justify-content:space-between;gap:20px;align-items:center;box-shadow:0 8px 24px rgba(0,0,0,.08)} h1{font-size:clamp(28px,4vw,44px);margin:4px 0}.eyebrow{font-size:12px;font-weight:800;letter-spacing:.14em;color:#e67e22}.score{padding:14px 18px;border:1px solid var(--divider-color,#ddd);border-radius:16px;text-align:center}.score b{display:block;font-size:26px;margin-top:3px} nav{display:flex;flex-wrap:wrap;gap:6px;background:var(--card-background-color,#fff);padding:8px;border-radius:16px;margin:14px 0;box-shadow:0 4px 16px rgba(0,0,0,.06)}.tab{flex:1;min-width:130px;border:0;background:transparent;border-radius:12px;padding:12px;cursor:pointer;color:var(--secondary-text-color,#666);font-weight:700}.tab:hover{background:rgba(230,126,34,.08)}.tab.active{background:#e67e22;color:#fff}main{padding-bottom:20px}h2{color:#e67e22;font-size:28px;margin:12px 0;border-bottom:3px solid #e67e22;padding-bottom:7px}h3{margin-top:0} .card,.callout{background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ddd);border-radius:16px;padding:18px;margin:14px 0}.featured{border:2px solid #3498db}.callout{border-left:6px solid #f1c40f;background:color-mix(in srgb,#f1c40f 8%,var(--card-background-color,#fff))}.muted{color:var(--secondary-text-color,#666)}label{display:block;font-weight:700;margin:12px 0}input,textarea{width:100%;margin-top:6px;padding:11px 12px;border:1px solid var(--divider-color,#ccc);border-radius:10px;background:var(--input-fill-color,#fff);color:inherit;font:inherit}textarea{min-height:70px;resize:vertical}input[type=checkbox]{width:auto;transform:scale(1.2);margin:0 10px 0 0}.date-row{display:flex;align-items:center;gap:12px}.date-row input{max-width:220px}.actions{display:flex;justify-content:flex-end;margin-top:14px}.primary,.secondary{border:0;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer}.primary{background:#e67e22;color:#fff}.secondary{background:var(--secondary-background-color,#eee);color:inherit}.table-wrap{overflow:auto;border:1px solid var(--divider-color,#ddd);border-radius:14px}table{width:100%;min-width:900px;border-collapse:collapse}th,td{border:1px solid var(--divider-color,#ddd);padding:10px;vertical-align:top}thead th{background:#1e2a38;color:#fff}.person{font-size:12px;font-weight:900;margin:2px 0}.papa{color:#2980b9}.ninas{color:#f39c12}.checklist{list-style:none;padding:0;margin:0}.checklist li{border-bottom:1px solid var(--divider-color,#ddd);padding:11px 0}.checklist label{margin:0;display:flex;align-items:flex-start;font-weight:600}.large li{font-size:16px}.add-row{display:flex;gap:10px}.add-row input{margin:0}.head-row{display:flex;justify-content:space-between;gap:20px;align-items:center}.big-score{font-size:42px;font-weight:900}.big-score span{font-size:20px}.loading,.error{text-align:center;padding:60px}.error{color:#c0392b}footer{text-align:center;padding:24px;color:var(--secondary-text-color,#666);font-style:italic}
    @media(max-width:700px){.app{padding:10px}header{padding:20px;align-items:flex-start}.score{min-width:90px}.tab{min-width:110px}.date-row,.add-row,.head-row{flex-direction:column;align-items:stretch}.date-row input{max-width:none}.big-score{align-self:flex-end} }
  `}
}

customElements.define("app-papas-panel", AppPapasPanel);
