# Design / UX Assessment — RajibLabs Premium Studio

**Current:** Midnight Engineering already premium (Fraunces/DM Sans/JetBrains, #0e1320, glass + elegant cards, 1280px, section-pad 80-144). Hero 820px + grain/glow is strong, bento grids and timeline are editorial.

**Weak:** 1) Hero CTA secondary row (WhatsApp/Call/CV) competes with primary View Work/About Me — needs hierarchy. 2) Results strip 6 cards feel like dashboard metrics, not editorial proof. 3) Products + AppsShowcase + CompletedProjects duplicate same 5-8 products with divergent content. 4) WorkInProgress fake progress + heatmap not real GitHub. 5) Contact form is mailto: not API, no validation. 6) Portfolio/Product detail routes are stubs (window.location). 7) Mobile bottom bar + floating contact duplicate.

**Keep:** Midnight palette, Fraunces display, DM Sans body, JetBrains mono caps, glass/elegant cards (refine, not replace), grain/mesh/grid, section-pad rhythm, PWA, safe-area, nav hide-on-scroll.

**New IA (per spec §19-22):**
HOME: Hero (Rajib Mahata / Senior Architect .NET Azure AI Product) → What I Build (4-6 capabilities 01-06) → Selected Work (case-study panels, not grid) → Enterprise Engineering (timeline with outcomes) → Products (Page Flow + 4-5 verified) → Architecture & Technology (grouped, not wall) → Contact Let's Build (Start Conversation / Request Quote / Call / WA)
Nav: RajibLabs / Work / Products / Experience / About / Contact (preserve anchors #hero #applications #products #about #contact)
Detail: /portfolio/:slug and /products/:slug reuse same layout (Hero → Problem → Solution → Capabilities → Architecture → Value → CTA)
