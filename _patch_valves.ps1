$ErrorActionPreference = "Stop"
$path = Join-Path $PSScriptRoot "calcolatore-portate.html"
$utf8 = New-Object System.Text.UTF8Encoding $false
$c = [System.IO.File]::ReadAllText($path, $utf8)

# --- 1) HTML REGOLAZIONI §0b ---
$marker = 'id="regTk11021GeomHint"'
$idx = $c.IndexOf($marker)
if ($idx -lt 0) { throw "marker regTk11021GeomHint not found" }
$closeDiv = $c.IndexOf("</div>", $idx)
if ($closeDiv -lt 0) { throw "close div after TK11021 not found" }
# find the end of the geom section (first </div> after hint closes the settings-block)
# Actually structure: <p hint></p> then </div> closes settings-block
$afterHintP = $c.IndexOf("</p>", $idx)
$blockEnd = $c.IndexOf("</div>", $afterHintP)
if ($blockEnd -lt 0) { throw "geom block end not found" }

$insertAfter = $blockEnd + 6
$already = $c.IndexOf('id="regValvoleQ"')
if ($already -ge 0) {
  Write-Host "HTML section already present — skip insert"
} else {
  $section = @"

      <!-- 0b. Valvole regolazione portata UF / osmosi -->
      <div class="settings-block show" id="regValvoleQ">
        <h4>0b · Valvole regolazione portata (UF / osmosi)</h4>
        <p class="mini">A <strong>100%</strong> di apertura la linea eroga la portata qui indicata (dato di impianto). L'apertura di lavoro è proporzionale: <strong>% ≈ (setpoint ÷ Q@100%) × 100</strong>. Se l'ingresso è inferiore al set, la valvola sale al <strong>100%</strong> e la misura resta limitata dall'acqua disponibile — comportamento normale del regolatore. Il PROCESSO e lo schema leggono questi valori.</p>
        <div class="row">
          <label><strong>UF A–D · portata a valvola 100% (m³/h)</strong>
            <input type="number" id="regUfValveQ100" min="1" max="200" step="0.1" value="65" inputmode="decimal" />
          </label>
          <label><strong>Osmosi A–C · portata a valvola 100% (m³/h)</strong>
            <input type="number" id="regOsmValveQ100" min="1" max="200" step="0.1" value="80" inputmode="decimal" />
          </label>
        </div>
        <p class="mini" id="regValvoleQHint">Esempio UF @ 65: set 45 m³/h → apertura ≈ 69% (45÷65). Se l'ingresso linea &lt; set, valvola → 100% senza raggiungere il set.</p>
      </div>
"@
  $c = $c.Substring(0, $insertAfter) + $section + $c.Substring($insertAfter)
  Write-Host "Inserted REGOLAZIONI §0b HTML"
}

# --- 2) Replace constants with defaults + getters will be added near geom getters ---
$oldConst = @'
    const UF_VALVE_Q100 = 60;    // m³/h a valvola 100% (apertura di progetto per linea)
    const __ufValvePct = { A: 0, B: 0, C: 0, D: 0 };
    const __ufMeas = { A: 0, B: 0, C: 0, D: 0 }; // portata misurata (display lineare)
    const __ufValveTarget = { A: 0, B: 0, C: 0, D: 0 };
    const __ufMeasTarget = { A: 0, B: 0, C: 0, D: 0 };
    const __ufWobble = {
      A: { phase: Math.random() * Math.PI * 2, bias: 0 },
      B: { phase: Math.random() * Math.PI * 2, bias: 0 },
      C: { phase: Math.random() * Math.PI * 2, bias: 0 },
      D: { phase: Math.random() * Math.PI * 2, bias: 0 },
    };
    const OSM_LINES = ["A", "B", "C"];
    const OSM_VALVE_Q100 = 80;   // m³/h a valvola 100% per linea osmosi
    const __osmValvePct = { A: 0, B: 0, C: 0 };
'@

