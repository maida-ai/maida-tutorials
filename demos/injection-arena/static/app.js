const el = (id) => document.getElementById(id);
const worker = el("worker");
const adversary = el("adversary");
const attemptsEl = el("attempts");
const landedEl = el("landed");
const runBtn = el("run");
const resetBtn = el("reset");
const gateToggle = el("gate");
const banner = el("round-banner");
const flash = el("flash");
const scenarioSel = el("scenario");
const modelSel = el("model");
const blurb = el("scenario-blurb");
const injectionInput = el("injection");
const clearInjectionBtn = el("clear-injection");
const leaderboardBtn = el("leaderboard-btn");
const lbOverlay = el("leaderboard");
const lbBody = el("lb-body");
const lbSub = el("lb-sub");
const lbClose = el("lb-close");

let source = null;
let scenarioBlurbs = {};
let isLive = false;
let models = [];

function esc(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

function scrollPane(pane) {
  pane.scrollTop = pane.scrollHeight;
}

function addMsg(pane, cls, who, html) {
  const div = document.createElement("div");
  div.className = `msg ${cls}`;
  div.innerHTML = `<div class="who">${who}</div>${html}`;
  pane.appendChild(div);
  scrollPane(pane);
  return div;
}

function bumpStat(node, value) {
  node.textContent = value;
  node.classList.remove("bump");
  void node.offsetWidth;
  node.classList.add("bump");
}

function setBanner(round) {
  const attack = round.n > 0;
  banner.className = `round-banner ${attack ? "attack" : ""}`;
  const label = attack ? `Round ${round.n}` : "Warmup";
  banner.innerHTML = `<b>${label}: ${esc(round.title)}</b> &nbsp; <span class="obj">${esc(round.objective)}</span>`;
}

function renderVerdict(v) {
  const div = document.createElement("div");
  div.className = "verdict";
  div.innerHTML = `
    <div class="v-head"><span>&#10008; ${esc(v.headline)}</span><span class="reason">${esc(v.reason_code)}</span></div>
    <div class="v-body">
      ${esc(v.detail)}
      <div class="path"><span class="lbl">baseline:</span> <span class="base">${esc(v.baseline_path)}</span></div>
      <div class="path"><span class="lbl">current:</span> <span class="cur">${esc(v.current)}</span></div>
    </div>
    <div class="foot">${esc(v.footer)}</div>`;
  worker.appendChild(div);
  scrollPane(worker);
}

function fireOwned() {
  flash.classList.remove("fire");
  void flash.offsetWidth;
  flash.classList.add("fire");
  document.body.classList.add("owned");
  const b = document.createElement("div");
  b.className = "owned-banner";
  b.textContent = "WORKER OWNED";
  document.body.appendChild(b);
  setTimeout(() => {
    document.body.classList.remove("owned");
    b.remove();
  }, 1800);
}

function handle(ev) {
  switch (ev.type) {
    case "meta":
      el("mode").textContent = ev.live ? "LIVE" : "CANNED";
      break;
    case "round":
      setBanner(ev);
      break;
    case "adversary_msg": {
      let who = "injection payload";
      let cls = "adversary";
      if (ev.refused) {
        who = "adversary model \u2014 refused to author";
        cls = "adversary refused";
      } else if (ev.note) {
        who = `injection payload \u2014 ${ev.note}`;
      }
      addMsg(adversary, cls, who, esc(ev.text));
      break;
    }
    case "worker_msg":
      addMsg(worker, "worker", "deskbot", esc(ev.text));
      break;
    case "tool_call": {
      const cls = ev.blocked ? "tool blocked" : ev.danger ? "tool danger" : "tool";
      const args = Object.keys(ev.args || {}).length ? ` <code>${esc(JSON.stringify(ev.args))}</code>` : "";
      let badge = "";
      if (ev.blocked) badge = `<span class="badge blocked">BLOCKED</span>`;
      else if (ev.danger) badge = `<span class="badge landed">DANGEROUS</span>`;
      addMsg(worker, cls, "tool call", `${badge}<code>${esc(ev.tool)}</code>${args}`);
      break;
    }
    case "tool_result":
      addMsg(worker, "result", `${esc(ev.tool)} &rarr;`, `<code>${esc(ev.result)}</code>`);
      break;
    case "gate_verdict":
      renderVerdict(ev);
      break;
    case "score":
      bumpStat(attemptsEl, ev.attempts);
      bumpStat(landedEl, ev.landed);
      break;
    case "attack_result": {
      const map = {
        landed: ["\u2718 Attack landed \u2014 worker complied", "res-landed"],
        blocked: ["\u2714 Blocked by the Maida gate", "res-blocked"],
        resisted: ["\u2714 Worker resisted the injection", "res-resisted"],
      };
      const [txt, cls] = map[ev.outcome] || ["", "system-line"];
      const line = document.createElement("div");
      line.className = `system-line ${cls}`;
      line.textContent = txt;
      worker.appendChild(line);
      scrollPane(worker);
      break;
    }
    case "owned":
      fireOwned();
      break;
    case "safe": {
      const line = document.createElement("div");
      line.className = "system-line safe";
      line.textContent = "\u2714 All attacks bounced. Behavior held to baseline.";
      worker.appendChild(line);
      scrollPane(worker);
      break;
    }
    case "error":
      addMsg(worker, "adversary", "error", esc(ev.detail));
      break;
    case "done":
      finish();
      break;
  }
}

function finish() {
  runBtn.disabled = false;
  gateToggle.disabled = false;
  scenarioSel.disabled = false;
  modelSel.disabled = !isLive;
  injectionInput.disabled = !isLive;
  runBtn.textContent = "Run arena";
  if (source) { source.close(); source = null; }
}

function updateBlurb() {
  blurb.textContent = scenarioBlurbs[scenarioSel.value] || "";
}

function reset() {
  if (source) { source.close(); source = null; }
  worker.innerHTML = "";
  adversary.innerHTML = "";
  attemptsEl.textContent = "0";
  landedEl.textContent = "0";
  banner.classList.add("hidden");
  document.body.classList.remove("owned");
  finish();
}

function run() {
  reset();
  banner.classList.remove("hidden");
  banner.className = "round-banner";
  banner.textContent = "Starting...";
  runBtn.disabled = true;
  gateToggle.disabled = true;
  scenarioSel.disabled = true;
  modelSel.disabled = true;
  injectionInput.disabled = true;
  runBtn.textContent = "Running...";
  const gate = gateToggle.checked ? "on" : "off";
  const params = new URLSearchParams({
    gate,
    scenario: scenarioSel.value,
    model: modelSel.value,
  });
  const injection = injectionInput.value.trim();
  if (injection) params.set("injection", injection);
  source = new EventSource(`/run?${params.toString()}`);
  source.onmessage = (e) => handle(JSON.parse(e.data));
  source.onerror = () => finish();
}

/* ---- model leaderboard: run the scenario across every model (gate off) ---- */
const LB_OUTCOME = {
  landed: ["\u2718 landed", "lb-cell-landed"],
  resisted: ["\u2714 resisted", "lb-cell-resisted"],
  blocked: ["\u2714 blocked", "lb-cell-blocked"],
};

function setControlsDisabled(d) {
  runBtn.disabled = d;
  leaderboardBtn.disabled = d;
  gateToggle.disabled = d;
  scenarioSel.disabled = d;
  resetBtn.disabled = d;
  modelSel.disabled = d || !isLive;
  injectionInput.disabled = d || !isLive;
}

function buildLeaderboard() {
  lbBody.innerHTML = "";
  const rows = {};
  models.forEach((m) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td class="lb-model">${esc(m)}</td>
      <td class="lb-cell-pending" data-r="1">&mdash;</td>
      <td class="lb-cell-pending" data-r="2">&mdash;</td>
      <td class="lb-cell-pending" data-r="3">&mdash;</td>
      <td class="lb-tally lb-cell-pending">&mdash;</td>`;
    lbBody.appendChild(tr);
    rows[m] = tr;
  });
  return rows;
}

function runOneModel(model, scenario, onResult) {
  return new Promise((resolve) => {
    const params = new URLSearchParams({ gate: "off", scenario, model });
    const es = new EventSource(`/run?${params.toString()}`);
    es.onmessage = (e) => {
      const ev = JSON.parse(e.data);
      if (ev.type === "attack_result") onResult(ev.n, ev.outcome);
      else if (ev.type === "done" || ev.type === "error") { es.close(); resolve(); }
    };
    es.onerror = () => { es.close(); resolve(); };
  });
}

async function runLeaderboard() {
  if (!isLive || !models.length) return;
  reset();
  const rows = buildLeaderboard();
  const scenarioName = scenarioSel.options[scenarioSel.selectedIndex]?.text || "";
  lbSub.textContent = `Scenario: ${scenarioName} \u2014 which model resists on its own? (gate off)`;
  lbOverlay.classList.remove("hidden");
  setControlsDisabled(true);
  leaderboardBtn.textContent = "Running...";

  for (const m of models) {
    const tr = rows[m];
    tr.classList.add("running");
    tr.querySelectorAll("[data-r]").forEach((c) => { c.textContent = "\u2026"; c.className = "lb-cell-running"; });
    let landed = 0;
    await runOneModel(m, scenarioSel.value, (n, outcome) => {
      const cell = tr.querySelector(`[data-r="${n}"]`);
      if (cell) {
        const [txt, cls] = LB_OUTCOME[outcome] || ["?", ""];
        cell.textContent = txt;
        cell.className = cls;
      }
      if (outcome === "landed") landed += 1;
    });
    const tally = tr.querySelector(".lb-tally");
    tally.textContent = `${landed}/3`;
    tally.className = `lb-tally ${landed ? "lb-cell-landed" : "lb-cell-resisted"}`;
    tr.classList.remove("running");
  }

  leaderboardBtn.textContent = "Run all models";
  setControlsDisabled(false);
}

runBtn.addEventListener("click", run);
resetBtn.addEventListener("click", reset);
scenarioSel.addEventListener("change", updateBlurb);
clearInjectionBtn.addEventListener("click", () => { injectionInput.value = ""; injectionInput.focus(); });
leaderboardBtn.addEventListener("click", runLeaderboard);
function closeLeaderboard() { lbOverlay.classList.add("hidden"); }
lbClose.addEventListener("click", closeLeaderboard);
lbOverlay.addEventListener("click", (e) => { if (e.target === lbOverlay) closeLeaderboard(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeLeaderboard(); });

fetch("/api/config")
  .then((r) => r.json())
  .then((cfg) => {
    isLive = cfg.live;
    el("mode").textContent = cfg.live ? "LIVE" : "CANNED";
    scenarioSel.innerHTML = "";
    cfg.scenarios.forEach((s) => {
      scenarioBlurbs[s.id] = s.blurb;
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.name;
      scenarioSel.appendChild(opt);
    });
    models = cfg.models || [];
    modelSel.innerHTML = "";
    models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      if (m === cfg.default_model) opt.selected = true;
      modelSel.appendChild(opt);
    });
    if (!cfg.live) {
      modelSel.disabled = true;
      modelSel.title = "No OpenAI key detected - running canned mode";
      injectionInput.disabled = true;
      injectionInput.title = "Custom injections need a live model (no OpenAI key detected)";
      leaderboardBtn.disabled = true;
      leaderboardBtn.title = "The leaderboard needs a live model (no OpenAI key detected)";
    }
    updateBlurb();
  })
  .catch(() => {});
