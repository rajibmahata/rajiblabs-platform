import HeroSection from '../components/hero/HeroSection';
import CurrentWork from '../components/hero/CurrentWork';
import WorkforceSection from '../components/hero/WorkforceSection';
import ProjectGrid from '../components/projects/ProjectGrid';
import GitHubActivity from '../components/hero/GitHubActivity';
import InnovationLab from '../components/hero/InnovationLab';
import TechEcosystem from '../components/hero/TechEcosystem';
import SkillsSection from '../components/hero/SkillsSection';
import ResumeSection from '../components/hero/ResumeSection';
import ActivityFeed from '../components/activity/ActivityFeed';
import ContactSection from '../components/hero/ContactSection';
import FutureVision from '../components/hero/FutureVision';

export default function Home() {
  return (
    <>
      <HeroSection />
      <CurrentWork />
      <WorkforceSection />
      <ProjectGrid />
      <GitHubActivity />
      <SkillsSection />
      <TechEcosystem />
      <InnovationLab />
      <ActivityFeed />
      <ResumeSection />
      <ContactSection />
      <FutureVision />
    </>
  );
}
