import GlobalNav from '../components/layout/GlobalNav';
import GlobalFooter from '../components/layout/GlobalFooter';
import HeroSection from '../components/sections/HeroSection';
import ProfileSection from '../components/sections/ProfileSection';
import WorkInProgressSection from '../components/sections/WorkInProgressSection';
import CompletedProjectsSection, { projects } from '../components/sections/CompletedProjectsSection';
import GitHubActivitySection from '../components/sections/GitHubActivitySection';
import LinkedInSection from '../components/sections/LinkedInSection';
import ProductsSection from '../components/sections/ProductsSection';
import ContactSection from '../components/sections/ContactSection';

export default function Home() {
  const productCount = projects.length;
  const companyCount = 3; // TCS, Accenture, Keshri

  return (
    <>
      <GlobalNav />
      <main id="main-content">
        <HeroSection productCount={productCount} companyCount={companyCount} />
        <ProfileSection />
        <WorkInProgressSection />
        <CompletedProjectsSection />
        <GitHubActivitySection />
        <LinkedInSection />
        <ProductsSection />
        <ContactSection />
      </main>
      <GlobalFooter />
    </>
  );
}
