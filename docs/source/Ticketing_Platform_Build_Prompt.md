# OFFICIAL BUILD PROMPT: Ticketé (Ticketing Platform)

> Copy everything below this line and give it to the AI coding assistant or developer.
> Attach these with it: **Features List and Core Flow (PDF)**, **PRD (PDF)**, **ER Diagram (PDF/SVG)**, the **logo files** (`1.png` stacked logo, `2.png` horizontal logo, `3.png` icon only), and the **four reference screenshots** (two of the GP FutureMakers site, two of the CSE-UAP Film and Photography Club site).
> Brand name: **Ticketé**. Primary brand color: **#4E53FF**. Section 7A defines the whole look of the platform.

---

## 0. ROLE AND MISSION

You are a senior full-stack engineer (Django REST Framework + Next.js) and technical lead. Your mission is to design, build, test, and deploy a **Ticketing Platform** for the Bangladesh market, working with me as the product owner.

You will be given three documents: the **Features List and Core Flow**, the **PRD**, and the **ER Diagram**. They are the source of truth for scope, requirements, and data structure. If anything in this prompt conflicts with those documents, stop and ask me which one wins. Do not guess.

Work like a professional team member: plan first, build in small verified steps, document everything, and explain decisions in plain language.

---

## 1. WHAT THE PRODUCT IS (read this first)

A web platform where:

1. **Organizers** sign in, create events through a form, and submit them for approval.
2. An **Admin** is notified, reviews the event, and approves or rejects it (rejection requires a reason).
3. Once approved, a **public event link** is generated.
4. **Buyers** open the link and buy tickets either as a **guest** (email only) or as a **logged-in user** (email prefilled). No login is required.
5. Payment goes through a **dummy bKash/Nagad-style gateway** with a phone number and OTP step. Success confirms the order.
6. The system generates **one unique QR code per ticket** and **one PDF per order (one page per ticket)** in a fixed design. The PDF is emailed from the platform email and is also downloadable on the confirmation page.
7. A buyer can **gift** tickets by entering another person's email. The recipient receives the PDF; the buyer sees a confirmation screen and gets a receipt email.
8. At the venue, **volunteers scan the QR or type the ticket ID**. The ticket is marked as used, and it cannot be used again.
9. The organizer can **invite teammates by email** (invitation link) and give them roles: Manager, Scanner, Viewer.
10. The organizer gets a **basic dashboard with charts** during the event and a **final report** after closing it (sold, unsold, per category, revenue, checked-in vs no-show).

### Confirmed product decisions (do not change without asking)

- Seat limits are **per category** (blank limit = unlimited). Event capacity is the sum of categories.
- Attendee name per ticket (Attendee 1 name, Attendee 2 name...) is an **optional switch** the organizer turns on.
- Organizers can add **custom form fields** (text, number, dropdown, checkbox; required or optional). Answers are stored as flexible JSON on the order.
- **Refunds and cancellations are out of scope.** Organizer and attendee handle them directly. The organizer can mark a ticket Cancelled so it fails at the gate.
- **Payouts and platform fees are out of scope.** Treat dummy payments as going to the organizer.
- The payment module must sit behind a **clean gateway interface** so a real provider can replace the dummy later without touching order or ticket logic.
- The ticket PDF design is **fixed by the platform** (organizers do not customize it in this version).
- All times are **stored in UTC and displayed in Asia/Dhaka**. Currency is BDT.

---

## 2. REPOSITORY STRATEGY (decision made: ONE repo, two folders)

Use a **single monorepo** with separate `backend/` and `frontend/` folders.

**Why:**
- One commit can change the API and the screens that use it, so they never drift apart.
- One place for documentation, issues, and the project history (important because we document everything).
- Simpler for a small team and for intern-level collaboration; one clone, one pull request flow.
- Vercel can deploy a subfolder: set the **Root Directory** to `frontend` in the Vercel project. The Django backend is deployed separately from the `backend` folder.
- It can be split into two repos later without losing history if the team grows.

