# -*- coding: utf-8 -*-
"""Patch: previsione 8 ore + messaggi blocco spiccioli."""
from pathlib import Path

path = Path(__file__).with_name("index.html")
text = path.read_text(encoding="utf-8")
orig = text

# --- 1) CSS: badge warn + ok forecast ---
old_css = """.sim-time .chimico-blocks[data-count="0"] { opacity: 0.55; }
    #popBlocchi .block-explain p { margin: 0 0 10px; line-height: 1.45; }"""

new_css = """.sim-time .chimico-blocks[data-count="0"] { opacity: 0.55; }
    .sim-time .chimico-blocks[data-warn="1"] {
      opacity: 1;
      color: #fbbf24;
      border-color: #f59e0b;
      background: rgba(120, 53, 15, 0.35);
    }
    .sim-time .chimico-blocks[data-warn="1"]:hover {
      border-color: #fbbf24;
      background: rgba(120, 53, 15, 0.5);
      color: #fde68a;
    }
    #popBlocchi .block-explain .ok-line { color: #bbf7d0; }
    #popBlocchi .block-forecast {
      margin: 0 0 12px;
      padding: 10px 12px;
      border-radius: 8px;
      background: #0f172a;
      border: 1px solid #334155;
      font-size: 0.9rem;
      color: #e2e8f0;
      line-height: 1.45;
    }
    #popBlocchi .block-forecast.is-ok { border-color: #166534; background: #052e16; }
    #popBlocchi .block-forecast.is-bad { border-color: #b45309; background: #451a03; }
    #popBlocchi .block-explain p { margin: 0 0 10px; line-height: 1.45; }"""

if old_css not in text:
    raise SystemExit("CSS marker not found")
text = text.replace(old_css, new_css, 1)

# --- 2) Constant near SIM_STEP_MIN ---
old_sim = """    const SIM_STEP_MIN = 1;   // passo TIME (minuti) — Start: 1 s reale = 1′"""
new_sim = """    const SIM_STEP_MIN = 1;   // passo TIME (minuti) — Start: 1 s reale = 1′
    const BLOCK_FORECAST_HORIZON = 480; // previsione blocchi chimico: 8 ore"""
if old_sim not in text:
    raise SystemExit("SIM_STEP_MIN marker not found")
text = text.replace(old_sim, new_sim, 1)

# --- 3) Insert forecast helpers before buildChimicoBlockReport ---
old_build_hdr = """    /** Diagnosi operativa: spicciola, quesito Sì/No, niente CF a zero su anomalie. */
    function buildChimicoBlockReport(ev) {"""

