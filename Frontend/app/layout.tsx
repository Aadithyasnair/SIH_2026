import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "SIH26146 | Bitcoin Transaction Monitor", description: "Offline Bitcoin transaction monitoring dashboard" };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
