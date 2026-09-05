import { useLayoutEffect } from "react";

// Adds .rlz-visible to .rlz-reveal descendants when scrolled into view.
// Safety net (mirrors the reference design): content is visible by default and
// only hidden once JS confirms it runs (.rlz-js on <html>); a 2.5s timeout
// force-reveals everything no matter what, so sections can never stick hidden.
export default function useRlzReveal(scopeRef: React.RefObject<HTMLElement | null>) {
  useLayoutEffect(() => {
    const root = scopeRef.current;
    if (!root) return;
    document.documentElement.classList.add("rlz-js");
    const showAll = () =>
      root.querySelectorAll(".rlz-reveal").forEach((el) => el.classList.add("rlz-visible"));
    const safety = window.setTimeout(showAll, 2500);
    const els = root.querySelectorAll(".rlz-reveal");
    if (!("IntersectionObserver" in window)) {
      showAll();
      return () => window.clearTimeout(safety);
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("rlz-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((el) => observer.observe(el));
    return () => {
      window.clearTimeout(safety);
      observer.disconnect();
    };
  }, [scopeRef]);
}
