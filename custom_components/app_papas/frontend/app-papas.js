const DOMAIN = "app_papas";
const API = `/api/${DOMAIN}`;

const DAYS = [
  ["lunes", "Lunes"], ["martes", "Martes"], ["miercoles", "Miércoles"],
  ["jueves", "Jueves"], ["viernes", "Viernes"], ["sabado", "Sábado"], ["domingo", "Domingo"]
];
const MEALS = [["desayuno", "Desayuno", "🍳"], ["almuerzo", "Almuerzo", "🍲"], ["cena", "Cena", "🌙"]];
const SHOPPING = [["proteina", "Proteína", "🥩"], ["carbohidratos", "Carbohidratos", "🍚"], ["verduras_frutas", "Verduras / Frutas", "🥦"], ["extras", "Extras", "🧂"]];
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
const PLAN = [
  ["Día 1", "Encuentra tu Punto Débil", "d1_problema", "Mi mayor problema es", "Ej: Me derrumbo por la noche...", false],
  ["Día 1", "Encuentra tu Punto Débil", "d1_cuando", "¿Cuándo suelo desmoronarme?", "Ej: 10:30 pm, en la oficina...", false],
  ["Día 2", "La Regla de la Palma", "d2_proteinas", "Mis 3 proteínas rápidas favoritas", "Ej: Huevos, Atún, Yogur Griego", false],
  ["Día 3", "El Interruptor de Líquidos", "d3_bebida", "¿Qué bebida azucarada voy a sustituir esta semana?", "Ej: Refresco de cola por agua con limón", false],
  ["Día 4", "Cocina Fantasma", "d4_rapida1", "Mi Comida Rápida 1 (Papá / Niñas)", "Ej: Revuelto de 3 huevos + arroz / Revuelto con jamón y queso", true],
  ["Día 4", "Cocina Fantasma", "d4_rapida2", "Mi Comida Rápida 2 (Papá / Niñas)", "Ej: Atún con frijoles y aguacate / Atún con maíz en sándwich", true],
  ["Día 4", "Cocina Fantasma", "d4_rapida3", "Mi Comida Rápida 3 (Papá / Niñas)", "Ej: Huevos duros + yogurt / Tostada con aguacate", true],
  ["Día 5", "Antirrestaurante", "d5_pedido", "Mi pedido saludable de comida rápida favorito", "Ej: Dos tacos de carne y agua, sin refresco", false],
  ["Día 6", "Protocolo de Reinicio", "d6_reinicio", "¿Qué haré si me salgo del camino?", "Ej: Beber agua, respirar hondo y decidir mi próxima comida sana", false],
  ["Día 7", "Tablero de Operaciones", "d7_problema", "Mi problema principal detectado", "Ej: Comer en la cama a medianoche", false],
  ["Día 7", "Tablero de Operaciones", "d7_bebida", "Mi bebida de emergencia (para no beber calorías)", "Ej: Agua con limón", false]
];

