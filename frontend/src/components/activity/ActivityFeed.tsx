import { useState, useEffect } from 'react';
import type { Activity } from '../../types';
import { getActivities } from '../../services/api';

const typeConfig: Record<string, { icon: string; color: string; bg: string }> = {
  commit:    { icon: '⬤', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/20' },
  deploy:    { icon: '◆', color: 'text-indigo-400', bg: 'bg-indigo-400/10 border-indigo-400/20' },
  milestone: { icon: '▲', color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/20' },
  blog:      { icon: '■', color: 'text-cyan-400', bg: 'bg-cyan-400/10 border-cyan-400/20' },
};

export default function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getActivities(10)
      .then(setActivities)
      .catch(() => setActivities([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="mt-24">
      <div className="flex items-center gap-3 mb-10">
        <div className="h-px flex-1 bg-[var(--color-border)]"></div>
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
          Currently Working
        </h2>
        <span className="text-xs text-[var(--color-text-muted)] bg-white/[0.03] px-2 py-0.5 rounded-full border border-[var(--color-border)]">
          {loading ? '...' : activities.length}
        </span>
        <div className="h-px flex-1 bg-[var(--color-border)]"></div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => (
            <div key={i} className="glass-card rounded-xl p-5 animate-pulse flex gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/5"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 w-2/3 bg-white/5 rounded"></div>
                <div className="h-3 w-1/2 bg-white/5 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      ) : activities.length === 0 ? (
        <div className="text-center py-12 glass-card rounded-2xl">
          <div className="text-3xl mb-3">👀</div>
          <p className="text-[var(--color-text-secondary)]">No recent activity</p>
          <p className="text-[var(--color-text-muted)] text-sm mt-1">The monitor agent updates this feed automatically.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {activities.map((a, i) => {
            const cfg = typeConfig[a.type] || typeConfig.commit;
            return (
              <div
                key={a.id}
                className="glass-card rounded-xl p-5 flex gap-4 items-start group animate-in"
                style={{ animationDelay: `${0.1 + i * 0.06}s`, opacity: 0 }}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${cfg.bg}`}>
                  <span className={`text-sm ${cfg.color}`}>{cfg.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white group-hover:text-indigo-300 transition-colors">
                    {a.title}
                  </p>
                  <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
                    {a.description}
                  </p>
                </div>
                <time className="text-xs text-[var(--color-text-muted)] whitespace-nowrap pt-1">
                  {new Date(a.timestamp).toLocaleDateString('en-US', {
                    month: 'short', day: 'numeric'
                  })}
                </time>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
