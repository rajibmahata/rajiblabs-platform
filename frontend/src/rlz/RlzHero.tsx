import { useEffect, useRef } from "react";
import { siteConfig } from "../config/site";
import { HERO_STATS } from "./data";
import { useLang } from "../i18n/langContext";

function useNeuralCanvas(canvasRef: React.RefObject<HTMLCanvasElement | null>) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let raf = 0;
    const mouse: { x: number | null; y: number | null } = { x: null, y: null };

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const count = Math.min(90, Math.floor(window.innerWidth / 14));
    const particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
    }));

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onOut = () => { mouse.x = null; mouse.y = null; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseout", onOut);

    const frame = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const isMobile = window.innerWidth < 768;
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(124, 58, 237, 0.35)";
        ctx.fill();
        if (mouse.x !== null && mouse.y !== null && !isMobile) {
          const dist = Math.hypot(mouse.x - p.x, mouse.y - p.y);
          if (dist < 180) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `rgba(6, 182, 212, ${0.3 * (1 - dist / 180)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dist = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(124, 58, 237, ${0.12 * (1 - dist / 120)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(frame);
    };
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduced) raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseout", onOut);
    };
  }, [canvasRef]);
}

function useTyping(textRef: React.RefObject<HTMLSpanElement | null>, phrases: string[]) {
  useEffect(() => {
    const el = textRef.current;
    if (!el || !phrases.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.textContent = phrases[0];
      return;
    }
    let phraseIdx = 0, charIdx = 0, deleting = false, timer = 0;
    const loop = () => {
      const current = phrases[phraseIdx % phrases.length];
      if (el) el.textContent = current.slice(0, charIdx);
      if (!deleting && charIdx < current.length) {
        charIdx++;
        timer = window.setTimeout(loop, 55);
      } else if (deleting && charIdx > 0) {
        charIdx--;
        timer = window.setTimeout(loop, 28);
      } else if (!deleting) {
        deleting = true;
        timer = window.setTimeout(loop, 1800);
      } else {
        deleting = false;
        phraseIdx = (phraseIdx + 1) % phrases.length;
        timer = window.setTimeout(loop, 400);
      }
    };
    timer = window.setTimeout(loop, 500);
    return () => window.clearTimeout(timer);
  }, [textRef, phrases]);
}

function useCounters(scopeRef: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = scopeRef.current;
    if (!root) return;
    const els = root.querySelectorAll<HTMLElement>(".rlz-counter");
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => { el.textContent = el.dataset.target ?? "0"; });
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const el = entry.target as HTMLElement;
          if (entry.isIntersecting && !el.dataset.done) {
            el.dataset.done = "1";
            const target = Number(el.dataset.target ?? 0);
            let count = 0;
            const step = Math.max(1, Math.ceil(target / 40));
            const timer = window.setInterval(() => {
              count += step;
              if (count >= target) { count = target; window.clearInterval(timer); }
              el.textContent = String(count);
            }, 40);
          }
        });
      },
      { threshold: 0.5 }
    );
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [scopeRef]);
}

export default function RlzHero({ scopeRef }: { scopeRef: React.RefObject<HTMLElement | null> }) {
  const { t, tArr } = useLang();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const typingRef = useRef<HTMLSpanElement | null>(null);
  useNeuralCanvas(canvasRef);
  useTyping(typingRef, tArr("hero.typing"));
  useCounters(scopeRef);
  const statLabels = [t("hero.statYears"), t("hero.statRepos"), t("hero.statProducts")];

  return (
    <section className="rlz-hero rlz-section" id="home" style={{ paddingTop: 160, paddingBottom: 80 }}>
      <canvas ref={canvasRef} className="rlz-neural-canvas" aria-hidden="true" />
      <div className="rlz-container">
        <div className="rlz-hero-grid">
          <div>
            <div className="rlz-hero-badge rlz-reveal">
              <span className="rlz-pulse-dot" />
              {t("hero.badge")}
            </div>
            <h1 className="rlz-reveal rlz-reveal-d1">
              {t("hero.titleA")}<br />
              <span className="rlz-grad-text">{t("hero.titleB")}</span><br />
              {t("hero.titleC")}
            </h1>
            <p className="rlz-hero-sub rlz-reveal rlz-reveal-d2">
              {t("hero.subtitle")}
            </p>
            <div className="rlz-typing-line rlz-reveal rlz-reveal-d2" aria-hidden="true">
              <span className="rlz-prompt">&gt;_</span> <span ref={typingRef} /> <span className="rlz-cursor" />
            </div>
            <div className="rlz-hero-actions rlz-reveal rlz-reveal-d3">
              <a href="#projects" className="rlz-btn rlz-btn-primary">
                {t("hero.explore")} <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
              </a>
              <a href="/Rajib-Mahata-Resume-2026.pdf" download className="rlz-btn rlz-btn-ghost">
                <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>download</i> {t("hero.resume")}
              </a>
            </div>
            <div className="rlz-hero-stats rlz-reveal rlz-reveal-d4">
              {HERO_STATS.map((s, i) => (
                <div className="rlz-stat" key={s.label}>
                  <h3><span className="rlz-counter" data-target={s.value}>0</span>{s.suffix}</h3>
                  <p>{statLabels[i] ?? s.label}</p>
                </div>
              ))}
            </div>
            <p className="rlz-mono rlz-reveal rlz-reveal-d4" style={{ fontSize: "0.78rem", color: "var(--rlz-text-faint)", marginTop: 28 }}>
              {siteConfig.contact.email} · {siteConfig.contact.phone}
            </p>
          </div>

          <div className="rlz-reveal rlz-reveal-d2">
            <div className="rlz-terminal" role="img" aria-label="Terminal showing AI deployment status">
              <div className="rlz-terminal-bar">
                <span className="rlz-dot r" /><span className="rlz-dot y" /><span className="rlz-dot g" />
                <span>rajiblabs — ai-architect</span>
              </div>
              <div className="rlz-terminal-body">
                <div><span className="rlz-t-dim">$</span> <span className="rlz-t-cyan">rajib</span> <span className="rlz-t-dim">deploy --stack=&quot;ai-native&quot;</span></div>
                <div><span className="rlz-t-violet">▶</span> Initializing neural pipeline...</div>
                <div><span className="rlz-t-green">✓</span> LLM integration layer <span className="rlz-t-dim">[ready]</span></div>
                <div><span className="rlz-t-green">✓</span> Microservices mesh <span className="rlz-t-dim">[ready]</span></div>
                <div><span className="rlz-t-green">✓</span> Event-driven core <span className="rlz-t-dim">[ready]</span></div>
                <div className="rlz-terminal-output">
                  <span className="rlz-t-fuchsia">◆ systems.status()</span> → <span className="rlz-t-green">&quot;All intelligent systems operational. Building the future, one architecture at a time.&quot;</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
