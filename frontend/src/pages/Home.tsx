import HeroSection from '../components/hero/HeroSection';
import AboutSection from '../components/hero/AboutSection';
import CurrentProjects from '../components/hero/CurrentProjects';
import PortfolioGallery from '../components/hero/PortfolioGallery';
import ResumeSection from '../components/hero/ResumeSection';
import ContactSection from '../components/hero/ContactSection';

export default function Home() {
  return (
    <>
      <HeroSection />
      <AboutSection />
      <CurrentProjects />
      <PortfolioGallery />
      <ResumeSection />
      <ContactSection />
    </>
  );
}
