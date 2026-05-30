import { useState, useEffect } from 'react';
import type { Activity } from '../../types';
import { getActivities } from '../../services/api';

const typeStyle: Record<string, { icon: string; border: string; bg: string }> = {
  commit:    { icon: '●', border: 'border-emerald-500/30', bg: 'bg-emerald-500/10' },
  deploy:    { icon: '◆', border: 'border-blue-500/30', bg: 'bg-blue-500/10' },
  milestone: { icon: '▲', border: 'border-amber-500/30', bg: 'bg-amber-500/10' },
  blog:      { icon: '■', border: 'border-purple-500/30', bg: 'bg-purple-500/10' },
};

export default function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getActivities(8)
      .then(setActivities)
      .catch(() => setActivities([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-6xl mx-auto px-6 pb-24">
      {/* Section header */}
      <div className="flex items-center gap-4 mb-10">
        <h2 className="text-sm font-semibold uppercase tracking-[0.15em] text-[var(--text-muted)]">
          Recent Activity
        </h2>
        <div className="h-px flex-1 bg-[var(--border)]"></div>
        <span className="text-xs text-[var(--text-muted)] tabular-nums">
          {loading ? '...' : activities.length}
        </span>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] animate-pulse">
              <div className="w-8 h-8 rounded-lg bg-[var(--bg-hover)]"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 w-2/3 bg-[var(--bg-hover)] rounded"></div>
                <div className="h-3 w-1/2 bg-[var(--bg-hover)] rounded"></div>
              </div>
              <div className="h-3 w-16 bg-[var(--bg-hover)] rounded"></div>
            </div>
          ))}
        </div>
      ) : activities.length === 0 ? (
        <div className="text-center py-16 rounded-2xl bg-[var(--bg-card)] border border-[var(--border)]">
          <div className="text-3xl mb-3">👀</div>
          <p className="text-sm text-[var(--text-muted)]">Monitor agent is watching. Activity will appear here.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {activities.map((a, i) => {
            const s = typeStyle[a.type] || typeStyle.commit;
            return (
              <div
                key={a.id}
                className="flex items-center gap-4 p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] hover:border-[var(--border-hover)] transition-colors animate-fade-up"
                style={{ animationDelay: `${i * 0.06}s`, opacity: 0 }}
              >
                <div className={`w-8 h-8 rounded-lg ${s.bg} ${s.border} border flex items-center justify-center text-xs text-[var(--text-secondary)]`}>
                  {s.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{a.title}</p>
                  <p className="text-xs text-[var(--text-muted)] truncate">{a.description}</p>
                </div>
                <time className="text-xs text-[var(--text-muted)] whitespace-nowrap">
                  {timeAgo(a.timestamp)}
                </time>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