$newConst = @'
    /** Default da REGOLAZIONI §0b: UF 65 m³/h @ 100% · Osmosi 80 m³/h @ 100% */
    const UF_VALVE_Q100_DEFAULT = 65;
    const OSM_VALVE_Q100_DEFAULT = 80;
    const __ufValvePct = { A: 0, B: 0, C: 0, D: 0 };
    const __ufMeas = { A: 0, B: 0, C: 0, D: 0 }; // portata misurata (display lineare)
    const __ufValveTarget = { A: 0, B: 0, C: 0, D: 0 };
    const __ufMeasTarget = { A: 0, B: 0, C: 0, D: 0 };
    const __ufWobble = {
      A: { phase: Math.random() * Math.PI * 2, bias: 0 },
      B: { phase: Math.random() * Math.PI * 2, bias: 0 },
      C: { phase: Math.random() * Math.PI * 2, bias: 0 },
      D: { phase: Math.random() * Math.PI * 2, bias: 0 },
    };
    const OSM_LINES = ["A", "B", "C"];
    const __osmValvePct = { A: 0, B: 0, C: 0 };
'@

if ($c.Contains($oldConst)) {
  $c = $c.Replace($oldConst, $newConst)
  Write-Host "Replaced UF/OSM valve constants"
} elseif ($c.Contains("UF_VALVE_Q100_DEFAULT")) {
  Write-Host "Constants already updated — skip"
} else {
  throw "UF_VALVE_Q100 block not found"
}

# --- 3) Add getter functions after getTk11021Geom ---
$getterAnchor = @'
    function getTk11021Geom() {
      let V = numOrNull("regTk11021Vutile");
      if (V === null || V < 0.5) V = 30;
      return { V: Math.max(0.5, V) };
    }
'@

$getterBlock = @'
    function getTk11021Geom() {
      let V = numOrNull("regTk11021Vutile");
      if (V === null || V < 0.5) V = 30;
      return { V: Math.max(0.5, V) };
    }

    /** Portata max per linea UF a valvola 100% — da REGOLAZIONI §0b (default 65). */
    function ufValveQ100() {
      let q = numOrNull("regUfValveQ100");
      if (q === null || q < 1) q = UF_VALVE_Q100_DEFAULT;
      return Math.max(1, q);
    }

    /** Portata max per linea osmosi a valvola 100% — da REGOLAZIONI §0b (default 80). */
    function osmValveQ100() {
      let q = numOrNull("regOsmValveQ100");
      if (q === null || q < 1) q = OSM_VALVE_Q100_DEFAULT;
      return Math.max(1, q);
    }

    /** Apertura teorica (%) per raggiungere il setpoint, clamp 0–100. */
    function valveOpenPctForSet(setM3h, qAt100) {
      const q100 = Math.max(1, Number(qAt100) || 1);
      const sp = Math.max(0, Number(setM3h) || 0);
      return Math.max(0, Math.min(100, (sp / q100) * 100));
    }

    function refreshValvoleQHint() {
      const ufQ = ufValveQ100();
      const osmQ = osmValveQ100();
      const hint = el("regValvoleQHint");
      if (!hint) return;
      const ex = 45;
      const pct = Math.round(valveOpenPctForSet(ex, ufQ));
      hint.textContent = "Esempio UF @ " + ufQ.toFixed(1).replace(/\.0$/, "") +
        ": set " + ex + " m³/h → apertura ≈ " + pct + "% (" + ex + "÷" +
        ufQ.toFixed(1).replace(/\.0$/, "") + "). Osmosi Q@100% = " +
        osmQ.toFixed(1).replace(/\.0$/, "") + " m³/h. Se ingresso linea < set, valvola → 100% senza raggiungere il set.";
    }
'@

if ($c.Contains("function ufValveQ100()")) {
  Write-Host "Getters already present — skip"
} elseif ($c.Contains($getterAnchor)) {
  $c = $c.Replace($getterAnchor, $getterBlock)
  Write-Host "Inserted ufValveQ100 / osmValveQ100 getters"
} else {
  throw "getTk11021Geom anchor not found"
}

# --- 4) Wire hint into refreshTankGeomHints ---
$oldRefreshStart = "function refreshTankGeomHints() {"
$refreshIdx = $c.IndexOf($oldRefreshStart)
if ($refreshIdx -lt 0) { throw "refreshTankGeomHints not found" }
# Find first line with try or const g20 after function
$insertHintCall = "function refreshTankGeomHints() {`r`n      try { refreshValvoleQHint(); } catch (_) { /* ignore */ }"
# Check if already wired
$slice = $c.Substring($refreshIdx, 200)
if ($slice -match "refreshValvoleQHint") {
  Write-Host "refreshValvoleQHint already wired — skip"
} else {
  $c = $c.Substring(0, $refreshIdx) + $insertHintCall + $c.Substring($refreshIdx + $oldRefreshStart.Length)
  Write-Host "Wired refreshValvoleQHint into refreshTankGeomHints"
}

