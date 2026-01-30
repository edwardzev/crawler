import type { Metadata } from "next";
import { Heebo, Assistant } from "next/font/google";
import "./globals.css";
import { OrderSummary } from "@/components/OrderSummary";
import { ToastProvider } from "@/lib/contexts/ToastContext";

const heebo = Heebo({
  variable: "--font-heebo",
  subsets: ["hebrew", "latin"],
});

const assistant = Assistant({
  variable: "--font-assistant",
  subsets: ["hebrew", "latin"],
});

const baseUrl = (process.env.NEXT_PUBLIC_BASE_URL || "https://example.com").replace(/\/$/, "");

export const metadata: Metadata = {
  title: "קטלוג מוצרים",
  description: "קטלוג מוצרים לספקים",
  metadataBase: new URL(baseUrl),
  openGraph: {
    type: "website",
    siteName: "קטלוג מוצרים",
    locale: "he_IL",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="he" dir="rtl">
      <body
        className={`${heebo.variable} ${assistant.variable} antialiased font-sans`}
      >
        <ToastProvider>
          {children}
          <OrderSummary />
        </ToastProvider>
      </body>
    </html>
  );
}
