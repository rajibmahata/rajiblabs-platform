import { useEffect } from "react";

// Adds .rlz-visible to .rlz-reveal descendants when scrolled into view.
export default function useRlzReveal(scopeRef: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = scopeRef.current;
    if (!root) return;
    const els = root.querySelectorAll(".rlz-reveal");
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("rlz-visible"));
      return;
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
    return () => observer.disconnect();
  }, [scopeRef]);
}
