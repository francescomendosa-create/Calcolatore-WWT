const fs = require("fs");
const path = "index.html";
let s = fs.readFileSync(path, "utf8");
const iFn = s.indexOf("    function forecastChimicoHorizon(horizonMin, opts) {");
const i1 = s.indexOf("    function maxQinSafeForHorizon(horizonMin, opts) {");
// include the comment block before forecast
let i0 = s.lastIndexOf("    /**", iFn);
if (i0 < 0 || iFn < 0 || i1 <= iFn) {
  console.error("markers", i0, iFn, i1);
  process.exit(1);
}
console.log("ok markers", i0, iFn, i1, "len", i1-i0);
