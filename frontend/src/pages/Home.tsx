import HeroSection from '../components/hero/HeroSection';
import SkillsSection from '../components/hero/SkillsSection';
import ProjectGrid from '../components/projects/ProjectGrid';
import ActivityFeed from '../components/activity/ActivityFeed';

export default function Home() {
  return (
    <>
      <HeroSection />
      <ProjectGrid />
      <SkillsSection />
      <ActivityFeed />
    </>
  );
}