**When to split instead:** only if separate teams need separate access or release schedules. That is not our case now.

**Required structure:**

```
ticketing-platform/
├── README.md                  # overview, setup, how to run everything
├── .gitignore
├── docker-compose.yml         # optional: local Redis (and Postgres if needed)
├── docs/
│   ├── 01-idea.md
│   ├── 02-research.md
│   ├── 03-user-definition.md
│   ├── 04-prd.md              # copy/summary of the PRD
│   ├── 05-system-design.md    # architecture, ER diagram, API design
│   ├── 06-project-rules.md    # coding standards, branching, commit style
│   ├── 07-task-breakdown.md   # phases, tasks, status
│   ├── 08-deployment.md
│   ├── 09-review-and-iterate.md
│   ├── decisions/             # one short file per major decision (ADR style)
│   └── CHANGELOG.md
├── backend/
│   ├── manage.py
│   ├── config/                # settings split: base, local, production
│   ├── apps/                  # accounts, events, teams, orders, payments,
│   │                          # tickets, checkin, notifications, reports, core
│   ├── requirements/          # base.txt, local.txt, production.txt
│   ├── .env.example
│   └── README.md
└── frontend/
    ├── (Next.js App Router, TypeScript, Tailwind)
    ├── public/brand/          # logos (stacked, horizontal, icon), favicon, OG image
    ├── styles/tokens          # design tokens from section 7A (colors, radii, shadows)
    ├── .env.example
    └── README.md
```

Also add `docs/10-design-system.md` documenting the design tokens, components, and screen patterns from section 7A.

---

## 3. REQUIRED WORKING PROCESS

Follow this flow strictly. **Document every step in `docs/`.** Do not skip stages.

**IDEA -> RESEARCH -> DEFINE THE USER -> PRD -> SYSTEM DESIGN -> PROJECT RULES -> TASK BREAKDOWN -> DEVELOP -> DEPLOY -> REVIEW -> ITERATE**

Status right now: Idea, Research, Define the User, and PRD are done (see attached documents). System Design is in progress.

How you must work:

1. **Start by confirming understanding.** Before writing code, reply with: a short summary of what you will build, any contradictions or gaps you found in the documents, and a numbered list of questions. Wait for my answers on blocking questions. For non-blocking ones, state your assumption and continue.
2. **Finish System Design first** (`docs/05-system-design.md`): architecture diagram description, final data model (based on the ER diagram), API endpoint list, permission matrix, state machines (event, order, ticket), and the seat-hold and check-in concurrency approach.
3. **Write Project Rules** (`docs/06-project-rules.md`) and **Task Breakdown** (`docs/07-task-breakdown.md`) and get my approval before developing.
4. **Develop in phases** (section 8). After each phase: run tests, update the docs and changelog, summarize what was done, and wait for my review before the next phase.
5. **Commit often** with clear messages (Conventional Commits, for example `feat(orders): add seat hold with row locking`). Use feature branches and pull requests: `main` (stable), `develop` (integration), `feature/<name>`.
6. **Never silently change scope.** If something is missing or you want to add something, propose it and wait.

---

## 4. TECH STACK (fixed)

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Django, Django REST Framework |
| Auth | Django-managed users. JWT via SimpleJWT, stored in **httpOnly cookies** (not readable by browser scripts). Optional Google login later. Do **not** use Supabase Auth. |
| Database | **PostgreSQL on Supabase** (used only as managed Postgres via `DATABASE_URL`). Use transactions and row-level locking. Check Supabase connection pooler mode compatibility with Django (persistent connections). |
| File storage | Supabase Storage (banners, generated PDFs) behind a storage abstraction |
| Background jobs | Celery with Redis (emails, PDF generation, hold expiry cleanup) |
| PDF | WeasyPrint (ticket designed in HTML/CSS). Note its system dependencies in the deployment docs. |
| QR | Python `qrcode` library (or `segno`), embedded in the PDF |
| Email | Transactional provider (Brevo, Resend, or SendGrid) sending from the platform address. Do not use a personal mailbox over SMTP. |
| API docs | `drf-spectacular` (OpenAPI/Swagger) |
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS, deployed to **Vercel** |
| Frontend libs | React Hook Form + Zod (forms, including the dynamic organizer form), a camera-based QR scanner library, a chart library for the dashboard, Radix UI or shadcn/ui as the headless component base (restyled to the Ticketé look in section 7A), `next/font` for fonts |
| Backend hosting | Render, Railway, Fly.io, or a VPS, in a region close to Bangladesh. Not Vercel. |
| Testing | pytest + pytest-django (backend); Vitest/Jest + Playwright for key flows (frontend) |
| Quality | Ruff + Black (Python), ESLint + Prettier (frontend), pre-commit hooks |

