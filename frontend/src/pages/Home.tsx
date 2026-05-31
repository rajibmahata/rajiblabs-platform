import HeroSection from '../components/hero/HeroSection';
import WorkforceSection from '../components/hero/WorkforceSection';
import CurrentWork from '../components/hero/CurrentWork';
import ProjectGrid from '../components/projects/ProjectGrid';
import SkillsSection from '../components/hero/SkillsSection';
import ActivityFeed from '../components/activity/ActivityFeed';

export default function Home() {
  return (
    <>
      <HeroSection />
      <CurrentWork />
      <WorkforceSection />
      <ProjectGrid />
      <SkillsSection />
      <ActivityFeed />
    </>
  );
}
