import { Brand } from "@/components/brand";
import { Pill } from "@/components/ui";

export const metadata = {
  title: "Ticket design preview",
  robots: { index: false, follow: false },
};

export default function Page() {
  return (
    <main id="main" className="container account-page ticket-design-page">
      <Pill>DESIGN REVIEW · FICTIONAL SAMPLE</Pill>
      <h1>
        A little keepsake.
        <br />A great night ahead.
      </h1>
      <p className="ticket-preview-note">
        Proposed TICKETÉ ticket layout. One page per ticket in the eventual
        order PDF. This is a design sample, not an admission ticket.
      </p>
      <article className="ticket-design" aria-label="Proposed ticket design">
        <div className="ticket-design-main">
          <header className="ticket-design-header">
            <Brand />
            <span>YOUR MOMENT IS HERE</span>
          </header>
          <div className="ticket-design-banner">
            <span>LIVE MUSIC · DHAKA</span>
            <h2>
              Afterglow
              <br />
              <em>Sessions.</em>
            </h2>
            <p>A fictional event for design review</p>
            <span className="ticket-design-orbit" aria-hidden="true" />
          </div>
          <div className="ticket-design-details">
            <Pill>GENERAL ADMISSION</Pill>
            <dl>
              <div>
                <dt>WHEN · ASIA/DHAKA</dt>
                <dd>
                  21 November 2026
                  <br />
                  6:00 PM – 10:00 PM
                </dd>
              </div>
              <div>
                <dt>WHERE</dt>
                <dd>
                  Sample Hall
                  <br />
                  Dhaka, Bangladesh
                </dd>
              </div>
              <div>
                <dt>ATTENDEE · OPTIONAL</dt>
                <dd>Samira Rahman</dd>
              </div>
              <div>
                <dt>ORDER NUMBER</dt>
                <dd className="ticket-mono">TE-SAMPLE-ORDER</dd>
              </div>
            </dl>
            <div className="ticket-design-identity">
              <span>TICKET ID</span>
              <strong>TE-SAMPLE-TICKET</strong>
              <span>1 OF 2</span>
            </div>
          </div>
          <footer className="ticket-design-footer">
            <p>One ticket. One entry. Keep your QR private.</p>
            <p>Organizer: organizer@example.com · Sample contact</p>
            <p>Platform support: hello.tickete@gmail.com</p>
          </footer>
        </div>
        <aside className="ticket-design-stub">
          <span className="ticket-stub-label">ADMIT ONE</span>
          <div className="ticket-qr-placeholder">
            <span>
              QR
              <br />
              reserved area
            </span>
            <small>
              35 mm minimum
              <br />
              Black on white
            </small>
          </div>
          <strong>Scan at entry</strong>
          <p>A unique, unobstructed QR will appear here in the final PDF.</p>
          <span className="ticket-sample-stamp">
            SAMPLE
            <br />
            NOT VALID
          </span>
          <span className="ticket-mono">1 / 2</span>
        </aside>
      </article>
      <p className="ticket-preview-note">
        The final version will use the actual event banner, title, venue,
        category, attendee name when provided, organizer contact and ticket
        identity. The QR placeholder will be replaced only when the PDF module
        is built after design approval.
      </p>
    </main>
  );
}
