import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YOUI – You Intelligence",
  description: "A personal AI based on your needs and verticals",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
