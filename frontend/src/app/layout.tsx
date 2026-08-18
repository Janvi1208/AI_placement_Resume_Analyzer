import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Placement Readiness Analyzer",
  description:
    "Know exactly how ready you are for your next job. AI-powered resume and job-description analysis.",
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
