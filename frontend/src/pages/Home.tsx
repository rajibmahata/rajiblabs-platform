import GlobalNav from '../components/layout/GlobalNav';
import GlobalFooter from '../components/layout/GlobalFooter';
import HeroSection from '../components/sections/HeroSection';
import ResultsSection from '../components/sections/ResultsSection';
import ProfileSection from '../components/sections/ProfileSection';
import AppsShowcaseSection from '../components/sections/AppsShowcaseSection';
import ProductsSection from '../components/sections/ProductsSection';
import CompletedProjectsSection from '../components/sections/CompletedProjectsSection';
import HowIWorkSection from '../components/sections/HowIWorkSection';
import ContactSection from '../components/sections/ContactSection';
import FloatingContact from '../components/ui/FloatingContact';
import MobileBottomBar from '../components/layout/MobileBottomBar';
import PWAInstallPrompt from '../components/pwa/PWAInstallPrompt';
import PWAUpdatePrompt from '../components/pwa/PWAUpdatePrompt';

export default function Home() {
  const productCount = 8;
  const companyCount = 3;

  return (
    <>
      <GlobalNav />
      <main id="main-content" className="pb-20 md:pb-0">
        <HeroSection productCount={productCount} companyCount={companyCount} />
        <HowIWorkSection />
        <CompletedProjectsSection />
        <ProfileSection />
        <ProductsSection />
        <AppsShowcaseSection />
        <ResultsSection />
        <ContactSection />
      </main>
      <GlobalFooter />
      <FloatingContact />
      <MobileBottomBar />
      <PWAInstallPrompt />
      <PWAUpdatePrompt />
    </>
  );
}
