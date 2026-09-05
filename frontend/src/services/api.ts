import type { Project, Activity, Profile, GitHubSummary, WipData, ContactForm } from '../types';
import { fallbackProjects, fallbackActivities, fallbackProfile, fallbackGitHubSummary, fallbackWipData } from './fallbackData';

const API_BASE = '/api';

async function fetchWithFallback<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch {
    console.warn(`API unavailable for ${url}, using fallback data`);
    return fallback;
  }
}

export async function getProjects(): Promise<Project[]> {
  return fetchWithFallback(`${API_BASE}/projects`, fallbackProjects);
}

export async function getProject(id: string): Promise<Project> {
  return fetchWithFallback(`${API_BASE}/projects/${id}`, fallbackProjects[0]);
}

export async function getActivities(limit = 20): Promise<Activity[]> {
  const activities = await fetchWithFallback(`${API_BASE}/activity?limit=${limit}`, fallbackActivities);
  return activities.slice(0, limit);
}

export async function getProfile(): Promise<Profile> {
  return fetchWithFallback(`${API_BASE}/profile`, fallbackProfile);
}

// ── Contact Submission ──

export async function submitContact(form: ContactForm): Promise<{ id: string; message: string }> {
  const res = await fetch(`${API_BASE}/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Failed to submit' }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Subscribe ──

export async function submitSubscribe(email: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Failed to subscribe' }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── GitHub Summary (derived from projects + activity) ──

const LANG_COLORS: Record<string, string> = {
  'C#': '#178600',
  'Python': '#3572A5',
  'TypeScript': '#3178C6',
  'JavaScript': '#F1E05A',
  'HTML': '#E34C26',
  'CSS': '#563D7C',
  'SQL': '#E38C41',
  'Blazor': '#512BD4',
  'Java': '#B07219',
};

function deriveLanguage(tech: string): string {
  for (const [lang] of Object.entries(LANG_COLORS)) {
    if (tech.toLowerCase().includes(lang.toLowerCase())) return lang;
  }
  return tech;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`;
  const months = Math.floor(days / 30);
  return `${months} month${months > 1 ? 's' : ''} ago`;
}

export async function getGitHubSummary(): Promise<GitHubSummary> {
  try {
    const [projects, activities] = await Promise.all([
      getProjects(),
      getActivities(50),
    ]);

    // Derive stats from actual data
    const languages = new Set<string>();
    projects.forEach(p => p.techStack.forEach(t => languages.add(deriveLanguage(t))));

    const stats = [
      { value: String(activities.length), label: 'activities', icon: '📊' },
      { value: String(projects.length), label: 'repos', icon: '📦' },
      { value: String(languages.size), label: 'languages', icon: '🔤' },
      { value: 'Kolkata', label: 'location', icon: '📍' },
    ];

    // Derive top repos from projects sorted by most recent activity
    const topRepos = projects
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, 6)
      .map(p => {
        const primaryLang = p.techStack.length > 0 ? deriveLanguage(p.techStack[0]) : 'Other';
        const projectActivities = activities.filter(a => a.projectId === p.id);
        return {
          name: p.title.replace(/\s+/g, '-'),
          language: primaryLang,
          stars: projectActivities.length,
          forks: 0,
          updated: p.lastCommitAt ? timeAgo(p.lastCommitAt) : timeAgo(p.updatedAt),
          langColor: LANG_COLORS[primaryLang] || '#8B8B8B',
        };
      });

    return { stats, topRepos };
  } catch {
    console.warn('GitHub summary unavailable, using fallback');
    return fallbackGitHubSummary;
  }
}

// ── Work In Progress ──

export async function getWorkInProgress(): Promise<WipData> {
  try {
    const [projects, activities] = await Promise.all([
      getProjects(),
      getActivities(50),
    ]);

    const devProjects = projects.filter(p => p.status === 'development');

    const wipProjects = devProjects.map(p => {
      const projectActivities = activities.filter(a => a.projectId === p.id);
      const progress = Math.min(95, 30 + projectActivities.length * 10);
      const latestActivity = projectActivities[0];

      return {
        name: p.title,
        stack: p.techStack.join(' · '),
        progress,
        lastActivity: latestActivity ? timeAgo(latestActivity.timestamp) : 'No recent activity',
        status: 'wip' as const,
      };
    });

    const commits = activities
      .filter(a => a.type === 'commit')
      .slice(0, 10)
      .map(a => {
        const project = projects.find(p => p.id === a.projectId);
        return {
          hash: a.id.substring(0, 7),
          message: a.title,
          repoName: project?.title || 'Unknown',
          timestamp: timeAgo(a.timestamp),
        };
      });

    return { projects: wipProjects, commits };
  } catch {
    console.warn('WIP data unavailable, using fallback');
    return fallbackWipData;
  }
}