function localDate() {
  const d = new Date();
  const off = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - off).toISOString().slice(0, 10);
}
function escapeHtml(v="") { return String(v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;"); }
function dayLabel(key) { return DAYS.find(x => x[0] === key)?.[1] || key; }
function weekdayKey(value) { const idx = new Date(`${value}T12:00:00`).getDay(); return DAYS[(idx + 6) % 7][0]; }

class AppPapasPanel extends HTMLElement {
  set hass(value) { this._hass = value; }

  connectedCallback() {
    if (this.shadowRoot) return;
    this.attachShadow({mode:"open"});
    this.state = this.initialState();
    this.stats = {today_score:0, streak:0, shopping_pending:0, history:[]};
    this.day = localDate();
    this.tab = "inicio";
    this.busy = true;
    this.error = "";
    this.render();
    this.load();
  }

  initialState() {
    return {
      schema_version: 2,
      settings: {active_tab:"inicio", adult_name:"Papá", children:["Niñas"], notifications_enabled:false, notify_service:""},
      plan: Object.fromEntries(PLAN.map(x => [x[2], ""])),
      days: {},
      menu: Object.fromEntries(DAYS.map(([d]) => [d, Object.fromEntries(MEALS.map(([m]) => [m,{papa:"",ninas:""}]))])),
      shopping: Object.fromEntries(SHOPPING.map(([c]) => [c, []])),
      emergency_meals: []
    };
  }

  async load() {
    try {
      if (!this._hass || typeof this._hass.fetchWithAuth !== "function") throw new Error("Esperando la sesión de Home Assistant…");
      const [dataRes, statsRes] = await Promise.all([
        this._hass.fetchWithAuth(`${API}/data`),
        this._hass.fetchWithAuth(`${API}/stats`)
      ]);
      if (!dataRes.ok) throw new Error(`No se pudieron cargar los datos (${dataRes.status})`);
      this.state = this.mergeState(this.initialState(), await dataRes.json());
      if (statsRes.ok) this.stats = await statsRes.json();
      this.tab = this.state.settings.active_tab || "inicio";
      this.busy = false;
      this.error = "";
      this.render();
    } catch (e) {
      this.busy = false;
      this.error = e.message || "No se pudo conectar con Home Assistant.";
      this.render();
    }
  }

  mergeState(base, src) {
    src = src || {};
    const out = {...base, ...src};
    out.settings = {...base.settings, ...(src.settings || {})};
    out.plan = {...base.plan, ...(src.plan || {})};
    out.days = {...base.days, ...(src.days || {})};
    out.menu = {...base.menu};
    for (const [d, meals] of Object.entries(src.menu || {})) {
      out.menu[d] = {...(base.menu[d] || {}), ...(meals || {})};
      for (const [m, v] of Object.entries(meals || {})) out.menu[d][m] = {papa:"",ninas:"",...(base.menu[d]?.[m] || {}),...(v || {})};
    }
    out.shopping = {...base.shopping};
    for (const [c] of SHOPPING) out.shopping[c] = Array.isArray(src.shopping?.[c]) ? src.shopping[c] : base.shopping[c];
    out.emergency_meals = Array.isArray(src.emergency_meals) ? src.emergency_meals : [];
    return out;
  }

  async saveData() {
    if (this._saveInFlight) { this._savePending = true; return; }
    this._saveInFlight = true;
    try {
      const res = await this._hass.fetchWithAuth(`${API}/data`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(this.state)});
      if (!res.ok) throw new Error(`Error guardando datos (${res.status})`);
      this.state = this.mergeState(this.initialState(), await res.json());
      this.error = "";
    } catch (e) { this.error = e.message || "No se pudieron guardar los datos."; this.showToast(this.error, true); }
    finally { this._saveInFlight = false; if (this._savePending) { this._savePending = false; this.saveData(); } }
  }

  scheduleDataSave() { clearTimeout(this._dataTimer); this._dataTimer=setTimeout(()=>this.saveData(),600); }

  async saveDay() {
    if (this._dayInFlight) { this._dayPending=true; return; }
    this._dayInFlight=true;
    try {
      const res = await this._hass.fetchWithAuth(`${API}/day/${this.day}`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(this.state.days[this.day] || this.emptyDay())});
      if (!res.ok) throw new Error(`Error guardando el día (${res.status})`);
      this.state.days[this.day] = await res.json();
      this.error="";
      await this.refreshStats(false);
    } catch(e) { this.error=e.message || "No se pudo guardar el día."; this.showToast(this.error,true); }
    finally { this._dayInFlight=false; if(this._dayPending){this._dayPending=false;this.saveDay();} }
  }
  scheduleDaySave(){clearTimeout(this._dayTimer);this._dayTimer=setTimeout(()=>this.saveDay(),550);}

  async refreshStats(renderAfter=true) {
    try { const r=await this._hass.fetchWithAuth(`${API}/stats`); if(r.ok) this.stats=await r.json(); }
    catch(_) {}
    if(renderAfter) this.render();
  }
  emptyDay(){return {desayuno:"",almuerzo:"",cena:"",notas:"",checklist:{}};}
  dayData(){if(!this.state.days[this.day])this.state.days[this.day]=this.emptyDay();this.state.days[this.day].checklist ||= {};return this.state.days[this.day];}
  score(){return CHECKLIST.reduce((n,[k])=>n+(this.dayData().checklist[k]?1:0),0);}
  pendingShopping(){return SHOPPING.reduce((n,[c])=>n+(this.state.shopping[c]||[]).filter(x=>!x.checked).length,0);}

  async callService(service, data={}) { if (!this._hass?.callService) return; await this._hass.callService(DOMAIN, service, data); await this.load(); }

  async resetToday(){this.state.days[this.day]=this.emptyDay();await this.saveDay();this.render();}
  async copyWeek(){await this.callService("copy_week",{source_offset:7});}
  async generateShopping(){await this.callService("generate_shopping",{});}
  async completeChecklist(){const d=this.dayData();d.checklist=Object.fromEntries(CHECKLIST.map(x=>[x[0],true]));await this.saveDay();this.render();}
  async notifyToday(){try{await this.callService("notify_today",{});this.showToast("Resumen enviado.");}catch(e){this.showToast(e.message||"No se pudo enviar.",true);}}

  setTab(tab){this.tab=tab;this.state.settings.active_tab=tab;this.render();this.scheduleDataSave();}

  addProduct(){const input=this.shadowRoot.querySelector("#new-product");const cat=this.shadowRoot.querySelector("#new-category")?.value||"extras";const name=input?.value.trim();if(!name)return;this.state.shopping[cat].push({id:`manual_${Date.now()}`,name,checked:false,source:"manual"});input.value="";this.render();this.scheduleDataSave();}
  removeProduct(cat,id){this.state.shopping[cat]=(this.state.shopping[cat]||[]).filter(x=>x.id!==id);this.render();this.scheduleDataSave();}
  toggleShop(cat,id,checked){const item=(this.state.shopping[cat]||[]).find(x=>x.id===id);if(item){item.checked=checked;this.render();this.scheduleDataSave();}}
  toggleCheck(key,checked){this.dayData().checklist[key]=checked;this.render();this.scheduleDaySave();}
  setDayField(field,value){this.dayData()[field]=value;this.scheduleDaySave();}
  setPlan(id,value){this.state.plan[id]=value;this.scheduleDataSave();}
  setMenu(d,m,p,value){this.state.menu[d][m][p]=value;this.scheduleDataSave();}
  setDay(v){if(!v)return;this.day=v;this.render();}

  async useEmergency(text){const parts=text.split("/").map(x=>x.trim());const d=this.dayData();d.almuerzo=parts.length>1?`Papá: ${parts[0]} | Niñas: ${parts.slice(1).join(" / ")}`:text;await this.saveDay();this.setTab("hoy");}

  render(){
    if(!this.shadowRoot)return;
    this.shadowRoot.innerHTML=`<style>${this.css()}</style><div class="app ${this.state.settings.theme==='dark'?'dark':''}">
      <header><div><div class="eyebrow">APP DE ALIMENTACIÓN</div><h1>Para papás ocupados</h1><p>Cocina una vez, come bien tú y que tus hijas aprendan de ti.</p></div><div class="header-actions"><div class="score">Hoy <b>${this.score()}/8</b></div><button class="icon-btn" id="theme">${this.state.settings.theme==='dark'?"☀️":"🌙"}</button></div></header>
      <nav>${this.nav()}</nav><main>${this.busy?`<div class="loading">Cargando…</div>`:this.error?`<div class="error"><b>No se pudo cargar la aplicación.</b><div>${escapeHtml(this.error)}</div><button class="primary" id="retry">Reintentar</button></div>`:this.content()}</main>
      <footer>“Cocinad y comed juntos, sé el mejor ejemplo que tus hijas pueden ver” — Alfonso</footer><div id="toast" class="toast"></div></div>`;
    this.bind();
  }

  nav(){return [["inicio","🏠 Inicio"],["hoy","📅 Hoy"],["menu","🍽️ Menú"],["compra","🛒 Compra"],["checklist","📋 Progreso"],["plan","🧭 Plan 7 días"]].map(([k,l])=>`<button class="tab ${this.tab===k?"active":""}" data-tab="${k}">${l}</button>`).join("");}

  content(){switch(this.tab){case"hoy":return this.todayPage();case"menu":return this.menuPage();case"compra":return this.shoppingPage();case"checklist":return this.progressPage();case"plan":return this.planPage();default:return this.homePage();}}

  homePage(){const today=this.dayData();const registered=MEALS.filter(([m])=>Boolean((today[m]||"").trim())).length;const wk=weekdayKey(this.day);const next=this.state.menu[wk]||{};const pending=this.pendingShopping();const history=this.stats.history||[];return `<section>
    <div class="hero"><div><span class="pill">${dayLabel(wk)} · ${this.day}</span><h2>Tu centro de operaciones</h2><p class="muted">Menú, comida real, compra y progreso en un solo sitio.</p></div><div class="hero-score"><span>${this.score()}/8</span><small>objetivos de hoy</small></div></div>
    <div class="grid four"><button class="metric" data-tab="hoy"><span>🍽️</span><strong>${registered}</strong><small>comidas registradas</small></button><button class="metric" data-tab="compra"><span>🛒</span><strong>${pending}</strong><small>productos pendientes</small></button><div class="metric"><span>🔥</span><strong>${this.stats.streak||0}</strong><small>días de racha</small></div><div class="metric"><span>📈</span><strong>${this.avg7()}</strong><small>media últimos 7</small></div></div>
    <div class="grid two"><div class="card"><div class="card-title"><h3>🍴 Hoy en el menú</h3><button class="link-btn" data-tab="menu">Editar menú</button></div>${MEALS.map(([m,label,icon])=>`<div class="meal-row"><span class="meal-icon">${icon}</span><div><b>${label}</b><div class="meal-text">${escapeHtml(next[m]?.papa||"Sin planificar")}</div><small>Niñas: ${escapeHtml(next[m]?.ninas||"Sin adaptar")}</small></div></div>`).join("")}</div>
      <div class="card"><div class="card-title"><h3>✅ Últimos 7 días</h3><button class="link-btn" data-tab="checklist">Ver progreso</button></div><div class="history">${(history.slice(-7)||[]).map(x=>`<div><span>${escapeHtml(x.date.slice(5))}</span><div class="bar"><i style="width:${(x.score/8)*100}%"></i></div><b>${x.score}/8</b></div>`).join("")}</div></div></div>
    <div class="grid two"><div class="card"><h3>🚨 Comidas de emergencia</h3><p class="muted">Para esos días en los que no hay tiempo.</p>${this.emergencyList(3)}</div><div class="card"><h3>🛒 Acciones rápidas</h3><div class="action-grid"><button class="primary" id="gen-shop">Generar compra</button><button class="secondary" id="copy-week">Copiar semana</button><button class="secondary" id="complete-check">Completar checklist</button>${this.state.settings.notify_service?`<button class="secondary" id="notify">Enviar resumen</button>`:""}</div><p class="muted small">${this.state.settings.adult_name||"Papá"} · ${(this.state.settings.children||["Niñas"]).join(", ")}</p></div></div>
  </section>`;}

  avg7(){const h=(this.stats.history||[]).slice(-7);if(!h.length)return "0/8";return `${(h.reduce((n,x)=>n+x.score,0)/h.length).toFixed(1)}/8`;}
  emergencyList(limit){const entries=["d4_rapida1","d4_rapida2","d4_rapida3"].map(k=>this.state.plan[k]).filter(Boolean).slice(0,limit);if(!entries.length)return `<div class="empty">Aún no has definido comidas de emergencia en el Plan 7 días.</div>`;return entries.map((x,i)=>`<div class="emergency"><b>⚡ Opción ${i+1}</b><span>${escapeHtml(x)}</span><button class="link-btn" data-emergency="${escapeHtml(x)}">Usar hoy</button></div>`).join("");}

  todayPage(){const d=this.dayData();return `<section><div class="head-row"><div><h2>📅 ¿Qué comemos hoy?</h2><p class="muted">Registra lo que realmente has comido. Se guarda automáticamente.</p></div><div class="date-row"><label>Fecha</label><input id="date" type="date" value="${this.day}"></div></div>
    <div class="grid two"><div class="card featured"><div class="card-title"><h3>Plan del día</h3><button class="link-btn" data-tab="menu">Editar menú</button></div>${MEALS.map(([m,label,icon])=>{const wk=weekdayKey(this.day);const v=this.state.menu[wk]?.[m]||{};return `<div class="planned"><span>${icon}</span><div><b>${label}</b><p>${escapeHtml(v.papa||"Sin planificar")}</p><small>Niñas: ${escapeHtml(v.ninas||"Sin adaptar")}</small></div></div>`}).join("")}</div>
    <div class="card"><h3>📝 Lo que realmente comí</h3>${this.area("Desayuno","desayuno",d.desayuno,"Café, huevos y tostadas…")}${this.area("Almuerzo","almuerzo",d.almuerzo,"Pollo asado y ensalada…")}${this.area("Cena","cena",d.cena,"Sopa de verduras y pan…")}${this.area("Notas","notas",d.notas,"Opcional…")}</div></div>
    <div class="card"><div class="card-title"><h3>🚨 Una salida rápida</h3><button class="link-btn" data-tab="plan">Editar emergencias</button></div><div class="emergency-grid">${this.emergencyList(3)}</div></div>
    <div class="actions"><button class="secondary" id="reset-day">Reiniciar día</button></div></section>`;}
  area(label,field,value,ph){return `<label>${label}<textarea data-day-field="${field}" placeholder="${escapeHtml(ph)}">${escapeHtml(value)}</textarea></label>`;}

  menuPage(){let html=`<section><div class="head-row"><div><h2>🍽️ Menú semanal</h2><p class="muted">Una sola base para todos, con adaptación para ${escapeHtml((this.state.settings.children||["Niñas"]).join(", "))}.</p></div><div class="action-row"><button class="secondary" id="copy-week">Copiar semana anterior</button><button class="secondary" id="gen-shop">Generar compra</button></div></div><div class="table-wrap"><table><thead><tr><th>Día</th>${MEALS.map(m=>`<th>${m[2]} ${m[1]}</th>`).join("")}</tr></thead><tbody>`;
    DAYS.forEach(([d,label])=>{html+=`<tr><th>${label}</th>`;MEALS.forEach(([m])=>{const v=this.state.menu[d]?.[m]||{papa:"",ninas:""};html+=`<td><div class="person papa">${escapeHtml(this.state.settings.adult_name||"PAPÁ")}</div><textarea data-menu="${d}|${m}|papa">${escapeHtml(v.papa)}</textarea><div class="person ninas">${escapeHtml((this.state.settings.children||["Niñas"]).join(" / "))}</div><textarea data-menu="${d}|${m}|ninas">${escapeHtml(v.ninas)}</textarea></td>`});html+=`</tr>`});
    return html+`</tbody></table></div><div class="tip">💡 Los cambios se guardan automáticamente. Puedes deslizar horizontalmente en móvil.</div></section>`;}

  shoppingPage(){let total=this.pendingShopping();let html=`<section><div class="head-row"><div><h2>🛒 Lista de la compra</h2><p class="muted">${total} productos pendientes. Los productos generados desde el menú se mantienen separados de los personalizados.</p></div><div class="action-row"><button class="primary" id="gen-shop">Generar desde menú</button></div></div>`;
    SHOPPING.forEach(([cat,label,icon])=>{const items=this.state.shopping[cat]||[];html+=`<div class="card"><div class="card-title"><h3>${icon} ${label}</h3><span class="badge">${items.filter(x=>!x.checked).length} pendientes</span></div><ul class="shopping-list">${items.map(item=>`<li><label><input type="checkbox" data-shop="${cat}|${item.id}" ${item.checked?"checked":""}><span class="${item.checked?"done":""}">${escapeHtml(item.name)}</span></label>${["manual","custom"].includes(item.source)?`<button class="delete" data-remove="${cat}|${item.id}" title="Eliminar">✕</button>`:""}</li>`).join("")}</ul>${!items.length?`<div class="empty">Sin productos.</div>`:""}</div>`});
    return html+`<div class="card"><h3>➕ Añadir producto</h3><div class="add-row"><input id="new-product" placeholder="Ej: Leche entera"><select id="new-category">${SHOPPING.map(([k,l])=>`<option value="${k}">${l}</option>`).join("")}</select><button class="primary" id="add-product">Añadir</button></div></div></section>`;}

  progressPage(){const d=this.dayData();return `<section><div class="hero"><div><h2>📋 Progreso</h2><p class="muted">No necesitas hacerlo perfecto: busca mejorar poco a poco.</p></div><div class="hero-score"><span>${this.score()}/8</span><small>hoy</small></div></div><div class="grid three"><div class="metric"><span>🔥</span><strong>${this.stats.streak||0}</strong><small>racha</small></div><div class="metric"><span>📊</span><strong>${this.avg7()}</strong><small>media 7 días</small></div><div class="metric"><span>🛒</span><strong>${this.stats.shopping_pending??this.pendingShopping()}</strong><small>compra pendiente</small></div></div><div class="card featured"><ul class="checklist large">${CHECKLIST.map(([k,t])=>`<li><label><input type="checkbox" data-check="${k}" ${d.checklist[k]?"checked":""}><span>${t}</span></label></li>`).join("")}</ul><div class="actions"><button class="secondary" id="complete-check">Marcar todo</button><button class="primary" id="reset-day">Reiniciar hoy</button></div></div><div class="card"><h3>📈 Histórico de 14 días</h3><div class="history big">${(this.stats.history||[]).map(x=>`<div><span>${escapeHtml(x.date)}</span><div class="bar"><i style="width:${x.score*12.5}%"></i></div><b>${x.score}/8</b></div>`).join("")}</div></div></section>`;}

  planPage(){let last="";let html=`<section><h2>🧭 Plan de los 7 días</h2><p class="muted">Construye tu propio sistema. Lo que escribas queda guardado.</p>`;PLAN.forEach(([day,title,id,label,ph,multi])=>{if(title!==last){if(last)html+="</div>";html+=`<div class="card"><div class="section-kicker">${day}</div><h3>${title}</h3>`;last=title;}html+=`<label>${label}${multi?`<textarea data-plan="${id}" placeholder="${escapeHtml(ph)}">${escapeHtml(this.state.plan[id])}</textarea>`:`<input data-plan="${id}" value="${escapeHtml(this.state.plan[id])}" placeholder="${escapeHtml(ph)}">`}</label>`});return html+`</div><div class="card callout"><h3>🚨 Tus comidas de emergencia</h3>${this.emergencyList(3)}</div></section>`;}

  bind(){
    this.shadowRoot.querySelectorAll("[data-tab]").forEach(el=>el.onclick=()=>this.setTab(el.dataset.tab));
    const retry=this.shadowRoot.querySelector("#retry");if(retry)retry.onclick=()=>{this.error="";this.busy=true;this.render();this.load();};
    const theme=this.shadowRoot.querySelector("#theme");if(theme)theme.onclick=()=>{this.state.settings.theme=this.state.settings.theme==='dark'?'light':'dark';this.scheduleDataSave();this.render();};
    const date=this.shadowRoot.querySelector("#date");if(date)date.onchange=()=>this.setDay(date.value);
    this.shadowRoot.querySelectorAll("[data-day-field]").forEach(el=>el.oninput=()=>this.setDayField(el.dataset.dayField,el.value));
    this.shadowRoot.querySelectorAll("[data-plan]").forEach(el=>el.oninput=()=>this.setPlan(el.dataset.plan,el.value));
    this.shadowRoot.querySelectorAll("[data-menu]").forEach(el=>el.oninput=()=>{const [d,m,p]=el.dataset.menu.split("|");this.setMenu(d,m,p,el.value);});
    this.shadowRoot.querySelectorAll("[data-shop]").forEach(el=>el.onchange=()=>{const [c,id]=el.dataset.shop.split("|");this.toggleShop(c,id,el.checked);});
    this.shadowRoot.querySelectorAll("[data-check]").forEach(el=>el.onchange=()=>this.toggleCheck(el.dataset.check,el.checked));
    this.shadowRoot.querySelectorAll("[data-remove]").forEach(el=>el.onclick=()=>{const [c,id]=el.dataset.remove.split("|");this.removeProduct(c,id);});
    const add=this.shadowRoot.querySelector("#add-product");if(add)add.onclick=()=>this.addProduct();
    this.shadowRoot.querySelectorAll("#gen-shop").forEach(el=>el.onclick=()=>this.generateShopping());
    this.shadowRoot.querySelectorAll("#copy-week").forEach(el=>el.onclick=()=>this.copyWeek());
    this.shadowRoot.querySelectorAll("#complete-check").forEach(el=>el.onclick=()=>this.completeChecklist());
    this.shadowRoot.querySelectorAll("#reset-day").forEach(el=>el.onclick=()=>this.resetToday());
    const notify=this.shadowRoot.querySelector("#notify");if(notify)notify.onclick=()=>this.notifyToday();
    this.shadowRoot.querySelectorAll("[data-emergency]").forEach(el=>el.onclick=()=>this.useEmergency(el.getAttribute("data-emergency")));
  }

  showToast(message,error=false){const t=this.shadowRoot?.querySelector("#toast");if(!t)return;t.textContent=message;t.className=`toast show ${error?"danger":""}`;clearTimeout(this._toastTimer);this._toastTimer=setTimeout(()=>t.className="toast",3000);}

  css(){return `
  :host{display:block;min-height:100vh;background:var(--primary-background-color,#f4f4f4);color:var(--primary-text-color,#222);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.app{max-width:1240px;margin:auto;padding:18px} .app.dark{background:#151515;color:#eee;min-height:100vh;border-radius:22px}.app.dark .card,.app.dark header,.app.dark nav,.app.dark .metric,.app.dark .hero-score{background:#222;border-color:#444}.app.dark input,.app.dark textarea,.app.dark select{background:#2d2d2d;color:#eee;border-color:#555}.app.dark .bar{background:#444}.app.dark .secondary{background:#333;color:#eee}*{box-sizing:border-box}header{display:flex;justify-content:space-between;align-items:center;gap:20px;background:var(--card-background-color,#fff);padding:24px 28px;border-radius:22px;box-shadow:0 6px 24px rgba(0,0,0,.07)}.eyebrow,.section-kicker{font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;color:#e67e22}h1{font-size:clamp(28px,4vw,44px);margin:4px 0}header p{margin:0;color:var(--secondary-text-color,#666)}.header-actions{display:flex;align-items:center;gap:10px}.score{border:1px solid var(--divider-color,#ddd);padding:10px 16px;border-radius:14px;text-align:center}.score b{display:block;font-size:24px}.icon-btn{border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);border-radius:50%;width:42px;height:42px;cursor:pointer;font-size:18px}nav{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0;background:var(--card-background-color,#fff);padding:8px;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.05)}.tab{flex:1;min-width:120px;padding:12px;border:0;border-radius:11px;background:transparent;font-weight:800;color:var(--secondary-text-color,#666);cursor:pointer}.tab.active{background:#e67e22;color:#fff}.tab:hover{background:rgba(230,126,34,.1)}main{padding-bottom:20px}h2{color:#e67e22;font-size:30px;margin:10px 0;border-bottom:3px solid #e67e22;padding-bottom:6px}h3{margin:0 0 8px}.muted{color:var(--secondary-text-color,#666)}.small{font-size:12px}.hero{display:flex;justify-content:space-between;gap:20px;align-items:center;background:linear-gradient(135deg,var(--card-background-color,#fff),rgba(230,126,34,.08));padding:24px;border-radius:20px;border:1px solid var(--divider-color,#ddd)}.pill,.badge{display:inline-block;border-radius:999px;padding:5px 9px;background:rgba(230,126,34,.12);color:#b85d0d;font-size:12px;font-weight:800}.hero-score{border-radius:18px;padding:16px 20px;background:var(--card-background-color,#fff);text-align:center;border:1px solid var(--divider-color,#ddd)}.hero-score span{display:block;font-size:38px;font-weight:900}.hero-score small{color:var(--secondary-text-color,#666)}.grid{display:grid;gap:14px;margin:14px 0}.grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.grid.four{grid-template-columns:repeat(4,minmax(0,1fr))}.metric{border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);border-radius:16px;padding:15px;text-align:left;cursor:pointer}.metric span{font-size:24px}.metric strong{display:block;font-size:27px;margin:3px 0}.metric small{color:var(--secondary-text-color,#666)}.metric:hover{transform:translateY(-1px)}.card{background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ddd);border-radius:18px;padding:18px}.featured{border:2px solid #3498db}.callout{border-left:6px solid #f1c40f}.card-title,.head-row{display:flex;justify-content:space-between;gap:14px;align-items:center}.link-btn{border:0;background:none;color:#c45f0f;font-weight:800;cursor:pointer}.meal-row,.planned{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--divider-color,#ddd)}.meal-row:last-child,.planned:last-child{border-bottom:0}.meal-icon{font-size:24px}.meal-text{font-weight:700;margin-top:3px}.meal-row small,.planned small{color:var(--secondary-text-color,#666)}.history>div{display:grid;grid-template-columns:55px 1fr 40px;gap:8px;align-items:center;margin:9px 0}.bar{height:9px;background:var(--secondary-background-color,#eee);border-radius:999px;overflow:hidden}.bar i{display:block;height:100%;background:#e67e22;border-radius:999px}.emergency{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid var(--divider-color,#ddd)}.emergency:last-child{border-bottom:0}.emergency span{color:var(--secondary-text-color,#666)}.action-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.primary,.secondary{border:0;padding:10px 15px;border-radius:11px;font-weight:800;cursor:pointer}.primary{background:#e67e22;color:#fff}.secondary{background:var(--secondary-background-color,#eee);color:inherit}.action-row{display:flex;gap:8px;flex-wrap:wrap}.date-row{display:flex;gap:8px;align-items:center}.date-row input{width:auto}.card label{display:block;font-weight:800;margin:11px 0}.card input[type=text],.card input[type=date],.card textarea,.card select{width:100%;padding:10px 12px;border:1px solid var(--divider-color,#ccc);background:var(--input-fill-color,#fff);color:inherit;border-radius:10px;font:inherit;margin-top:5px}.card textarea{min-height:72px;resize:vertical}.table-wrap{overflow:auto;border:1px solid var(--divider-color,#ddd);border-radius:14px}table{width:100%;min-width:960px;border-collapse:collapse}th,td{border:1px solid var(--divider-color,#ddd);padding:9px;vertical-align:top}thead th{background:#1e2a38;color:#fff}.person{font-size:11px;font-weight:900;margin:4px 0}.papa{color:#2980b9}.ninas{color:#f39c12}.tip{padding:12px;color:var(--secondary-text-color,#666);font-size:12px}.shopping-list,.checklist{list-style:none;padding:0;margin:0}.shopping-list li{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid var(--divider-color,#ddd)}.shopping-list label,.checklist label{display:flex;align-items:flex-start;gap:8px;margin:0;font-weight:600}.shopping-list input,.checklist input{width:auto;margin-top:2px}.done{text-decoration:line-through;opacity:.55}.delete{border:0;background:none;color:#c0392b;cursor:pointer}.checklist.large li{padding:13px 0;border-bottom:1px solid var(--divider-color,#ddd)}.add-row{display:grid;grid-template-columns:1fr 180px auto;gap:10px}.add-row input,.add-row select{margin-top:0}.actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}.empty{padding:16px;border:1px dashed var(--divider-color,#ccc);border-radius:12px;color:var(--secondary-text-color,#666)}.loading,.error{text-align:center;padding:70px 20px}.error{color:#c0392b}.toast{position:fixed;right:24px;bottom:24px;opacity:0;pointer-events:none;background:#333;color:#fff;padding:12px 16px;border-radius:10px;transform:translateY(10px);transition:.2s}.toast.show{opacity:1;transform:none}.toast.danger{background:#c0392b}footer{text-align:center;padding:22px;color:var(--secondary-text-color,#666);font-style:italic}.emergency-grid{display:grid;gap:8px}@media(max-width:900px){.grid.two,.grid.three,.grid.four{grid-template-columns:1fr 1fr}.hero{align-items:flex-start}.add-row{grid-template-columns:1fr}.date-row{align-items:stretch}.date-row input{width:100%}}@media(max-width:650px){.app{padding:10px}header{align-items:flex-start;padding:20px}.score{display:none}.grid.two,.grid.three,.grid.four{grid-template-columns:1fr}.hero{flex-direction:column}.tab{min-width:100px}.action-grid{grid-template-columns:1fr}.emergency{grid-template-columns:1fr}.head-row{align-items:stretch;flex-direction:column}.date-row{flex-direction:column;align-items:stretch}.history>div{grid-template-columns:48px 1fr 34px}}
  `;}
}

customElements.define("app-papas-panel", AppPapasPanel);
