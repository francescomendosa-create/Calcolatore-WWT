/**
 * Harness: carica calcolatore-portate.html in un DOM minimo (senza jsdom),
 * esegue Reset → Start → N passi simPlus5, stampa livelli e portate.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "calcolatore-portate.html");
const html = fs.readFileSync(htmlPath, "utf8");
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/i);
if (!scriptMatch) {
  console.error("No script block found");
  process.exit(1);
}
let script = scriptMatch[1];

// Stub import() firebase e service worker
script = script.replace(
  /import\s*\(\s*["']https:\/\/www\.gstatic\.com[^"']+["']\s*\)/g,
  'Promise.reject(new Error("no-firebase"))'
);

const inputs = new Map();
const texts = new Map();
const attrs = new Map();

function makeEl(id, tag) {
  const isInput = /^(q|livello|freq|reg|start|stop|ciclo|carb|uf|view)/i.test(id)
    || id.includes("Attuale") || id.includes("Riemp") || id.includes("Svuot");
  const el = {
    id,
    tagName: (tag || (isInput ? "INPUT" : "DIV")).toUpperCase(),
    value: "",
    textContent: "",
    checked: false,
    disabled: false,
    parentElement: null,
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      toggle(c, on) { if (on === false) this._s.delete(c); else if (on === true) this._s.add(c); else if (this._s.has(c)) this._s.delete(c); else this._s.add(c); return this._s.has(c); },
      contains(c) { return this._s.has(c); },
    },
    style: {},
    dataset: {},
    children: [],
    innerHTML: "",
    getAttribute(n) { return (attrs.get(id) || {})[n] ?? null; },
    setAttribute(n, v) {
      if (!attrs.has(id)) attrs.set(id, {});
      attrs.get(id)[n] = String(v);
    },
    removeAttribute() {},
    addEventListener() {},
    removeEventListener() {},
    appendChild(ch) { this.children.push(ch); if (ch) ch.parentElement = this; return ch; },
    removeChild() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    closest() { return this.parentElement || this; },
    focus() {},
    blur() {},
    click() {},
    scrollIntoView() {},
  };
  // Seed from HTML value= if present
  const re = new RegExp(`id=["']${id}["'][^>]*value=["']([^"']*)["']`, "i");
  const re2 = new RegExp(`value=["']([^"']*)["'][^>]*id=["']${id}["']`, "i");
  const m = html.match(re) || html.match(re2);
  if (m) el.value = m[1];
  if (el.tagName === "INPUT" && el.value === "" && /livelloAttuale/.test(id)) {
    el.value = id.includes("Tk") ? "91.0" : "90.0";
  }
  return el;
}

const store = new Map();
const memInputs = {};
function getEl(id) {
  if (!id) return null;
  if (!store.has(id)) store.set(id, makeEl(id));
  return store.get(id);
}
function ensureMemInputs() {
  ["A", "B", "C", "D", "E", "F", "G", "H"].forEach((L) => {
    if (memInputs[L]) return;
    const lab = makeEl("memLab" + L, "LABEL");
    const inp = makeEl("memQ" + L, "INPUT");
    inp.classList.add("mem-q");
    inp.dataset.mem = L;
    inp.value = L === "H" ? "0" : "26";
    lab.appendChild(inp);
    memInputs[L] = inp;
  });
  return Object.values(memInputs);
}

const fakeDoc = {
  getElementById: getEl,
  querySelector(sel) {
    const idm = sel && sel.match(/^#([\w-]+)$/);
    if (idm) return getEl(idm[1]);
    const memm = sel && sel.match(/\.mem-q\[data-mem=["']?([A-H])["']?\]/);
    if (memm) {
      ensureMemInputs();
      return memInputs[memm[1]] || null;
    }
    return null;
  },
  querySelectorAll(sel) {
    if (sel && sel.includes("mem-q")) return ensureMemInputs();
    return [];
  },
  createElement(tag) {
    return makeEl("anon_" + Math.random(), tag || "DIV");
  },
  createElementNS(_ns, tag) {
    return makeEl("svg_" + Math.random(), tag || "path");
  },
  addEventListener() {},
  body: { appendChild() {}, style: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } } },
  documentElement: { style: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } } },
  head: { appendChild() {} },
  activeElement: null,
};

const fakeWin = {
  document: fakeDoc,
  navigator: {
    serviceWorker: {
      register: () => Promise.resolve({ update() {}, waiting: null, installing: null }),
      addEventListener() {},
    },
    userAgent: "NodeTest",
  },
  location: { href: "file:///test", reload() {} },
  localStorage: {
    _d: {},
    getItem(k) { return this._d[k] ?? null; },
    setItem(k, v) { this._d[k] = String(v); },
    removeItem(k) { delete this._d[k]; },
  },
  sessionStorage: { getItem() { return null; }, setItem() {} },
  requestAnimationFrame(cb) { return setTimeout(() => cb(Date.now()), 0); },
  cancelAnimationFrame(id) { clearTimeout(id); },
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  performance: { now: () => Date.now() },
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  addEventListener() {},
  removeEventListener() {},
  getComputedStyle: () => ({}),
  innerWidth: 1200,
  self: null,
  top: null,
  console,
  Math,
  Date,
  Number,
  String,
  Array,
  Object,
  JSON,
  parseFloat,
  parseInt,
  isFinite,
  Infinity,
  NaN,
  undefined,
  Promise,
  Map,
  Set,
  Error,
  URL,
};

fakeWin.self = fakeWin;
fakeWin.top = fakeWin;
fakeWin.window = fakeWin;
fakeWin.globalThis = fakeWin;

// Seed critical defaults
const seeds = {
  qIn: "150",
  qPump: "345",
  qMandata: "345",
  qRecycle: "195",
  qP11019: "140",
  qP11019Ias: "0",
  qMemTotale: "182",
  livelloAttuale: "90.0",
  livelloAttualeA10611: "90.0",
  livelloAttualeH: "90.0",
  livelloAttualeMbr: "90.0",
  livelloAttualeTk11007: "91.0",
  livelloAttualeTk11021: "91.0",
  freqHz: "45",
  cicloLavoro: "7",
  cicloPausa: "1",
  regA10620Vutile: "450",
  regTk11007Vutile: "30",
  regTk11021Vutile: "30",
  regA10611OnFrom: "91",
  regA10611OnTo: "80",
  regA10611Min: "6",
  regA10611OffFrom: "80",
  regA10611OffTo: "91",
  equiparaMandata: "",
};
Object.entries(seeds).forEach(([id, v]) => {
  const el = getEl(id);
  el.value = v;
  if (id === "equiparaMandata") el.checked = true;
});

const context = vm.createContext(fakeWin);
let booted = false;
try {
  vm.runInContext(script, context, { timeout: 20000, filename: "calcolatore-portate.html" });
  booted = true;
} catch (e) {
  console.error("BOOT FAIL:", e.message);
  console.error(e.stack.split("\n").slice(0, 8).join("\n"));
}

function lv(id) {
  return parseFloat(getEl(id).value);
}
function dump(tag) {
  console.log(
    tag,
    "t=",
    fakeWin.__simMin ?? "?",
    "L20=",
    lv("livelloAttuale").toFixed(2),
    "L11=",
    lv("livelloAttualeA10611").toFixed(2),
    "L07=",
    lv("livelloAttualeTk11007").toFixed(2),
    "L21=",
    lv("livelloAttualeTk11021").toFixed(2),
    "qPump=",
    lv("qPump").toFixed(1),
    "qP19=",
    lv("qP11019").toFixed(1),
    "qMem=",
    lv("qMemTotale").toFixed(1)
  );
}

(async () => {
  if (!booted) process.exit(2);
  // Allow microtasks from boot
  await new Promise((r) => setTimeout(r, 50));

  const g = fakeWin;
  // Try to call through DOM buttons if handlers attached — call functions on window if exposed
  // Functions are in script IIFE? Check if they're global.
  const keys = Object.keys(g).filter((k) => /sim|Sim|forcePlant|simulate/.test(k));
  console.log("exposed sim-like keys:", keys.slice(0, 40));

  // The script is NOT wrapped in IIFE — functions are global on window in browser.
  // In our vm they should be on fakeWin if declared as function foo() at top level.
  dump("before");

  if (typeof g.simReset === "function") {
    g.simReset({ silent: true });
  } else {
    console.error("simReset not found — script may be scoped");
    // List function-like
    const fns = Object.keys(g).filter((k) => typeof g[k] === "function");
    console.log("fn count", fns.length, fns.filter((n) => /sim|tick|force|apply/.test(n)).slice(0, 50));
    process.exit(3);
  }

  dump("after reset");
  g.simStart();
  dump("after start");

  for (let i = 0; i < 15; i++) {
    try { g.simPlus5(); } catch (e) { console.log("simPlus5 err", i, e.message); }
    if (i === 0 || i === 4 || i === 7 || i === 14) dump("step" + (i + 1));
  }

  const d07 = Math.abs(lv("livelloAttualeTk11007") - 91);
  const d11 = Math.abs(lv("livelloAttualeA10611") - 90);
  const d20 = Math.abs(lv("livelloAttuale") - 90);
  const moved = d07 > 0.05 || d11 > 0.05 || d20 > 0.05;
  console.log("RESULT", moved ? "LEVELS_MOVED" : "LEVELS_FROZEN", { d07, d11, d20 });
  process.exit(moved ? 0 : 10);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
