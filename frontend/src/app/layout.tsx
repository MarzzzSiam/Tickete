import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});
const display = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  style: ["normal", "italic"],
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});
export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL || "http://127.0.0.1:3000"),
  title: {
    default: "TICKETÉ — Your next unforgettable moment",
    template: "%s | TICKETÉ",
  },
  description:
    "A new home for live experiences in Bangladesh. Discover what moves you, bring your people, and make it a moment.",
  openGraph: {
    title: "TICKETÉ — Little tickets. Big moments.",
    description: "Your next unforgettable moment starts here.",
    locale: "en_BD",
    type: "website",
    images: [
      {
        url: "/brand/horizontal.png",
        width: 2000,
        height: 2000,
        alt: "TICKETÉ",
      },
    ],
  },
  robots: { index: false, follow: false }, // Preview only; revisit before production launch.
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body
        className={`${inter.variable} ${display.variable} ${mono.variable}`}
      >
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <Navigation />
        {children}
        <Footer />
      </body>
    </html>
  );
}
