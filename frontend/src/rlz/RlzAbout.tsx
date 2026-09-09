import { useEffect, useState } from "react";
import { siteConfig } from "../config/site";

type Profile = {
  fullName?: string; title?: string; bio?: string; headline?: string;
  location?: string; email?: string; phone?: string;
  socialLinks?: { github?: string; linkedin?: string };
  linkedIn?: string; gitHub?: string; website?: string;
  profileImageUrl?: string; skills?: string[]; career?: unknown[];
};

export default function RlzAbout() {
  const [p, setP] = useState<Profile | null>(null);

  useEffect(() => {
    fetch("/api/profile")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d && (d.fullName || d.bio)) setP(d); })
      .catch(() => {});
  }, []);

  const name = p?.fullName || siteConfig.owner;
  const title = p?.title || siteConfig.tagline;
  const bio = p?.bio || "";
  const github = p?.socialLinks?.github || p?.gitHub || siteConfig.social.github;
  const linkedin = p?.socialLinks?.linkedin || p?.linkedIn || siteConfig.social.linkedin;
  const email = p?.email || siteConfig.contact.email;
  const location = p?.location || siteConfig.contact.location;
  const img = p?.profileImageUrl || null;
  const skills: string[] = Array.isArray(p?.skills) ? p!.skills!.slice(0, 8) : [];
  const roles = Array.isArray(p?.career) ? p!.career!.length : 0;

  return (
    <section id="about" className="rlz-section">
      <div className="rlz-container">
        <div className="rlz-center rlz-reveal">
          <div className="rlz-section-tag"><i className="material-symbols-outlined">person</i> ABOUT</div>
          <h2 className="rlz-section-title">The Engineer <span className="rlz-grad-text">Behind RajibLabs</span></h2>
        </div>

        <div className="rlz-bento" style={{ marginTop: 40 }}>
          <div className="rlz-bento-card rlz-b-12 rlz-reveal" style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 28, alignItems: "start" }}>
            <div>
              {img ? (
                <img src={img} alt={name} loading="lazy" decoding="async"
                  style={{ width: 140, height: 140, objectFit: "cover", borderRadius: 20, display: "block" }} />
              ) : (
                <div className="rlz-media-fallback" aria-hidden="true"
                  style={{ width: 140, height: 140, borderRadius: 20, minHeight: 0 }}>
                  <i className="material-symbols-outlined">person</i>
                </div>
              )}
            </div>
            <div style={{ minWidth: 0 }}>
              <p style={{ margin: 0, fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem", color: "var(--rlz-violet)", fontWeight: 600 }}>
                {p?.headline || "Senior Software Architect · AI & SaaS Platform Builder"}
              </p>
              <h3 style={{ margin: "6px 0 2px", fontSize: "1.6rem" }}>{name}</h3>
              <p style={{ margin: 0, color: "var(--rlz-text-dim)", fontSize: "0.95rem" }}>{title}</p>
              {bio && <p style={{ marginTop: 12, color: "var(--rlz-text-dim)", lineHeight: 1.65 }}>{bio}</p>}
              <p style={{ marginTop: 10, fontSize: "0.85rem", color: "var(--rlz-text-faint)" }}>
                <i className="material-symbols-outlined" style={{ fontSize: "1rem", verticalAlign: "-3px" }}>location_on</i> {location}
                {skills.length > 0 && <> · {skills.length}+ verified skills</>}
                {roles > 0 && <> · {roles} career roles</>}
              </p>
              {!!skills.length && (
                <div className="rlz-chip-row" style={{ marginTop: 12 }}>
                  {skills.map((s) => <span className="rlz-chip" key={s}>{s}</span>)}
                </div>
              )}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 16 }}>
                {github && (
                  <a href={github} target="_blank" rel="noopener noreferrer" className="rlz-btn rlz-btn-ghost" style={{ padding: "10px 18px", fontSize: "0.85rem" }}>
                    <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>code</i> GitHub
                  </a>
                )}
                {linkedin && (
                  <a href={linkedin} target="_blank" rel="noopener noreferrer" className="rlz-btn rlz-btn-ghost" style={{ padding: "10px 18px", fontSize: "0.85rem" }}>
                    <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>work</i> LinkedIn
                  </a>
                )}
                <a href={`mailto:${email}`} className="rlz-btn rlz-btn-primary" style={{ padding: "10px 18px", fontSize: "0.85rem" }}>
                  <i className="material-symbols-outlined" style={{ fontSize: "1rem" }}>mail</i> Email Me
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
      <style>{`@media (max-width: 640px) { #about .rlz-bento-card { grid-template-columns: 1fr !important; } }`}</style>
    </section>
  );
}
