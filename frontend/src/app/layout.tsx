import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ReactQueryProvider } from "@/lib/react-query";
import { AuthProvider } from "@/contexts/auth-context";
import { OnboardingProvider } from "@/contexts/onboarding-context";
import { CreatorProvider } from "@/contexts/creator-context";
import { DemoModeProvider } from "@/contexts/demo-mode-context";
import { ErrorBoundaryWrapper } from "@/components/error-boundary";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "UATP Capsule Engine",
  description: "Civilization-grade AI attribution infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ReactQueryProvider>
          <ErrorBoundaryWrapper>
            <DemoModeProvider>
              <AuthProvider>
                <CreatorProvider>
                  <OnboardingProvider>
                    {children}
                  </OnboardingProvider>
                </CreatorProvider>
              </AuthProvider>
            </DemoModeProvider>
          </ErrorBoundaryWrapper>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
