import type { Project, Activity, Profile } from '../types';
import { fallbackProjects, fallbackActivities, fallbackProfile } from './fallbackData';

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
