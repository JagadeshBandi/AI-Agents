"use client";

import { useEffect, useRef } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

interface CVDoc {
  x: number;
  y: number;
  w: number;
  h: number;
  speed: number;
  alpha: number;
  scale: number;
  scaleDelta: number;
  rotation: number;
}

interface KWParticle {
  text: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  alpha: number;
  maxAlpha: number;
  size: number;
  colorBase: string;
  life: number;
  maxLife: number;
}

interface Laser {
  y: number;
  vy: number;
  alpha: number;
  colorBase: string;
}

interface Connector {
  cvIdx: number;
  kwIdx: number;
  alpha: number;
  life: number;
  maxLife: number;
}

// ── Constants ────────────────────────────────────────────────────────────────

const KEYWORDS = [
  "Python", "React", "FastAPI", "ATS Passed",
  "SEEK", "Indeed", "Docker", "Leadership",
  "PostgreSQL", "TypeScript", "✓ Submitted", "✓ Matched",
  "Autopilot ON", "Node.js", "AWS", "Reed.co.uk",
];

const KW_COLORS = [
  "99,102,241",   // indigo
  "139,92,246",   // violet
  "34,211,238",   // cyan
  "148,163,184",  // slate
  "99,102,241",   // indigo (weighted heavier)
];

const NUM_CVS = 22;
const NUM_KWS = 14;

// ── Helpers ──────────────────────────────────────────────────────────────────

const rand = (min: number, max: number) => min + Math.random() * (max - min);

function makeCVDoc(W: number, H: number, spreadY = true): CVDoc {
  return {
    x: rand(0, W),
    y: spreadY ? rand(-H, H) : H + rand(40, 120),
    w: rand(52, 84),
    h: rand(70, 110),
    speed: rand(0.14, 0.32),
    alpha: rand(0.055, 0.14),
    scale: rand(0.75, 1.15),
    scaleDelta: (Math.random() > 0.5 ? 1 : -1) * rand(0.0001, 0.0003),
    rotation: rand(-0.14, 0.14),
  };
}

function makeKWParticle(W: number, H: number, text: string): KWParticle {
  const maxAlpha = rand(0.14, 0.34);
  return {
    text,
    x: rand(0, W),
    y: rand(H * 0.1, H * 0.9),
    vx: rand(-0.18, 0.18),
    vy: rand(-0.18, -0.08),
    alpha: 0,
    maxAlpha,
    size: rand(10, 20),
    colorBase: KW_COLORS[Math.floor(Math.random() * KW_COLORS.length)],
    life: rand(0, 200),
    maxLife: rand(280, 480),
  };
}

// ── Rounded rect (polyfill for browsers without ctx.roundRect) ───────────────

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number,
  w: number, h: number,
  r: number,
) {
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
  } else {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }
}

// ── Draw routines ─────────────────────────────────────────────────────────────