The public event page **must be server-rendered** with proper Open Graph metadata so shared links show the banner, title, and description on Facebook and WhatsApp.

---

## 5. DATA MODEL

Follow the attached **ER Diagram**. Entities: `User`, `OtpCode`, `Event`, `EventFormField`, `TicketCategory`, `TeamMember`, `Invitation`, `Order`, `SeatHold`, `Payment`, `Ticket`, `CheckInLog`, `Notification`, `AuditLog`.

Non-negotiable data rules:

- Primary keys are UUIDs for public-facing records (Event, Order, Ticket).
- Unique constraints: `Event.slug`, `Order.order_number`, `Ticket.ticket_code`, `Ticket.qr_token`, `Invitation.token`, and `TeamMember(event_id, user_id)`.
- `Ticket.ticket_code` is short and human-friendly (typed at the gate). `Ticket.qr_token` is long and cryptographically random. **The QR must encode the secure token, never a sequential ID.**
- `Order.buyer_user_id` is nullable (guest). `Order.buyer_email` is always filled. `Ticket.recipient_email` differs from `buyer_email` for gifts.
- Custom form definitions live in `EventFormField`; answers live in `Order.custom_answers` (JSON). Attendee names live on `Ticket.attendee_name`.
- Add database indexes for lookups by slug, token, ticket code, event, and status.

---

## 6. CRITICAL BUSINESS RULES (must be implemented exactly)

1. **No overselling.** Availability per category = `seat_limit - sold - active holds`. The check and the hold creation happen inside **one database transaction with row locking** (`select_for_update`). Write a concurrency test that fires parallel purchases for the last seats.
2. **Seat hold:** 10 minutes while the buyer is on the payment step. Expired holds release automatically (scheduled job plus a lazy check on read).
3. **Single-use tickets.** Check-in is an **atomic conditional update** (valid -> used). Two simultaneous scans of the same ticket: exactly one succeeds; the other returns "Already used at HH:MM by <scanner>". Every scan attempt, including failed ones, is written to `CheckInLog`.
4. **Per-buyer limit:** maximum tickets per order, set by the organizer.
5. **Sales window:** sales start and end times are separate from the event time. Outside the window, purchase is blocked.
6. **Event lifecycle:** Draft -> Pending approval -> Approved or Rejected (rejected can be edited and resubmitted) -> On sale -> Sales closed -> Event ended -> Report ready.
7. **Ticket lifecycle:** Held -> Valid -> Used, or Cancelled.
8. **Email and PDF generation run in the background** (Celery), with retries. The buyer must not wait for them during checkout. The confirmation page still offers a direct download.
9. **Find my ticket:** guests retrieve tickets using email plus an emailed OTP, and can request a resend.
10. **Permissions (per event):**

| Action | Admin | Owner | Manager | Scanner | Viewer |
|---|---|---|---|---|---|
| Approve/reject event | Yes | No | No | No | No |
| Edit event | No | Yes | Yes | No | No |
| Manage team | No | Yes | No | No | No |
| View dashboard/report | Yes | Yes | Yes | No | Yes |
| Check-in tickets | No | Yes | Yes | Yes | No |
| View attendee list | Yes | Yes | Yes | Scan result only | No |

