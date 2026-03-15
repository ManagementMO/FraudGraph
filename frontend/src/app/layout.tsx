import type { Metadata } from "next";
import { Rajdhani, Fragment_Mono } from "next/font/google";
import "./globals.css";

const rajdhani = Rajdhani({
  weight: ['400', '500', '600', '700'],
  variable: "--font-ui",
  subsets: ["latin"],
});

const fragmentMono = Fragment_Mono({
  weight: '400',
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FraudGraph — Deep Space Surveillance",
  description: "Real-time fraud detection with multi-agent analysis and 3D graph visualization",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${rajdhani.variable} ${fragmentMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
