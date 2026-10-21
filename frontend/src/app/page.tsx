import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Heart,
  ScanLine,
  Ticket,
  Users,
  WandSparkles,
} from "lucide-react";
import { ButtonLink, Pill } from "@/components/ui";
import { HeroTicket } from "@/components/hero-ticket";

const steps = [
  {
    number: "01",
    icon: WandSparkles,
    title: "Dream it up.",
    text: "A concert, a workshop, a whole new idea. Give your event a place to call home.",
  },
  {
    number: "02",
    icon: Ticket,
    title: "Make it official.",
    text: "Get your event reviewed, share your link, and invite the world. Or just your people.",
  },
  {
    number: "03",
    icon: ScanLine,
    title: "Let the good in.",
    text: "A ticket on your phone. A scan at the door. More time for the moment itself.",
  },
];
const faqs = [
  [
    "What is TICKETÉ?",
    "TICKETÉ is an upcoming ticketing platform for events in Bangladesh, from campus gatherings and workshops to concerts and cultural celebrations.",
  ],
  [
    "Can I buy tickets right now?",
    "You can explore approved events and try checkout. Payments are currently simulated; no money is charged.",
  ],
  [
    "Will I need an account to buy a ticket?",
    "You can check out with your email as a guest, or sign in to have it filled in for you.",
  ],
  [
    "Can I send a ticket as a gift?",
    "Yes. Enter your recipient’s email at checkout: they’ll receive the tickets, and you’ll receive a receipt.",
  ],
];
export default function Home() {
  return (
    <main id="main">
      <section className="hero container">
        <div className="hero-copy">
          <Pill>
            <span className="blue-dot" /> BIG MOMENTS START SMALL
          </Pill>
          <h1>
            Your people.
            <br />
            Your thing.
            <br />
            Your next <em>moment.</em>
          </h1>
          <p>
            The music you feel. The ideas you share. The nights you remember.
            Find your way there with TICKETÉ.
          </p>
          <div className="hero-actions">
            <ButtonLink href="/events">
              Find your next event <ArrowUpRight size={20} />
            </ButtonLink>
            <a className="text-link" href="#how-it-works">
              See how it works <ArrowDown size={17} />
            </a>
          </div>
          <div className="hero-footnote">
            <span className="mini-icon">
              <Heart size={16} />
            </span>
            <span>Made for Bangladesh. Made for being there.</span>
          </div>
        </div>
        <HeroTicket />
      </section>
      <div className="category-strip" aria-label="Event possibilities">
        <div className="marquee-track">
          {[0, 1].map((copy) => (
            <div
              className="marquee-group"
              key={copy}
              aria-hidden={copy === 1 ? true : undefined}
            >
              {[
                "LIVE MUSIC",
                "CAMPUS CULTURE",
                "NEW IDEAS",
                "CREATIVE PEOPLE",
                "GOOD TIMES",
              ].map((item) => (
                <span key={item}>
                  {item}
                  <span className="strip-star" aria-hidden="true">
                    ✳
                  </span>
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
      <section className="section container" id="how-it-works">
        <div className="section-heading">
          <div>
            <Pill>01 · FROM IDEA TO ENCORE</Pill>
            <h2>
              A little less hassle.
              <br />A lot more <em>happening.</em>
            </h2>
          </div>
          <p>
            For the ones making it happen.
            <br />
            And everyone who wants to be there.
          </p>
        </div>
        <div className="steps-grid">
          {steps.map(({ number, icon: Icon, title, text }) => (
            <article className="card step-card" key={number}>
              <div className="step-top">
                <span className="mono">/ {number}</span>
                <Icon size={25} strokeWidth={1.6} />
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
              <div className="detail-dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="organizer-section container" id="for-organizers">
        <div className="organizer-card">
          <div className="organizer-copy">
            <Pill>02 · YOUR CROWD IS OUT THERE</Pill>
            <h2>
              You bring the idea.
              <br />
              We’ll bring the <em>tickets.</em>
            </h2>
            <p>
              From your first campus meetup to a night that fills the room. Give
              your next big thing a simple way in.
            </p>
            <ul className="feature-list">
              <li>
                <Check size={18} /> Your event. Your ticket categories.
              </li>
              <li>
                <Check size={18} /> A shareable link for your whole community.
              </li>
              <li>
                <Check size={18} /> Less time at the gate. More time in the
                moment.
              </li>
            </ul>
            <ButtonLink href="/start">
              Let’s make it happen <ArrowUpRight size={20} />
            </ButtonLink>
          </div>
          <div className="organizer-art" aria-hidden="true">
            <div className="mini-ticket">
              <span className="mono">ONE IDEA. ENDLESS POSSIBILITIES.</span>
              <Users size={64} strokeWidth={1} />
              <span className="serif">
                Your event.
                <br />
                <em>Your people.</em>
              </span>
              <div className="mini-perforation" />
              <span className="mono">GOOD THINGS HAPPEN TOGETHER</span>
            </div>
            <span className="organizer-sticker">
              SAVE
              <br />
              THE DATE!
            </span>
            <span className="organizer-spark">✳</span>
          </div>
        </div>
      </section>
      <section className="section container faq-section" id="faq">
        <div>
          <Pill>03 · GOOD QUESTIONS</Pill>
          <h2>
            A few things
            <br />
            you might <em>wonder.</em>
          </h2>
          <p className="muted">A little clarity before the curtain goes up.</p>
        </div>
        <div className="faq-list">
          {faqs.map(([q, a]) => (
            <details key={q}>
              <summary>
                {q}
                <ChevronDown size={20} aria-hidden="true" />
              </summary>
              <p>{a}</p>
            </details>
          ))}
        </div>
      </section>
      <section className="closing-band">
        <div className="container">
          <span className="mono">LESS SCROLLING. MORE SHOWING UP.</span>
          <h2>
            Life happens <em>out there.</em>
          </h2>
          <ButtonLink href="/events" variant="secondary">
            Be there for it <ArrowRight size={20} />
          </ButtonLink>
        </div>
      </section>
    </main>
  );
}
