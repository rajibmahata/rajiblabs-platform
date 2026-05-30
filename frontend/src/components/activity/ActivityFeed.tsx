import { useState, useEffect } from 'react';
import type { Activity } from '../../types';
import { getActivities } from '../../services/api';

const STATIC_ACTIVITIES: Activity[] = [
  { id: '1', projectId: '4', type: 'milestone', title: 'Rajib Labs — Redesigned & deployed', description: 'Premium portfolio UI live on SmarterASP.NET', timestamp: new Date().toISOString() },
  { id: '2', projectId: '1', type: 'commit', title: 'DocSignerHub — Auth refactor shipped', description: 'Rate limiting, API security, session hardening', timestamp: new Date(Date.now() - 4 * 3600000).toISOString() },
  { id: '3', projectId: '2', type: 'milestone', title: 'RAG Platform — Embedding pipeline live', description: 'Hybrid vector search with semantic ranking', timestamp: new Date(Date.now() - 24 * 3600000).toISOString() },
  { id: '4', projectId: '1', type: 'deploy', title: 'DocSignerHub — Blog engine launched', description: 'AI-generated tutorials live on docsignerhub.com/blog', timestamp: new Date(Date.now() - 2 * 86400000).toISOString() },
  { id: '5', projectId: '3', type: 'commit', title: 'Solicitor CMS — Workflow engine started', description: 'Visual case flow builder prototype', timestamp: new Date(Date.now() - 6 * 86400000).toISOString() },
];

const typeCfg: Record<string, { color: string; bg: string; ring: string }> = {
  commit:    { color: 'text-emerald-400', bg: 'bg-emerald-400/10', ring: 'ring-emerald-400/20' },
  deploy:    { color: 'text-blue-400', bg: 'bg-blue-400/10', ring: 'ring-blue-400/20' },
  milestone: { color: 'text-amber-400', bg: 'bg-amber-400/10', ring: 'ring-amber-400/20' },
  blog:      { color: 'text-purple-400', bg: 'bg-purple-400/10', ring: 'ring-purple-400/20' },
};

export default function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>(STATIC_ACTIVITIES);

  useEffect(() => {
    getActivities(6).then(setActivities).catch(() => {});
  }, []);

  return (
    <section className="max-w-7xl mx-auto px-6 pb-24">
      <div className="flex items-center gap-4 mb-8">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-muted)]">Recent Activity</h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
      </div>

      <div className="relative pl-8 border-l border-[var(--border)] ml-2 space-y-6">
        {activities.map((a, i) => {
          const c = typeCfg[a.type] || typeCfg.commit;
          return (
            <div key={a.id} className="relative animate-fade-up" style={{ animationDelay: `${i * 0.06}s`, opacity: 0 }}>
              {/* Dot on timeline */}
              <div className={`absolute -left-[2.15rem] top-1 w-3 h-3 rounded-full ${c.bg} ring-4 ${c.ring} ring-[var(--bg)]`}>
                <div className={`w-full h-full rounded-full ${c.color} opacity-60`}></div>
              </div>

              <div className="glass-card p-4 -ml-2">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-white">{a.title}</p>
                    <p className="text-xs text-[var(--text-muted)] mt-1">{a.description}</p>
                  </div>
                  <time className="text-[11px] text-[var(--text-muted)] whitespace-nowrap">{fmt(a.timestamp)}</time>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function fmt(d: string): string {
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'now';
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const days = Math.floor(h / 24);
  if (days < 7) return `${days}d`;
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
