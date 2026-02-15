(function () {
  "use strict";

  function throttle(func, limit) {
    var lastCall = 0;
    return function throttled() {
      var now = performance.now();
      if (now - lastCall >= limit) {
        lastCall = now;
        func.apply(this, arguments);
      }
    };
  }

  function hexToRgb(hex) {
    var match = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (!match) return { r: 0, g: 0, b: 0 };
    return {
      r: parseInt(match[1], 16),
      g: parseInt(match[2], 16),
      b: parseInt(match[3], 16),
    };
  }

  function DotGrid(target, options) {
    this.target = target;
    this.opts = Object.assign(
      {
        dotSize: 16,
        gap: 32,
        baseColor: "#5227FF",
        activeColor: "#5227FF",
        proximity: 150,
        speedTrigger: 100,
        shockRadius: 250,
        shockStrength: 5,
        maxSpeed: 5000,
        resistance: 750,
        returnDuration: 1.5,
      },
      options || {}
    );

    this.wrapper = null;
    this.canvas = null;
    this.ctx = null;
    this.dots = [];
    this.rafId = 0;
    this.resizeObserver = null;

    this.pointer = {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      speed: 0,
      lastTime: 0,
      lastX: 0,
      lastY: 0,
    };

    this.baseRgb = hexToRgb(this.opts.baseColor);
    this.activeRgb = hexToRgb(this.opts.activeColor);
    this.circlePath = null;
    if (window.Path2D) {
      this.circlePath = new Path2D();
      this.circlePath.arc(0, 0, this.opts.dotSize / 2, 0, Math.PI * 2);
    }

    this.onMouseMove = null;
    this.onClick = null;
    this.onResize = null;
  }

  DotGrid.prototype.buildGrid = function () {
    if (!this.wrapper || !this.canvas || !this.ctx) return;

    var rect = this.wrapper.getBoundingClientRect();
    var width = rect.width;
    var height = rect.height;
    var dpr = window.devicePixelRatio || 1;

    this.canvas.width = Math.max(1, Math.floor(width * dpr));
    this.canvas.height = Math.max(1, Math.floor(height * dpr));
    this.canvas.style.width = width + "px";
    this.canvas.style.height = height + "px";

    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);

    var cols = Math.floor((width + this.opts.gap) / (this.opts.dotSize + this.opts.gap));
    var rows = Math.floor((height + this.opts.gap) / (this.opts.dotSize + this.opts.gap));
    cols = Math.max(cols, 1);
    rows = Math.max(rows, 1);

    var cell = this.opts.dotSize + this.opts.gap;
    var gridW = cell * cols - this.opts.gap;
    var gridH = cell * rows - this.opts.gap;
    var startX = (width - gridW) / 2 + this.opts.dotSize / 2;
    var startY = (height - gridH) / 2 + this.opts.dotSize / 2;

    var dots = [];
    for (var y = 0; y < rows; y += 1) {
      for (var x = 0; x < cols; x += 1) {
        dots.push({
          cx: startX + x * cell,
          cy: startY + y * cell,
          xOffset: 0,
          yOffset: 0,
          _inertiaApplied: false,
        });
      }
    }

    this.dots = dots;
    this.width = width;
    this.height = height;
  };

  DotGrid.prototype.draw = function () {
    if (!this.ctx || !this.canvas) return;

    this.ctx.clearRect(0, 0, this.width, this.height);
    var px = this.pointer.x;
    var py = this.pointer.y;
    var proxSq = this.opts.proximity * this.opts.proximity;

    for (var i = 0; i < this.dots.length; i += 1) {
      var dot = this.dots[i];
      var ox = dot.cx + dot.xOffset;
      var oy = dot.cy + dot.yOffset;
      var dx = dot.cx - px;
      var dy = dot.cy - py;
      var dsq = dx * dx + dy * dy;

      var style = this.opts.baseColor;
      if (dsq <= proxSq) {
        var dist = Math.sqrt(dsq);
        var t = 1 - dist / this.opts.proximity;
        var r = Math.round(this.baseRgb.r + (this.activeRgb.r - this.baseRgb.r) * t);
        var g = Math.round(this.baseRgb.g + (this.activeRgb.g - this.baseRgb.g) * t);
        var b = Math.round(this.baseRgb.b + (this.activeRgb.b - this.baseRgb.b) * t);
        style = "rgb(" + r + "," + g + "," + b + ")";
      }

      this.ctx.save();
      this.ctx.translate(ox, oy);
      this.ctx.fillStyle = style;
      if (this.circlePath) {
        this.ctx.fill(this.circlePath);
      } else {
        this.ctx.beginPath();
        this.ctx.arc(0, 0, this.opts.dotSize / 2, 0, Math.PI * 2);
        this.ctx.fill();
      }
      this.ctx.restore();
    }

    this.rafId = requestAnimationFrame(this.draw.bind(this));
  };

  DotGrid.prototype.initEvents = function () {
    var self = this;

    var onMove = function (e) {
      if (!self.canvas) return;
      var now = performance.now();
      var dt = self.pointer.lastTime ? now - self.pointer.lastTime : 16;
      var dx = e.clientX - self.pointer.lastX;
      var dy = e.clientY - self.pointer.lastY;

      var vx = (dx / dt) * 1000;
      var vy = (dy / dt) * 1000;
      var speed = Math.hypot(vx, vy);
      if (speed > self.opts.maxSpeed) {
        var scale = self.opts.maxSpeed / speed;
        vx *= scale;
        vy *= scale;
        speed = self.opts.maxSpeed;
      }

      self.pointer.lastTime = now;
      self.pointer.lastX = e.clientX;
      self.pointer.lastY = e.clientY;
      self.pointer.vx = vx;
      self.pointer.vy = vy;
      self.pointer.speed = speed;

      var rect = self.canvas.getBoundingClientRect();
      self.pointer.x = e.clientX - rect.left;
      self.pointer.y = e.clientY - rect.top;

      for (var i = 0; i < self.dots.length; i += 1) {
        var dot = self.dots[i];
        var dist = Math.hypot(dot.cx - self.pointer.x, dot.cy - self.pointer.y);
        if (
          speed > self.opts.speedTrigger &&
          dist < self.opts.proximity &&
          !dot._inertiaApplied
        ) {
          dot._inertiaApplied = true;
          window.gsap.killTweensOf(dot);
          var pushX = dot.cx - self.pointer.x + vx * 0.005;
          var pushY = dot.cy - self.pointer.y + vy * 0.005;
          window.gsap.to(dot, {
            inertia: { xOffset: pushX, yOffset: pushY, resistance: self.opts.resistance },
            onComplete: (function (targetDot) {
              return function () {
                window.gsap.to(targetDot, {
                  xOffset: 0,
                  yOffset: 0,
                  duration: self.opts.returnDuration,
                  ease: "elastic.out(1,0.75)",
                  onComplete: function () {
                    targetDot._inertiaApplied = false;
                  },
                });
              };
            })(dot),
          });
        }
      }
    };

    var onClick = function (e) {
      if (!self.canvas) return;
      var rect = self.canvas.getBoundingClientRect();
      var cx = e.clientX - rect.left;
      var cy = e.clientY - rect.top;

      for (var i = 0; i < self.dots.length; i += 1) {
        var dot = self.dots[i];
        var dist = Math.hypot(dot.cx - cx, dot.cy - cy);
        if (dist < self.opts.shockRadius && !dot._inertiaApplied) {
          dot._inertiaApplied = true;
          window.gsap.killTweensOf(dot);
          var falloff = Math.max(0, 1 - dist / self.opts.shockRadius);
          var pushX = (dot.cx - cx) * self.opts.shockStrength * falloff;
          var pushY = (dot.cy - cy) * self.opts.shockStrength * falloff;
          window.gsap.to(dot, {
            inertia: { xOffset: pushX, yOffset: pushY, resistance: self.opts.resistance },
            onComplete: (function (targetDot) {
              return function () {
                window.gsap.to(targetDot, {
                  xOffset: 0,
                  yOffset: 0,
                  duration: self.opts.returnDuration,
                  ease: "elastic.out(1,0.75)",
                  onComplete: function () {
                    targetDot._inertiaApplied = false;
                  },
                });
              };
            })(dot),
          });
        }
      }
    };

    this.onMouseMove = throttle(onMove, 50);
    this.onClick = onClick;
    this.onResize = this.buildGrid.bind(this);

    window.addEventListener("mousemove", this.onMouseMove, { passive: true });
    window.addEventListener("click", this.onClick);

    if ("ResizeObserver" in window) {
      this.resizeObserver = new ResizeObserver(this.onResize);
      this.resizeObserver.observe(this.wrapper);
    } else {
      window.addEventListener("resize", this.onResize);
    }
  };

  DotGrid.prototype.mount = function () {
    if (!this.target) return;
    if (!window.gsap || !window.InertiaPlugin) {
      console.error("DotGrid requires GSAP and InertiaPlugin.");
      return;
    }

    window.gsap.registerPlugin(window.InertiaPlugin);

    this.target.innerHTML =
      '<div class="dot-grid"><div class="dot-grid__wrap"><canvas class="dot-grid__canvas"></canvas></div></div>';

    this.wrapper = this.target.querySelector(".dot-grid__wrap");
    this.canvas = this.target.querySelector(".dot-grid__canvas");
    this.ctx = this.canvas.getContext("2d");
    if (!this.wrapper || !this.canvas || !this.ctx) return;

    this.buildGrid();
    this.initEvents();
    this.draw();
  };

  function mountBackground() {
    var target = document.getElementById("dotGridBackground");
    if (!target) return;

    var grid = new DotGrid(target, {
      dotSize: 5,
      gap: 15,
      baseColor: "#271E37",
      activeColor: "#5227FF",
      proximity: 120,
      shockRadius: 250,
      shockStrength: 5,
      resistance: 750,
      returnDuration: 1.5,
    });
    grid.mount();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountBackground);
  } else {
    mountBackground();
  }
})();
