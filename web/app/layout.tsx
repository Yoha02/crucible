import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Crucible",
  description: "Product-market fit wedge discovery dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
