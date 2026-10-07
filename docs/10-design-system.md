# TICKETÉ design system

Status: Phase 0 implementation available at `/design`; desktop and 360 px browser checks passed. User visual approval remains pending.

White-dominant editorial layouts, vivid blue, elegant italic serif emphasis, outlined cards, hard shadows and ticket notches/perforations. Public pages are expressive; dashboards calmer; scanning prioritizes large, unmistakable result states.

| Token | Value |
|---|---|
| brand-500 | #4E53FF |
| brand-700 | #3838B8 |
| brand-100 | #E8E9FF |
| brand-50 | #F5F5FF |
| background | #FFFFFF |
| ink | #0A0A14 |
| muted | #5B5F73 |
| line | #E3E4EC |
| success | #12B76A |
| warning | #F5A524 |
| danger | #E5484D |
| highlight | #FFD43B |
| pink-accent | #FF5FA2 |

Implement CSS variables mapped into Tailwind; no hard-coded palette in components. Status fills need verified foreground contrast; white text is not automatically safe on green, yellow or red. Include semantic contrast-tested status text tokens as necessary.

Implemented fonts: Playfair Display regular/italic for headings, Inter for body/UI, JetBrains Mono for labels/ticket codes/prices, loaded with next/font. Bangla fallback planned for later localization. Main body paragraphs are 16 px; compact labels/captions are smaller; desktop hero up to 72 px, phone 40 px. Spacing scale 8 px with small 4 px optical adjustments. Cards 16–24 px radius, pills fully rounded; 2 px ink border, default hard shadow 4px 4px 0 ink. Reduced-motion styles and visible keyboard focus are implemented.

First component: accessible Button with primary, secondary, destructive, disabled, loading and focus states. Follow with Input/Select/Checkbox, Card/TicketCard, numbered Pill, Badge, Modal/Drawer, Toast, Table, Stepper, EmptyState and Skeleton. Compose a floating pill navbar and landing page shell. Provide internal `/design` review page.

Original horizontal and stacked artwork is used in the navbar and footer. Source PNGs remain unchanged under `public/brand`; CSS viewports hide the original whitespace and next/image serves resized variants. The icon is embedded unchanged in an SVG viewport wrapper for the favicon. This wrapper is not an original vector logo. The inverse fourth logo is preserved for future use. No wordmark tracing, rotation or recoloring was performed. True vector originals would improve scaling.

Ticket card: left event content, notches at perforation, narrow ADMIT ONE stub. Decorative barcode is never substituted for a valid QR. Scannable QR uses pure black on white and a quiet zone, without logo overlays (proposed conflict resolution).

Required checks: 360 px and desktop screenshots, no horizontal overflow, keyboard operation of menus/dialogs, form labels/errors, semantic structure, image alternatives, status meaning beyond color, adequate touch targets and reduced motion. Avoid fabricated live stats and unlabelled demo event listings.
