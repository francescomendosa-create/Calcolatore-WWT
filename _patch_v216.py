# -*- coding: utf-8 -*-
from pathlib import Path

root = Path(r"C:\Users\franc\Documents\GitHub\Calcolatore-WWT")
path = root / "calcolatore-portate.html"
text = path.read_text(encoding="utf-8")
n = 0


def rep(old, new, label):
    global text, n
    if old not in text:
        raise SystemExit(f"MISSING: {label}\n---\n{old[:200]}")
    c = text.count(old)
    if c != 1:
        raise SystemExit(f"COUNT {c} for {label}")
    text = text.replace(old, new, 1)
    n += 1
    print("OK", label)


rep(">v215</span>", ">v216</span>", "build tag")

# Helper snapFlowClosed after paintFlowLive block / before commitFlow
rep(
    """    /** Aggiorna campo + occhio SVG con la portata viva (senza toccare il setpoint popup). */
    function paintFlowLive(id, v) {""",
    """    /** Azzera misura+desiderata (processo fermo): niente rampa che “manda” ancora ai livelli. */
    function snapFlowClosed(id) {
      const key = String(id || "");
      if (!key) return;
      __flowDesire[key] = 0;
      __flowAnimFrom[key] = 0;
      __flowAnimTo[key] = 0;
      try { paintFlowLive(key, 0); } catch (_) { __flowLive[key] = 0; }
    }

    /** Aggiorna campo + occhio SVG con la portata viva (senza toccare il setpoint popup). */
    function paintFlowLive(id, v) {""",
    "snapFlowClosed",
)

rep(
    """    /** A11004 pieno: non può ricevere altro liquido → scarico MBR bloccato. */
    function a11004IsFull(livHOpt) {
      const h = livHOpt != null && Number.isFinite(Number(livHOpt))
        ? Number(livHOpt)
        : (numOrNull("livelloAttualeH") ?? 90);
      return Number.isFinite(h) && h >= 99.95;
    }""",
    """    /** A11004 quasi pieno: non riceve più scarico MBR (prima era 99.95% → mai “pieno”, livelli eterni). */
    function a11004IsFull(livHOpt) {
      const h = livHOpt != null && Number.isFinite(Number(livHOpt))
        ? Number(livHOpt)
        : (numOrNull("livelloAttualeH") ?? 90);
      return Number.isFinite(h) && h >= 97 - 1e-9;
    }""",
    "a11004IsFull 97",
)

rep(
    """    function estimateA10611RatePctPerMin(qPump, qMandata) {
      // Solo portate EFFETTIVE: se MP 11036 ferme, out=0 (A10611 si riempie da P11011).
      // Mai usare il setpoint/rampa: altrimenti "210 fantasma" svuota/riempie a pompe rosse.
      const qInEff = Math.max(0, Number(qPump) || 0);
      const qOutEff = Math.max(0, Number(qMandata) || 0);
      if (qInEff < 0.05 && qOutEff < 0.05) return 0;
      const cal = getA10611Calib();
      const inR = cal.qPumpRef > 0 ? Math.max(0, qInEff / cal.qPumpRef) : 0;
      const outR = cal.qMandRef > 0 ? Math.max(0, qOutEff / cal.qMandRef) : 0;
      // inR=1,outR=0 → rateOff (sale); inR=1,outR=1 → rateOn (scende); tutto fermo → 0
      let r = inR * cal.rateOff + outR * (cal.rateOn - cal.rateOff);
      if (!Number.isFinite(r)) return 0;
      return Math.max(-RATE_PCT_CLAMP, Math.min(RATE_PCT_CLAMP, r));
    }""",
    """    function estimateA10611RatePctPerMin(qPump, qMandata) {
      // Solo portate EFFETTIVE: se MP 11036 ferme, out=0 (A10611 si riempie da P11011).
      // Mai usare il setpoint/rampa: altrimenti "210 fantasma" svuota/riempie a pompe rosse.
      const qInEff = Math.max(0, Number(qPump) || 0);
      const qOutEff = Math.max(0, Number(qMandata) || 0);
      if (qInEff < 0.05 && qOutEff < 0.05) return 0;
      const cal = getA10611Calib();
      const inR = cal.qPumpRef > 0 ? Math.max(0, qInEff / cal.qPumpRef) : 0;
      const outR = cal.qMandRef > 0 ? Math.max(0, qOutEff / cal.qMandRef) : 0;
      // inR=1,outR=0 → rateOff (sale); inR=1,outR=1 → rateOn (scende); tutto fermo → 0
      let r = inR * cal.rateOff + outR * (cal.rateOn - cal.rateOff);
      // Senza P11011 (qIn=0) A10611 NON può salire — solo restare o scendere con 11036.
      if (qInEff < 0.05 && r > 0) r = 0;
      if (!Number.isFinite(r)) return 0;
      return Math.max(-RATE_PCT_CLAMP, Math.min(RATE_PCT_CLAMP, r));
    }""",
    "estimateA10611 no fill without pump",
)

