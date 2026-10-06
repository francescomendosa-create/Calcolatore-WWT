    function buildChimicoBlockReport(ev) {
      if (!ev) {
        return {
          chain: [], meta: "", verdict: "", action: "", alt: "", eq: "",
          ask: null, fault: "", forceAlt: false, anomaly: false,
        };
      }
      const chain = [];
      if (ev.blockP11011) {
        chain.push(
          `A10611 alto (${fmtBlockPct(ev.liv11)} ≥ ${fmtBlockPct(ev.hiBlock)}) → <strong>P11011 ferme</strong>.`
        );
        chain.push(
          `A10620 ha ricevuto ingresso ${fmtQ(ev.qInLive)} m³/h`
          + (ev.qRecLive > 0.05 ? ` + riciclo ${fmtQ(ev.qRecLive)}` : "")
          + ` senza scarico P11011.`
        );
      } else if (!ev.pumpOn) {
        if (!ev.runP11011By20) {
          chain.push(
            `P11011 OFF: A10620 sotto start svuotamento (serve ≥ ${fmtBlockPct(ev.startSvuot)}).`
          );
        } else {
          chain.push(`P11011 non scaricavano.`);
        }
        chain.push(
          `Ingresso ${fmtQ(ev.qInLive)} m³/h` + (ev.qRecLive > 0.05 ? ` + riciclo ${fmtQ(ev.qRecLive)}` : "")
          + ` ha riempito A10620.`
        );
      } else {
        chain.push(
          `Verso A10620: <strong>${fmtQ(ev.qInTo20)} m³/h</strong> (IN ${fmtQ(ev.qInLive)}`
          + (ev.qRecLive > 0.05 ? ` + riciclo ${fmtQ(ev.qRecLive)}` : "") + `).`
        );
        chain.push(
          `P11011 solo <strong>${fmtQ(ev.qOut)} m³/h</strong> (set ${fmtQ(ev.qPumpSp)}) — manca ≈ <strong>${fmtQ(ev.deficit)}</strong>.`
        );
      }
      chain.push(
        `A10620 ${fmtBlockPct(ev.liv20 != null ? ev.liv20 : ev.liv)} ≥ stop ${fmtBlockPct(ev.stop)} → <strong>blocco chimico</strong>.`
      );

      let qMax = 334;
      try { qMax = getPumpMax(); } catch (_) { /* ok */ }
      const qPumpTarget = round1(Math.max(ev.qEq20 || 0, ev.qEqPlant || 0));
      const hzBit = hzBitForNeed(qPumpTarget);
      const qHavePump = Math.max(ev.qPumpSp || 0, ev.pumpOn ? (ev.qOut || 0) : 0);
      const anomalyPump = isAnomalousLowFlow(qHavePump, qPumpTarget, ev.qInSp);
      const nearPump = isNearMissFlow(qHavePump, qPumpTarget);

      // Target 11036 / membrane: scaricare almeno quanto arriva da P11011 (o il bisogno impianto)
      const qMandTarget = round1(Math.max(qPumpTarget, ev.qInTo20 || 0, ev.qPumpSp || 0));
      const qMemTarget = round1(Math.max(qMandTarget * 0.85, ev.qMemSp || 0));
      const qHaveMand = Math.max(ev.qMandSp || 0, ev.run11036 ? (ev.qMandLive || 0) : 0);
      const anomalyMand = isAnomalousLowFlow(qHaveMand, qMandTarget, ev.qInSp);
      const nearMand = isNearMissFlow(qHaveMand, qMandTarget);

      let verdict = "";
      let action = "";
      let alt = "";
      let fault = "";
      let ask = null;
      let forceAlt = false;
      let anomaly = false;

      if (ev.blockP11011) {
        anomaly = anomalyMand;
        verdict = `Male: <strong>MP 11036 / membrane</strong> non scaricano A10611 `
          + `(${fmtBlockPct(ev.liv11)}) → P11011 ferme → blocco.`;
        action = `Metti <strong>MP 11036 A/B a <span class="fix-val">${fmtQ(qMandTarget)} m³/h</span></strong> `
          + `(e membrane ≥ <span class="fix-val">${fmtQ(qMemTarget)} m³/h</span>) `
          + `finché A10611 scende sotto <strong class="fix-val">${fmtBlockPct(ev.hiRestart)}</strong>, `
          + `poi P11011 ≥ <span class="fix-val">${fmtQ(qPumpTarget)}</span>${hzBit}.`;
        if (anomaly) {
          fault = `Portata 11036/membrane anomala rispetto all’ingresso `
            + `(IN ${fmtQ(ev.qInSp)} · 11036 ${fmtQ(qHaveMand)} · serve ≈ ${fmtQ(qMandTarget)}). `
            + `Non abbassare il chimico: regola la pompa sottodimensionata.`;
          alt = "";
          ask = {
            key: `mand-${fmtQ(qMandTarget)}-${fmtQ(ev.qInSp)}`,
            q: `Puoi aumentare <strong>MP 11036 A/B</strong> a <strong class="fix-val">${fmtQ(qMandTarget)} m³/h</strong> `
              + `(o le membrane a ≥ ${fmtQ(qMemTarget)})?`,
            yesHtml: `Ok: regola <strong>MP 11036 A/B → <span class="fix-val">${fmtQ(qMandTarget)} m³/h</span></strong> `
              + `e membrane ≥ <span class="fix-val">${fmtQ(qMemTarget)} m³/h</span>. `
              + `Poi P11011 ≥ <span class="fix-val">${fmtQ(qPumpTarget)}</span>${hzBit}.`,
            noHtml: `Allora c’è un problema su 11036/membrane: non è un set del chimico. `
              + `Controlla pompe/linee e porta la portata esercibile a ≈ <span class="fix-val">${fmtQ(qMandTarget)}</span>.`,
            hideAltOnNo: true,
          };
        } else {
          const qSafe = qInCapAtPump(Math.min(qMax, Math.max(ev.qPumpSp || 0, qPumpTarget * 0.5)));
          alt = `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(Math.min(ev.qInSp, qSafe))} m³/h</strong> `
            + `finché A10611 scende sotto ${fmtBlockPct(ev.hiRestart)}.`;
          ask = {
            key: `mand-ok-${fmtQ(qMandTarget)}-${fmtQ(ev.qInSp)}`,
            q: `Puoi aumentare <strong>MP 11036 A/B</strong> / membrane a quanto serve `
              + `(≈ <strong class="fix-val">${fmtQ(qMandTarget)}</strong> / ≥ ${fmtQ(qMemTarget)})?`,
            yesHtml: `Regola <strong>MP 11036 → <span class="fix-val">${fmtQ(qMandTarget)} m³/h</span></strong>, `
              + `membrane ≥ <span class="fix-val">${fmtQ(qMemTarget)}</span>, poi P11011 ≥ `
              + `<span class="fix-val">${fmtQ(qPumpTarget)}</span>${hzBit}.`,
            noHtml: alt,
            hideAltOnNo: false,
          };
          if (!nearMand && !anomaly) {
            // gap medio: chiedi comunque, alt solo su No
            ask.hideAltOnNo = false;
          }
        }
      } else if (!ev.pumpOn) {
        anomaly = anomalyPump || (ev.qInSp >= 80 && qHavePump < 40);
        verdict = `Male: <strong>P11011 OFF</strong> con chimico a <strong>${fmtQ(ev.qInSp)} m³/h</strong>.`;
        action = `Metti in marcia <strong>P11011 a <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit} `
          + `(A10620 ≥ ${fmtBlockPct(ev.startSvuot)}, A10611 &lt; stop alto).`;
        if (anomaly) {
          fault = `Con ingresso ${fmtQ(ev.qInSp)} m³/h e scarico ~${fmtQ(qHavePump)} c’è un set/pompa sbagliata — `
            + `non scendere il chimico a zero: alza le P11011.`;
          alt = "";
          ask = {
            key: `p11off-anom-${fmtQ(qPumpTarget)}`,
            q: `Puoi portare <strong>P11011</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`,
            yesHtml: `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`,
            noHtml: `Allora verifica avaria/consensi P11011: con ingresso ${fmtQ(ev.qInSp)} non ha senso azzerare il chimico `
              + `se la pompa può esercire ≈ ${fmtQ(Math.min(qMax, qPumpTarget))} m³/h.`,
            hideAltOnNo: true,
          };
        } else {
          const qSafe = qInCapAtOut(ev.qOut, ev.qRecLive);
          alt = `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qSafe)} m³/h</strong> `
            + `(scarico attuale ${fmtQ(ev.qOut)} m³/h).`;
          ask = {
            key: `p11off-${fmtQ(qPumpTarget)}`,
            q: `Puoi mettere in marcia <strong>P11011</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`,
            yesHtml: `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`,
            noHtml: alt,
            hideAltOnNo: false,
          };
        }
      } else if (ev.deficit > 0.5) {
        if (qPumpTarget > qMax + 0.05) {
          const qInMaxPlant = qInCapAtPump(qMax);
          forceAlt = true;
          verdict = `Male: <strong>chimico troppo alto</strong> (${fmtQ(ev.qInSp)} m³/h) — `
            + `P11011 max ${fmtQ(qMax)} m³/h, servirebbero ≥ ${fmtQ(qPumpTarget)}.`;
          action = `Non puoi alzare abbastanza le P11011 (max <strong>${fmtQ(qMax)}</strong>).`;
          alt = `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qInMaxPlant)} m³/h</strong> `
            + `(P11011 a ${fmtQ(qMax)}, riciclo min ${Q_RECYCLE_MIN}).`;
          ask = null;
        } else if (anomalyPump) {
          anomaly = true;
          verdict = `Male: <strong>P11011 sottodimensionata</strong> — set <strong>${fmtQ(ev.qPumpSp)}</strong> `
            + `con ingresso ${fmtQ(ev.qInSp)} (serve ≥ <strong>${fmtQ(qPumpTarget)}</strong>).`;
          action = `Regola <strong>P11011 a <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
          fault = `Portata anomala (IN ${fmtQ(ev.qInSp)} vs P11011 ${fmtQ(qHavePump)}): `
            + `non abbassare il chimico — sposta la pompa al valore esercibile.`;
          alt = "";
          ask = {
            key: `p11-anom-${fmtQ(qPumpTarget)}-${fmtQ(ev.qPumpSp)}`,
            q: `Puoi aumentare <strong>P11011 A/B</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`,
            yesHtml: `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit} `
              + `e lascia il chimico a ${fmtQ(ev.qInSp)} m³/h.`,
            noHtml: `Allora c’è un limite/avaria sulla pompa: porta comunque P11011 al massimo esercibile `
              + `(fino a <span class="fix-val">${fmtQ(qMax)}</span>). Non azzerare il chimico per un set a ${fmtQ(ev.qPumpSp)}.`,
            hideAltOnNo: true,
          };
        } else {
          anomaly = false;
          verdict = `Male: <strong>P11011 bassa</strong> — ${fmtQ(ev.qPumpSp)} m³/h, serve ≥ <strong>${fmtQ(qPumpTarget)}</strong> `
            + `(manca ${fmtQ(ev.deficit)}).`;
          action = `Regola <strong>P11011 a <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
          const qSafe = Math.min(qInCapAtPump(ev.qPumpSp), qInCapAtOut(ev.qOut, ev.qRecLive));
          alt = nearPump
            ? `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qSafe)} m³/h</strong> `
              + `(lasciando P11011 a ${fmtQ(ev.qPumpSp)}).`
            : `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qSafe)} m³/h</strong> `
              + `solo se non puoi alzare le P11011.`;
          ask = {
            key: `p11-${fmtQ(qPumpTarget)}-${fmtQ(ev.qPumpSp)}`,
            q: `Puoi aumentare <strong>P11011 A/B</strong> a <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`,
            yesHtml: `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`,
            noHtml: alt,
            hideAltOnNo: false,
          };
        }
      } else {
        verdict = `Male: A10620 allo stop con portate quasi in pareggio `
          + `(IN ${fmtQ(ev.qInSp)} · P11011 ${fmtQ(ev.qPumpSp)}).`;
        action = `Tieni <strong>P11011 ≥ <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`;
        const qSafe = qInCapAtPump(Math.min(ev.qPumpSp, ev.qOut));
        alt = `Abbassa il chimico-fisico a ≤ <strong class="fix-val">${fmtQ(qSafe)} m³/h</strong>.`;
        ask = {
          key: `near-${fmtQ(qPumpTarget)}`,
          q: `Puoi alzare un filo le <strong>P11011</strong> a ≥ <strong class="fix-val">${fmtQ(qPumpTarget)} m³/h</strong>?`,
          yesHtml: `Regola <strong>P11011 → <span class="fix-val">${fmtQ(qPumpTarget)} m³/h</span></strong>${hzBit}.`,
          noHtml: alt,
          hideAltOnNo: false,
        };
      }

      const meta = `<div><strong>Al blocco</strong> · ${ev.tMin}′ di sim</div>
        <div>Ingresso: set <strong>${fmtQ(ev.qInSp)}</strong> · viva <strong>${fmtQ(ev.qInLive)} m³/h</strong></div>
        <div>Riciclo 11014: set <strong>${fmtQ(ev.qRecSp)}</strong> · viva <strong>${fmtQ(ev.qRecLive)}</strong></div>
        <div>P11011: set <strong>${fmtQ(ev.qPumpSp)}</strong> · scarico <strong>${fmtQ(ev.qOut)}</strong>${ev.pumpOn ? "" : " (OFF)"}</div>
        <div>MP 11036: set <strong>${fmtQ(ev.qMandSp)}</strong> · viva <strong>${fmtQ(ev.qMandLive)}</strong>${ev.run11036 ? "" : " (OFF)"}</div>
        <div>Membrane: set <strong>${fmtQ(ev.qMemSp)}</strong> · viva <strong>${fmtQ(ev.qMemLive)}</strong></div>
        <div>Ripresa chimico: A10620 ≤ <strong>${fmtBlockPct(ev.start)}</strong></div>`;

      const eq = `<strong>In sintesi</strong><br>${verdict}<br><br>${action}`
        + (alt ? `<br><br>${alt}` : "");
      return { chain, meta, verdict, action, alt, eq, ask, fault, forceAlt, anomaly };
    }

    function resetBlocchiPanelPos() {
      const panel = el("blocchiPanel");
      if (!panel) return;
      panel.classList.remove("is-dragging");
      panel.style.position = "";
      panel.style.left = "";
      panel.style.top = "";
      panel.style.margin = "";
      panel.style.transform = "";
    }

    function paintBlocchiExplain() {
      const body = el("blocchiBody");
      if (!body) return;
      const last = __chimicoBlockLog.length ? __chimicoBlockLog[__chimicoBlockLog.length - 1] : null;
      const blockedNow = !__chimicoAllowFill;
      const livNow = numOrNull("livelloAttuale");
      const startNow = numOrNull("startRiempA10620");
      const startV = startNow !== null ? startNow : 92;

      let html = "";
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
      } else if (__chimicoBlockCount === 0) {
        const qInSp = Math.max(0, num("qIn"));
        let qNeed = qInSp;
        try { qNeed = round1(pumpFloorForIngresso(qInSp)); } catch (_) { /* ok */ }
        const hzBit = hzBitForNeed(qNeed);
        const qSafe = round1(Math.max(0, qNeed - Q_RECYCLE_MIN));
        html += `<div class="block-action">Nessun blocco dal Reset.<br>`
          + `Con ingresso <strong>${fmtQ(qInSp)} m³/h</strong>, tieni <strong>P11011 ≥ <span class="fix-val">${fmtQ(qNeed)} m³/h</span></strong>${hzBit}.</div>`;
        html += `<div class="block-qa"><p>Se non puoi alzare le P11011, vuoi il set del chimico-fisico?</p>`
          + `<div class="block-qa-btns">`
          + `<button type="button" data-block-qa="yes"${__blockQaAnswer === "yes" ? ' class="is-picked"' : ""}>Sì</button>`
          + `<button type="button" data-block-qa="no"${__blockQaAnswer === "no" ? ' class="is-picked"' : ""}>No</button>`
          + `</div></div>`;
        if (__blockQaAnswer === "yes") {
          html += `<div class="block-alt">Chimico-fisico ≤ <strong class="fix-val">${fmtQ(qSafe)} m³/h</strong> `
            + `(riciclo min ${Q_RECYCLE_MIN}).</div>`;
        }
        __blockQaKey = `idle-${fmtQ(qInSp)}`;
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
    }

    function openBlocchiPopup() {
      resetBlocchiPanelPos();
      paintBlocchiExplain();
      openPopup("blocchi");
    }

    /** Avanza oscillazione lenta intorno al setpoint digitato (tipicamente ±1…2 m³/h, max ±2.5). */
    function advanceQInWobble(dtMin) {
      const set = Math.max(0, num("qIn"));
      if (set < 0.05) {
        __qInLive = 0;
        return;
      }
      if (!(__simPlaying || __simBusy)) {
        __qInLive = set;
        return;
      }
      const dt = Math.max(0.05, Number(dtMin) || 1);
      __qInWobblePhase += dt * (0.38 + Math.random() * 0.4);
      __qInWobbleBias += (Math.random() - 0.5) * 0.6 * dt;
      __qInWobbleBias = Math.max(-1.35, Math.min(1.35, __qInWobbleBias));
      const osc = Math.sin(__qInWobblePhase) * 1.1
        + Math.sin(__qInWobblePhase * 0.41 + 1.3) * 0.5;
      let live = set + osc + __qInWobbleBias;
      live = Math.max(set - 2.5, Math.min(set + 2.5, live));
      __qInLive = round1(Math.max(0, live));
    }

    function resetQInWobble() {
      __qInWobblePhase = Math.random() * Math.PI * 2;
      __qInWobbleBias = 0;
      __qInLive = null;
    }
    const isEditing = (id) => {