forecast_code = r'''    /** Previsione locale (senza muovere lo schema): A10620 / P11011 / A10611 / MP 11036. */
    function forecastChimicoHorizon(horizonMin, opts) {
      opts = opts || {};
      const H = Math.max(1, Math.round(Number(horizonMin) || BLOCK_FORECAST_HORIZON));
      const dt = 1;
      const stopR = numOrNull("stopRiempA10620");
      const startR = numOrNull("startRiempA10620");
      const stop = stopR !== null ? stopR : 95;
      const start = startR !== null ? startR : 92;
      const startSvuot = numOrNull("startSvuotA10620");
      const stopSvuot = numOrNull("stopSvuotA10620");
      const startS = startSvuot !== null ? startSvuot : 92;
      const stopS = stopSvuot !== null ? stopSvuot : 88;
      const hiBlock = numOrNull("stopAltoA10611");
      const hiRestart = numOrNull("ripartenzaP11011A10611");
      const hiB = hiBlock !== null ? hiBlock : 96;
      const hiR = hiRestart !== null ? hiRestart : 90;
      const stopSvuot11 = numOrNull("stopSvuotA10611");
      const startSvuot11 = numOrNull("startSvuotA10611");
      const loStop = stopSvuot11 !== null ? stopSvuot11 : 80;
      const loStart = startSvuot11 !== null ? startSvuot11 : 88;

      const qInSp = opts.qIn != null ? Math.max(0, Number(opts.qIn) || 0) : Math.max(0, num("qIn"));
      let qPumpSp = opts.qPump != null ? Math.max(0, Number(opts.qPump) || 0) : Math.max(0, flowSetpointOf("qPump"));
      let qMandSp = opts.qMand != null ? Math.max(0, Number(opts.qMand) || 0) : Math.max(0, flowSetpointOf("qMandata"));
      const qMemSp = opts.qMem != null ? Math.max(0, Number(opts.qMem) || 0) : Math.max(0, num("qMemTotale"));
      let qRecSp = opts.qRec != null ? Math.max(0, Number(opts.qRec) || 0) : Math.max(0, flowSetpointOf("qRecycle"));

      // In Automatico la P11011 segue il pavimento ingresso+riciclo (come in marcia).
      try {
        if (opts.forceManualFlows !== true && isAutoMode() && deviceAutoControlled("pompa")) {
          const floor = pumpFloorForIngresso(qInSp);
          const step = pumpStepForNeed(floor);
          if (step && Number.isFinite(step.q)) qPumpSp = Math.max(qPumpSp, step.q);
        }
        if (opts.forceManualFlows !== true && isAutoMode() && deviceAutoControlled("mandata") && el("equiparaMandata")?.checked) {
          qMandSp = qPumpSp;
        }
        if (opts.forceManualFlows !== true && ricicloAutoControlled()) {
          qRecSp = Math.max(Q_RECYCLE_MIN, round1(Math.max(0, qPumpSp - qInSp)));
        }
      } catch (_) { /* ok */ }

      let liv20 = opts.liv20 != null ? Number(opts.liv20) : (numOrNull("livelloAttuale") ?? 90);
      let liv11 = opts.liv11 != null ? Number(opts.liv11) : (numOrNull("livelloAttualeA10611") ?? 90);
      if (!Number.isFinite(liv20)) liv20 = 90;
      if (!Number.isFinite(liv11)) liv11 = 90;

      let chimicoOn = opts.chimicoOn != null ? !!opts.chimicoOn : (__chimicoAllowFill !== false);
      let pumpBy20 = opts.pumpBy20 != null ? !!opts.pumpBy20 : (__runP11011By20 !== false);
      let blockP11 = opts.blockP11 != null ? !!opts.blockP11 : !!__blockP11011By11;
      let run11036 = opts.run11036 != null ? !!opts.run11036 : (__run11036 !== false);
      const startupHold = opts.startupHold != null ? !!opts.startupHold : (__startupPumpHold !== false);

      const blocks = [];
      let firstBlockMin = null;
      let firstSnap = null;
      let reason = "";

      for (let t = dt; t <= H; t += dt) {
        if (liv20 <= stopS + 0.05) pumpBy20 = false;
        else if (liv20 >= startS - 0.05) pumpBy20 = true;
        else if (startupHold && t <= 2) pumpBy20 = true;

        if (liv11 >= hiB - 0.05) blockP11 = true;
        else if (liv11 <= hiR + 0.05) blockP11 = false;

        if (liv11 <= loStop + 0.05) run11036 = false;
        else if (liv11 >= loStart - 0.05) run11036 = true;

        const pumpOn = pumpBy20 && !blockP11;
        const qPump = pumpOn ? qPumpSp : 0;
        const qMand = run11036 ? qMandSp : 0;
        const qIn = chimicoOn ? qInSp : 0;
        const qRec = (qRecSp > 0.05 && pumpOn) ? qRecSp : (ricicloAutoControlled() && pumpOn ? Math.max(Q_RECYCLE_MIN, round1(Math.max(0, qPumpSp - qInSp))) : 0);

        const r20 = rateA10620PctPerMin(qIn, qPump, qRec);
        const r11 = estimateA10611RatePctPerMin(qPump, qMand);
        liv20 = Math.max(0, Math.min(100, liv20 + r20 * dt));
        liv11 = Math.max(0, Math.min(100, liv11 + r11 * dt));

        if (chimicoOn && qInSp > 0.5 && liv20 >= stop - 0.05) {
          liv20 = stop;
          chimicoOn = false;
          if (firstBlockMin == null) {
            firstBlockMin = t;
            reason = blockP11
              ? "mand"
              : (!pumpOn ? "p11off" : ((qIn + qRec) - qPump > 0.5 ? "p11low" : "near"));
            firstSnap = {
              tMin: t,
              liv20: round2(liv20),
              liv11: round2(liv11),
              stop, start, startSvuot: startS, stopSvuot: stopS,
              hiBlock: hiB, hiRestart: hiR,
              qInSp: round1(qInSp), qInLive: round1(qInSp),
              qRecSp: round1(qRecSp), qRecLive: round1(qRec),
              qPumpSp: round1(qPumpSp), qPumpLive: round1(qPumpSp),
              qOut: round1(qPump),
              qMandSp: round1(qMandSp), qMandLive: round1(qMand),
              qMemSp: round1(qMemSp), qMemLive: round1(qMemSp),
              run11036: !!run11036,
              qInTo20: round1(qInSp + qRec),
              qEq20: round1(qInSp + qRec),
              qEqPlant: round1(Math.max(qInSp + qRec, qInSp + Q_RECYCLE_MIN)),
              deficit: round1(Math.max(0, (qInSp + qRec) - qPump)),
              pumpOn: !!pumpOn,
              runP11011By20: !!pumpBy20,
              blockP11011: !!blockP11,
            };
          }
          blocks.push(t);
        } else if (!chimicoOn && liv20 <= start + 0.05) {
          chimicoOn = true;
        }
      }

      return {
        ok: firstBlockMin == null,
        horizonMin: H,
        firstBlockMin,
        blockCount: blocks.length,
        reason,
        snap: firstSnap,
        qInSp: round1(qInSp),
        qPumpSp: round1(qPumpSp),
        qMandSp: round1(qMandSp),
        qMemSp: round1(qMemSp),
        endLiv20: round2(liv20),
        endLiv11: round2(liv11),
      };
    }

    /** Massimo chimico-fisico che evita il blocco per l'orizzonte (stessi set pompe). */
    function maxQinSafeForHorizon(horizonMin, opts) {
      opts = opts || {};
      const cur = Math.max(0, opts.qIn != null ? Number(opts.qIn) : num("qIn"));
      const base = { ...opts };
      delete base.qIn;
      if (forecastChimicoHorizon(horizonMin, { ...base, qIn: cur }).ok) return round1(cur);
      let lo = 0;
      let hi = cur;
      let best = 0;
      for (let i = 0; i < 20; i++) {
        const mid = (lo + hi) / 2;
        if (forecastChimicoHorizon(horizonMin, { ...base, qIn: mid }).ok) {
          best = mid;
          lo = mid;
        } else {
          hi = mid;
        }
      }
      return round1(best);
    }

    function fmtForecastWhen(min) {
      const m = Math.max(0, Math.round(Number(min) || 0));
      if (m < 60) return m + "′";
      const h = Math.floor(m / 60);
      const r = m % 60;
      return r ? (h + " h " + r + "′") : (h + " h");
    }

    /** Diagnosi + previsione 8 ore: quale portata regolare, quesito, CF solo se serve. */
    function buildHorizonAdvice(fc) {
      const qInSp = fc.qInSp;
      let qMax = 334;
      try { qMax = getPumpMax(); } catch (_) { /* ok */ }
      let qPumpTarget = round1(Math.max(0, qInSp + Q_RECYCLE_MIN));
      try { qPumpTarget = round1(Math.max(qPumpTarget, pumpFloorForIngresso(qInSp))); } catch (_) { /* ok */ }
      const qMandTarget = round1(Math.max(qPumpTarget, fc.qPumpSp || 0));
      const qMemTarget = round1(Math.max(qMandTarget * 0.85, fc.qMemSp || 0));
      const hzBit = hzBitForNeed(qPumpTarget);
      const qHavePump = fc.qPumpSp || 0;
      const qHaveMand = fc.qMandSp || 0;
      const anomalyPump = isAnomalousLowFlow(qHavePump, qPumpTarget, qInSp);
      const anomalyMand = isAnomalousLowFlow(qHaveMand, qMandTarget, qInSp);
      const nearPump = isNearMissFlow(qHavePump, qPumpTarget);
      const nearMand = isNearMissFlow(qHaveMand, qMandTarget);
      const qSafeSamePumps = maxQinSafeForHorizon(fc.horizonMin || BLOCK_FORECAST_HORIZON, {
        qPump: fc.qPumpSp,
        qMand: fc.qMandSp,
        qMem: fc.qMemSp,
        forceManualFlows: true,
      });

      if (fc.ok) {
        return {
          ok: true,
          forecastHtml: `<div class="block-forecast is-ok"><strong>Tutto OK — prossime 8 ore</strong><br>`
            + `Con le portate attuali (chimico <strong>${fmtQ(qInSp)}</strong> · P11011 <strong>${fmtQ(fc.qPumpSp)}</strong>`
            + ` · MP 11036 <strong>${fmtQ(fc.qMandSp)}</strong> · membrane <strong>${fmtQ(fc.qMemSp)}</strong>) `
            + `il chimico-fisico <strong>non va in blocco</strong> e l'impianto resta in marcia.</div>`,
          verdict: "",
          action: "",
          ask: null,
          fault: "",
          alt: "",
          forceAlt: false,
        };
      }

      const when = fmtForecastWhen(fc.firstBlockMin);
      let device = "P11011 A/B";
      let target = qPumpTarget;
      let anomaly = anomalyPump;
      let near = nearPump;
      let askQ = "";
      let yesHtml = "";
      let noHtml = "";
      let verdict = "";
      let action = "";
      let fault = "";
      let forceAlt = false;

      if (fc.reason === "mand" || (fc.snap && fc.snap.blockP11011)) {
        device = "MP 11036 A/B";
        target = qMandTarget;
        anomaly = anomalyMand;
        near = nearMand;
        verdict = `Previsto blocco tra <strong>${when}</strong>: <strong>MP 11036 / membrane</strong> basse → A10611 alto → P11011 ferme.`;
        action = `Regola <strong>MP 11036 A/B a <span class="fix-val">${fmtQ(qMandTarget)} m³/h</span></strong> `
          + `e membrane ≥ <span class="fix-val">${fmtQ(qMemTarget)} m³/h</span>.`;
        askQ = `Puoi aumentare <strong>MP 11036 A/B</strong> a <strong class="fix-val">${fmtQ(qMandTarget)} m³/h</strong> `
          + `(o le membrane a ≥ ${fmtQ(qMemTarget)})?`;
        yesHtml = action + ` Poi P11011 ≥ <span class="fix-val">${fmtQ(qPumpTarget)}</span>${hzBit}.`;
      } else if (qPumpTarget > qMax + 0.05) {
        forceAlt = true;
        anomaly = false;
        verdict = `Previsto blocco tra <strong>${when}</strong>: chimico <strong>${fmtQ(qInSp)}</strong> sopra la capacità P11011 (max ${fmtQ(qMax)}).`;
        action = `Non puoi alzare abbastanza le P11011.`;
        askQ = "";
      } else if (fc.reason === "p11off" || qHavePump < 0.5) {
        device = "P11011 A/B";
        verdict = `Previsto blocco tra <strong>${when}</strong>: <strong>P11011 OFF / troppo basse</strong> con chimico a ${fmtQ(qInSp)} m³/h.`;
        action = `Metti in marcia <strong>P11011 a <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
        askQ = `Puoi portare <strong>P11011 A/B</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`;
        yesHtml = `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
      } else {
        device = "P11011 A/B";
        anomaly = anomalyPump;
        near = nearPump;
        verdict = `Previsto blocco tra <strong>${when}</strong>: <strong>P11011</strong> a ${fmtQ(qHavePump)} m³/h, `
          + `serve ≥ <strong>${fmtQ(qPumpTarget)}</strong> (chimico ${fmtQ(qInSp)}).`;
        action = `Regola <strong>P11011 a <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
        askQ = `Puoi aumentare <strong>P11011 A/B</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`;
        yesHtml = `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit} `
          + `e lascia il chimico a ${fmtQ(qInSp)} m³/h.`;
      }

      if (anomaly) {
        fault = `Portata anomala (ingresso ${fmtQ(qInSp)} vs ${device} ${fmtQ(device.indexOf("11036") >= 0 ? qHaveMand : qHavePump)}): `
          + `non abbassare il chimico — sposta la pompa al valore esercibile (≈ <span class="fix-val">${fmtQ(target)}</span>).`;
        noHtml = `Allora c'è un limite/avaria su <strong>${device}</strong>: porta comunque al massimo esercibile `
          + `(fino a <span class="fix-val">${fmtQ(device.indexOf("11036") >= 0 ? qMandTarget : qMax)}</span>). `
          + `Non azzerare il chimico per un set sbagliato.`;
      } else if (forceAlt) {
        const qInMaxPlant = qInCapAtPump(qMax);
        noHtml = `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qInMaxPlant)} m³/h</strong> `
          + `per restare in marcia 8 ore (P11011 a ${fmtQ(qMax)}).`;
      } else {
        noHtml = `Allora scendi il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qSafeSamePumps)} m³/h</strong> `
          + `(minimo giusto per non andare in blocco per 8 ore, con le pompe così).`;
      }

      const ask = (!forceAlt && askQ)
        ? {
            key: `fc-${fc.reason || "x"}-${fmtQ(target)}-${fmtQ(qInSp)}-${fc.firstBlockMin}`,
            q: askQ,
            yesHtml,
            noHtml,
            hideAltOnNo: !!anomaly,
          }
        : null;

      return {
        ok: false,
        forecastHtml: `<div class="block-forecast is-bad"><strong>Attenzione — entro 8 ore</strong><br>${verdict}</div>`,
        verdict,
        action,
        ask,
        fault,
        alt: forceAlt ? noHtml : (near && !anomaly ? noHtml : ""),
        forceAlt,
        qSafeSamePumps,
        qPumpTarget,
        qMandTarget,
        qMemTarget,
      };
    }

    /** Diagnosi operativa: spicciola, quesito Sì/No, niente CF a zero su anomalie. */
    function buildChimicoBlockReport(ev) {'''

