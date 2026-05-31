export default function Home() {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  const projects = [
    { name: 'DocSignerHub', desc: 'Complete digital signature SaaS platform. AI-powered clause analysis, blockchain notarisation, visual workflow builder, Stripe payments, 140+ REST API endpoints.', live: 'https://docsignerhub.com', git: 'https://github.com/rajibmahata/DocumentSigningPlatform', tech: '.NET 8 • React • SQL Server • Azure • OpenAI • Stripe', status: 'Active', progress: 85 },
    { name: 'AI Avatar RAG Platform', desc: 'Enterprise AI knowledge retrieval with avatar-based interaction. Hybrid vector search, semantic ranking, multi-tenant RAG pipelines.', live: null, git: 'https://github.com/rajibmahata/AI-Avatar-RAG-Platform', tech: 'Python • FastAPI • OpenAI • RAG • Vector DB • React', status: 'Active', progress: 60 },
    { name: 'Solicitor Case Management', desc: 'Legal enterprise workflow platform. Case tracking, document management, client communication, visual workflow builder.', live: null, git: 'https://github.com/rajibmahata/SolicitorCaseManagementSystem', tech: '.NET 8 • Blazor • SQL Server • Azure • Cosmos DB', status: 'Planning', progress: 25 },
    { name: 'Rajib Labs', desc: 'This portfolio platform — premium personal brand, AI-managed content, responsive design, real-time activity tracking.', live: 'https://rajiblabs.com', git: 'https://github.com/rajibmahata/rajiblabs-platform', tech: 'React • TypeScript • .NET 8 • Tailwind CSS • OpenClaw', status: 'Active', progress: 95 },
    { name: 'FoodFleet', desc: 'Multi-branch restaurant delivery platform. Location detection, local menu, cart management, branch routing.', live: null, git: 'https://github.com/rajibmahata/FoodFleet', tech: 'C# • ASP.NET Core • SQL Server', status: 'Complete', progress: 100 },
    { name: 'BudgetEase', desc: 'Modern event expense tracking application. Budget management, vendor communications, financial monitoring.', live: null, git: 'https://github.com/rajibmahata/BudgetEase', tech: 'C# • ASP.NET Core • SQL Server', status: 'Complete', progress: 100 },
    { name: 'AI Resume Portfolio', desc: 'AI-powered resume to portfolio generator. Upload PDF/DOC, AI generates single-page portfolio. Blazor Server app.', live: null, git: 'https://github.com/rajibmahata/AI-Resume-Portfolio', tech: 'Blazor • AI • C# • .NET', status: 'Complete', progress: 100 },
    { name: 'AI Blog Portfolio', desc: 'Seamless blogging platform where authors focus on writing while AI ensures content quality, engagement, and discoverability.', live: null, git: 'https://github.com/rajibmahata/AI-Powered-Blog-Portfolio', tech: 'C# • AI • ASP.NET Core • SQL', status: 'Complete', progress: 100 },
  ];

  const skills = ['.NET 8/10', 'C#', 'ASP.NET Core', 'Blazor', 'React', 'TypeScript', 'Python', 'FastAPI', 'Azure Cloud', 'Microservices', 'SQL Server', 'Cosmos DB', 'Docker', 'REST APIs', 'Entity Framework', 'AI/LLM Integration', 'RAG Systems', 'OpenAI API', 'Gemini API', 'GitHub Copilot', 'OpenClaw', 'CI/CD'];

  const experience = [
    { role: 'Independent Software Architect', period: '2019 — Present', desc: 'Designing and building complete SaaS platforms from scratch. Architecting AI-integrated systems, managing cloud infrastructure, leading autonomous AI workforce initiatives. Key projects: DocSignerHub, AI Avatar RAG Platform, Solicitor CMS, Rajib Labs.' },
    { role: 'Senior Software Engineer', period: '2015 — 2019', desc: 'Led .NET development teams building enterprise applications. Architected microservices, designed REST APIs, managed Azure cloud infrastructure. Mentored junior developers and established coding standards.' },
    { role: 'Software Engineer', period: '2012 — 2015', desc: 'Full-stack .NET development. Built web applications, REST APIs, and database systems for enterprise clients. Developed expertise in SQL Server, ASP.NET, and frontend technologies.' },
  ];

  const statusColors: Record<string, string> = {
    Active: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
    Planning: 'bg-amber-400/10 text-amber-400 border-amber-400/20',
    Complete: 'bg-slate-400/10 text-slate-400 border-slate-400/20',
  };

  return (
    <>
      {/* ── HERO ── */}
      <section className="min-h-[90vh] flex items-center max-w-5xl mx-auto px-4 sm:px-6 pt-20 pb-12 sm:pb-16">
        <div className="w-full">
          <div className="animate-in mb-6">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-[var(--border)] text-xs sm:text-sm text-[var(--accent-light)]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Available for projects
            </span>
          </div>

          <h1 className="animate-in d1 text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.08] mb-3 sm:mb-4">
            Rajib Mahata
          </h1>

          <p className="animate-in d2 text-lg sm:text-xl md:text-2xl text-white font-medium mb-2 sm:mb-3 leading-snug">
            Senior Software Architect & SaaS Platform Builder
          </p>

          <p className="animate-in d2 text-sm sm:text-base md:text-lg text-[var(--text-secondary)] max-w-xl mb-6 sm:mb-8">
            Building modern software, products, and digital experiences. 10+ years in .NET, Azure, AI/LLM integrations.
          </p>

          <div className="animate-in d3 flex flex-wrap gap-2.5 sm:gap-3">
            <button onClick={() => scrollTo('projects')}
              className="px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-[var(--accent)] text-white font-semibold text-sm hover:bg-[var(--accent-light)] transition-all">
              View Projects
            </button>
            <button onClick={() => scrollTo('resume')}
              className="px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl border border-[var(--border)] text-white font-medium text-sm hover:border-[var(--text-muted)] transition-all">
              Resume
            </button>
            <button onClick={() => scrollTo('contact')}
              className="px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] font-medium text-sm hover:border-[var(--text-muted)] hover:text-white transition-all">
              Contact
            </button>
          </div>

          {/* Quick stats */}
          <div className="animate-in d4 grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-10 sm:mt-12 max-w-md sm:max-w-lg">
            {[
              ['10+', 'Years experience'],
              ['15+', 'Projects shipped'],
              ['8+', 'Technologies'],
              ['Global', 'Clients'],
            ].map(([v, l]) => (
              <div key={l}>
                <div className="text-xl sm:text-2xl font-bold text-white">{v}</div>
                <div className="text-[10px] sm:text-[11px] text-[var(--text-muted)]">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ABOUT ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16 sm:pb-20">
        <div className="animate-in">
          <div className="section-label">About</div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">Professional Profile</h2>

          <div className="grid sm:grid-cols-2 gap-3 sm:gap-4 mb-6 sm:mb-8">
            {[
              ['📍', 'Kolkata, India · Remote'],
              ['⏳', '10+ years experience'],
              ['🎯', '.NET · Azure · AI/LLM'],
              ['🚀', '15+ production systems'],
              ['🤖', '9 AI agents running'],
              ['🌍', 'International clients'],
            ].map(([icon, val]) => (
              <div key={val} className="card p-3 sm:p-4 flex items-center gap-3">
                <span className="text-lg sm:text-xl flex-shrink-0">{icon}</span>
                <span className="text-xs sm:text-sm text-[var(--text-secondary)]">{val}</span>
              </div>
            ))}
          </div>

          <p className="text-sm sm:text-base text-[var(--text-secondary)] leading-relaxed">
            Independent software architect with 10+ years designing and building production-grade software. I specialize in the .NET ecosystem, Azure cloud architecture, and AI/LLM integrations. I've built complete SaaS platforms end-to-end — handling database design, API architecture, frontend development, and CI/CD pipelines. Currently building DocSignerHub, AI Avatar RAG Platform, and Rajib Labs — each powered by autonomous AI agents for development, QA, and deployment.
          </p>
        </div>
      </section>

      {/* ── PROJECTS ── */}
      <section id="projects" className="max-w-5xl mx-auto px-4 sm:px-6 pb-16 sm:pb-20">
        <div className="section-label">Projects</div>
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">What I've Built</h2>

        <div className="space-y-3 sm:space-y-4">
          {projects.map((p, i) => (
            <div key={p.name} className="card p-4 sm:p-6 animate-in" style={{ animationDelay: `${i*0.06}s`, opacity: 0 }}>
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 sm:gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-base sm:text-lg font-semibold text-white">{p.name}</h3>
                    <span className={`badge border ${statusColors[p.status]}`}>{p.status}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-0.5">{p.tech}</p>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
                  {p.live && <a href={p.live} target="_blank" rel="noopener noreferrer" className="text-xs sm:text-sm font-medium text-[var(--accent-light)] hover:text-white transition-colors">Live ↗</a>}
                  <a href={p.git} target="_blank" rel="noopener noreferrer" className="text-xs sm:text-sm font-medium text-[var(--text-muted)] hover:text-white transition-colors">GitHub ↗</a>
                </div>
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed mb-3">{p.desc}</p>
              {/* Progress bar */}
              <div className="h-1 bg-[var(--border)] rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all" style={{ width: `${p.progress}%` }}></div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── RESUME ── */}
      <section id="resume" className="max-w-5xl mx-auto px-4 sm:px-6 pb-16 sm:pb-20">
        <div className="section-label">Resume</div>
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">Experience & Skills</h2>

        <div className="grid lg:grid-cols-5 gap-6 sm:gap-8">
          {/* Experience — 3 cols */}
          <div className="lg:col-span-3 animate-in">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4 sm:mb-5">Work History</h3>
            <div className="space-y-3 sm:space-y-4">
              {experience.map((exp, i) => (
                <div key={i} className="card p-4 sm:p-5">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-2">
                    <h4 className="text-sm font-semibold text-white">{exp.role}</h4>
                    <span className="text-[11px] sm:text-xs text-[var(--text-muted)]">{exp.period}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed">{exp.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Skills + Certs — 2 cols */}
          <div className="lg:col-span-2 animate-in d2 space-y-6">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4">Technical Skills</h3>
              <div className="card p-4 sm:p-5">
                <div className="flex flex-wrap gap-1.5 sm:gap-2">
                  {skills.map(s => (
                    <span key={s} className="text-[11px] sm:text-xs px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-white/[0.03] border border-[var(--border)] text-[var(--text-secondary)] hover:text-white hover:border-[var(--text-muted)] transition-colors cursor-default">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4">Certifications</h3>
              <div className="card p-4 sm:p-5 space-y-3">
                {[
                  'Microsoft Certified: Azure Solutions Architect',
                  'Microsoft Certified: Azure Developer Associate',
                  'B.Tech in Computer Science & Engineering',
                ].map(c => (
                  <div key={c} className="flex items-center gap-2 text-xs sm:text-sm text-[var(--text-secondary)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] flex-shrink-0"></span> {c}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4">Links</h3>
              <div className="card p-4 sm:p-5 space-y-2.5">
                {[
                  ['GitHub', 'github.com/rajibmahata'],
                  ['LinkedIn', 'linkedin.com/in/rajib-mahata'],
                  ['Website', 'rajiblabs.com'],
                ].map(([label, url]) => (
                  <div key={label} className="flex items-center gap-2 text-xs sm:text-sm">
                    <span className="text-[var(--text-muted)] w-16 flex-shrink-0">{label}</span>
                    <span className="text-[var(--text-secondary)]">{url}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CONTACT ── */}
      <section id="contact" className="max-w-5xl mx-auto px-4 sm:px-6 pb-20 sm:pb-24">
        <div className="section-label">Contact</div>
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">Get In Touch</h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 animate-in">
          <a href="https://github.com/rajibmahata" target="_blank" rel="noopener noreferrer" className="card p-5 sm:p-6 text-center group">
            <svg className="w-7 h-7 sm:w-8 sm:h-8 text-white mx-auto mb-3 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            <h3 className="text-sm sm:text-base font-semibold text-white mb-1">GitHub</h3>
            <p className="text-[11px] sm:text-xs text-[var(--text-muted)]">@rajibmahata</p>
          </a>

          <a href="https://linkedin.com/in/rajib-mahata" target="_blank" rel="noopener noreferrer" className="card p-5 sm:p-6 text-center group">
            <svg className="w-7 h-7 sm:w-8 sm:h-8 text-white mx-auto mb-3 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            <h3 className="text-sm sm:text-base font-semibold text-white mb-1">LinkedIn</h3>
            <p className="text-[11px] sm:text-xs text-[var(--text-muted)]">@rajib-mahata</p>
          </a>

          <a href="mailto:contact@rajiblabs.com" className="card p-5 sm:p-6 text-center group">
            <svg className="w-7 h-7 sm:w-8 sm:h-8 text-white mx-auto mb-3 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            <h3 className="text-sm sm:text-base font-semibold text-white mb-1">Email</h3>
            <p className="text-[11px] sm:text-xs text-[var(--text-muted)]">contact@rajiblabs.com</p>
          </a>
        </div>
      </section>
    </>
  );
}
