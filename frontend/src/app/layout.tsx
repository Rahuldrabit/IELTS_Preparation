import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { MainLayout } from "@/components/layout/MainLayout";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { MediaPipePreloader } from "@/components/providers/MediaPipePreloader";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI IELTS Tutor - Your Personal Learning Mentor",
  description: "An AI-powered IELTS Learning Operating System that acts as a personal mentor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}>
        <QueryProvider>
          <ThemeProvider>
            <MediaPipePreloader />
            <MainLayout>{children}</MainLayout>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}