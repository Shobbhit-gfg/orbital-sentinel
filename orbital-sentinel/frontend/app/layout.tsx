import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ORBITAL SENTINEL",
  description: "Deterministic space situational awareness screening console",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
