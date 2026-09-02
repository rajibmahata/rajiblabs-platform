export default function Settings() {
  return (
    <div>
      <h1 className="text-xl font-bold" style={{ fontFamily: "Fraunces, serif" }}>Settings</h1>
      <div className="mt-4 p-4 rounded-xl border text-sm leading-relaxed" style={{ background: "var(--c-bg-secondary)", borderColor: "var(--c-border)", color: "var(--c-text-secondary)" }}>
        <p><strong style={{ color: "var(--c-text-primary)" }}>Admin credentials:</strong> Set <code>Admin__Username</code>, <code>Admin__Password</code> or <code>Admin__PasswordHash</code> (BCrypt) in environment / <code>appsettings.json</code>. First login creates DB user.</p>
        <p className="mt-2"><strong style={{ color: "var(--c-text-primary)" }}>JWT:</strong> <code>Jwt__Key</code> (32+ chars) and <code>Jwt__Issuer</code>. Token in HttpOnly cookie <code>rlabs_token</code>.</p>
        <p className="mt-2"><strong style={{ color: "var(--c-text-primary)" }}>GitHub:</strong> <code>GITHUB_TOKEN</code> (or <code>GitHub:Token</code>) + <code>GITHUB_OWNER=rajibmahata</code> — server-only, never exposed to browser.</p>
        <p className="mt-2"><strong style={{ color: "var(--c-text-primary)" }}>Uploads:</strong> <code>wwwroot/uploads/resumes</code> — 10MB, PDF/DOCX only, safe filenames, not directly enumerable.</p>
        <p className="mt-2"><strong style={{ color: "var(--c-text-primary)" }}>Deploy:</strong> <code>frontend/dist</code> via FTP; <code>rajiblabs.db</code> is SQLite file — exclude from FTP delete, backup before deploy.</p>
      </div>
    </div>
  );
}
