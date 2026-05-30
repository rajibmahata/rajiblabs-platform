import { useState, useEffect } from 'react';
import type { Activity } from '../../types';
import { getActivities } from '../../services/api';

const typeIcons: Record<string, string> = {
  commit: '📝',
  deploy: '🚀',
  milestone: '🏁',
  blog: '📄',
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

  if (loading) return <div className="text-center text-gray-500 py-6">Loading activity...</div>;

  return (
    <section className="mt-16">
      <h2 className="text-2xl font-bold mb-8">Currently Working</h2>

      {activities.length === 0 ? (
        <p className="text-gray-500 text-center py-6">
          No recent activity. Agents will update this feed automatically.
        </p>
      ) : (
        <div className="space-y-4">
          {activities.map(a => (
            <div key={a.id} className="flex gap-4 p-4 rounded-lg border border-gray-800 bg-gray-900/50">
              <div className="text-xl mt-0.5">{typeIcons[a.type] || '•'}</div>
              <div className="flex-1">
                <p className="text-sm text-gray-300">{a.title}</p>
                <p className="text-sm text-gray-500">{a.description}</p>
              </div>
              <time className="text-xs text-gray-600 whitespace-nowrap">
                {new Date(a.timestamp).toLocaleDateString('en-US', {
                  month: 'short', day: 'numeric'
                })}
              </time>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
