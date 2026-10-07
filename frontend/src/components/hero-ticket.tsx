import { ArrowUpRight, Sparkles } from "lucide-react";

export function HeroTicket() {
  return (
    <div
      className="ticket-scene"
      aria-label="Illustrative TICKETÉ ticket, not valid for entry"
    >
      <div className="orbit orbit-one" aria-hidden="true" />
      <div className="orbit orbit-two" aria-hidden="true" />
      <span className="scene-spark" aria-hidden="true">
        ✳
      </span>
      <div className="ticket-behind" aria-hidden="true">
        <span>YOU HAD TO BE THERE.</span>
      </div>
      <div className="hero-ticket">
        <div className="hero-ticket-main">
          <div className="ticket-top mono">
            <span>TICKETÉ PRESENTS</span>
            <ArrowUpRight size={22} />
          </div>
          <div className="ticket-art" aria-hidden="true">
            <span className="art-orbit art-orbit-a" />
            <span className="art-orbit art-orbit-b" />
            <span className="art-orbit art-orbit-c" />
            <span className="art-star">✧</span>
          </div>
          <div className="ticket-headline">
            Good times.
            <br />
            <em>Great company.</em>
          </div>
          <div className="ticket-bottom">
            <span className="mono">
              YOUR NEXT
              <br />
              UNFORGETTABLE MOMENT
            </span>
            <Sparkles size={26} />
          </div>
        </div>
        <div className="hero-ticket-stub">
          <span className="mono">ADMIT ONE</span>
          <div className="barcode" aria-hidden="true" />
          <span className="mono">SAMPLE · NOT FOR ENTRY</span>
        </div>
      </div>
      <div className="scene-sticker">
        <Sparkles size={17} /> MORE THAN A TICKET.
      </div>
      <div className="scene-caption mono">01 / THE START OF A GOOD STORY</div>
    </div>
  );
}