11. **Privacy:** buyer data is visible only to that event's team and admins.
12. **Invitations:** email link with expiring token (7 days), must be accepted; the Owner can change a role or revoke access any time.

---

## 7. FEATURE SCOPE

Build everything marked **MVP** in the Features List. Tag work as MVP, V2, or Later in the task breakdown.

- **MVP:** authentication (organizer, buyer, guest), event form builder with categories and custom fields, admin approval with notifications, public event page, guest/login checkout, seat hold, gifting, dummy payment with OTP, ticket and QR generation, ticket PDF, email delivery, find-my-ticket, scanner page (QR plus manual entry), single-use check, live attendance count, team invitations and roles, dashboard charts, final report, rate limiting, image validation.
- **V2 (only after MVP is accepted):** Google login, CSV export, report as PDF, offline attendee list, edit-after-approval rules with holder notifications, order history, activity trail, audit log views, suspend event/organizer.
- **Later:** promo codes, waitlist, duplicate event, real payment gateway.
- **Out of scope:** refunds, payouts, fees, native apps, reserved seat maps.

### Ticket PDF design (fixed)
One page per ticket. Header with platform logo and event name; event banner; details block (date and time in Asia/Dhaka, venue, category, attendee name if collected); identity block (ticket ID, order number, "X of Y"); large QR (minimum 35 mm) labeled "Scan at entry"; footer with a one-use notice, organizer contact, and platform support email. Before building the PDF module, show me an HTML mock-up of the design for approval.

### Scanner page
Mobile-first web page using the phone camera. Result screen: **green** for valid; **red** with a clear reason for already used, invalid, wrong event, or cancelled. Show attendee name and category. Show the live checked-in count. Include manual ticket ID entry as a fallback.

### Dashboard (MVP charts)
Tickets sold over time, sales by category, revenue, check-in progress.

---

## 7A. DESIGN, BRANDING AND UI STYLE

The platform must look bold, playful, modern, and clearly "ticket-themed", with a **white background and our vivid brand blue**. The visual references are attached as screenshots. Use them as **style inspiration only**.

### 7A.1 Brand identity (source of truth)

- **Name:** Ticketé (the "é" is part of the name; keep the accent everywhere: logo, titles, emails, PDF).
- **Logo files:** `1.png` stacked (icon above the wordmark), `2.png` horizontal (icon left, wordmark right), `3.png` icon only. All are 2000x2000 transparent PNGs with a lot of empty padding. **Crop them to their content**, export web-sized versions, and ask me for SVG versions if sharper output is needed.
- **Logo usage:**
  - Navbar and email header: horizontal logo (`2.png`).
  - Footer, login/registration pages, empty states: stacked logo (`1.png`).
  - Favicon, app icon, loading spinner, QR center decoration: icon only (`3.png`).
  - Ticket PDF header: horizontal logo.
  - Keep clear space around the logo equal to the height of the dot-circles in the icon. Never recolor, stretch, rotate, add shadows to, or place it on a busy or low-contrast background.
- **Wordmark:** an elegant high-contrast display serif in black with the final "É" in brand blue. Do not redraw it. For headings, use a similar Google serif (see typography).

### 7A.2 Color palette

The brand blue was taken directly from the logo. Define all colors as design tokens (CSS variables plus the Tailwind theme). Do not hard-code hex values in components.

| Token | Hex | Use |
|---|---|---|
| `brand-500` (primary) | **#4E53FF** | Primary buttons, links, active states, key accents, chart primary series |
| `brand-700` (deep) | #3838B8 | Hover/pressed state, the darker shape of the logo, shadows on blue elements |
| `brand-100` (tint) | #E8E9FF | Soft backgrounds, selected rows, badges |
| `brand-50` (wash) | #F5F5FF | Section backgrounds, table zebra rows |
| `background` | #FFFFFF | Page background (default) |
| `ink` (text) | #0A0A14 | Headings, body text, borders, hard shadows (near-black, matches the wordmark) |
| `muted` | #5B5F73 | Secondary text |
| `line` | #E3E4EC | Light dividers (use ink borders for the chunky style, see 7A.4) |
| `success` | #12B76A | Valid ticket, paid, approved, "Sold" progress |
| `warning` | #F5A524 | Pending approval, low stock ("Few left"), seat hold timer |
| `danger` | #E5484D | Already used, invalid, failed payment, rejected |
| `highlight` | #FFD43B | Small sticker accents only (e.g., "New", "Few left" tags); use sparingly |
| `pink-accent` | #FF5FA2 | Optional tiny accent dots and one-off decorations only |

