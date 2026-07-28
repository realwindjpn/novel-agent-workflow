/* ANSI -> HTML for the _visual.py palette, and the relay waveform strip. */
(function () {
  "use strict";

  var ANSI_CLASS = {
    "0": null, "1": "a-bold", "2": "a-dim",
    "31": "a-red", "32": "a-green", "33": "a-yellow",
    "34": "a-blue", "35": "a-magenta", "36": "a-cyan",
    "1;31": "a-bred", "1;32": "a-bgreen", "1;33": "a-byellow", "1;36": "a-bcyan"
  };

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
  }

  /* Convert a string with ANSI SGR codes to HTML spans. */
  function ansiToHtml(src) {
    var out = [];
    var open = false;
    var re = /\x1b\[([0-9;]*)m/g;
    var last = 0, m;
    while ((m = re.exec(src)) !== null) {
      out.push(escapeHtml(src.slice(last, m.index)));
      var code = m[1] || "0";
      if (open) { out.push("</span>"); open = false; }
      var cls = ANSI_CLASS[code];
      if (cls) { out.push('<span class="' + cls + '">'); open = true; }
      last = re.lastIndex;
    }
    out.push(escapeHtml(src.slice(last)));
    if (open) out.push("</span>");
    return out.join("");
  }

  /* ---------------- relay waveform ----------------
   * Baseline slow-breathing carrier; each command run injects a pulse
   * packet that sweeps left -> right; release fires a long burst. */
  function Waveform(canvas) {
    this.cv = canvas;
    this.cx = canvas.getContext("2d");
    this.pulses = [];
    this.t0 = performance.now();
    this.reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this._resize = this.resize.bind(this);
    window.addEventListener("resize", this._resize);
    this.resize();
    if (this.reduced) { this.draw(); return; }
    var self = this;
    function frame() { self.draw(); requestAnimationFrame(frame); }
    requestAnimationFrame(frame);
  }
  Waveform.prototype.resize = function () {
    var dpr = window.devicePixelRatio || 1;
    var w = this.cv.clientWidth, h = this.cv.clientHeight;
    this.cv.width = w * dpr; this.cv.height = h * dpr;
    this.cx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = w; this.h = h;
  };
  Waveform.prototype.pulse = function (strength) {
    if (this.reduced) return;       // skip animation under reduced motion
    this.pulses.push({ start: performance.now(), amp: strength || 1 });
    if (this.pulses.length > 12) this.pulses.shift();
  };
  Waveform.prototype.draw = function () {
    var cx = this.cx, w = this.w, h = this.h, mid = h / 2;
    var now = performance.now();
    var t = (now - this.t0) / 1000;
    cx.clearRect(0, 0, w, h);

    // faint graticule
    cx.strokeStyle = "rgba(26,36,54,0.7)";
    cx.lineWidth = 1;
    cx.beginPath();
    cx.moveTo(0, mid); cx.lineTo(w, mid);
    cx.stroke();

    // carrier: slow breathing sine
    cx.beginPath();
    for (var x = 0; x <= w; x += 2) {
      var y = mid + Math.sin(x * 0.018 + t * 0.7) * 2.2 * Math.sin(t * 0.23);
      if (x === 0) cx.moveTo(x, y); else cx.lineTo(x, y);
    }
    cx.strokeStyle = "rgba(61,90,110,0.55)";
    cx.stroke();

    // pulses
    this.pulses = this.pulses.filter(function (p) { return now - p.start < 2600; });
    for (var i = 0; i < this.pulses.length; i++) {
      var p = this.pulses[i];
      var age = (now - p.start) / 2600;           // 0..1
      var head = age * (w + 160) - 80;            // sweep position
      var fade = 1 - age;
      cx.beginPath();
      for (var x2 = 0; x2 <= w; x2 += 2) {
        var d = (x2 - head) / 46;
        var env = Math.exp(-d * d) * fade * p.amp;
        var y2 = mid + Math.sin(x2 * 0.35 + t * 22) * 13 * env;
        if (x2 === 0) cx.moveTo(x2, y2); else cx.lineTo(x2, y2);
      }
      cx.strokeStyle = "rgba(57,213,192," + (0.85 * fade).toFixed(3) + ")";
      cx.lineWidth = 1.6;
      cx.stroke();
      cx.lineWidth = 1;
    }
  };

  window.NWA = { ansiToHtml: ansiToHtml, escapeHtml: escapeHtml, Waveform: Waveform };
})();
