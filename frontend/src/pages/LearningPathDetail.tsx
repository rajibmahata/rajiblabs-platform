import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import Markdown from "../components/Markdown";
import "../rlz/rlz.css";

type Block = {
  day_number: number;
  status: string;
  topic?: string;
  title?: string;
  learning_objective: string;
  why_matters: string;
  real_world_example?: string;
  simple_explanation?: string;
  concept_explanation: string;
  step_by_step?: string[];
  practical_example?: string;
  examples?: { title: string; code: string; explanation: string; expected_output?: string }[];
  try_it_yourself?: string;
  common_mistakes?: string[];
  exercise: string;
  homework?: string;
  challenge?: string;
  quick_review?: string[];
  what_you_can_do_now?: string[];
  questions?: string[];
  next_preview?: string;
};

type PathData = {
  slug: string;
  topic: string;
  duration: number;
  goal?: string;
  level?: string;
  progress?: number;
  current_day?: number;
  prerequisites?: string[];
  roadmap?: { day: number; title: string; objective: string; why_matters: string }[];
};

export default function LearningPathDetail() {
  const { slug = "" } = useParams<{ slug: string }>();
  const [path, setPath] = useState<PathData | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [activeDay, setActiveDay] = useState<number>(1);
  const [progress, setProgress] = useState<{ progress: number } | null>(null);
  const [error, setError] = useState(false);
  const [loadedSlug, setLoadedSlug] = useState<string | null>(null);

  const loading = loadedSlug !== slug;

  useEffect(() => {
    let cancelled = false;
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    Promise.all([
      fetch(`${base}/api/learning/paths/${slug}`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch(`${base}/api/learning/paths/${slug}/blocks`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
    ])
      .then(([pathRes, blocksRes]) => {
        if (cancelled) return;
        if (!pathRes) { setError(true); setLoadedSlug(slug); return; }
        setPath(pathRes);
        const arr = Array.isArray(blocksRes) ? blocksRes : [];
        setBlocks(arr);
        const firstPublished = arr.find((b: Block) => b.status === "published");
        if (firstPublished) setActiveDay(firstPublished.day_number);
        else if (arr[0]) setActiveDay(arr[0].day_number);
        setLoadedSlug(slug);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoadedSlug(slug);
      });
    return () => { cancelled = true; };
  }, [slug]);

  const markProgress = useCallback(async (day: number, done: boolean) => {
    const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
    const r = await fetch(`${base}/api/learning/paths/${slug}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ day, exercise_done: done }),
    });
    const j = await r.json().catch(() => null);
    if (j) setProgress(j);
  }, [slug]);

  if (loading) {
    return (
      <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh" }}>
        <div className="rlz-page-bg" /><div className="rlz-bg-grid" />
        <div className="rlz-container rlz-ld-hero">
          <div style={{ display: "grid", gap: 12, maxWidth: 500 }}>
            <div style={{ height: 18, width: 120, background: "var(--rlz-bg-2)", borderRadius: 8 }} />
            <div style={{ height: 36, width: "80%", background: "var(--rlz-bg-2)", borderRadius: 10 }} />
            <div style={{ height: 16, width: "60%", background: "var(--rlz-bg-2)", borderRadius: 6 }} />
          </div>
        </div>
      </div>
    );
  }

  if (error || !path) {
    return (
      <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh" }}>
        <div className="rlz-page-bg" /><div className="rlz-bg-grid" />
        <div className="rlz-container rlz-ld-empty" style={{ minHeight: "60vh", display: "grid", placeItems: "center" }}>
          <div>
            <i className="material-symbols-outlined">error_outline</i>
            <p>Learning path not found.</p>
            <Link to="/learning" className="rlz-btn rlz-btn-ghost" style={{ marginTop: 16, display: "inline-flex", textDecoration: "none" }}>← All Learning</Link>
          </div>
        </div>
      </div>
    );
  }

  const block = blocks.find((b) => b.day_number === activeDay);
  const currentIdx = blocks.findIndex((b) => b.day_number === activeDay);
  const prevDay = currentIdx > 0 ? blocks[currentIdx - 1].day_number : null;
  const nextDay = currentIdx < blocks.length - 1 ? blocks[currentIdx + 1].day_number : null;
  const publishedCount = blocks.filter((b) => b.status === "published").length;

  return (
    <div className="rlz" style={{ background: "var(--rlz-bg)", minHeight: "100vh" }}>
      <div className="rlz-page-bg" /><div className="rlz-bg-grid" />

      {/* Hero */}
      <section className="rlz-ld-hero">
        <div className="rlz-container">
          <Link to="/learning" className="rlz-ld-breadcrumb">
            <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_back</i> All Learning
          </Link>

          <h1 style={{ fontFamily: "'Sora', sans-serif", fontSize: "clamp(1.8rem, 4vw, 2.6rem)", letterSpacing: "-0.02em" }}>
            {path.topic}
          </h1>
          <p style={{ color: "var(--rlz-text-dim)", maxWidth: 720, fontSize: "1.02rem", marginTop: 4 }}>
            {path.goal || "Mentor-guided progression through daily lessons."}
          </p>

          <div className="rlz-ld-hero-meta">
            <span className="rlz-chip" style={{ background: "var(--rlz-bg-2)", border: "1px solid var(--rlz-border)" }}>
              <i className="material-symbols-outlined" style={{ fontSize: "0.85rem", marginRight: 2 }}>schedule</i>
              {path.duration} Days
            </span>
            {path.level && (
              <span className="rlz-chip" style={{ background: "var(--rlz-violet-soft)", color: "var(--rlz-violet)", border: "none" }}>
                {path.level}
              </span>
            )}
            <span className="rlz-chip" style={{ background: "rgba(16,185,129,0.1)", color: "var(--rlz-green)", border: "1px solid rgba(16,185,129,0.2)" }}>
              {publishedCount}/{path.duration} lessons ready
            </span>
          </div>

          <div className="rlz-ld-progress-bar">
            <div className="rlz-learning-progress-track" style={{ flex: 1 }}>
              <div className="rlz-learning-progress-fill" style={{ width: `${path.progress || 0}%` }} />
            </div>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem", color: "var(--rlz-text-faint)" }}>
              {path.progress || 0}%
            </span>
          </div>
        </div>
      </section>

      <div className="rlz-container" style={{ paddingBottom: 60 }}>
        {/* Prerequisites */}
        {path.prerequisites && path.prerequisites.length > 0 && (
          <div className="rlz-ld-section" style={{ marginTop: 10 }}>
            <h3>
              <i className="material-symbols-outlined">checklist</i> Prerequisites
            </h3>
            <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
              {path.prerequisites.map((p, i) => (
                <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7 }}>{p}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Roadmap overview */}
        {path.roadmap && path.roadmap.length > 0 && (
          <div className="rlz-ld-section" style={{ marginTop: 14 }}>
            <h3>
              <i className="material-symbols-outlined">map</i> Learning Roadmap
            </h3>
            <div style={{ display: "grid", gap: 6, marginTop: 6 }}>
              {path.roadmap.map((r) => {
                const isPublished = blocks.some((b) => b.day_number === r.day && b.status === "published");
                const isCurrent = r.day === activeDay;
                return (
                  <button
                    key={r.day}
                    onClick={() => setActiveDay(r.day)}
                    style={{
                      display: "flex", alignItems: "center", gap: 12, width: "100%",
                      padding: "10px 14px", borderRadius: 10, border: "1px solid",
                      borderColor: isCurrent ? "var(--rlz-violet)" : "var(--rlz-border)",
                      background: isCurrent ? "var(--rla-violet-soft)" : "var(--rla-surface)",
                      cursor: "pointer", textAlign: "left", transition: "all 0.2s",
                    }}
                  >
                    <span style={{
                      width: 28, height: 28, borderRadius: 8, display: "grid", placeItems: "center",
                      fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72rem", fontWeight: 700,
                      background: isPublished ? "var(--rlz-green)" : isCurrent ? "var(--rlz-violet)" : "var(--rlz-bg-2)",
                      color: isPublished || isCurrent ? "#fff" : "var(--rlz-text-faint)",
                      flexShrink: 0,
                    }}>
                      {isPublished ? "✓" : r.day}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--rlz-text)" }}>{r.title}</div>
                      <div style={{ fontSize: "0.78rem", color: "var(--rlz-text-faint)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.objective}</div>
                    </div>
                    {isCurrent && <i className="material-symbols-outlined" style={{ fontSize: "1rem", color: "var(--rlz-violet)" }}>chevron_right</i>}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Day navigation chips */}
        <div className="rlz-ld-day-nav">
          {blocks.map((b) => {
            const isActive = b.day_number === activeDay;
            const isDone = b.status === "published" && b.day_number < activeDay;
            return (
              <button
                key={b.day_number}
                onClick={() => setActiveDay(b.day_number)}
                className={`rlz-ld-day-btn${isActive ? " rlz-ld-active" : ""}${isDone ? " rlz-ld-done" : ""}`}
              >
                Day {b.day_number}
              </button>
            );
          })}
        </div>

        {/* Block content */}
        {!block ? (
          <div className="rlz-ld-empty">
            <i className="material-symbols-outlined">hourglass_empty</i>
            <p>No published lesson for this day yet — the agent generates daily at 06:30 IST.</p>
            <Link to="/learning" className="rlz-btn rlz-btn-ghost" style={{ marginTop: 16, display: "inline-flex", textDecoration: "none" }}>← Back to Learning</Link>
          </div>
        ) : (
          <article className="rlz-ld-article">
            {/* Day header */}
            <div className="rlz-section-tag" style={{ marginBottom: 8 }}>
              <i className="material-symbols-outlined">auto_stories</i> Day {block.day_number} — {block.topic || block.title}
            </div>

            {/* What you will learn + Why this matters */}
            <div className="rlz-ld-section" style={{ marginTop: 0, background: "rgba(124,58,237,0.04)", borderColor: "rgba(124,58,237,0.15)" }}>
              <h3>
                <i className="material-symbols-outlined">flag</i> What you will learn
              </h3>
              <p style={{ fontWeight: 600, color: "var(--rlz-text)", fontSize: "1rem" }}>{block.learning_objective}</p>
              <h4 style={{ marginTop: 12, fontSize: "0.88rem", color: "var(--rla-text-dim)", display:"flex", gap:6, alignItems:"center"}}><i className="material-symbols-outlined" style={{fontSize:"1rem"}}>favorite</i> Why this matters</h4>
              <p style={{ marginTop: 4, color:"var(--rla-text-dim)" }}>{block.why_matters}</p>
            </div>

            {/* Real-world example - FIRST, before theory */}
            {block.real_world_example && (
              <div className="rlz-ld-section" style={{ background: "rgba(8,145,178,0.06)", borderColor:"rgba(8,145,178,0.18)"}}>
                <h3>
                  <i className="material-symbols-outlined">public</i> Real-world example
                </h3>
                <p style={{ lineHeight:1.75 }}>{block.real_world_example}</p>
              </div>
            )}

            {/* Simple explanation */}
            <div className="rlz-ld-section">
              <h3>
                <i className="material-symbols-outlined">lightbulb</i> Simple explanation
              </h3>
              <div style={{ lineHeight: 1.75 }}>
                <Markdown text={block.simple_explanation || block.concept_explanation || ""} />
              </div>
              {block.concept_explanation && block.simple_explanation && block.concept_explanation !== block.simple_explanation && (
                <div style={{ marginTop:14, padding:"12px 14px", background:"var(--rla-bg)", border:"1px solid var(--rla-border)", borderRadius:10 }}>
                  <h4 style={{fontSize:"0.85rem", fontWeight:600, marginBottom:6}}>A bit deeper</h4>
                  <div style={{ lineHeight:1.7}}><Markdown text={block.concept_explanation} /></div>
                </div>
              )}
              {!!block.step_by_step?.length && (
                <div style={{marginTop:14}}>
                  <h4 style={{fontSize:"0.88rem", fontWeight:600, display:"flex", gap:6, alignItems:"center"}}><i className="material-symbols-outlined" style={{fontSize:"1rem", color:"var(--rla-cyan)"}}>format_list_numbered</i> Step-by-step</h4>
                  <ol style={{ marginLeft: 18, marginTop: 8, paddingLeft: 0 }}>
                    {block.step_by_step.map((s, i) => (
                      <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7, marginBottom: 6 }}><span style={{fontWeight:600, color:"var(--rla-text)"}}>{i+1}.</span> {s}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>

            {/* Practical example description */}
            {block.practical_example && (
              <div className="rlz-ld-section">
                <h3>
                  <i className="material-symbols-outlined">visibility</i> Practical example
                </h3>
                <p style={{ lineHeight:1.75 }}>{block.practical_example}</p>
              </div>
            )}

            {/* Code Examples */}
            {!!block.examples?.length && block.examples.some(e=>e.code?.trim()) && (
              <div className="rlz-ld-section">
                <h3>
                  <i className="material-symbols-outlined">code</i> Code — see it run
                </h3>
                {block.examples.filter(e=>e.code?.trim()).map((ex, i) => (
                  <div key={i} className="rlz-ld-code-block">
                    <span className="rlz-ld-code-label">{ex.title}</span>
                    <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{ex.code}</pre>
                    {ex.explanation && <div className="rlz-ld-code-explain"><b>How it works:</b> {ex.explanation}</div>}
                    {ex.expected_output && (
                      <div className="rlz-ld-code-output">▶ Expected: {ex.expected_output}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Try it yourself */}
            {block.try_it_yourself && (
              <div className="rlz-ld-section" style={{background:"rgba(16,185,129,0.06)", borderColor:"rgba(16,185,129,0.18)"}}>
                <h3>
                  <i className="material-symbols-outlined">touch_app</i> Try it yourself
                </h3>
                <p style={{ lineHeight:1.7 }}>{block.try_it_yourself}</p>
              </div>
            )}

            {/* Common mistakes */}
            {!!block.common_mistakes?.length && (
              <div className="rlz-ld-section" style={{borderLeft:"3px solid var(--rla-amber)"}}>
                <h3 style={{color:"var(--rla-amber)"}}>
                  <i className="material-symbols-outlined">warning</i> Common mistakes
                </h3>
                <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
                  {block.common_mistakes.map((m, i) => (
                    <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7 }}>{m}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Exercise */}
            <div className="rlz-ld-exercise" style={{marginTop:24}}>
              <h3>
                <i className="material-symbols-outlined">fitness_center</i> Exercise — your turn
              </h3>
              <p>{block.exercise}</p>
              {progress ? (
                <div className="rlz-ld-exercise-done">
                  <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>check_circle</i>
                  Completed — Progress {progress.progress}%
                </div>
              ) : (
                <button
                  onClick={() => markProgress(block.day_number, true)}
                  className="rlz-btn rlz-btn-primary"
                  style={{ marginTop: 12, fontSize: "0.88rem", padding: "10px 22px" }}
                >
                  <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>check</i> Mark Exercise Done
                </button>
              )}
            </div>

            {/* Homework + Challenge */}
            {(block.homework || block.challenge) && (
              <div style={{ display: "grid", gap: 14, marginTop: 24 }}>
                {block.homework && (
                  <div className="rlz-ld-section" style={{background:"rgba(251,191,36,0.06)", borderColor:"rgba(251,191,36,0.25)"}}>
                    <h3>
                      <i className="material-symbols-outlined">edit_note</i> Homework
                    </h3>
                    <p>{block.homework}</p>
                  </div>
                )}
                {block.challenge && (
                  <div className="rlz-ld-section">
                    <h3>
                      <i className="material-symbols-outlined">emoji_events</i> Challenge (optional)
                    </h3>
                    <p>{block.challenge}</p>
                  </div>
                )}
              </div>
            )}

            {/* Quick recap */}
            {!!block.quick_review?.length && (
              <div className="rlz-ld-section">
                <h3>
                  <i className="material-symbols-outlined">replay</i> Quick recap
                </h3>
                <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
                  {block.quick_review.map((q, i) => (
                    <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7 }}>{q}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* What you can do now */}
            {!!block.what_you_can_do_now?.length && (
              <div className="rlz-ld-section" style={{background:"rgba(16,185,129,0.06)", borderColor:"rgba(16,185,129,0.2)"}}>
                <h3 style={{color:"var(--rla-green)"}}>
                  <i className="material-symbols-outlined">verified</i> What you can do now
                </h3>
                <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
                  {block.what_you_can_do_now.map((w, i) => (
                    <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7 }}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Questions */}
            {!!block.questions?.length && (
              <div className="rlz-ld-section">
                <h3>
                  <i className="material-symbols-outlined">quiz</i> Check yourself
                </h3>
                <ul style={{ margin: "6px 0 0", paddingLeft: 20 }}>
                  {block.questions.map((q, i) => (
                    <li key={i} style={{ color: "var(--rlz-text-dim)", fontSize: "0.92rem", lineHeight: 1.7 }}>{q}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next preview */}
            {block.next_preview && (
              <div style={{ marginTop: 20, padding: "14px 18px", background: "var(--rlz-bg)", border: "1px dashed var(--rlz-border)", borderRadius: 12 }}>
                <p style={{ color: "var(--rlz-text-dim)", fontSize: "0.88rem", margin: 0 }}>
                  <strong style={{ color: "var(--rlz-violet)" }}>Next — Day {block.day_number + 1}:</strong> {block.next_preview}
                </p>
              </div>
            )}

            {/* Footer navigation */}
            <div className="rlz-ld-footer-nav">
              {prevDay ? (
                <button onClick={() => setActiveDay(prevDay)} className="rlz-ld-footer-btn rlz-ld-prev">
                  <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_back</i> Day {prevDay}
                </button>
              ) : <span />}
              {nextDay ? (
                <button onClick={() => setActiveDay(nextDay)} className="rlz-ld-footer-btn rlz-ld-next">
                  Day {nextDay} <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>arrow_forward</i>
                </button>
              ) : (
                <Link to="/learning" className="rlz-ld-footer-btn rlz-ld-next" style={{ textDecoration: "none" }}>
                  <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>school</i> All Learning
                </Link>
              )}
            </div>
          </article>
        )}
      </div>
    </div>
  );
}