Rules:
- White is the dominant background. Blue is the hero color; use it for roughly 10 to 20 percent of any screen. Support colors appear only where they carry meaning (status) or as small decoration.
- **Contrast:** white text on #4E53FF and #4E53FF text on white both pass WCAG AA for normal text (about 5.2:1). **Do not** put small blue text on black or on dark backgrounds (it fails). Check all status colors on their backgrounds.
- Dark mode is not needed in this version. The scanner page may use a dark high-contrast layout (see 7A.6).

### 7A.3 Typography

- **Display and headings:** an elegant serif with an italic style (for example **Playfair Display** or **Fraunces**), in `ink`, with one emphasized word per heading in italic brand blue, for example "Your next *Event*." This matches the wordmark and the editorial feel of the Film and Photography Club reference.
- **Body and UI:** a clean geometric or neo-grotesque sans (for example **Inter** or **Space Grotesk**).
- **Labels, step numbers, small pills, ticket IDs, and prices in tickets:** a monospace (for example **JetBrains Mono** or **Space Mono**) in uppercase with wide letter spacing, like the labels "04 · WHAT CAN YOU BUILD" in the GP FutureMakers reference.
- Load fonts with `next/font` (no layout shift). Support Bangla later: choose fonts and spacing that can fall back to a Bangla font such as Noto Sans Bengali.
- Type scale: large and confident on public pages (hero headings 48 to 72 px desktop, 32 to 40 px mobile). Body 16 px minimum.

### 7A.4 Visual style (what "looks like the reference" means)

The overall style is **playful neo-brutalism combined with editorial serif typography and ticket motifs**:

- **Floating pill navbar:** rounded, white, 2 px `ink` border, centered with margin from the top, small hard shadow, with the logo on the left, links in the center, and one primary action (Log in / Create event) on the right. Becomes a compact menu on mobile.
- **Chunky outlined cards:** white cards, 2 px `ink` border, 16 to 20 px radius, and a **hard offset shadow** (for example `4px 4px 0 0 ink`) instead of soft blur shadows. Hover: the card lifts by moving 2 px up-left while the shadow grows slightly.
- **Buttons:** primary = `brand-500` fill, white bold text, 2 px `ink` border, hard shadow; on hover the shadow shrinks, on press the button moves into the shadow. Secondary = white fill with ink border. Destructive = `danger`. All buttons have a visible focus ring.
- **Small pill labels:** rounded outlined pills with mono uppercase text and a number prefix (for example "01 · UPCOMING EVENTS") above section headings.
- **Section numbering and little detail dots:** three tiny colored dots (brand blue, highlight, pink-accent) in card corners, as in the GP FutureMakers cards; use consistently but sparingly.
- **Subtle patterns:** faint dotted background pattern in `brand-50` areas; optional scrolling marquee strip of event categories under the navbar on the landing page.
- **Sticker/ribbon accents:** slightly rotated tag labels ("Prompt your future" style) for highlights like "Selling fast" or "Free entry". Max one or two per screen.
- **Ticket motif (our signature):** the key shape of the platform is a **ticket**: rectangle with semicircle notches on the left and right edges, a dashed perforation line, and a stub on the right with "ADMIT ONE" and a barcode-like strip (as in the CSE-UAP reference). Use it for event cards, the ticket selection list, the confirmation page, the "My ticket" view, and the PDF.
- **Illustration and imagery:** use event banners as the main imagery. For empty states and decoration, use simple original flat illustrations or 3D-style icons that match the brand (tickets, QR codes, stars, sparkles). Do not use copyrighted mascots, characters, or stock props from the reference sites.
- **Motion:** light and purposeful (card lift, button press, fade/slide on scroll, a countdown tick on the seat-hold timer). Respect `prefers-reduced-motion`. No heavy animation on checkout or scanner screens.
- **Corners and spacing:** generous whitespace, consistent 8 px spacing scale, 16 to 24 px card radii, pills fully rounded.

