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
}
