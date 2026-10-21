import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Brand } from "./brand";

export function Footer() {
  return (
    <footer className="footer container">
      <div className="footer-main">
        <div>
          <Link href="/" aria-label="TICKETÉ home">
            <Brand stacked />
          </Link>
          <p>Little tickets. Unforgettable moments.</p>
        </div>
        <div>
          <span className="eyebrow">Make a little history</span>
          <Link href="/events">
            Explore events <ArrowUpRight size={16} />
          </Link>
          <Link href="/start">
            Become an organizer <ArrowUpRight size={16} />
          </Link>
          <Link href="/find-my-ticket">
            Find my ticket <ArrowUpRight size={16} />
          </Link>
          <Link href="/#faq">
            A few answers <ArrowUpRight size={16} />
          </Link>
        </div>
        <div className="footer-note">
          <span className="little-star" aria-hidden="true">
            ✳
          </span>
          <p>
            Made for the moments
            <br />
            that bring Bangladesh together.
          </p>
          <span className="mono">DHAKA, BD · UTC +06:00</span>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} TICKETÉ. All moments welcome.</span>
        <span className="mono">A NEW EXPERIENCE IS TAKING SHAPE</span>
      </div>
    </footer>
  );
}
