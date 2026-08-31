import GlobalNav from '../components/layout/GlobalNav';
import GlobalFooter from '../components/layout/GlobalFooter';
import HeroSection from '../components/sections/HeroSection';
import ResultsSection from '../components/sections/ResultsSection';
import ProfileSection from '../components/sections/ProfileSection';
import AppsShowcaseSection from '../components/sections/AppsShowcaseSection';
import ProductsSection from '../components/sections/ProductsSection';
import WorkInProgressSection from '../components/sections/WorkInProgressSection';
import CompletedProjectsSection from '../components/sections/CompletedProjectsSection';
import GitHubActivitySection from '../components/sections/GitHubActivitySection';
import HowIWorkSection from '../components/sections/HowIWorkSection';
import ContactSection from '../components/sections/ContactSection';
import FloatingContact from '../components/ui/FloatingContact';
import PWAInstallPrompt from '../components/pwa/PWAInstallPrompt';
import PWAUpdatePrompt from '../components/pwa/PWAUpdatePrompt';

export default function Home() {
  const productCount = 8;
  const companyCount = 3; // Fortune 500 Healthcare, Telecom, Product Studio

  return (
    <>
      <GlobalNav />
      <main id="main-content">
        <HeroSection productCount={productCount} companyCount={companyCount} />
        <AppsShowcaseSection />
        <ResultsSection />
        <ProfileSection />
        <ProductsSection />
        <WorkInProgressSection />
        <CompletedProjectsSection />
        <GitHubActivitySection />
        <HowIWorkSection />
        <ContactSection />
      </main>
      <GlobalFooter />
      <FloatingContact />
      <PWAInstallPrompt />
      <PWAUpdatePrompt />
    </>
  );
}