### 7A.5 Reference sites: what to take from each (and what not to)

**GP FutureMakers (reference 1 and 2, the green playful campaign site):** take the floating pill navbar, chunky outlined cards with hard shadows, numbered mono pills, colored detail dots, big bold heading with a punchy sticker tag, dotted background, and the friendly floating help button (bottom-right; here it can open a simple FAQ/support panel). **Do not use** its lime green background, its colors, its mascot, 3D characters, tagline, or any text or images.

**CSE-UAP Film and Photography Club (reference 3 and 4):** take the elegant serif headings with an italic accent word, the ticket-shaped manifesto card with perforated stub and barcode, the stats cards row (for example "120+ events", "5,000 tickets sold"), the contact section with icon rows, and the scroll-to-top button. **Do not use** its dark red/cream palette, popcorn and camera imagery, or its text.

**Our own identity:** white background, **#4E53FF** brand blue, near-black ink, serif plus mono typography, and the ticket motif everywhere. If a reference color or style conflicts with the brand palette, the brand palette wins.

All reference material is for inspiration. Do not copy another site's code, images, logos, mascots, or wording.

### 7A.6 Screen-by-screen design direction

Public pages use the full expressive style. **Organizer and admin dashboards use the same components but a calmer layout** (less decoration, more density, clear data) so they stay readable. The scanner is functional first.

1. **Landing page:** hero with a large serif headline ("Sell tickets. Fill the *room*." or similar), a primary "Create your event" button and a secondary "Browse events" button, ticket-shaped floating cards as decoration, a marquee strip, a "How it works" section in 3 to 4 numbered chunky cards (Create, Get approved, Sell, Scan), a stats row, featured events, FAQ, and a footer with the stacked logo.
2. **Events listing:** grid of **ticket-shaped event cards** (banner, date badge, venue, "from BDT X", "Few left" or "Sold out" sticker), search, and filters (date, category).
3. **Public event page (server-rendered):** large banner, title in serif, date/time/venue chips, description, a **ticket category list** where each category is a ticket-shaped row with price, remaining seats, and a quantity stepper, and a sticky summary card on desktop / sticky bottom bar on mobile with the total and a "Get tickets" button. Must also have strong Open Graph share images.
4. **Checkout:** a clear 4-step progress bar (Tickets, Details, Payment, Done). Step 2 shows the guest vs login choice as two large selectable cards, email field (prefilled when logged in), gifting toggle with the recipient email, attendee name fields (Attendee 1, Attendee 2...), and custom fields. A visible **10-minute hold countdown** (warning color when under 2 minutes). Step 3: payment provider tiles (bKash, Nagad, etc. as neutral dummy tiles; do not use official logos), phone number, then a 6-digit OTP input with resend timer.
5. **Confirmation page:** success state with a ticket-shaped card per ticket (with QR), a download PDF button, an "email sent to ..." note, and a gift receipt line when gifted.
6. **Find my ticket:** simple two-step form (email, then OTP) using the same chunky cards.
7. **Organizer dashboard:** left sidebar or top tabs (Overview, Tickets, Orders, Team, Form, Settings), summary stat cards, charts (tickets sold over time, sales by category, revenue, check-in progress), and tables. Charts use `brand-500` as the primary series with a defined categorical palette built from the tokens; always include labels and do not rely on color alone.
8. **Event creation form:** multi-step form (Details, Tickets, Form fields, Review). Live preview of the public ticket card on the right on desktop. Clear validation messages. Status chip showing Draft / Pending / Approved / Rejected with the status colors.
9. **Admin approval queue:** clean table plus a review drawer with the full event preview and approve / reject buttons (rejection requires a reason).
10. **Scanner page (mobile-first, functional first):** full-screen camera view with a large result panel. **Valid = full green screen state** with attendee name and category; **Invalid/used/cancelled = full red screen state** with the reason, who scanned it, and when. Large touch targets, sound/vibration feedback optional, manual ticket ID input at the bottom, and a visible live count (checked in / total). High contrast; minimal decoration.
11. **Emails:** white background, horizontal logo at the top, brand-blue button, ticket summary block, footer with support address. Plain-text fallback included.
12. **Error, empty, and loading states:** friendly short messages with simple illustrations; skeleton loaders in `brand-50`.

