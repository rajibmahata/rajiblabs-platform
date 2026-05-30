import HeroSection from '../components/hero/HeroSection';
import ProjectGrid from '../components/projects/ProjectGrid';
import ActivityFeed from '../components/activity/ActivityFeed';

export default function Home() {
  return (
    <>
      <HeroSection />
      <ProjectGrid />
      <ActivityFeed />
    </>
  );
}
