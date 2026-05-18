import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: "Prithvi SEO Portal",
  description:
    "Standalone SEO auditing portal for Kedar Estate and PropOS.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
    >
      <body>
        <div className="flex">
          <Sidebar />
          <div className="flex h-screen flex-1 flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto px-6 py-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