### 7A.7 Ticket PDF styling (extends section 7 PDF spec)

- White page with a thick `ink` outline and rounded ticket shape, semicircle notches and a dashed perforation separating the main part and the **stub**.
- Header: horizontal logo and event name in the display serif. Brand-blue accent bar. Banner image below.
- Details in mono uppercase labels with values in the sans font. Category shown as a blue pill.
- The **QR sits on the stub** with a white quiet zone (do not place logos or colors over it). Keep high contrast: **QR modules in pure black on white**, not blue, so any scanner reads them reliably.
- Footer: one-use notice and support email in small muted text.
- Show me the HTML mock-up for approval before building the PDF module (also checks that fonts embed correctly in WeasyPrint).

### 7A.8 Implementation requirements for the design

- Build a small **design system** in the frontend first (Phase 0): tokens, typography, buttons, inputs, cards, ticket card, pill label, badge, modal/drawer, toast, table, stepper, empty state, skeleton. Document it in `docs/10-design-system.md`. Use Tailwind with the tokens above, and a headless component base such as Radix UI or shadcn/ui, restyled to this look.
- **Responsive and mobile-first:** design for 360 px first. Breakpoints for tablet and desktop. The checkout and scanner must be comfortable on small phones.
- **Accessibility:** WCAG AA contrast, visible focus states (do not remove outlines), labeled fields, keyboard navigation for forms and dialogs, semantic HTML, alt text on banners, reduced-motion support. Hard shadows and borders must not be the only way to show state.
- **Performance:** optimized images with `next/image`, fonts via `next/font`, avoid heavy animation libraries on checkout, target good Lighthouse scores (performance and accessibility 90+ on the public event page).
- Provide a Storybook or a simple `/design` internal page showing all components for review.
- At the end of each phase, show me screenshots of the new screens (mobile and desktop) for design approval.

---

## 8. BUILD PHASES (stop for my review after each)

| Phase | Scope | Done when |
|---|---|---|
| 0 | Repo setup, docs skeleton, tooling, CI, environment config, Supabase connection, local run instructions, **brand assets and design system (tokens, core components, landing page shell)** | Both apps run locally; README steps work from a clean machine; I have approved the look on mobile and desktop |
| 1 | Auth, event form + categories + custom fields, admin approval + notifications, public event page (SSR + share preview) | An event can be created, approved, and viewed via its link |
| 2 | Seat hold, order, dummy payment + OTP, ticket + QR, PDF, background email, confirmation page, gifting, find-my-ticket | A guest and a logged-in user can both buy and receive a valid PDF |
| 3 | Scanner, single-use check, check-in log, team invitations and roles | An event can run on the day with several volunteers |
| 4 | Dashboard charts, final report, hardening, performance and security pass, deployment | Production deployment works end to end |
| 5 | V2 items (separate approval) | As agreed |

---

## 9. SECURITY AND QUALITY REQUIREMENTS

