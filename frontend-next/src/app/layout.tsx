import type { Metadata, Viewport } from "next";
import { Be_Vietnam_Pro, Lora } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/header";
import Footer from "@/components/footer";
import PwaRegister from "@/components/pwa-register";
import SiteBackground from "@/components/site-background";

const SITE_URL = "https://hoa-tien-ai-assistant-nu.vercel.app";

const beVietnamPro = Be_Vietnam_Pro({
  variable: "--font-sans",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700", "800"],
});

const lora = Lora({
  variable: "--font-serif",
  subsets: ["latin", "vietnamese"],
  weight: ["500", "600"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Hòa Tiến AI · Trợ lý hành chính số",
    template: "%s · Hòa Tiến AI",
  },
  description:
    "Trợ lý hành chính số xã Hòa Tiến (TP Đà Nẵng): hỏi thủ tục bằng tiếng Việt tự nhiên, nhận hướng dẫn hồ sơ kèm nguồn và mã QR nộp trực tuyến.",
  openGraph: {
    type: "website",
    title: "Hòa Tiến AI · Trợ lý hành chính số",
    description:
      "Hỏi thủ tục hành chính bằng tiếng Việt tự nhiên — trả lời kèm dẫn nguồn, hồ sơ cần chuẩn bị và mã QR nộp trực tuyến.",
    url: SITE_URL,
    locale: "vi_VN",
    images: ["/icons/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    images: ["/icons/og-image.png"],
  },
  icons: {
    icon: [
      { url: "/icons/icon.svg", type: "image/svg+xml" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/icons/icon-192.png",
  },
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#2f7d4f",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="vi"
      className={`${beVietnamPro.variable} ${lora.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <SiteBackground />
        <AuthProvider>
          <TooltipProvider>
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
            <PwaRegister />
          </TooltipProvider>
        </AuthProvider>
        {/* Phải là con TRỰC TIẾP của <body>: CSS @media print ẩn mọi anh em của nó. */}
        <div id="printArea" className="hidden" aria-hidden="true" />
      </body>
    </html>
  );
}
