import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "why machine",
  description:
    "Ask Claude \"why?\" until you reach a first-principles answer. Inspired by @jen_spies.",
  openGraph: {
    title: "why machine",
    description: "Ask Claude \"why?\" until you reach bedrock.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
