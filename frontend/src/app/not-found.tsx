import { ButtonLink, Pill } from "@/components/ui";
export default function NotFound() {
  return (
    <main id="main" className="container inner-page">
      <Pill>404 · A LITTLE OFFSTAGE</Pill>
      <h1>
        This moment
        <br />
        is <em>somewhere else.</em>
      </h1>
      <p className="page-lead">
        We couldn’t find that page. Let’s take you back.
      </p>
      <ButtonLink href="/">Back to TICKETÉ</ButtonLink>
    </main>
  );
}