# --- 5) Replace UF_VALVE_Q100 / OSM_VALVE_Q100 usages in regulation ---
$c2 = $c
$c2 = $c2.Replace("const ff = (sp / UF_VALVE_Q100) * 100;", "const q100 = ufValveQ100();`r`n          const ff = valveOpenPctForSet(sp, q100);")
$c2 = $c2.Replace("const qHyd = Math.min(share, UF_VALVE_Q100 * (Math.max(0, valveTarget) / 100));", "const qHyd = Math.min(share, q100 * (Math.max(0, valveTarget) / 100));")
# Fix: q100 must be in scope for qHyd — the starved branch doesn't define q100.
# Better rewrite tickUfRegulationOnce valve section more carefully.

# Revert naive replace if we did partial — check
if ($c2 -ne $c) {
  $c = $c2
  Write-Host "Updated UF valve formula references (pass 1)"
}

# Osmosi: need q100 in scope similarly
$c = $c.Replace("const ff = (sp / OSM_VALVE_Q100) * 100;", "const q100 = osmValveQ100();`r`n          const ff = valveOpenPctForSet(sp, q100);")
$c = $c.Replace("const qHyd = Math.min(share, OSM_VALVE_Q100 * (Math.max(0, valveTarget) / 100));", "const qHyd = Math.min(share, q100 * (Math.max(0, valveTarget) / 100));")
Write-Host "Updated OSM valve formula references"

# Fix starved branch: q100 undefined when starved=true then qHyd uses q100
# In tickUfRegulationOnce:
# if (starved) { valveTarget = 100; } else { const q100 = ... }
# then qHyd uses q100 — BROKEN for starved case
# Fix by defining q100 before the if

$brokenUf = @'
        const share = ufLineShare(L);
        const starved = share + 0.35 < sp || share < 0.05;
        let valveTarget;
        if (starved) {
          valveTarget = 100;
        } else {
          const q100 = ufValveQ100();
          const ff = valveOpenPctForSet(sp, q100);
          const err = sp - measNow;
          valveTarget = ff + err * 14;
          if (measNow + 0.4 < sp) valveTarget = Math.max(valveTarget, ff + 8);
          valveTarget = Math.max(10, Math.min(100, valveTarget));
        }

        // Target portata dal target valvola (non dalla % ancora in rampa), cosí la Q sale subito in lineare.
        const qHyd = Math.min(share, q100 * (Math.max(0, valveTarget) / 100));
'@

# The encoding of "così" may vary — search a smaller unique pattern
$ufSharePat = '        const share = ufLineShare(L);'
$ufShareIdx = $c.IndexOf($ufSharePat)
if ($ufShareIdx -lt 0) { throw "ufLineShare block not found" }

# Find from share to __ufValveTarget assignment and replace whole block
$ufTargetPat = '        __ufValveTarget[L] = Math.max(0, Math.min(100, valveTarget));'
$ufTargetIdx = $c.IndexOf($ufTargetPat, $ufShareIdx)
if ($ufTargetIdx -lt 0) { throw "ufValveTarget assign not found" }

$ufBlockNew = @'
        const share = ufLineShare(L);
        const q100 = ufValveQ100();
        const starved = share + 0.35 < sp || share < 0.05;
        let valveTarget;
        if (starved) {
          // Ingresso < set: la valvola si apre al massimo cercando il set (non lo raggiunge).
          valveTarget = 100;
        } else {
          // Feed-forward: % = set / Q@100% · poi correzione sull'errore misura.
          const ff = valveOpenPctForSet(sp, q100);
          const err = sp - measNow;
          valveTarget = ff + err * 14;
          if (measNow + 0.4 < sp) valveTarget = Math.max(valveTarget, ff + 8);
          valveTarget = Math.max(10, Math.min(100, valveTarget));
        }

        // Target portata dal target valvola (non dalla % ancora in rampa), così la Q sale subito in lineare.
        const qHyd = Math.min(share, q100 * (Math.max(0, valveTarget) / 100));
