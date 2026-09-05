import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "Anxin (安心) -- Gonka-verified scam & misinformation checker",
  description:
    "A bilingual English/Simplified Chinese scam and misinformation checker, cross-verified by two independent AI models on the Gonka decentralized network.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