function drawBackground(ctx: CanvasRenderingContext2D, W: number, H: number) {
  const g = ctx.createLinearGradient(0, 0, W * 0.7, H);
  g.addColorStop(0,    "#070b16");
  g.addColorStop(0.45, "#0b1122");
  g.addColorStop(0.75, "#090e1c");
  g.addColorStop(1,    "#060a15");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  // Subtle centre radial glow
  const glow = ctx.createRadialGradient(W * 0.5, H * 0.42, 0, W * 0.5, H * 0.42, W * 0.55);
  glow.addColorStop(0,   "rgba(99,102,241,0.045)");
  glow.addColorStop(0.5, "rgba(99,102,241,0.012)");
  glow.addColorStop(1,   "rgba(99,102,241,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);
}

function drawGrid(ctx: CanvasRenderingContext2D, W: number, H: number) {
  const vx = W * 0.5, vy = H * 0.42;

  for (let i = 0; i <= 20; i++) {
    const endX = (i / 20) * W * 1.4 - W * 0.2;
    ctx.strokeStyle = "rgba(99,102,241,0.042)";
    ctx.lineWidth = 0.7;
    ctx.beginPath();
    ctx.moveTo(vx, vy);
    ctx.lineTo(endX, H);
    ctx.stroke();
  }

  for (const t of [0.56, 0.65, 0.74, 0.83, 0.93]) {
    ctx.strokeStyle = "rgba(59,130,246,0.028)";
    ctx.lineWidth = 0.6;
    ctx.beginPath();
    ctx.moveTo(0, H * t);
    ctx.lineTo(W, H * t);
    ctx.stroke();
  }
}

function drawCV(ctx: CanvasRenderingContext2D, cv: CVDoc) {
  ctx.save();
  ctx.translate(cv.x, cv.y);
  ctx.rotate(cv.rotation);
  ctx.scale(cv.scale, cv.scale);
  ctx.globalAlpha = cv.alpha;

  const hw = cv.w / 2, hh = cv.h / 2;

  roundRect(ctx, -hw, -hh, cv.w, cv.h, 4);
  ctx.fillStyle = "rgba(255,255,255,0.92)";
  ctx.fill();
  ctx.strokeStyle = "rgba(160,160,185,0.55)";
  ctx.lineWidth = 0.5;
  ctx.stroke();

  // Avatar circle
  ctx.fillStyle = "#b0bec5";
  ctx.beginPath();
  ctx.arc(-hw + 13, -hh + 13, 7, 0, Math.PI * 2);
  ctx.fill();

  // Name lines
  ctx.fillStyle = "#94a3b8";
  ctx.fillRect(-hw + 26, -hh + 8,  cv.w * 0.44, 4);
  ctx.fillRect(-hw + 26, -hh + 15, cv.w * 0.30, 3);

  // Content stubs
  const stubW = [0.70, 0.52, 0.80, 0.60, 0.72, 0.45, 0.65];
  const stubY = -hh + 30;
  for (let i = 0; i < stubW.length; i++) {
    if (stubY + i * 8.5 > hh - 6) break;
    ctx.fillStyle = i < 2 ? "#94a3b8" : "#dde3ea";
    ctx.fillRect(-hw + 7, stubY + i * 8.5, (cv.w - 14) * stubW[i], 3.5);
  }

  ctx.restore();
}

function drawKeyword(ctx: CanvasRenderingContext2D, kw: KWParticle) {
  ctx.save();
  ctx.globalAlpha = kw.alpha;
  ctx.font = `700 ${kw.size}px 'Courier New', monospace`;
  ctx.fillStyle = `rgba(${kw.colorBase},1)`;
  ctx.fillText(kw.text, kw.x, kw.y);
  ctx.restore();
}

function drawLaser(ctx: CanvasRenderingContext2D, laser: Laser, W: number) {
  const g = ctx.createLinearGradient(0, laser.y, W, laser.y);
  g.addColorStop(0,    `rgba(${laser.colorBase},0)`);
  g.addColorStop(0.18, `rgba(${laser.colorBase},${laser.alpha})`);
  g.addColorStop(0.5,  `rgba(${laser.colorBase},${laser.alpha * 1.7})`);
  g.addColorStop(0.82, `rgba(${laser.colorBase},${laser.alpha})`);
  g.addColorStop(1,    `rgba(${laser.colorBase},0)`);

  ctx.save();
  ctx.strokeStyle = g;
  ctx.lineWidth = 1;
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.moveTo(0, laser.y);
  ctx.lineTo(W, laser.y);
  ctx.stroke();
  // Soft glow halo
  ctx.lineWidth = 5;
  ctx.globalAlpha = 0.10;
  ctx.stroke();
  ctx.restore();
}

function drawConnector(
  ctx: CanvasRenderingContext2D,
  conn: Connector,
  cvs: CVDoc[],
  kws: KWParticle[],
  tick: number,
) {
  const cv = cvs[conn.cvIdx];
  const kw = kws[conn.kwIdx];
  if (!cv || !kw) return;

  const progress = conn.life / conn.maxLife;
  const fade =
    progress < 0.2  ? progress / 0.2 :
    progress > 0.8  ? (1 - progress) / 0.2 :
    1;

  const cpx = (cv.x + kw.x) / 2;
  const cpy = (cv.y + kw.y) / 2 - 70;

  ctx.save();
  ctx.globalAlpha = conn.alpha * fade;
  ctx.strokeStyle = "rgba(99,102,241,0.55)";
  ctx.lineWidth = 0.8;
  ctx.setLineDash([4, 9]);
  ctx.lineDashOffset = -(tick * 0.5);
  ctx.beginPath();
  ctx.moveTo(cv.x, cv.y);
  ctx.quadraticCurveTo(cpx, cpy, kw.x, kw.y);
  ctx.stroke();
  ctx.restore();
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function AutomationBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf: number;
    let W = 0, H = 0;

    const resize = () => {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const cvs: CVDoc[]      = Array.from({ length: NUM_CVS }, () => makeCVDoc(W, H, true));
    const kws: KWParticle[] = Array.from({ length: NUM_KWS }, (_, i) =>
      makeKWParticle(W, H, KEYWORDS[i % KEYWORDS.length])
    );

    const lasers: Laser[] = [
      { y: H * 0.28, vy:  0.28, alpha: 0.22, colorBase: "99,102,241" },
      { y: H * 0.62, vy: -0.18, alpha: 0.16, colorBase: "34,211,238" },
      { y: H * 0.80, vy:  0.12, alpha: 0.10, colorBase: "139,92,246" },
    ];

    const connectors: Connector[] = [];
    let connTimer = 0;
    let tick = 0;

    const spawnConnector = () => {
      if (connectors.length < 7) {
        connectors.push({
          cvIdx:   Math.floor(Math.random() * NUM_CVS),
          kwIdx:   Math.floor(Math.random() * NUM_KWS),
          alpha:   0,
          life:    0,
          maxLife: rand(160, 320),
        });
      }
    };

    const frame = () => {
      tick++;
      ctx.clearRect(0, 0, W, H);

      drawBackground(ctx, W, H);
      drawGrid(ctx, W, H);

      for (const cv of cvs) {
        cv.y -= cv.speed;
        cv.scale += cv.scaleDelta;
        if (cv.scale > 1.18 || cv.scale < 0.72) cv.scaleDelta *= -1;
        if (cv.y < -cv.h - 20) {
          cv.y = H + cv.h + rand(0, 80);
          cv.x = rand(0, W);
        }
        drawCV(ctx, cv);
      }

      for (const laser of lasers) {
        laser.y += laser.vy;
        if (laser.y > H + 10) laser.y = -10;
        if (laser.y < -10)    laser.y = H + 10;
        drawLaser(ctx, laser, W);
      }

      for (const kw of kws) {
        kw.life++;
        kw.x += kw.vx;
        kw.y += kw.vy;

        const p = kw.life / kw.maxLife;
        kw.alpha =
          p < 0.15 ? (p / 0.15) * kw.maxAlpha :
          p > 0.82 ? ((1 - p) / 0.18) * kw.maxAlpha :
          kw.maxAlpha;

        if (kw.life >= kw.maxLife) {
          Object.assign(kw, makeKWParticle(W, H, KEYWORDS[Math.floor(Math.random() * KEYWORDS.length)]));
        }

        drawKeyword(ctx, kw);
      }

      connTimer++;
      if (connTimer % 85 === 0) spawnConnector();

      for (let i = connectors.length - 1; i >= 0; i--) {
        const c = connectors[i];
        c.life++;
        c.alpha = Math.min(c.alpha + 0.018, 0.5);
        if (c.life >= c.maxLife) {
          connectors.splice(i, 1);
        } else {
          drawConnector(ctx, c, cvs, kws, tick);
        }
      }

      raf = requestAnimationFrame(frame);
    };

    raf = requestAnimationFrame(frame);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 -z-10 w-full h-full pointer-events-none"
    />
  );
}