'@

# Keep from qAim onward — find qAim after share
$qAimIdx = $c.IndexOf('        let qAim = qHyd;', $ufShareIdx)
if ($qAimIdx -lt 0 -or $qAimIdx -gt $ufTargetIdx) { throw "qAim not found in UF block" }
$c = $c.Substring(0, $ufShareIdx) + $ufBlockNew + $c.Substring($qAimIdx)
Write-Host "Rewrote UF regulation valve block with q100 in scope"

# Same for osmosi
$osmSharePat = '        const share = osmLineShare(L);'
$osmShareIdx = $c.IndexOf($osmSharePat)
if ($osmShareIdx -lt 0) { throw "osmLineShare block not found" }
$osmQAimIdx = $c.IndexOf('        let qAim = qHyd;', $osmShareIdx)
if ($osmQAimIdx -lt 0) { throw "osm qAim not found" }

$osmBlockNew = @'
        const share = osmLineShare(L);
        const q100 = osmValveQ100();
        const starved = share + 0.35 < sp || share < 0.05;
        let valveTarget;
        if (starved) {
          valveTarget = 100;
        } else {
          const ff = valveOpenPctForSet(sp, q100);
          const err = sp - measNow;
          valveTarget = ff + err * 14;
          if (measNow + 0.4 < sp) valveTarget = Math.max(valveTarget, ff + 8);
          valveTarget = Math.max(10, Math.min(100, valveTarget));
        }

        const qHyd = Math.min(share, q100 * (Math.max(0, valveTarget) / 100));
'@
$c = $c.Substring(0, $osmShareIdx) + $osmBlockNew + $c.Substring($osmQAimIdx)
Write-Host "Rewrote OSM regulation valve block with q100 in scope"

# --- 6) Persist + input listeners ---
$oldPersist = '"regTk11021Vutile",'
$newPersist = '"regTk11021Vutile",' + "`r`n      `"regUfValveQ100`", `"regOsmValveQ100`","
# Appears twice (listeners + persist fields) — replace all
$countBefore = ([regex]::Matches($c, [regex]::Escape($oldPersist))).Count
$c = $c.Replace($oldPersist, $newPersist)
Write-Host "Updated persist/listener lists ($countBefore occurrences)"

# Also UF popup mini hint
$ufHintOld = '<p class="mini">Quattro ingressi A–D. La somma = totale. Variando il totale si ripartiscono in modo uguale sulle <strong>abilitate</strong>; variando una linea si aggiorna il totale.</p>'
$ufHintNew = '<p class="mini">Quattro ingressi A–D. La somma = totale. Variando il totale si ripartiscono in modo uguale sulle <strong>abilitate</strong>; variando una linea si aggiorna il totale.</p>
      <p class="mini">Apertura valvola da REGOLAZIONI: % ≈ set ÷ Q@100% (default <strong>65 m³/h</strong> a 100%). Se l''ingresso &lt; set, la valvola va al 100% e non raggiunge la portata desiderata.</p>'
if ($c.Contains($ufHintOld) -and -not $c.Contains("Apertura valvola da REGOLAZIONI")) {
  $c = $c.Replace($ufHintOld, $ufHintNew)
  Write-Host "Added UF popup hint"
} else {
  Write-Host "UF popup hint skip/already"
}

# Safety: leftover bare UF_VALVE_Q100 / OSM_VALVE_Q100 (not DEFAULT)
$leftoverUf = ([regex]::Matches($c, '(?<![A-Z_])UF_VALVE_Q100(?!_DEFAULT)')).Count
$leftoverOsm = ([regex]::Matches($c, '(?<![A-Z_])OSM_VALVE_Q100(?!_DEFAULT)')).Count
Write-Host "Leftover UF_VALVE_Q100=$leftoverUf OSM_VALVE_Q100=$leftoverOsm"

[System.IO.File]::WriteAllText($path, $c, $utf8)
Copy-Item -Path $path -Destination (Join-Path $PSScriptRoot "index.html") -Force
Write-Host "Wrote calcolatore-portate.html and synced index.html"
Write-Host "DONE"