// ── Admin CMS helper (credentials include for HttpOnly cookie) ──
const ADMIN_BASE = import.meta.env.VITE_API_BASE ?? "";
async function adminRequest<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${ADMIN_BASE}${path}`, { credentials: "include", headers: { "Content-Type": "application/json", ...(opts.headers || {}) }, ...opts });
  if (!res.ok) { const err = await res.text(); throw new Error(err || `${res.status} ${res.statusText}`); }
  const text = await res.text(); return text ? (JSON.parse(text) as T) : ({} as T);
}
export const api = {
  get: <T>(p: string) => adminRequest<T>(p, { method: "GET" }),
  post: <T>(p: string, body?: unknown) => adminRequest<T>(p, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(p: string, body: unknown) => adminRequest<T>(p, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(p: string, body: unknown) => adminRequest<T>(p, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T>(p: string) => adminRequest<T>(p, { method: "DELETE" }),
  upload: async <T>(p: string, form: FormData): Promise<T> => {
    const res = await fetch(`${ADMIN_BASE}${p}`, { method: "POST", credentials: "include", body: form });
    if (!res.ok) throw new Error(await res.text());
    return (await res.json()) as T;
  },
};

// ── New FastAPI public CMS (published only) with graceful fallback ──
export interface CmsProject {
  id?: string; slug: string; name: string; category: string;
  short_description?: string; full_description?: string;
  problem?: string; solution?: string; business_value?: string;
  features?: string[]; architecture?: string; technologies?: string[];
  github_url?: string | null; live_url?: string | null; demo_url?: string | null;
  video_url?: string | null; featured_image?: string | null; gallery?: string[];
  featured?: boolean; published?: boolean; status?: string;
}
async function publicGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${ADMIN_BASE}${path}`);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch { return null; }
}
export const getCmsProjects = () => publicGet<CmsProject[]>(withLang("/api/public/projects"));
export const getCmsProject = (slug: string) => publicGet<CmsProject>(withLang(`/api/public/projects/${slug}`));

// Multilingual: UI language persisted by LanguageContext; non-English requests
// get server-side translated overlays (cache-first, English fallback).
export function getUiLang(): string {
  try { return localStorage.getItem("rlabs_lang") || "en"; } catch { return "en"; }
}
export function withLang(path: string): string {
  const lang = getUiLang();
  if (!lang || lang === "en") return path;
  return `${path}${path.includes("?") ? "&" : "?"}lang=${encodeURIComponent(lang)}`;
}
export interface UILanguage {
  code: string; name: string; native_name: string; direction: string; is_default?: boolean;
}
export async function fetchLanguages(): Promise<UILanguage[]> {
  try {
    const res = await fetch(`${ADMIN_BASE}/api/public/languages`);
    if (!res.ok) return [];
    const list = await res.json();
    return Array.isArray(list) ? list : [];
  } catch { return []; }
}
export interface RagSource {
  title: string; source_type: string; url?: string | null; score?: number;
}
export interface ChatTurn {
  reply: string; session_token: string;
  // extended lead-conversation fields (additive — old callers ignore them)
  session_id?: string; message?: string;
  lead_captured?: boolean; missing_fields?: string[];
  show_blueprint?: boolean; scope_ready?: boolean;
  // RAG grounding metadata (§15) — present when the backend indexed knowledge
  intent?: string | null; sources?: RagSource[]; mode?: string;
}
export async function sendChat(message: string, session_token?: string, extra?: { name?: string; email?: string; phone?: string; mode?: string; language?: string }) {
  const res = await fetch(`${ADMIN_BASE}/api/public/chat`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_token, ...extra }),
  });
  if (!res.ok) throw new Error("Chat unavailable");
  return res.json() as Promise<ChatTurn>;
}
export interface AgentTurn {
  reply: string; sources: RagSource[]; intent: string; tools_called: string[];
  session_token: string; session_id?: string;
  lead_captured?: boolean; missing_fields?: string[]; agent?: string;
}
export interface AgentCard {
  name: string; description: string; slug: string; starters: string[];
}
export async function getAgentCard(): Promise<AgentCard | null> {
  try {
    const res = await fetch(`${ADMIN_BASE}/api/public/agent/config`);
    if (!res.ok) return null;
    return res.json() as Promise<AgentCard>;
  } catch { return null; }
}
export async function sendAgentChat(message: string, session_token?: string, language?: string): Promise<AgentTurn> {
  const res = await fetch(`${ADMIN_BASE}/api/public/agent/chat`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_token, language: language || getUiLang() }),
  });
  if (!res.ok) throw new Error("Agent unavailable");
  return res.json() as Promise<AgentTurn>;
}
export interface RagAnswer {
  answer: string; intent: string; grounded: boolean;
  sources: { chunk_id: string; document_id: string; score: number; source_type: string; title: string; url?: string | null }[];
}
export async function askRag(question: string, session_id?: string, language?: string): Promise<RagAnswer> {
  const res = await fetch(`${ADMIN_BASE}/api/rag/query`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id, language: language || getUiLang() }),
  });
  if (!res.ok) throw new Error("Knowledge search unavailable");
  return res.json();
}
export async function createChatSession(): Promise<{ session_id: string }> {
  const res = await fetch(`${ADMIN_BASE}/api/public/chat/session`, { method: "POST" });
  if (!res.ok) throw new Error("Chat unavailable");
  return res.json();
}
export interface ChatHistory {
  session_id: string; status: string;
  messages: { role: string; text: string }[];
  lead_captured?: boolean; missing_fields?: string[];
  show_blueprint?: boolean; scope_ready?: boolean;
}
export async function getChatHistory(session_id: string): Promise<ChatHistory> {
  const res = await fetch(`${ADMIN_BASE}/api/public/chat/session/${encodeURIComponent(session_id)}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}
export interface ScopeResult {
  scope: Record<string, unknown>; scope_markdown: string;
  cached: boolean; disclaimer: string;
}
export async function analyzeScope(session_id: string): Promise<ScopeResult> {
  const res = await fetch(`${ADMIN_BASE}/api/public/chat/${encodeURIComponent(session_id)}/analyze`, { method: "POST" });
  if (!res.ok) throw new Error((await res.json().catch(() => null) as { error?: string } | null)?.error ?? "Analysis unavailable");
  return res.json();
}
export async function submitLead(lead: { name: string; email: string; phone: string; description: string; product?: string }) {
  const res = await fetch(`${ADMIN_BASE}/api/public/leads`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lead),
  });
  if (!res.ok) throw new Error("Lead submission failed");
  return res.json();
}
