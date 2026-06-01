export interface Project {
  id: string;
  title: string;
  slug: string;
  description: string;
  techStack: string[];
  githubUrl: string;
  liveUrl: string | null;
  status: 'planning' | 'development' | 'qa' | 'deployed';
  createdAt: string;
  updatedAt: string;
  lastCommitAt: string | null;
}

export interface Activity {
  id: string;
  projectId: string;
  type: 'commit' | 'deploy' | 'milestone' | 'blog';
  title: string;
  description: string;
  timestamp: string;
}

export interface Profile {
  id: string;
  fullName: string;
  title: string;
  bio: string;
  skills: string[];
  socialLinks: {
    github: string;
    linkedin: string;
  };
  career?: CareerEntry[];
  updatedAt?: string;
}

export interface CareerEntry {
  company: string;
  role: string;
  period: string;
  client?: string;
  achievements: string[];
  techStack: string[];
  color: string;
}

export interface GitHubSummary {
  stats: { value: string; label: string; icon: string }[];
  topRepos: {
    name: string;
    language: string;
    stars: number;
    forks: number;
    updated: string;
    langColor: string;
  }[];
}

export interface WipData {
  projects: WipProject[];
  commits: WipCommit[];
}

export interface WipProject {
  name: string;
  stack: string;
  progress: number;
  lastActivity: string;
  status: 'live' | 'wip';
}

export interface WipCommit {
  hash: string;
  message: string;
  repoName: string;
  timestamp: string;
}

export interface ContactForm {
  name: string;
  email: string;
  company?: string;
  message: string;
}