if old_build_hdr not in text:
    raise SystemExit("buildChimicoBlockReport header not found")
text = text.replace(old_build_hdr, forecast_code, 1)

# --- 4) Replace updateChimicoBlockUI ---
old_ui = """    function updateChimicoBlockUI() {
      const node = el("chimicoBlockCount");
      if (!node) return;
      node.textContent = String(__chimicoBlockCount);
      node.setAttribute("data-count", String(__chimicoBlockCount));
      const n = __chimicoBlockCount;
      node.title = n === 0
        ? "Nessun blocco — clic per la catena di causa"
        : (n === 1 ? "1 blocco — clic per la catena" : `${n} blocchi — clic per la catena`);
    }"""

new_ui = """    function updateChimicoBlockUI() {
      const node = el("chimicoBlockCount");
      if (!node) return;
      node.textContent = String(__chimicoBlockCount);
      node.setAttribute("data-count", String(__chimicoBlockCount));
      const n = __chimicoBlockCount;
      let warn = false;
      try {
        const fc = forecastChimicoHorizon(BLOCK_FORECAST_HORIZON);
        warn = !fc.ok;
        if (n === 0) {
          node.title = warn
            ? `Previsto blocco entro 8 ore (~${fmtForecastWhen(fc.firstBlockMin)}) — clic per consigli`
            : "Nessun blocco — previsione 8 ore OK — clic per dettagli";
        } else {
          node.title = n === 1
            ? "1 blocco — clic per cosa regolare"
            : `${n} blocchi — clic per cosa regolare`;
        }
      } catch (_) {
        node.title = n === 0
          ? "Nessun blocco — clic per previsione 8 ore"
          : (n === 1 ? "1 blocco — clic" : `${n} blocchi — clic`);
      }
      node.setAttribute("data-warn", warn ? "1" : "0");
    }"""

