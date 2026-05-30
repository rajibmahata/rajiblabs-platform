const API_BASE = '/api';

export async function getProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function getProject(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  if (!res.ok) throw new Error('Failed to fetch project');
  return res.json();
}

export async function getActivities(limit = 20): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/activity?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch activities');
  return res.json();
}

export async function getProfile(): Promise<Profile> {
  const res = await fetch(`${API_BASE}/profile`);
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}
