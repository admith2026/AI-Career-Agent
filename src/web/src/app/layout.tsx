import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Career Agent — Global Career Intelligence Platform',
  description: 'AI-powered platform that discovers, analyzes, and auto-applies to ALL technical roles across the US.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-navy-950 font-[Inter]">{children}</body>
    </html>
  );
}