- Password hashing with Django defaults (Argon2 preferred). Email verification before an organizer can submit an event.
- JWT in httpOnly, Secure, SameSite cookies; CSRF protection configured correctly; strict CORS (frontend origin only).
- **Rate limiting** on login, OTP, purchase, and find-my-ticket endpoints.
- Validate uploads: banner type (JPEG/PNG/WebP) and size limit; re-encode images.
- Permission checks on **every** endpoint and object (event-scoped roles). Add tests that prove a Scanner cannot view reports and a user cannot access another event's data.
- Never expose `qr_token`, other buyers' data, or internal IDs unnecessarily in public responses.
- Secrets only in environment variables. Provide `.env.example` files. Never commit secrets.
- Server-side validation for everything; the frontend validation is only for convenience.
- Structured logging and error tracking hooks; an audit log for admin actions.
- Tests: unit tests for business rules, integration tests for the full purchase flow, and **concurrency tests** for seat holds and double scanning. Target at least 80 percent coverage on the orders, tickets, and check-in apps.
- Accessibility basics: labeled fields, good contrast, keyboard-friendly forms. The UI is mobile-first and English only for now (design text so Bangla can be added later).

---

## 10. API AND CODE CONVENTIONS

- REST API under `/api/v1/`, versioned, documented with OpenAPI. Consistent error format: `{ "error": { "code": "...", "message": "...", "fields": {...} } }`.
- Pagination and filtering on list endpoints.
- Keep business logic in service modules (not in views or serializers). Keep views thin.
- Payment gateway interface: `initiate(order)`, `verify_otp(payment, otp)`, `status(payment)`. The dummy provider implements it; settings choose the active provider.
- Storage abstraction: one interface, with Supabase Storage as the implementation.
- Frontend: typed API client generated from or aligned with the OpenAPI schema; reusable components; no business rules duplicated in the UI beyond display and validation.
- Write clear docstrings and comments only where logic is not obvious.

---

## 11. DEPLOYMENT

- **Frontend:** Vercel, Root Directory = `frontend`, environment variables for the API base URL.
- **Backend + Celery worker + Redis:** Render, Railway, Fly.io, or a VPS near Bangladesh, deployed from the `backend` folder. Include a Dockerfile (with WeasyPrint dependencies) and the process commands for web and worker.
- **Database and storage:** Supabase (use a paid plan for real events; free projects can pause).
- **Email:** verified sender domain (SPF/DKIM) for the platform address.
- Document everything in `docs/08-deployment.md`: environments (local, staging, production), environment variables, migration and rollback steps, backup plan.

---

## 12. DELIVERABLES

1. Working code in the monorepo, organized as in section 2.
2. All documents in `docs/`, kept current (including the changelog and decision records).
3. README files that let a new developer run everything from scratch in under 15 minutes.
4. Seed script with demo data: one admin, one organizer, one approved event with three categories, sample orders and tickets.
5. Test suite passing, including the concurrency tests.
6. A short demo script showing the full flow: create event -> approve -> buy as guest -> receive PDF -> scan -> report.
7. A final review document listing what was built, known limitations, and suggestions for iteration.

---

## 13. DEFINITION OF DONE (every task)

A task is done only when: the code works; tests are added and passing; permissions are checked; errors are handled with clear messages; docs and changelog are updated; **any UI follows the design tokens and components from section 7A (no hard-coded colors), is checked on a 360 px phone and on desktop, and passes the accessibility basics**; and a short summary is given to me.

---

## 14. YOUR FIRST RESPONSE MUST CONTAIN

1. A 5 to 8 line summary of the project in your own words.
2. Any gaps, contradictions, or risks you found in the documents.
3. A numbered list of questions (mark which ones block you).
4. Your proposed **System Design outline** and **task breakdown** for Phase 0 and Phase 1.
5. Confirmation that you will use **one monorepo with `backend/` and `frontend/` folders** as specified.
6. Your reading of the **design direction** in section 7A: describe the style in your own words, list the design tokens you will create (colors from #4E53FF, fonts, radii, shadows), the font choices, and which component you will build first. Flag anything in the logos or screenshots that is unclear (for example, if SVG logos are needed).

Do not write application code until I approve step 4.
