import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Below the Line — How Money Shapes Power in Dallas",
  description:
    "An interactive atlas of the five-layer capital stack that directs public investment away from majority-Black and Hispanic communities south of I-30.",
  openGraph: {
    title: "Below the Line",
    description: "How money shapes power — Dallas displacement atlas",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
