"use client";
import Link from "next/link";
import * as Dialog from "@radix-ui/react-dialog";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useState } from "react";
import { Brand } from "./brand";
import { ButtonLink } from "./ui";

const links = [
  { href: "/events", label: "Explore events" },
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#for-organizers", label: "For organizers" },
  { href: "/account", label: "My account" },
];
export function Navigation() {
  const [open, setOpen] = useState(false);
  return (
    <header className="nav-wrap">
      <nav className="navbar" aria-label="Main navigation">
        <Link href="/" aria-label="TICKETÉ home">
          <Brand />
        </Link>
        <div className="nav-links">
          {links.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </div>
        <div className="nav-action">
          <ButtonLink href="/start">
            Create an event <ArrowUpRight size={17} aria-hidden="true" />
          </ButtonLink>
        </div>
        <Dialog.Root open={open} onOpenChange={setOpen}>
          <Dialog.Trigger
            className="icon-button mobile-menu"
            aria-label="Open navigation"
          >
            <Menu />
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="dialog-overlay" />
            <Dialog.Content className="dialog-panel menu-panel">
              <Dialog.Title className="dialog-title">
                Find your next moment.
              </Dialog.Title>
              <Dialog.Description className="muted">
                Explore TICKETÉ
              </Dialog.Description>
              <Dialog.Close
                className="icon-button dialog-close"
                aria-label="Close navigation"
              >
                <X />
              </Dialog.Close>
              <div className="mobile-links">
                {links.map((link) => (
                  <Link
                    onClick={() => setOpen(false)}
                    key={link.href}
                    href={link.href}
                  >
                    {link.label}
                    <ArrowUpRight size={20} />
                  </Link>
                ))}
                <ButtonLink href="/start">
                  Create an event <ArrowUpRight size={18} />
                </ButtonLink>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </nav>
    </header>
  );
}
