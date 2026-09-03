import { useRef } from "react";
import "../rlz/rlz.css";
import useRlzReveal from "../rlz/Reveal";
import RlzNav from "../rlz/RlzNav";
import RlzHero from "../rlz/RlzHero";
import RlzMarquee from "../rlz/RlzMarquee";
import RlzExpertise from "../rlz/RlzExpertise";
import RlzArchitecture from "../rlz/RlzArchitecture";
import RlzProjects from "../rlz/RlzProjects";
import RlzDemos from "../rlz/RlzDemos";
import RlzExperience from "../rlz/RlzExperience";
import RlzContact from "../rlz/RlzContact";
import RlzFooter from "../rlz/RlzFooter";
import MobileBottomBar from "../components/layout/MobileBottomBar";
import PWAInstallPrompt from "../components/pwa/PWAInstallPrompt";
import PWAUpdatePrompt from "../components/pwa/PWAUpdatePrompt";
import ChatWidget from "../components/ChatWidget";

export default function Home() {
  const scopeRef = useRef<HTMLElement | null>(null);
  useRlzReveal(scopeRef);

  return (
    <>
      <main id="main-content" className="rlz pb-20 md:pb-0" ref={scopeRef}>
        <div className="rlz-bg-grid" aria-hidden="true" />
        <div className="rlz-orb rlz-orb-1" aria-hidden="true" />
        <div className="rlz-orb rlz-orb-2" aria-hidden="true" />
        <div className="rlz-orb rlz-orb-3" aria-hidden="true" />
        <RlzNav />
        <RlzHero scopeRef={scopeRef} />
        <RlzMarquee />
        <RlzExpertise />
        <RlzArchitecture />
        <RlzProjects />
        <RlzDemos />
        <RlzExperience />
        <RlzContact />
        <RlzFooter />
      </main>
      <ChatWidget />
      <MobileBottomBar />
      <PWAInstallPrompt />
      <PWAUpdatePrompt />
    </>
  );
}