if old_ui not in text:
    raise SystemExit("updateChimicoBlockUI not found")
text = text.replace(old_ui, new_ui, 1)

# --- 5) Replace paintBlocchiExplain ---
# Find function start to openBlocchiPopup
start = text.find("    function paintBlocchiExplain() {")
if start < 0:
    raise SystemExit("paintBlocchiExplain not found")
end = text.find("    function openBlocchiPopup() {", start)
if end < 0:
    raise SystemExit("openBlocchiPopup not found after paint")

new_paint = r'''    function paintBlocchiExplain() {
      const body = el("blocchiBody");
      if (!body) return;
      const last = __chimicoBlockLog.length ? __chimicoBlockLog[__chimicoBlockLog.length - 1] : null;
      const blockedNow = !__chimicoAllowFill;
      const livNow = numOrNull("livelloAttuale");
      const startNow = numOrNull("startRiempA10620");
      const startV = startNow !== null ? startNow : 92;

      let html = "";
      let fc = null;
      try { fc = forecastChimicoHorizon(BLOCK_FORECAST_HORIZON); } catch (_) { fc = null; }
      const adv = fc ? buildHorizonAdvice(fc) : null;

      if (last) {
        const rep = buildChimicoBlockReport(last);
        const ask = rep.ask;
        if (ask && ask.key !== __blockQaKey) {
          __blockQaKey = ask.key;
          __blockQaAnswer = null;
        }
        html += `<div class="block-verdict">${rep.verdict}</div>`;
        html += `<div class="block-action"><strong>Cosa regolare</strong><br>${rep.action}</div>`;
        if (rep.fault) {
          html += `<div class="block-fault">${rep.fault}</div>`;
        }
        if (ask) {
          html += `<div class="block-qa" data-qa-key="${ask.key}">`;
          html += `<p>${ask.q}</p>`;
          html += `<div class="block-qa-btns">`;
          html += `<button type="button" data-block-qa="yes"${__blockQaAnswer === "yes" ? ' class="is-picked"' : ""}>Sì</button>`;
          html += `<button type="button" data-block-qa="no"${__blockQaAnswer === "no" ? ' class="is-picked"' : ""}>No</button>`;
          html += `</div></div>`;
          if (__blockQaAnswer === "yes") {
            html += `<div class="block-action">${ask.yesHtml}</div>`;
          } else if (__blockQaAnswer === "no") {
            html += `<div class="block-alt">${ask.noHtml}</div>`;
          }
        } else if (rep.forceAlt && rep.alt) {
          html += `<div class="block-alt"><strong>Obbligatorio</strong><br>${rep.alt}</div>`;
        } else if (rep.alt && !ask) {
          html += `<div class="block-alt">${rep.alt}</div>`;
        }
        html += `<div class="block-meta">${rep.meta}</div>`;
        html += `<p class="mini" style="margin-top:10px"><strong>Catena</strong></p><ul class="block-chain">`;
        rep.chain.forEach((step) => { html += `<li>${step}</li>`; });
        html += `</ul>`;
        if (blockedNow) {
          html += `<p class="mini" style="margin-top:10px">Ancora in blocco (A10620 ${livNow !== null ? fmtBlockPct(livNow) : "—"}). `
            + `Il chimico riparte a ≤ ${fmtBlockPct(startV)}.</p>`;
        }
        if (adv) {
          html += `<p class="mini" style="margin-top:12px"><strong>Se riparti con questi set</strong></p>`;
          html += adv.forecastHtml;
        }
      } else if (adv) {
        html += adv.forecastHtml;
        if (adv.ok) {
          html += `<div class="block-action ok-line">Nessuna regolazione necessaria: le portate sono coerenti.</div>`;
          __blockQaKey = `ok-${fmtQ(fc.qInSp)}-${fmtQ(fc.qPumpSp)}`;
          __blockQaAnswer = null;
        } else {
          html += `<div class="block-action"><strong>Cosa regolare</strong><br>${adv.action}</div>`;
          if (adv.fault) html += `<div class="block-fault">${adv.fault}</div>`;
          const ask = adv.ask;
          if (ask) {
            if (ask.key !== __blockQaKey) {
              __blockQaKey = ask.key;
              __blockQaAnswer = null;
            }
            html += `<div class="block-qa" data-qa-key="${ask.key}">`;
            html += `<p>${ask.q}</p>`;
            html += `<div class="block-qa-btns">`;
            html += `<button type="button" data-block-qa="yes"${__blockQaAnswer === "yes" ? ' class="is-picked"' : ""}>Sì</button>`;
            html += `<button type="button" data-block-qa="no"${__blockQaAnswer === "no" ? ' class="is-picked"' : ""}>No</button>`;
            html += `</div></div>`;
            if (__blockQaAnswer === "yes") {
              html += `<div class="block-action">${ask.yesHtml}</div>`;
            } else if (__blockQaAnswer === "no") {
              html += `<div class="block-alt">${ask.noHtml}</div>`;
            } else {
              html += `<p class="mini">Rispondi Sì/No: prima prova a regolare la pompa; solo se non puoi, compare il set del chimico-fisico per le 8 ore.</p>`;
            }
          } else if (adv.forceAlt && adv.alt) {
            html += `<div class="block-alt"><strong>Obbligatorio</strong><br>${adv.alt}</div>`;
          }
          if (fc && fc.snap) {
            html += `<div class="block-meta"><div><strong>Previsione</strong> · primo blocco a ${fmtForecastWhen(fc.firstBlockMin)}`
              + ` · A10620→${fmtBlockPct(fc.snap.liv20)} · A10611→${fmtBlockPct(fc.snap.liv11)}</div>`
              + `<div>Chimico ${fmtQ(fc.qInSp)} · P11011 ${fmtQ(fc.qPumpSp)} · MP 11036 ${fmtQ(fc.qMandSp)} · membrane ${fmtQ(fc.qMemSp)}</div></div>`;
          }
        }
      } else if (__chimicoBlockCount === 0) {
        html += `<div class="block-action">Nessun blocco dal Reset. Apri di nuovo dopo aver impostato le portate.</div>`;
      } else {
        html += `<p>Ci sono ${__chimicoBlockCount} blocco/i contati, ma senza snapshot della catena (evento precedente).</p>`;
      }

      if (__chimicoBlockLog.length > 1) {
        const prev = __chimicoBlockLog.slice(0, -1).slice(-3).reverse();
        html += `<p class="mini" style="margin-top:12px">Precedenti: `
          + prev.map((e) => `${e.tMin}′ · IN ${fmtQ(e.qInLive)} / P11011 ${fmtQ(e.qOut)}`).join(" · ")
          + `</p>`;
      }

      body.innerHTML = html;
      body.querySelectorAll("[data-block-qa]").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          const ans = btn.getAttribute("data-block-qa");
          __blockQaAnswer = ans === "no" ? "no" : "yes";
          paintBlocchiExplain();
        });
      });
      try { updateChimicoBlockUI(); } catch (_) { /* ok */ }
    }

'''

text = text[:start] + new_paint + text[end:]

# --- 6) Title tweak ---
text = text.replace(
    '<span id="blocchiTitle">Blocco — cosa regolare</span>',
    '<span id="blocchiTitle">Blocco / previsione 8 ore</span>',
    1,
)

if text == orig:
    raise SystemExit("No changes applied")

path.write_text(text, encoding="utf-8")
print("OK patched", path)
print("delta bytes", len(text) - len(orig))
