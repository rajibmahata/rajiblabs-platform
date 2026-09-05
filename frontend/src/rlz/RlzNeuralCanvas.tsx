import { useEffect, useRef } from "react";

/**
 * Full-page neural canvas — fixed background for the entire homepage.
 * Mirrors the vanilla-JS design: 80-100 particles, 120px link radius,
 * 180px mouse radius, DPR-aware, pause on hidden tab, reduced-motion.
 */
export default function RlzNeuralCanvas() {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let W = 0;
    let H = 0;
    let parts: { x: number; y: number; vx: number; vy: number; r: number }[] = [];
    let raf = 0;
    let mx: number | null = null;
    let my: number | null = null;

    const seed = () => {
      const count = Math.min(100, Math.floor((W * H) / 15000));
      parts = Array.from({ length: count }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.7 + 0.6,
      }));
    };

    const draw = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);
      // move
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
      }
      // inter-particle
      ctx.lineWidth = 1;
      for (let i = 0; i < parts.length; i++) {
        const a = parts[i];
        for (let j = i + 1; j < parts.length; j++) {
          const b = parts[j];
          const d = Math.hypot(a.x - b.x, a.y - b.y);
          if (d < 120) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(124,58,237,${(0.12 * (1 - d / 120)).toFixed(3)})`;
            ctx.stroke();
          }
        }
      }
      // mouse
      if (mx !== null && my !== null) {
        for (let i = 0; i < parts.length; i++) {
          const a = parts[i];
          const d = Math.hypot(a.x - mx, a.y - my);
          if (d < 180) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(mx, my);
            ctx.strokeStyle = `rgba(6,182,212,${(0.3 * (1 - d / 180)).toFixed(3)})`;
            ctx.stroke();
          }
        }
      }
      // dots
      for (let i = 0; i < parts.length; i++) {
        const a = parts[i];
        ctx.beginPath();
        ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(124,58,237,0.35)";
        ctx.fill();
      }
    };

    const loop = () => {
      draw();
      raf = requestAnimationFrame(loop);
    };

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
      if (reduced) draw();
    };

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
    };
    const onLeave = () => {
      mx = null;
      my = null;
    };
    const onVis = () => {
      if (document.hidden) {
        if (raf) {
          cancelAnimationFrame(raf);
          raf = 0;
        }
      } else if (!reduced && !raf) {
        loop();
      }
    };

    window.addEventListener("resize", resize);
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseleave", onLeave);
    document.addEventListener("visibilitychange", onVis);
    resize();
    if (!reduced) loop();

    return () => {
      if (raf) cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseleave", onLeave);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return <canvas ref={ref} className="rlz-neural-canvas" aria-hidden="true" />;
}
