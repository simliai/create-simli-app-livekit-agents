import type { Metadata } from "next";
import { abcRepro, abcReproMono } from "./fonts/fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "Simli App",
  description: "create-simli-app (LiveKit Agents)",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${abcRepro.variable} ${abcReproMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
