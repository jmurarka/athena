import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATHENA - Agentic Product Planner & Systems Design Platform",
  description: "Automated Product Planning, Market Research, and Systems Design Canvas",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased font-sans">
      <body className="min-h-full flex flex-col bg-white text-slate-800">{children}</body>
    </html>
  );
}
