import GlobalNav from '../components/layout/GlobalNav';
import GlobalFooter from '../components/layout/GlobalFooter';
import HeroSection from '../components/sections/HeroSection';
import ResultsSection from '../components/sections/ResultsSection';
import ProfileSection from '../components/sections/ProfileSection';
import ProductsSection from '../components/sections/ProductsSection';
import WorkInProgressSection from '../components/sections/WorkInProgressSection';
import CompletedProjectsSection from '../components/sections/CompletedProjectsSection';
import GitHubActivitySection from '../components/sections/GitHubActivitySection';
import HowIWorkSection from '../components/sections/HowIWorkSection';
import ContactSection from '../components/sections/ContactSection';

export default function Home() {
  const productCount = 6;
  const companyCount = 3; // Fortune 500 Healthcare, Telecom, Product Studio

  return (
    <>
      <GlobalNav />
      <main id="main-content">
        <HeroSection productCount={productCount} companyCount={companyCount} />
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
    </>
  );
}