rep(
    """    function mbrScaricoToH(qMandata, qPerm, livMbrOpt, livHOpt) {
      if (a11004IsFull(livHOpt)) return 0;
      const qM = Math.max(0, Number(qMandata) || 0);
      const qP = Math.max(0, Number(qPerm) || 0);
      const excess = Math.max(0, qM - qP);
      return round1(excess * MBR_SCARICO_TO_H_FRAC);
    }""",
    """    function mbrScaricoToH(qMandata, qPerm, livMbrOpt, livHOpt) {
      if (a11004IsFull(livHOpt)) return 0;
      const h = livHOpt != null && Number.isFinite(Number(livHOpt))
        ? Number(livHOpt)
        : (numOrNull("livelloAttualeH") ?? 90);
      const qM = Math.max(0, Number(qMandata) || 0);
      const qP = Math.max(0, Number(qPerm) || 0);
      const excess = Math.max(0, qM - qP);
      // Vicino al pieno: riduci scarico → eccesso resta in MBR → sale a stop 11036
      let frac = MBR_SCARICO_TO_H_FRAC;
      if (Number.isFinite(h) && h >= 94) {
        frac *= Math.max(0, Math.min(1, (97 - h) / 3));
      }
      return round1(excess * frac);
    }""",
    "mbrScaricoToH taper",
)

rep(
    """      applyBalance("sim");
      const qInSet = num("qIn");
      const qIn = qInEffective(qInSet);
      // Marcia/arresto SEMPRE da livelli. Portate = MISURA (flowMeasureOf): live 0 resta 0.
      const qPump = flowMeasureOf("qPump");
      const qMandata = flowMeasureOf("qMandata");""",
    """      applyBalance("sim");
      const qInSet = num("qIn");
      const qIn = qInEffective(qInSet);
      // Processo fermo → misura a 0 SUBITO (niente rampa che riempie A10611 a P11011 rosse).
      if (pumpEstopped("pompa") || !p11011Allowed()) snapFlowClosed("qPump");
      if (pumpEstopped("mandata") || !__run11036) snapFlowClosed("qMandata");
      const qPump = flowMeasureOf("qPump");
      const qMandata = flowMeasureOf("qMandata");""",
    "simulateOneStep snap closed",
)

rep(
    """          if (!pumpOn && !isEditing("qPump")) {
            qPump = 0;
            commitFlow("qPump", 0, { instant: true });
            if (!isEditing("freqHz")) {
              const hzNode = el("freqHz");
              if (hzNode) hzNode.value = "0";
              const svgHz0 = el("svgFreqHz");
              if (svgHz0) svgHz0.textContent = "0";
            }
          }
        }""",
    """          if (!pumpOn && !isEditing("qPump")) {
            qPump = 0;
            snapFlowClosed("qPump");
            if (!isEditing("freqHz")) {
              const hzNode = el("freqHz");
              if (hzNode) hzNode.value = "0";
              const svgHz0 = el("svgFreqHz");
              if (svgHz0) svgHz0.textContent = "0";
            }
          }
        }""",
    "applyBalance snap qPump",
)

rep(
    """        if (!autoPump && !isEditing("qPump") && source !== "freq" && qFromFreqThisPass == null) {
          if (pumpOn) commitFlow("qPump", qPumpSet, { setpoint: qPumpSet });
          else commitFlow("qPump", 0, { setpoint: qPumpSet, instant: true });
        }""",
    """        if (!autoPump && !isEditing("qPump") && source !== "freq" && qFromFreqThisPass == null) {
          if (pumpOn) commitFlow("qPump", qPumpSet, { setpoint: qPumpSet });
          else {
            rememberFlowSetpoint("qPump", qPumpSet);
            snapFlowClosed("qPump");
          }
        }""",
    "manual snap qPump",
)

rep(
        """        if (!__run11036) {
          qMandata = 0;
          if (__flowLive.qMandata && __flowLive.qMandata > 0.05) {
            try { paintFlowLive("qMandata", 0); } catch (_) { /* ok */ }
          }
        }""",
        """        if (!__run11036) {
          qMandata = 0;
          snapFlowClosed("qMandata");
        }""",
    "snap qMandata when 11036 off",
)

rep(
    """        if (autoPump && !pumpOn) {
          if (!isEditing("qPump")) commitFlow("qPump", 0, { instant: true });
          qPumpEff2 = 0;
        }""",
    """        if (autoPump && !pumpOn) {
          if (!isEditing("qPump")) snapFlowClosed("qPump");
          qPumpEff2 = 0;
        }""",
    "qPumpEff2 snap",
)

rep(
    """      let net11 = round1(net11FromCalib);
      if (totAvg + 0.25 < qMandata) {
        net11 = round1(Math.max(net11, qMandata - totAvg));
      }""",
    """      let net11 = round1(net11FromCalib);
      // Override valle solo se P11011 manda davvero — altrimenti “sale” fantasma a pompe ferme
      if (qPump > 0.05 && totAvg + 0.25 < qMandata) {
        net11 = round1(Math.max(net11, qMandata - totAvg));
      }
      if (qPump < 0.05) net11 = Math.min(net11, 0);""",
    "net11 no phantom fill",
)

rep(
    """        updateLevelRangeUI(qInEff, qPumpEff2, qMandata, qRecycle, totAvg);""",
    """        updateLevelRangeUI(
          qInEff,
          flowMeasureOf("qPump"),
          flowMeasureOf("qMandata"),
          flowMeasureOf("qRecycle"),
          totAvg
        );""",
    "updateLevelRangeUI measures",
)

path.write_text(text, encoding="utf-8", newline="\n")
(root / "index.html").write_text(text, encoding="utf-8", newline="\n")

sw = root / "sw.js"
sw_text = sw.read_text(encoding="utf-8")
if "process-managed-sw-v215" not in sw_text:
    raise SystemExit("sw cache tag missing v215")
sw.write_text(
    sw_text.replace("process-managed-sw-v215", "process-managed-sw-v216", 1),
    encoding="utf-8",
    newline="\n",
)
print(f"DONE patches={n}")
